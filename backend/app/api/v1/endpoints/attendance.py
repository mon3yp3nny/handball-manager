from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from app.core.deps import get_db, get_current_user, require_coach_or_supervisor
from app.models.user import User, UserRole
from app.models.attendance import Attendance, AttendanceStatus
from app.models.game import Game
from app.models.event import Event
from app.models.player import Player
from app.schemas.attendance import (
    AttendanceCreate, AttendanceUpdate, AttendanceResponse,
    AttendanceWithPlayer, BulkAttendanceUpdate
)

router = APIRouter()


@router.get("/", response_model=List[AttendanceResponse])
def get_attendance(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    game_id: Optional[int] = None,
    event_id: Optional[int] = None,
    player_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = db.query(Attendance)
    
    if game_id:
        query = query.filter(Attendance.game_id == game_id)
    
    if event_id:
        query = query.filter(Attendance.event_id == event_id)
    
    if player_id:
        query = query.filter(Attendance.player_id == player_id)
    
    # Filter by role
    if current_user.role == UserRole.PLAYER:
        current_player = db.query(Player).filter(Player.user_id == current_user.id).first()
        if current_player:
            query = query.filter(Attendance.player_id == current_player.id)
    elif current_user.role == UserRole.PARENT:
        from app.models.parent_child import ParentChild
        child_ids = db.query(ParentChild.child_id).filter(ParentChild.parent_id == current_user.id).subquery()
        query = query.filter(Attendance.player_id.in_(child_ids))
    
    records = query.offset(skip).limit(limit).all()
    return records


@router.post("/", response_model=AttendanceResponse, status_code=status.HTTP_201_CREATED)
def create_attendance(
    attendance_data: AttendanceCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Validate that either game_id or event_id is provided
    if not attendance_data.game_id and not attendance_data.event_id:
        raise HTTPException(
            status_code=400,
            detail="Either game_id or event_id must be provided"
        )
    
    # Verify player belongs to current user or user has permission
    if current_user.role == UserRole.PLAYER:
        player = db.query(Player).filter(Player.user_id == current_user.id).first()
        if not player or player.id != attendance_data.player_id:
            raise HTTPException(status_code=403, detail="Not authorized")
    elif current_user.role == UserRole.PARENT:
        from app.models.parent_child import ParentChild
        parent_link = db.query(ParentChild).filter(
            ParentChild.parent_id == current_user.id,
            ParentChild.child_id == attendance_data.player_id
        ).first()
        if not parent_link and current_user.role != UserRole.ADMIN:
            raise HTTPException(status_code=403, detail="Not authorized")
    
    # Check for existing record
    existing = db.query(Attendance).filter(
        Attendance.player_id == attendance_data.player_id,
        ((Attendance.game_id == attendance_data.game_id) if attendance_data.game_id else True),
        ((Attendance.event_id == attendance_data.event_id) if attendance_data.event_id else True)
    ).first()
    
    if existing:
        raise HTTPException(status_code=400, detail="Attendance record already exists")
    
    db_record = Attendance(
        **attendance_data.dict(),
        recorded_by=current_user.id
    )
    db.add(db_record)
    db.commit()
    db.refresh(db_record)
    return db_record


@router.get("/{attendance_id}", response_model=AttendanceWithPlayer)
def get_attendance_record(
    attendance_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    record = db.query(Attendance).filter(Attendance.id == attendance_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Attendance record not found")
    
    # Authorization
    if current_user.role == UserRole.PLAYER:
        player = db.query(Player).filter(Player.user_id == current_user.id).first()
        if not player or record.player_id != player.id:
            raise HTTPException(status_code=403, detail="Not authorized")
    elif current_user.role == UserRole.PARENT:
        from app.models.parent_child import ParentChild
        parent_link = db.query(ParentChild).filter(
            ParentChild.parent_id == current_user.id,
            ParentChild.child_id == record.player_id
        ).first()
        if not parent_link and current_user.role != UserRole.ADMIN:
            raise HTTPException(status_code=403, detail="Not authorized")
    
    return record


@router.put("/{attendance_id}", response_model=AttendanceResponse)
def update_attendance(
    attendance_id: int,
    attendance_data: AttendanceUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    record = db.query(Attendance).filter(Attendance.id == attendance_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Attendance record not found")
    
    # Players can only update their own pending records
    if current_user.role == UserRole.PLAYER:
        player = db.query(Player).filter(Player.user_id == current_user.id).first()
        if not player or record.player_id != player.id:
            raise HTTPException(status_code=403, detail="Not authorized")
        # Players can only set status to present/absent, not change once recorded
        if record.status != AttendanceStatus.PENDING:
            raise HTTPException(status_code=400, detail="Cannot modify recorded attendance")
    elif current_user.role == UserRole.PARENT:
        from app.models.parent_child import ParentChild
        parent_link = db.query(ParentChild).filter(
            ParentChild.parent_id == current_user.id,
            ParentChild.child_id == record.player_id
        ).first()
        if not parent_link and current_user.role != UserRole.ADMIN:
            raise HTTPException(status_code=403, detail="Not authorized")
    
    update_data = attendance_data.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(record, field, value)
    
    record.recorded_by = current_user.id
    db.commit()
    db.refresh(record)
    return record


@router.post("/bulk-update", response_model=List[AttendanceResponse])
def bulk_update_attendance(
    bulk_data: BulkAttendanceUpdate,
    game_id: Optional[int] = None,
    event_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_coach_or_supervisor)
):
    """Bulk update attendance for multiple players"""
    if not game_id and not event_id:
        raise HTTPException(
            status_code=400,
            detail="Either game_id or event_id must be provided"
        )
    
    updated_records = []
    
    for player_id in bulk_data.player_ids:
        record = db.query(Attendance).filter(
            Attendance.player_id == player_id,
            ((Attendance.game_id == game_id) if game_id else True),
            ((Attendance.event_id == event_id) if event_id else True)
        ).first()
        
        if record:
            record.status = bulk_data.status
            record.notes = bulk_data.notes or record.notes
            record.recorded_by = current_user.id
        else:
            # Create new record
            record = Attendance(
                player_id=player_id,
                game_id=game_id,
                event_id=event_id,
                status=bulk_data.status,
                notes=bulk_data.notes,
                recorded_by=current_user.id
            )
            db.add(record)
        
        updated_records.append(record)
    
    db.commit()
    return updated_records


@router.get("/stats/player/{player_id}")
def get_player_attendance_stats(
    player_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get attendance statistics for a player"""
    # Authorization
    if current_user.role == UserRole.PLAYER:
        player = db.query(Player).filter(Player.user_id == current_user.id).first()
        if not player or player.id != player_id:
            raise HTTPException(status_code=403, detail="Not authorized")
    elif current_user.role == UserRole.PARENT:
        from app.models.parent_child import ParentChild
        parent_link = db.query(ParentChild).filter(
            ParentChild.parent_id == current_user.id,
            ParentChild.child_id == player_id
        ).first()
        if not parent_link:
            raise HTTPException(status_code=403, detail="Not authorized")
    
    from sqlalchemy import func
    
    stats = db.query(
        Attendance.player_id,
        func.count(Attendance.id).label('total'),
        func.sum((Attendance.status == AttendanceStatus.PRESENT)).label('present'),
        func.sum((Attendance.status == AttendanceStatus.ABSENT)).label('absent'),
        func.sum((Attendance.status == AttendanceStatus.EXCUSED)).label('excused')
    ).filter(Attendance.player_id == player_id).group_by(Attendance.player_id).first()
    
    if not stats:
        return {
            "player_id": player_id,
            "total": 0,
            "present": 0,
            "absent": 0,
            "excused": 0,
            "attendance_rate": 0
        }
    
    total = stats.total
    present = stats.present or 0
    
    return {
        "player_id": player_id,
        "total": total,
        "present": present,
        "absent": stats.absent or 0,
        "excused": stats.excused or 0,
        "attendance_rate": round((present / total) * 100, 2) if total > 0 else 0
    }
