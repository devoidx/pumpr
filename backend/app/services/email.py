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


async def send_welcome_setup_email(email: str, token: str) -> None:
    """Send welcome email with password setup link after Stripe payment."""
    link = f"{settings.app_base_url}/setup-password?token={token}"
    html = f"""
<!DOCTYPE html>
<html>
<body style="font-family: sans-serif; background: #0f0f0f; color: #e8e8e8; padding: 40px;">
  <div style="max-width: 480px; margin: 0 auto; background: #1a1a1a; border-radius: 12px; padding: 32px; border: 1px solid #2a2a2a;">
    <h1 style="color: #f5a623; font-size: 28px; margin: 0 0 8px;">⛽ Welcome to Pumpr!</h1>
    <h2 style="color: #e8e8e8; font-size: 18px; margin: 0 0 24px;">Your Pro account is ready</h2>
    <p style="color: #a0a0a8; line-height: 1.6;">Thanks for subscribing to Pumpr Pro. Click the button below to set your password and start saving on fuel.</p>
    <a href="{link}" style="display: inline-block; margin: 24px 0; background: #f5a623; color: #000; font-weight: 700; padding: 12px 28px; border-radius: 8px; text-decoration: none;">Set your password →</a>
    <p style="color: #5a5a68; font-size: 13px;">This link expires in 24 hours. If you didn't subscribe to Pumpr, please ignore this email.</p>
  </div>
</body>
</html>"""
    text = f"Welcome to Pumpr!\n\nSet your password:\n{link}\n\nExpires in 24 hours."
    _send(email, "Welcome to Pumpr — set your password", html, text)


async def send_resend_verification_email(email: str) -> None:
    """Resend a new verification email - generates a fresh token."""
    # This is called from the API endpoint - token generation happens there
    pass


async def send_newsletter_email(email: str, title: str, summary: str, slug: str, post_type: str) -> None:
    """Send a single blog newsletter email to one subscriber."""
    url = f"https://pumpr.co.uk/blog/{slug}"
    label = "Weekly Fuel Price Update" if post_type == "weekly_prices" else "Fuel Industry News"
    html = f"""
<!DOCTYPE html>
<html>
<body style="font-family: sans-serif; background: #0f0f0f; color: #e8e8e8; padding: 40px;">
  <div style="max-width: 520px; margin: 0 auto; background: #1a1a1a; border-radius: 12px; padding: 32px; border: 1px solid #2a2a2a;">
    <h1 style="color: #f5a623; font-size: 24px; margin: 0 0 4px;">⛽ Pumpr</h1>
    <p style="color: #5a5a68; font-size: 12px; margin: 0 0 24px; font-family: monospace;">{label}</p>
    <h2 style="color: #e8e8e8; font-size: 20px; margin: 0 0 16px; line-height: 1.3;">{title}</h2>
    <p style="color: #a0a0a8; line-height: 1.7; font-size: 15px;">{summary}</p>
    <a href="{url}" style="display: inline-block; margin: 28px 0 16px; background: #f5a623; color: #000; font-weight: 700; padding: 12px 28px; border-radius: 8px; text-decoration: none; font-size: 15px;">Read full post →</a>
    <hr style="border: none; border-top: 1px solid #2a2a2a; margin: 24px 0;" />
    <p style="color: #3a3a48; font-size: 12px; line-height: 1.6;">
      You're receiving this because you subscribed to Pumpr blog updates.<br/>
      <a href="https://pumpr.co.uk/profile" style="color: #5a5a68;">Unsubscribe</a>
    </p>
  </div>
</body>
</html>"""
    text = f"{label}\n\n{title}\n\n{summary}\n\nRead more: {url}\n\nUnsubscribe: https://pumpr.co.uk/profile"
    _send(email, f"Pumpr: {title}", html, text)


async def send_blog_newsletter(post_id: str) -> int:
    """Send newsletter email to all opted-in verified subscribers for a given blog post. Returns send count."""
    import uuid

    from sqlalchemy import select

    from app.db.session import AsyncSessionLocal
    from app.models.blog import BlogPost
    from app.models.user import User

    sent = 0
    async with AsyncSessionLocal() as db:
        post = await db.get(BlogPost, uuid.UUID(post_id))
        if not post:
            logger.error("send_blog_newsletter: post %s not found", post_id)
            return 0
        result = await db.execute(
            select(User).where(
                User.blog_newsletter,
                User.is_verified,
                User.email.is_not(None),
            )
        )
        subscribers = result.scalars().all()
        logger.info("Sending newsletter for '%s' to %d subscribers", post.title, len(subscribers))
        for user in subscribers:
            try:
                await send_newsletter_email(
                    email=user.email,
                    title=post.title,
                    summary=post.summary,
                    slug=post.slug,
                    post_type=post.post_type,
                )
                sent += 1
            except Exception as e:
                logger.error("Newsletter send failed for %s: %s", user.email, e)
    logger.info("Newsletter sent to %d/%d subscribers", sent, len(subscribers))
    return sent
