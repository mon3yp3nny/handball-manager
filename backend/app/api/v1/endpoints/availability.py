"""Player availability windows (#136)."""
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.deps import get_db, get_current_user
from app.core.permissions import can_access_team
from app.models.parent_child import ParentChild
from app.models.player import Player
from app.models.player_availability import PlayerAvailability
from app.models.user import User, UserRole
from app.schemas.player_availability import (
    AvailabilityCreate,
    AvailabilityResponse,
    AvailabilityUpdate,
)


router = APIRouter()


def _ensure_player_visible(db: Session, user: User, player_id: int) -> Player:
    """Same rules as `GET /players/{id}` — admin/supervisor see all,
    coach sees their team's players, player sees self, parent sees own
    children.
    """
    player = db.query(Player).filter(Player.id == player_id).first()
    if not player:
        raise HTTPException(status_code=404, detail="Player not found")

    if user.has_role(UserRole.ADMIN) or user.has_role(UserRole.SUPERVISOR):
        return player
    if player.team_id and can_access_team(user, player.team_id, db):
        return player
    if user.has_role(UserRole.PLAYER):
        self_player = db.query(Player).filter(Player.user_id == user.id).first()
        if self_player and self_player.id == player_id:
            return player
    if user.has_role(UserRole.PARENT):
        link = (
            db.query(ParentChild)
            .filter(
                ParentChild.parent_id == user.id,
                ParentChild.child_id == player_id,
            )
            .first()
        )
        if link:
            return player
    raise HTTPException(status_code=403, detail="Not authorized for this player")


def _can_see_medical(user: User) -> bool:
    """Per #12: medical entries surface only to admin / supervisor /
    coach of the team. Player themselves and parents see the row but
    not the `note` field. Re-evaluate when #12 lands its definitive
    role matrix."""
    return user.has_any_role([UserRole.ADMIN, UserRole.SUPERVISOR, UserRole.COACH])


def _redact_medical(row: PlayerAvailability, user: User) -> dict:
    payload = AvailabilityResponse.from_orm(row).dict()
    if row.is_medical and not _can_see_medical(user):
        payload["note"] = None
    return payload


@router.get(
    "/players/{player_id}/availability",
    response_model=List[AvailabilityResponse],
)
def list_player_availability(
    player_id: int,
    upcoming_only: bool = Query(False, description="Hide windows whose to_date is in the past"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _ensure_player_visible(db, current_user, player_id)
    q = db.query(PlayerAvailability).filter(PlayerAvailability.player_id == player_id)
    rows = q.order_by(PlayerAvailability.from_date.desc()).all()
    if upcoming_only:
        from datetime import date as _date
        today = _date.today()
        rows = [r for r in rows if r.to_date is None or r.to_date >= today]
    return [_redact_medical(r, current_user) for r in rows]


@router.post(
    "/players/{player_id}/availability",
    response_model=AvailabilityResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_player_availability(
    player_id: int,
    payload: AvailabilityCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Players + parents may self-report; coaches/supervisors/admin may
    create for anyone they can see. Medical entries are gated to
    coach+ (no player/parent can flag is_medical=True themselves)."""
    player = _ensure_player_visible(db, current_user, player_id)

    if payload.is_medical and not _can_see_medical(current_user):
        raise HTTPException(
            status_code=403,
            detail="Only coach / supervisor / admin may flag a window as medical",
        )

    row = PlayerAvailability(
        player_id=player.id,
        from_date=payload.from_date,
        to_date=payload.to_date,
        reason=payload.reason,
        note=payload.note,
        is_medical=payload.is_medical,
        created_by=current_user.id,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return _redact_medical(row, current_user)


@router.put(
    "/players/{player_id}/availability/{availability_id}",
    response_model=AvailabilityResponse,
)
def update_player_availability(
    player_id: int,
    availability_id: int,
    payload: AvailabilityUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _ensure_player_visible(db, current_user, player_id)
    row = (
        db.query(PlayerAvailability)
        .filter(
            PlayerAvailability.id == availability_id,
            PlayerAvailability.player_id == player_id,
        )
        .first()
    )
    if not row:
        raise HTTPException(status_code=404, detail="Availability window not found")

    data = payload.dict(exclude_unset=True)
    if "is_medical" in data and data["is_medical"] and not _can_see_medical(current_user):
        raise HTTPException(
            status_code=403,
            detail="Only coach / supervisor / admin may flag a window as medical",
        )
    for k, v in data.items():
        setattr(row, k, v)

    if row.to_date is not None and row.to_date < row.from_date:
        raise HTTPException(status_code=422, detail="to_date must be on or after from_date")

    db.commit()
    db.refresh(row)
    return _redact_medical(row, current_user)


@router.delete(
    "/players/{player_id}/availability/{availability_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_player_availability(
    player_id: int,
    availability_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _ensure_player_visible(db, current_user, player_id)
    row = (
        db.query(PlayerAvailability)
        .filter(
            PlayerAvailability.id == availability_id,
            PlayerAvailability.player_id == player_id,
        )
        .first()
    )
    if not row:
        raise HTTPException(status_code=404, detail="Availability window not found")
    db.delete(row)
    db.commit()
    return {"message": "Deleted"}
