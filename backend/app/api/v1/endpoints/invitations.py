"""Invitation endpoints for coaches to invite players and parents."""
import logging
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks, Request
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime

from app.core.config import settings
from app.core.deps import get_db, get_current_user, require_role
from app.core.rate_limit import limiter
from app.models.user import User, UserRole
from app.models.invitation import Invitation, InvitationStatus
from app.models.team import Team
from app.schemas.invitation import (
    InvitationCreate,
    InvitationResponse,
    InvitationListResponse,
    InvitationVerifyResponse
)
from app.services.email_service import email_service

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/send", response_model=InvitationResponse)
@limiter.limit("10/hour")
async def send_invitation(
    request: Request,
    invitation_data: InvitationCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role([UserRole.COACH, UserRole.ADMIN]))
):
    """Send an invitation to a player or parent via email."""
    # Validate team exists and user has access
    if invitation_data.team_id:
        team = db.query(Team).filter(Team.id == invitation_data.team_id).first()
        if not team:
            raise HTTPException(status_code=404, detail="Team not found")
        if current_user.role == UserRole.COACH and team.coach_id != current_user.id:
            raise HTTPException(status_code=403, detail="Not authorized for this team")

    # Check if user with this email already exists
    existing_user = db.query(User).filter(User.email == invitation_data.email).first()
    if existing_user:
        raise HTTPException(
            status_code=400,
            detail="User with this email already exists"
        )

    # Check if pending invitation already exists
    existing_invitation = db.query(Invitation).filter(
        Invitation.email == invitation_data.email,
        Invitation.status == InvitationStatus.PENDING
    ).first()

    if existing_invitation and not existing_invitation.is_expired():
        raise HTTPException(
            status_code=400,
            detail="Pending invitation already exists for this email"
        )

    # Create invitation
    invitation = Invitation(
        email=invitation_data.email,
        first_name=invitation_data.first_name,
        last_name=invitation_data.last_name,
        role=invitation_data.role,
        team_id=invitation_data.team_id,
        invited_by=current_user.id
    )

    db.add(invitation)
    db.commit()
    db.refresh(invitation)

    # Send email in background
    team_name = team.name if invitation_data.team_id else None
    invitation_link = f"{settings.FRONTEND_URL}/accept-invitation?token={invitation.token}"

    logger.info(
        "Invitation sent by user_id=%s to email=%s for role=%s",
        current_user.id, invitation_data.email, invitation_data.role,
    )

    background_tasks.add_task(
        email_service.send_invitation_email,
        to_email=invitation_data.email,
        first_name=invitation_data.first_name,
        inviter_name=f"{current_user.first_name} {current_user.last_name}",
        team_name=team_name,
        role=invitation_data.role,
        invitation_link=invitation_link
    )

    return invitation


@router.get("/sent", response_model=InvitationListResponse)
def get_sent_invitations(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role([UserRole.COACH, UserRole.ADMIN])),
    skip: int = 0,
    limit: int = 50
):
    """Get all invitations sent by the current user."""
    query = db.query(Invitation).filter(Invitation.invited_by == current_user.id)

    total = query.count()
    invitations = query.offset(skip).limit(limit).all()

    return InvitationListResponse(items=invitations, total=total)


@router.get("/verify/{token}", response_model=InvitationVerifyResponse)
def verify_invitation(
    token: str,
    db: Session = Depends(get_db)
):
    """Verify if an invitation token is valid."""
    invitation = db.query(Invitation).filter(Invitation.token == token).first()

    if not invitation:
        return InvitationVerifyResponse(
            valid=False,
            message="Invalid invitation token"
        )

    if invitation.is_expired():
        invitation.status = InvitationStatus.EXPIRED
        db.commit()
        return InvitationVerifyResponse(
            valid=False,
            message="Invitation has expired"
        )

    if invitation.status != InvitationStatus.PENDING:
        return InvitationVerifyResponse(
            valid=False,
            message=f"Invitation is {invitation.status}"
        )

    team_name = invitation.team.name if invitation.team else None

    return InvitationVerifyResponse(
        valid=True,
        email=invitation.email,
        role=invitation.role,
        team_id=invitation.team_id,
        team_name=team_name,
        message="Invitation is valid"
    )


@router.post("/resend/{invitation_id}")
def resend_invitation(
    invitation_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role([UserRole.COACH, UserRole.ADMIN]))
):
    """Resend an existing invitation."""
    invitation = db.query(Invitation).filter(
        Invitation.id == invitation_id,
        Invitation.invited_by == current_user.id
    ).first()

    if not invitation:
        raise HTTPException(status_code=404, detail="Invitation not found")

    if invitation.status != InvitationStatus.PENDING:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot resend invitation with status: {invitation.status}"
        )

    # Update expiry and token
    from datetime import datetime, timedelta
    import uuid
    invitation.expires_at = datetime.utcnow() + timedelta(days=7)
    invitation.token = str(uuid.uuid4())
    db.commit()

    # Resend email
    team_name = invitation.team.name if invitation.team else None
    invitation_link = f"{settings.FRONTEND_URL}/accept-invitation?token={invitation.token}"

    logger.info("Resending invitation id=%s to email=%s", invitation_id, invitation.email)

    background_tasks.add_task(
        email_service.send_invitation_email,
        to_email=invitation.email,
        first_name=invitation.first_name,
        inviter_name=f"{current_user.first_name} {current_user.last_name}",
        team_name=team_name,
        role=invitation.role,
        invitation_link=invitation_link
    )

    return {"message": "Invitation resent successfully"}


@router.delete("/{invitation_id}", status_code=status.HTTP_204_NO_CONTENT)
def revoke_invitation(
    invitation_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role([UserRole.COACH, UserRole.ADMIN]))
):
    """Revoke an invitation."""
    invitation = db.query(Invitation).filter(
        Invitation.id == invitation_id,
        Invitation.invited_by == current_user.id
    ).first()

    if not invitation:
        raise HTTPException(status_code=404, detail="Invitation not found")

    if invitation.status != InvitationStatus.PENDING:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot revoke invitation with status: {invitation.status}"
        )

    invitation.status = InvitationStatus.REVOKED
    db.commit()

    return {"message": "Invitation revoked"}


@router.get("/{team_id}/invitations")
def get_team_invitations(
    team_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role([UserRole.COACH, UserRole.ADMIN]))
):
    """Get all invitations for a specific team."""
    team = db.query(Team).filter(Team.id == team_id).first()
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")

    if current_user.role == UserRole.COACH and team.coach_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized for this team")

    invitations = db.query(Invitation).filter(
        Invitation.team_id == team_id
    ).order_by(Invitation.created_at.desc()).all()

    return invitations
