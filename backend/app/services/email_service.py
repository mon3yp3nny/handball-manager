"""Email service for sending emails via SMTP."""
import logging
from typing import Optional
from pathlib import Path

from fastapi_mail import FastMail, MessageSchema, ConnectionConfig
from fastapi_mail.errors import ConnectionErrors
from jinja2 import Template

from app.core.config import settings

logger = logging.getLogger(__name__)


class EmailService:
    """Service for sending emails via SMTP with HTML templates."""
    
    def __init__(self):
        self._fm: Optional[FastMail] = None
        self._templates_dir = Path(__file__).parent.parent / "templates" / "email"
    
    def _get_fastmail(self) -> Optional[FastMail]:
        """Initialize FastMail connection if SMTP is configured."""
        if self._fm is not None:
            return self._fm
        
        if not settings.SMTP_HOST or not settings.SMTP_USER:
            logger.warning("SMTP not configured. Emails will be logged only.")
            return None
        
        conf = ConnectionConfig(
            MAIL_USERNAME=settings.SMTP_USER,
            MAIL_PASSWORD=settings.SMTP_PASSWORD,
            MAIL_FROM=f"{settings.SMTP_FROM_NAME} <{settings.SMTP_FROM_EMAIL}>",
            MAIL_PORT=settings.SMTP_PORT,
            MAIL_SERVER=settings.SMTP_HOST,
            MAIL_STARTTLS=settings.SMTP_USE_TLS,
            MAIL_SSL_TLS=settings.SMTP_USE_SSL,
            USE_CREDENTIALS=True,
            VALIDATE_CERTS=True,
        )
        
        self._fm = FastMail(conf)
        return self._fm
    
    def _render_template(self, template_name: str, context: dict, text_fallback: bool = False) -> str:
        """Render a Jinja2 template."""
        ext = ".txt" if text_fallback else ".html"
        template_path = self._templates_dir / f"{template_name}{ext}"
        
        if not template_path.exists():
            # Fallback to text if HTML not found
            if not text_fallback:
                return self._render_template(template_name, context, text_fallback=True)
            return f"Error: Template {template_name} not found"
        
        template_content = template_path.read_text(encoding='utf-8')
        template = Template(template_content)
        return template.render(**context)
    
    def _log_email(self, to_email: str, subject: str, body: str, body_html: Optional[str] = None):
        """Log email when in dry-run mode or SMTP unavailable."""
        logger.info("=" * 60)
        logger.info("📧 EMAIL (DRY-RUN MODE)")
        logger.info("=" * 60)
        logger.info(f"To: {to_email}")
        logger.info(f"Subject: {subject}")
        logger.info("-" * 60)
        if body_html:
            logger.info("HTML Body:")
            logger.info(body_html[:500] + "..." if len(body_html) > 500 else body_html)
        else:
            logger.info("Text Body:")
            logger.info(body)
        logger.info("=" * 60)
    
    async def _send_email(
        self,
        to_email: str,
        subject: str,
        body_text: str,
        body_html: Optional[str] = None
    ) -> bool:
        """Send email via SMTP or log in dry-run mode."""
        if settings.EMAIL_DRY_RUN or not settings.SMTP_HOST:
            self._log_email(to_email, subject, body_text, body_html)
            return True
        
        fm = self._get_fastmail()
        if fm is None:
            self._log_email(to_email, subject, body_text, body_html)
            return True
        
        try:
            message = MessageSchema(
                subject=subject,
                recipients=[to_email],
                body=body_text,
                subtype="plain",
            )
            
            if body_html:
                message.body = body_html
                message.subtype = "html"
                # Also attach plain text as alternative
                message.alternatives = [(body_text, "text/plain")]
            
            await fm.send_message(message)
            logger.info(f"Email sent successfully to {to_email}")
            return True
            
        except ConnectionErrors as e:
            logger.error(f"SMTP connection error: {e}")
            self._log_email(to_email, subject, body_text, body_html)
            return False
        except Exception as e:
            logger.error(f"Failed to send email: {e}")
            self._log_email(to_email, subject, body_text, body_html)
            return False
    
    def _get_role_display(self, role: str) -> str:
        """Get German display name for role."""
        role_map = {
            "admin": "Administrator",
            "coach": "Trainer/Coach",
            "supervisor": "Betreuer",
            "player": "Spieler",
            "parent": "Elternteil"
        }
        return role_map.get(role.lower(), role)
    
    async def send_invitation_email(
        self,
        to_email: str,
        first_name: str,
        inviter_name: str,
        team_name: Optional[str],
        role: str,
        invitation_link: str
    ) -> bool:
        """Send invitation email to new user."""
        context = {
            "first_name": first_name,
            "inviter_name": inviter_name,
            "team_name": team_name,
            "role": role,
            "role_display": self._get_role_display(role),
            "invitation_link": invitation_link
        }
        
        subject = "Einladung zum Handball Manager"
        body_text = self._render_template("invitation", context, text_fallback=True)
        body_html = self._render_template("invitation", context)
        
        return await self._send_email(to_email, subject, body_text, body_html)
    
    async def send_welcome_email(
        self,
        to_email: str,
        first_name: str
    ) -> bool:
        """Send welcome email after successful registration."""
        context = {
            "first_name": first_name,
            "login_link": f"{settings.FRONTEND_URL}/login"
        }
        
        subject = "Willkommen beim Handball Manager!"
        body_text = self._render_template("welcome", context, text_fallback=True)
        body_html = self._render_template("welcome", context)
        
        return await self._send_email(to_email, subject, body_text, body_html)
    
    async def send_parent_credentials_email(
        self,
        to_email: str,
        first_name: str,
        last_name: str,
        password: str,
        child_name: str,
        child_team: str,
        coach_name: str
    ) -> bool:
        """Send credentials email to new parent accounts."""
        context = {
            "first_name": first_name,
            "last_name": last_name,
            "email": to_email,
            "password": password,
            "child_name": child_name,
            "child_team": child_team,
            "coach_name": coach_name,
            "login_link": f"{settings.FRONTEND_URL}/login"
        }
        
        subject = "Ihr Handball Manager Konto - Zugangsdaten"
        body_text = self._render_template("parent_credentials", context, text_fallback=True)
        body_html = self._render_template("parent_credentials", context)
        
        return await self._send_email(to_email, subject, body_text, body_html)
    
    async def send_child_linked_notification(
        self,
        to_email: str,
        parent_name: str,
        child_name: str,
        team_name: Optional[str] = None
    ) -> bool:
        """Send notification when a child is linked to an existing parent account."""
        team_info = f" ({team_name})" if team_name else ""
        
        subject = f"Neues Kind mit Ihrem Konto verknüpft"
        body_text = f"""Hallo {parent_name},

{child_name}{team_info} wurde mit Ihrem Handball Manager Konto verknüpft.

Sie können jetzt alle Termine und Informationen dieses Kindes in Ihrem Dashboard einsehen.

Zu Ihrem Dashboard:
{settings.FRONTEND_URL}/dashboard

Mit freundlichen Grüßen,
Das Handball Manager Team
"""
        
        return await self._send_email(to_email, subject, body_text, None)


email_service = EmailService()
