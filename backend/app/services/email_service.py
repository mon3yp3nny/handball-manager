"""Email service for sending invitation emails."""
import logging
from typing import Optional

logger = logging.getLogger(__name__)


class EmailService:
    """Service for sending emails."""

    @staticmethod
    def send_invitation_email(
        to_email: str,
        first_name: str,
        inviter_name: str,
        team_name: Optional[str],
        role: str,
        invitation_link: str
    ) -> bool:
        """Send invitation email to new user."""
        # Mock email sending for now
        # In production, integrate with SendGrid, AWS SES, or SMTP

        logger.info(
            "Sending invitation email to=%s, role=%s, team=%s, inviter=%s",
            to_email, role, team_name or "none", inviter_name,
        )

        return True

    @staticmethod
    def send_welcome_email(to_email: str, first_name: str) -> bool:
        """Send welcome email after successful registration."""
        logger.info("Sending welcome email to=%s, name=%s", to_email, first_name)

        return True


email_service = EmailService()
