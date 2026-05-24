"""Email service for sending emails via SMTP."""
import logging
from typing import Optional
from pathlib import Path

from fastapi_mail import FastMail, MessageSchema, ConnectionConfig
from fastapi_mail.errors import ConnectionErrors
from jinja2 import Environment, FileSystemLoader, TemplateNotFound, select_autoescape

from app.core.config import settings

logger = logging.getLogger(__name__)


class EmailService:
    """Service for sending emails via SMTP with HTML templates."""

    def __init__(self):
        self._fm: Optional[FastMail] = None
        self._templates_dir = Path(__file__).parent.parent / "templates" / "email"
        # Real Jinja Environment with a FileSystemLoader — without this the
        # `{% extends "base.html" %}` in the HTML templates raises
        # "no loader for this environment specified" and every HTML email
        # silently fails (the BackgroundTasks swallow the traceback).
        self._jinja = Environment(
            loader=FileSystemLoader(self._templates_dir),
            autoescape=select_autoescape(["html"]),  # text templates stay raw
            keep_trailing_newline=True,
        )
    
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
        """Render a Jinja2 template through the FileSystemLoader so the
        HTML variants can `{% extends "base.html" %}` cleanly. Falls back
        to the .txt variant if the requested file is missing.
        """
        ext = ".txt" if text_fallback else ".html"
        name = f"{template_name}{ext}"
        try:
            template = self._jinja.get_template(name)
        except TemplateNotFound:
            if not text_fallback:
                return self._render_template(template_name, context, text_fallback=True)
            return f"Error: Template {template_name} not found"
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
            # fastapi-mail 1.4 MessageSchema has no `alternatives` attribute;
            # trying to set it raises and tanks every HTML send. Send the
            # HTML version when present (mail clients downgrade to a
            # text/plain rendering automatically); fall back to text
            # otherwise.
            if body_html:
                message = MessageSchema(
                    subject=subject,
                    recipients=[to_email],
                    body=body_html,
                    subtype="html",
                )
            else:
                message = MessageSchema(
                    subject=subject,
                    recipients=[to_email],
                    body=body_text,
                    subtype="plain",
                )

            await fm.send_message(message)
            logger.info("Email sent successfully to %s", to_email)
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

    async def send_password_reset_email(
        self,
        to_email: str,
        first_name: str,
        reset_link: str,
        expires_in: str = "1 Stunde",
    ) -> bool:
        """Send a password-reset link. Closes the long-standing TODO at
        api/v1/endpoints/auth.py:222.
        """
        context = {
            "first_name": first_name,
            "reset_link": reset_link,
            "expires_in": expires_in,
        }
        subject = "Passwort zurücksetzen — Handball Manager"
        body_text = self._render_template("password_reset", context, text_fallback=True)
        body_html = self._render_template("password_reset", context)
        return await self._send_email(to_email, subject, body_text, body_html)

    async def send_test_email(self, to_email: str) -> bool:
        """Send a no-template "ping" so operators can verify SMTP wiring
        from the admin UI / curl without dragging real flows in.
        """
        subject = "Handball Manager — SMTP-Test"
        body_text = (
            "Dies ist eine Test-E-Mail vom Handball Manager Backend.\n\n"
            "Wenn du diese E-Mail erhältst, sind die SMTP-Einstellungen korrekt konfiguriert.\n"
        )
        body_html = (
            "<p>Dies ist eine <strong>Test-E-Mail</strong> vom Handball Manager Backend.</p>"
            "<p>Wenn du diese E-Mail erhältst, sind die SMTP-Einstellungen korrekt konfiguriert.</p>"
        )
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

    async def send_registration_pending_to_approver(
        self,
        to_email: str,
        approver_name: str,
        applicant_name: str,
        role: str,
        team_name: Optional[str] = None,
    ) -> bool:
        """Tell an approver a new registration awaits their decision."""
        role_display = self._get_role_display(role)
        team_info = f" für das Team {team_name}" if team_name else ""
        subject = "Neue Registrierung wartet auf Freigabe"
        body_text = f"""Hallo {approver_name},

{applicant_name} hat sich als {role_display}{team_info} registriert und wartet auf Ihre Freigabe.

Bitte prüfen Sie die Anfrage in den Genehmigungen:
{settings.FRONTEND_URL}/approvals

Mit freundlichen Grüßen,
Das Handball Manager Team
"""
        return await self._send_email(to_email, subject, body_text, None)

    async def send_registration_approved(
        self, to_email: str, first_name: str
    ) -> bool:
        """Tell an applicant their registration was approved."""
        subject = "Ihre Registrierung wurde freigegeben"
        body_text = f"""Hallo {first_name},

Ihre Registrierung beim Handball Manager wurde freigegeben. Sie können sich jetzt anmelden:
{settings.FRONTEND_URL}/login

Mit freundlichen Grüßen,
Das Handball Manager Team
"""
        return await self._send_email(to_email, subject, body_text, None)

    async def send_registration_rejected(
        self, to_email: str, first_name: str, reason: str
    ) -> bool:
        """Tell an applicant their registration was declined, with a reason."""
        subject = "Ihre Registrierung wurde abgelehnt"
        body_text = f"""Hallo {first_name},

Ihre Registrierung beim Handball Manager wurde leider abgelehnt.

Begründung: {reason}

Bei Fragen wenden Sie sich bitte an Ihren Verein.

Mit freundlichen Grüßen,
Das Handball Manager Team
"""
        return await self._send_email(to_email, subject, body_text, None)


email_service = EmailService()
