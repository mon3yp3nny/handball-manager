"""Approver-facing endpoints for the registration approval workflow."""
import logging
from typing import List

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.deps import get_db, require_coach
from app.models.user import User, ApprovalStatus
from app.models.team import Team
from app.schemas.registration import PendingRegistration, RejectionRequest
from app.services import approval
from app.websocket.manager import notify_resource

logger = logging.getLogger(__name__)

router = APIRouter()


def _to_pending(db: Session, user: User) -> PendingRegistration:
    team_name = None
    if user.requested_team_id:
        team = db.query(Team).filter(Team.id == user.requested_team_id).first()
        team_name = team.name if team else None
    return PendingRegistration(
        id=user.id,
        email=user.email,
        first_name=user.first_name,
        last_name=user.last_name,
        role=user.role,
        roles=user.roles,
        requested_team_id=user.requested_team_id,
        requested_team_name=team_name,
        created_at=user.created_at,
    )


@router.get("/pending", response_model=List[PendingRegistration])
def list_pending(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_coach),
):
    """Pending registrations the caller may review (admins: all; coaches:
    players/parents who chose one of the coach's teams)."""
    users = approval.pending_visible_to(db, current_user).order_by(User.created_at).all()
    return [_to_pending(db, u) for u in users]


def _load_pending(db: Session, user_id: int) -> User:
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if user.approval_status != ApprovalStatus.PENDING:
        raise HTTPException(status_code=400, detail="This registration is not pending.")
    return user


@router.post("/{user_id}/approve", response_model=PendingRegistration)
def approve(
    user_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_coach),
):
    pending = _load_pending(db, user_id)
    if not approval.can_approve(db, current_user, pending):
        raise HTTPException(status_code=403, detail="Not authorized to approve this registration.")
    approval.approve_registration(db, current_user, pending, background_tasks)
    notify_resource("registrations", "updated")
    return _to_pending(db, pending)


@router.post("/{user_id}/reject", response_model=PendingRegistration)
def reject(
    user_id: int,
    body: RejectionRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_coach),
):
    pending = _load_pending(db, user_id)
    if not approval.can_approve(db, current_user, pending):
        raise HTTPException(status_code=403, detail="Not authorized to reject this registration.")
    approval.reject_registration(db, current_user, pending, body.reason, background_tasks)
    notify_resource("registrations", "updated")
    return _to_pending(db, pending)
