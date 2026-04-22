"""
Transactional email for auth flows.
Set SMTP_HOST in .env to send real mail.
If SMTP_HOST is blank, tokens are logged to stdout (dev mode).
"""
from __future__ import annotations

import logging
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from app.core.config import settings

logger = logging.getLogger(__name__)


def _send(to: str, subject: str, html: str, text: str) -> None:
    if not settings.smtp_host:
        logger.info("=== [DEV EMAIL] To: %s | Subject: %s ===", to, subject)
        logger.info(text)
        return

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

    logger.info("Email sent to %s: %s", to, subject)


async def send_verification_email(email: str, token: str) -> None:
    link = f"{settings.app_base_url}/verify-email?token={token}"
    html = f"""
    <h2>Welcome to Pumpr ⛽</h2>
    <p>Please verify your email address:</p>
    <p><a href="{link}">Verify email address</a></p>
    <p>This link expires in 24 hours.</p>
    """
    text = f"Welcome to Pumpr!\n\nVerify your email:\n{link}\n\nExpires in 24 hours."
    _send(email, "Verify your Pumpr email address", html, text)


async def send_password_reset_email(email: str, token: str) -> None:
    link = f"{settings.app_base_url}/reset-password?token={token}"
    html = f"""
    <h2>Pumpr password reset</h2>
    <p>Reset your password:</p>
    <p><a href="{link}">Reset password</a></p>
    <p>This link expires in 1 hour.</p>
    """
    text = f"Pumpr password reset\n\nReset your password:\n{link}\n\nExpires in 1 hour."
    _send(email, "Reset your Pumpr password", html, text)
