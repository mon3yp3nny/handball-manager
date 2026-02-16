from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from typing import List, Optional

from app.core.deps import get_db, get_current_user, require_coach, require_coach_or_supervisor
from app.models.user import User, UserRole
from app.models.event import Event, EventType
from app.models.team import Team
from app.models.player import Player
from app.schemas.event import EventCreate, EventUpdate, EventResponse, EventWithTeam

router = APIRouter()


@router.get("/", response_model=List[EventResponse])
def get_events(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    team_id: Optional[int] = None,
    event_type: Optional[EventType] = None,
    upcoming: bool = Query(False),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = db.query(Event).join(Team, Event.team_id == Team.id)
    
    # Role-based filtering
    if current_user.role == UserRole.PLAYER:
        current_player = db.query(Player).filter(Player.user_id == current_user.id).first()
        if current_player and current_player.team_id:
            query = query.filter(Event.team_id == current_player.team_id)
    elif current_user.role == UserRole.PARENT:
        from app.models.parent_child import ParentChild
        child_team_ids = db.query(Player.team_id).join(
            ParentChild, ParentChild.child_id == Player.id
        ).filter(ParentChild.parent_id == current_user.id).distinct().subquery()
        query = query.filter(Event.team_id.in_(child_team_ids))
    elif current_user.role == UserRole.COACH:
        coach_team_ids = db.query(Team.id).filter(Team.coach_id == current_user.id).subquery()
        query = query.filter(Event.team_id.in_(coach_team_ids))
    
    if team_id:
        query = query.filter(Event.team_id == team_id)
    
    if event_type:
        query = query.filter(Event.event_type == event_type)
    
    if upcoming:
        now = datetime.utcnow()
        week_later = now + timedelta(days=7)
        query = query.filter(Event.start_time >= now).filter(Event.end_time <= week_later)
    
    events = query.order_by(Event.start_time).offset(skip).limit(limit).all()
    return events


@router.post("/", response_model=EventResponse, status_code=status.HTTP_201_CREATED)
def create_event(
    event_data: EventCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_coach)
):
    # Verify team exists
    team = db.query(Team).filter(Team.id == event_data.team_id).first()
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")
    
    # Authorization
    if current_user.role == UserRole.COACH and team.coach_id != current_user.id:
        if current_user.role != UserRole.ADMIN:
            raise HTTPException(status_code=403, detail="Not authorized")
    
    # Validate times
    if event_data.end_time <= event_data.start_time:
        raise HTTPException(
            status_code=400,
            detail="End time must be after start time"
        )
    
    db_event = Event(**event_data.dict())
    db.add(db_event)
    db.commit()
    db.refresh(db_event)
    return db_event


@router.get("/{event_id}", response_model=EventWithTeam)
def get_event(
    event_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    event = db.query(Event).filter(Event.id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    
    # Authorization
    if current_user.role == UserRole.PLAYER:
        current_player = db.query(Player).filter(Player.user_id == current_user.id).first()
        if current_player and event.team_id != current_player.team_id:
            raise HTTPException(status_code=403, detail="Not authorized")
    elif current_user.role == UserRole.PARENT:
        from app.models.parent_child import ParentChild
        child_team_ids = db.query(Player.team_id).join(
            ParentChild, ParentChild.child_id == Player.id
        ).filter(ParentChild.parent_id == current_user.id).distinct().subquery()
        if event.team_id not in [tid for tid, in db.query(child_team_ids).all()]:
            raise HTTPException(status_code=403, detail="Not authorized")
    
    return event


@router.put("/{event_id}", response_model=EventResponse)
def update_event(
    event_id: int,
    event_data: EventUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_coach)
):
    event = db.query(Event).filter(Event.id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    
    # Authorization
    team = db.query(Team).filter(Team.id == event.team_id).first()
    if current_user.role == UserRole.COACH and team.coach_id != current_user.id:
        if current_user.role != UserRole.ADMIN:
            raise HTTPException(status_code=403, detail="Not authorized")
    
    update_data = event_data.dict(exclude_unset=True)
    
    # Validate times if both provided
    if "start_time" in update_data and "end_time" in update_data:
        if update_data["end_time"] <= update_data["start_time"]:
            raise HTTPException(
                status_code=400,
                detail="End time must be after start time"
            )
    
    for field, value in update_data.items():
        setattr(event, field, value)
    
    db.commit()
    db.refresh(event)
    return event


@router.delete("/{event_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_event(
    event_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_coach)
):
    event = db.query(Event).filter(Event.id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    
    team = db.query(Team).filter(Team.id == event.team_id).first()
    if current_user.role == UserRole.COACH and team.coach_id != current_user.id:
        if current_user.role != UserRole.ADMIN:
            raise HTTPException(status_code=403, detail="Not authorized")
    
    db.delete(event)
    db.commit()
    return {"message": "Event deleted"}


@router.get("/calendar/all", response_model=List[EventResponse])
def get_event_calendar(
    days: int = Query(30, ge=1, le=365),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all events for calendar view"""
    now = datetime.utcnow()
    future = now + timedelta(days=days)
    
    query = db.query(Event).filter(
        Event.start_time >= now,
        Event.start_time <= future
    )
    
    # Filter by role
    if current_user.role == UserRole.PLAYER:
        current_player = db.query(Player).filter(Player.user_id == current_user.id).first()
        if current_player and current_player.team_id:
            query = query.filter(Event.team_id == current_player.team_id)
    elif current_user.role == UserRole.PARENT:
        from app.models.parent_child import ParentChild
        child_team_ids = db.query(Player.team_id).join(
            ParentChild, ParentChild.child_id == Player.id
        ).filter(ParentChild.parent_id == current_user.id).distinct().subquery()
        query = query.filter(Event.team_id.in_(child_team_ids))
    elif current_user.role == UserRole.COACH:
        coach_team_ids = db.query(Team.id).filter(Team.coach_id == current_user.id).subquery()
        query = query.filter(Event.team_id.in_(coach_team_ids))
    
    events = query.order_by(Event.start_time).all()
    return events
