"""
Transactional email via Resend (https://resend.com).
Falls back to SMTP if RESEND_API_KEY is not set.
Falls back to console logging in dev if neither is configured.
"""
from __future__ import annotations

import logging
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from app.core.config import settings

logger = logging.getLogger(__name__)


def _send(to: str, subject: str, html: str, text: str) -> None:
    # Try Resend first
    if settings.resend_api_key:
        try:
            import resend
            resend.api_key = settings.resend_api_key
            resend.Emails.send({
                "from": "Pumpr <noreply@pumpr.co.uk>",
                "to": [to],
                "subject": subject,
                "html": html,
                "text": text,
            })
            logger.info("Email sent via Resend to %s: %s", to, subject)
            return
        except Exception as e:
            logger.error("Resend failed: %s", e)

    # Fall back to SMTP
    if settings.smtp_host:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = settings.smtp_from
        msg["To"] = to
        msg.attach(MIMEText(text, "plain"))
        msg.attach(MIMEText(html, "html"))
        with smtplib.SMTP(settings.smtp_host, settings.smtp_port) as server:
            server.ehlo()
            server.starttls()
            if settings.smtp_user and settings.smtp_password:
                server.login(settings.smtp_user, settings.smtp_password)
            server.sendmail(settings.smtp_from, to, msg.as_string())
        logger.info("Email sent via SMTP to %s: %s", to, subject)
        return

    # Dev fallback
    logger.info("=== [DEV EMAIL] To: %s | Subject: %s ===", to, subject)
    logger.info(text)


async def send_verification_email(email: str, token: str) -> None:
    link = f"{settings.app_base_url}/verify-email?token={token}"
    html = f"""
<!DOCTYPE html>
<html>
<body style="font-family: sans-serif; background: #0f0f0f; color: #e8e8e8; padding: 40px;">
  <div style="max-width: 480px; margin: 0 auto; background: #1a1a1a; border-radius: 12px; padding: 32px; border: 1px solid #2a2a2a;">
    <h1 style="color: #f5a623; font-size: 28px; margin: 0 0 8px;">⛽ Pumpr</h1>
    <h2 style="color: #e8e8e8; font-size: 18px; margin: 0 0 24px;">Verify your email address</h2>
    <p style="color: #a0a0a8; line-height: 1.6;">Thanks for signing up. Click the button below to verify your email address.</p>
    <a href="{link}" style="display: inline-block; margin: 24px 0; background: #f5a623; color: #000; font-weight: 700; padding: 12px 28px; border-radius: 8px; text-decoration: none;">Verify email address</a>
    <p style="color: #5a5a68; font-size: 13px;">This link expires in 24 hours. If you didn't create a Pumpr account, you can ignore this email.</p>
  </div>
</body>
</html>"""
    text = f"Welcome to Pumpr!\n\nVerify your email:\n{link}\n\nExpires in 24 hours."
    _send(email, "Verify your Pumpr email address", html, text)


async def send_password_reset_email(email: str, token: str) -> None:
    link = f"{settings.app_base_url}/reset-password?token={token}"
    html = f"""
<!DOCTYPE html>
<html>
<body style="font-family: sans-serif; background: #0f0f0f; color: #e8e8e8; padding: 40px;">
  <div style="max-width: 480px; margin: 0 auto; background: #1a1a1a; border-radius: 12px; padding: 32px; border: 1px solid #2a2a2a;">
    <h1 style="color: #f5a623; font-size: 28px; margin: 0 0 8px;">⛽ Pumpr</h1>
    <h2 style="color: #e8e8e8; font-size: 18px; margin: 0 0 24px;">Reset your password</h2>
    <p style="color: #a0a0a8; line-height: 1.6;">You requested a password reset. Click the button below to set a new password.</p>
    <a href="{link}" style="display: inline-block; margin: 24px 0; background: #f5a623; color: #000; font-weight: 700; padding: 12px 28px; border-radius: 8px; text-decoration: none;">Reset password</a>
    <p style="color: #5a5a68; font-size: 13px;">This link expires in 1 hour. If you didn't request this, you can safely ignore this email.</p>
  </div>
</body>
</html>"""
    text = f"Pumpr password reset\n\nReset your password:\n{link}\n\nExpires in 1 hour."
    _send(email, "Reset your Pumpr password", html, text)


async def send_resend_verification_email(email: str) -> None:
    """Resend a new verification email - generates a fresh token."""
    # This is called from the API endpoint - token generation happens there
    pass
