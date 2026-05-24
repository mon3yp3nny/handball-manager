"""Registration approval workflow: approver routing + state transitions.

Routing (see ApprovalStatus on the User model):
  - coach / supervisor sign-ups  → approved by an admin
  - player / parent sign-ups     → approved by the coach of their chosen
                                    team; admin is the fallback when the
                                    team has no coach (or none was chosen)
"""
import logging
from typing import List, Optional

from fastapi import BackgroundTasks
from sqlalchemy.orm import Session

from app.models.user import User, UserRole, ApprovalStatus
from app.models.team import Team
from app.models.player import Player
from app.services.email_service import email_service
from app.utils.time import utcnow

logger = logging.getLogger(__name__)


def _active_approved_admins(db: Session) -> List[User]:
    return (
        db.query(User)
        .filter(
            User.role == UserRole.ADMIN,
            User.is_active.is_(True),
            User.approval_status == ApprovalStatus.APPROVED,
        )
        .all()
    )


def approvers_for(db: Session, user: User) -> List[User]:
    """Who may approve this pending user. Players/parents route to their
    team's coach (admin fallback); everyone else routes to admins."""
    if user.role in (UserRole.PLAYER, UserRole.PARENT) and user.requested_team_id:
        team = db.query(Team).filter(Team.id == user.requested_team_id).first()
        if team and team.coach_id:
            coach = (
                db.query(User)
                .filter(
                    User.id == team.coach_id,
                    User.is_active.is_(True),
                    User.approval_status == ApprovalStatus.APPROVED,
                )
                .first()
            )
            if coach:
                return [coach]
    # coach/supervisor sign-ups, and the no-coach fallback for players/parents
    return _active_approved_admins(db)


def can_approve(db: Session, approver: User, pending_user: User) -> bool:
    """Whether `approver` is allowed to act on `pending_user`'s request."""
    if approver.has_role(UserRole.ADMIN):
        return True  # admins can act on any pending registration
    # A coach may approve players/parents whose chosen team they coach.
    if approver.has_role(UserRole.COACH) and pending_user.role in (
        UserRole.PLAYER, UserRole.PARENT,
    ):
        if not pending_user.requested_team_id:
            return False
        team = db.query(Team).filter(Team.id == pending_user.requested_team_id).first()
        return team is not None and team.coach_id == approver.id
    return False


def pending_visible_to(db: Session, approver: User):
    """Query of pending users `approver` is allowed to review."""
    q = db.query(User).filter(User.approval_status == ApprovalStatus.PENDING)
    if approver.has_role(UserRole.ADMIN):
        return q  # admins see the whole queue
    if approver.has_role(UserRole.COACH):
        coached_team_ids = [t.id for t in db.query(Team.id).filter(Team.coach_id == approver.id)]
        if not coached_team_ids:
            return q.filter(False)
        return q.filter(
            User.role.in_([UserRole.PLAYER, UserRole.PARENT]),
            User.requested_team_id.in_(coached_team_ids),
        )
    return q.filter(False)


def approve_registration(
    db: Session, approver: User, pending_user: User,
    background_tasks: Optional[BackgroundTasks] = None,
) -> User:
    pending_user.approval_status = ApprovalStatus.APPROVED
    pending_user.approved_by_id = approver.id
    pending_user.approved_at = utcnow()
    pending_user.rejection_reason = None
    # A newly-approved player joins the team they chose at sign-up — but
    # only if it still exists. requested_team_id is a soft reference, while
    # players.team_id is a real FK, so a team deleted between sign-up and
    # approval would otherwise blow up the commit. If it's gone, the player
    # is approved unassigned and a coach can place them later.
    if pending_user.role == UserRole.PLAYER and pending_user.requested_team_id:
        team_exists = db.query(Team.id).filter(
            Team.id == pending_user.requested_team_id
        ).first()
        if team_exists:
            player = db.query(Player).filter(Player.user_id == pending_user.id).first()
            if player and player.team_id is None:
                player.team_id = pending_user.requested_team_id
    db.commit()
    db.refresh(pending_user)
    logger.info("Registration approved: user_id=%s by approver_id=%s",
                pending_user.id, approver.id)
    if background_tasks is not None:
        background_tasks.add_task(
            email_service.send_registration_approved,
            to_email=pending_user.email,
            first_name=pending_user.first_name,
        )
    return pending_user


def reject_registration(
    db: Session, approver: User, pending_user: User, reason: str,
    background_tasks: Optional[BackgroundTasks] = None,
) -> User:
    pending_user.approval_status = ApprovalStatus.REJECTED
    pending_user.approved_by_id = approver.id
    pending_user.approved_at = utcnow()
    pending_user.rejection_reason = reason
    db.commit()
    db.refresh(pending_user)
    logger.info("Registration rejected: user_id=%s by approver_id=%s",
                pending_user.id, approver.id)
    if background_tasks is not None:
        background_tasks.add_task(
            email_service.send_registration_rejected,
            to_email=pending_user.email,
            first_name=pending_user.first_name,
            reason=reason,
        )
    return pending_user


def notify_approvers_of_registration(
    db: Session, user: User, team: Optional[Team],
    background_tasks: BackgroundTasks,
) -> None:
    """Best-effort email to whoever can approve this new registration."""
    applicant_name = f"{user.first_name} {user.last_name}"
    team_name = team.name if team else None
    for approver in approvers_for(db, user):
        background_tasks.add_task(
            email_service.send_registration_pending_to_approver,
            to_email=approver.email,
            approver_name=approver.first_name,
            applicant_name=applicant_name,
            role=user.role.value,
            team_name=team_name,
        )
