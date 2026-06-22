import smtplib
from email.message import EmailMessage
import logging
from app.core.config import get_settings
import asyncio

logger = logging.getLogger("systemforge.email")

def _send_email_sync(to_email: str, subject: str, content: str):
    settings = get_settings()
    if not settings.smtp_host:
        logger.info(f"\n*** SIMULATED EMAIL (MOCK/DEMO) ***\nTo: {to_email}\nSubject: {subject}\nContent: {content}\n***\n")
        return

    msg = EmailMessage()
    msg.set_content(content)
    msg["Subject"] = subject
    msg["From"] = settings.smtp_from_email
    msg["To"] = to_email

    try:
        with smtplib.SMTP(settings.smtp_host, settings.smtp_port) as server:
            server.starttls()
            if settings.smtp_user and settings.smtp_password:
                server.login(settings.smtp_user, settings.smtp_password)
            server.send_message(msg)
        logger.info(f"Email successfully sent to {to_email}")
    except Exception as e:
        logger.error(f"Failed to send email to {to_email}: {e}")

async def send_password_reset_email(to_email: str, token: str):
    settings = get_settings()
    link = f"{settings.public_app_url.rstrip('/')}/reset-password?token={token}"
    content = f"You requested a password reset. Click the link below to reset your password:\n\n{link}\n\nIf you did not request this, please ignore this email."
    
    loop = asyncio.get_running_loop()
    await loop.run_in_executor(None, _send_email_sync, to_email, "Password Reset", content)
