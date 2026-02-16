"""Email service for sending invitation emails."""
import os
from typing import Optional

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
        
        print(f"""
        📧 INVITATION EMAIL
        To: {to_email}
        Subject: Einladung zum Handball Manager
        
        Hallo {first_name},
        
        {inviter_name} lädt dich ein, dem Handball Manager beizutreten.
        
        Team: {team_name or 'Kein Team'}
        Rolle: {role}
        
        Klicke hier, um die Einladung anzunehmen:
        {invitation_link}
        
        Dieser Link ist 7 Tage gültig.
        
        Mit freundlichen Grüßen,
        Das Handball Manager Team
        """)
        
        return True
    
    @staticmethod
    def send_welcome_email(to_email: str, first_name: str) -> bool:
        """Send welcome email after successful registration."""
        print(f"""
        📧 WELCOME EMAIL
        To: {to_email}
        Subject: Willkommen beim Handball Manager!
        
        Hallo {first_name},
        
        Willkommen beim Handball Manager! Dein Konto wurde erfolgreich erstellt.
        
        Mit freundlichen Grüßen,
        Das Handball Manager Team
        """)
        
        return True


email_service = EmailService()
