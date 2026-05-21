from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from datetime import datetime
from app.utils.time import utcnow
from typing import List, Optional

from app.core.deps import get_db, get_current_user, require_coach_or_supervisor
from app.core.permissions import can_access_team, team_ids_visible_to
from app.models.user import User, UserRole
from app.models.news import News
from app.models.team import Team
from app.models.player import Player
from app.schemas.news import NewsCreate, NewsUpdate, NewsResponse, NewsWithAuthor, NewsPublish
from app.schemas.common import PaginatedResponse

router = APIRouter()


@router.get("/", response_model=PaginatedResponse[NewsResponse])
def get_news(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    team_id: Optional[int] = None,
    only_published: bool = Query(True),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = db.query(News)

    # Global news (team_id IS NULL) is visible to everyone; team news
    # uses the same visibility rule as the rest of the API. Coaches
    # additionally see their own drafts (rows they authored).
    visible_team_ids = team_ids_visible_to(db, current_user)
    if visible_team_ids is not None:
        from sqlalchemy import or_
        clauses = [News.team_id.is_(None)]
        if visible_team_ids:
            clauses.append(News.team_id.in_(visible_team_ids))
        if current_user.has_role(UserRole.COACH):
            clauses.append(News.author_id == current_user.id)
        query = query.filter(or_(*clauses))
    
    if team_id:
        query = query.filter(News.team_id == team_id)
    
    if only_published and current_user.role not in [UserRole.COACH, UserRole.ADMIN, UserRole.SUPERVISOR]:
        query = query.filter(News.is_published == True)
    elif only_published:
        query = query.filter(News.is_published == True)
    
    total = query.count()
    news = query.order_by(News.created_at.desc()).offset(skip).limit(limit).all()
    return {"items": news, "total": total, "skip": skip, "limit": limit}


@router.post("/", response_model=NewsResponse, status_code=status.HTTP_201_CREATED)
def create_news(
    news_data: NewsCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_coach_or_supervisor)
):
    # Verify team if specified
    if news_data.team_id:
        team = db.query(Team).filter(Team.id == news_data.team_id).first()
        if not team:
            raise HTTPException(status_code=404, detail="Team not found")
        
        # Coaches can only post to their teams
        if current_user.role == UserRole.COACH and team.coach_id != current_user.id:
            if current_user.role != UserRole.ADMIN:
                raise HTTPException(status_code=403, detail="Not authorized to post to this team")
    
    db_news = News(
        **news_data.dict(),
        author_id=current_user.id
    )
    db.add(db_news)
    db.commit()
    db.refresh(db_news)
    return db_news


@router.get("/{news_id}", response_model=NewsWithAuthor)
def get_news_item(
    news_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    news = db.query(News).filter(News.id == news_id).first()
    if not news:
        raise HTTPException(status_code=404, detail="News not found")
    
    # Check if published (unless author or admin)
    if not news.is_published and news.author_id != current_user.id:
        if current_user.role not in [UserRole.ADMIN, UserRole.COACH, UserRole.SUPERVISOR]:
            raise HTTPException(status_code=403, detail="News not yet published")
    
    # Team-scoped news uses the canonical can_access_team predicate.
    if news.team_id is not None and not can_access_team(current_user, news.team_id, db):
        raise HTTPException(status_code=403, detail="Not authorized")

    return news


@router.put("/{news_id}", response_model=NewsResponse)
def update_news(
    news_id: int,
    news_data: NewsUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    news = db.query(News).filter(News.id == news_id).first()
    if not news:
        raise HTTPException(status_code=404, detail="News not found")
    
    # Authorization - only author or admin can edit
    if news.author_id != current_user.id and current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Not authorized to edit this news")
    
    update_data = news_data.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(news, field, value)
    
    db.commit()
    db.refresh(news)
    return news


@router.patch("/{news_id}/publish", response_model=NewsResponse)
def publish_news(
    news_id: int,
    publish_data: NewsPublish,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_coach_or_supervisor)
):
    news = db.query(News).filter(News.id == news_id).first()
    if not news:
        raise HTTPException(status_code=404, detail="News not found")
    
    # Authorization
    if news.author_id != current_user.id and current_user.role != UserRole.ADMIN:
        # Coaches can only publish their own team's news
        if news.team_id:
            team = db.query(Team).filter(Team.id == news.team_id).first()
            if not team or team.coach_id != current_user.id:
                raise HTTPException(status_code=403, detail="Not authorized")
    
    news.is_published = publish_data.is_published
    if publish_data.is_published:
        news.published_at = utcnow()
    else:
        news.published_at = None
    
    db.commit()
    db.refresh(news)
    return news


@router.delete("/{news_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_news(
    news_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_coach_or_supervisor)
):
    news = db.query(News).filter(News.id == news_id).first()
    if not news:
        raise HTTPException(status_code=404, detail="News not found")
    
    # Authorization
    if news.author_id != current_user.id and current_user.role != UserRole.ADMIN:
        if news.team_id:
            team = db.query(Team).filter(Team.id == news.team_id).first()
            if not team or team.coach_id != current_user.id:
                raise HTTPException(status_code=403, detail="Not authorized")
    
    db.delete(news)
    db.commit()
    return {"message": "News deleted"}
