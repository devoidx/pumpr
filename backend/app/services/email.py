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


async def send_price_alert_email(
    email: str,
    station_name: str,
    station_id: str,
    fuel_type: str,
    alert_type: str,
    threshold: float,
    current_price: float,
    disable_token: str,
) -> None:
    """Send a price alert triggered email."""
    disable_url = f"https://pumpr.co.uk/alerts/disable?token={disable_token}"
    station_url = f"https://pumpr.co.uk/stations/{station_id}?fuel={fuel_type}"

    if alert_type == "below_pence":
        subject = f"Price alert: {fuel_type} at {station_name} is now {current_price:.1f}p"
        alert_desc = f"below your threshold of {threshold:.1f}p"
        detail_html = f"""
        <p style="color: #a0a0a8; line-height: 1.7; font-size: 15px;">
          The price of <strong style="color:#e8e8e8;">{fuel_type}</strong> at <strong style="color:#e8e8e8;">{station_name}</strong>
          has dropped to <span style="color:#f5a623; font-size:22px; font-weight:700;">{current_price:.1f}p/litre</span> —
          below your alert threshold of {threshold:.1f}p.
        </p>"""
        detail_text = f"{fuel_type} at {station_name} is now {current_price:.1f}p/litre (your threshold: {threshold:.1f}p)"
    else:
        subject = f"Price alert: {fuel_type} price changed at {station_name}"
        alert_desc = f"changed by more than {threshold:.1f}%"
        detail_html = f"""
        <p style="color: #a0a0a8; line-height: 1.7; font-size: 15px;">
          The price of <strong style="color:#e8e8e8;">{fuel_type}</strong> at <strong style="color:#e8e8e8;">{station_name}</strong>
          has changed by more than {threshold:.1f}% and is now <span style="color:#f5a623; font-size:22px; font-weight:700;">{current_price:.1f}p/litre</span>.
        </p>"""
        detail_text = f"{fuel_type} at {station_name} has changed by >{threshold:.1f}% and is now {current_price:.1f}p/litre"

    html = f"""
<!DOCTYPE html>
<html>
<body style="font-family: sans-serif; background: #0f0f0f; color: #e8e8e8; padding: 40px;">
  <div style="max-width: 520px; margin: 0 auto; background: #1a1a1a; border-radius: 12px; padding: 32px; border: 1px solid #2a2a2a;">
    <h1 style="color: #f5a623; font-size: 24px; margin: 0 0 4px;">⛽ Pumpr</h1>
    <p style="color: #5a5a68; font-size: 12px; margin: 0 0 24px; font-family: monospace;">Price Alert</p>
    <h2 style="color: #e8e8e8; font-size: 20px; margin: 0 0 16px;">🔔 {station_name}</h2>
    {detail_html}
    <div style="background:#111; border-radius:8px; padding:16px; margin:20px 0; border:1px solid #2a2a2a;">
      <table style="width:100%; font-size:13px; color:#a0a0a8;">
        <tr><td>Fuel type</td><td style="text-align:right; color:#e8e8e8;"><strong>{fuel_type}</strong></td></tr>
        <tr><td>Current price</td><td style="text-align:right; color:#f5a623;"><strong>{current_price:.1f}p/litre</strong></td></tr>
        <tr><td>Your alert</td><td style="text-align:right; color:#e8e8e8;">{alert_desc}</td></tr>
      </table>
    </div>
    <a href="{station_url}" style="display: inline-block; margin: 8px 0; background: #f5a623; color: #000; font-weight: 700; padding: 12px 28px; border-radius: 8px; text-decoration: none; font-size: 15px;">View station →</a>
    <hr style="border: none; border-top: 1px solid #2a2a2a; margin: 24px 0;" />
    <p style="color: #3a3a48; font-size: 12px; line-height: 1.8;">
      You set up this price alert on Pumpr. Alerts fire at most once every 24 hours.<br/>
      <a href="{disable_url}" style="color: #5a5a68;">Disable this alert</a> &nbsp;·&nbsp;
      <a href="https://pumpr.co.uk/my-alerts" style="color: #5a5a68;">Manage all alerts</a>
    </p>
  </div>
</body>
</html>"""
    text = f"{subject}\n\n{detail_text}\n\nView station: {station_url}\nDisable this alert: {disable_url}\nManage alerts: https://pumpr.co.uk/my-alerts"
    _send(email, subject, html, text)


async def send_spending_digest_email(
    email: str,
    username: str | None,
    month_label: str,
    total_spend_gbp: float,
    total_litres: float,
    avg_ppl: float,
    fillup_count: int,
    predicted_monthly: float | None,
    ytd_spend_gbp: float | None,
    vehicles: list[dict],
) -> None:
    """Send monthly fuel spending digest email to a Pro user."""
    name = username or "there"
    vehicle_rows = ""
    for v in vehicles:
        mpg_cell = f"{v['mpg']:.1f} mpg" if v.get('mpg') else "—"
        vehicle_rows += f"""
        <tr>
          <td style="padding:6px 0; color:#a0a0a8;">{v['name']}</td>
          <td style="padding:6px 0; text-align:right; color:#e8e8e8;">£{v['spend_gbp']:.2f}</td>
          <td style="padding:6px 0; text-align:right; color:#a0a0a8;">{v['litres']:.1f}L</td>
          <td style="padding:6px 0; text-align:right; color:#a0a0a8;">{v['fillups']} fill-up{'s' if v['fillups'] != 1 else ''}</td>
          <td style="padding:6px 0; text-align:right; color:#a0a0a8;">{mpg_cell}</td>
        </tr>"""

    ytd_html = ""
    if ytd_spend_gbp:
        ytd_html = f"""
    <div style="background:#111; border-radius:8px; padding:14px 16px; margin:16px 0; border:1px solid #2a2a2a;">
      <div style="font-size:12px; color:#5a5a68; margin-bottom:4px;">Year to date</div>
      <div style="font-size:20px; font-weight:700; color:#e8e8e8;">£{ytd_spend_gbp:.2f}</div>
      <div style="font-size:11px; color:#5a5a68; margin-top:2px;">Total fuel spend since 1 Jan {month_label.split()[-1]}</div>
    </div>"""

    prediction_html = ""
    if predicted_monthly:
        prediction_html = f"""
    <div style="background:#111; border-radius:8px; padding:14px 16px; margin:16px 0; border:1px solid #2a2a2a;">
      <div style="font-size:12px; color:#5a5a68; margin-bottom:4px;">Predicted next month</div>
      <div style="font-size:20px; font-weight:700; color:#f5a623;">£{predicted_monthly:.2f}</div>
      <div style="font-size:11px; color:#5a5a68; margin-top:2px;">Based on your last 3 months average</div>
    </div>"""

    html = f"""
<!DOCTYPE html>
<html>
<body style="font-family: sans-serif; background: #0f0f0f; color: #e8e8e8; padding: 40px;">
  <div style="max-width: 520px; margin: 0 auto; background: #1a1a1a; border-radius: 12px; padding: 32px; border: 1px solid #2a2a2a;">
    <h1 style="color: #f5a623; font-size: 24px; margin: 0 0 4px;">⛽ Pumpr</h1>
    <p style="color: #5a5a68; font-size: 12px; margin: 0 0 24px; font-family: monospace;">Monthly Spending Digest</p>
    <h2 style="color: #e8e8e8; font-size: 20px; margin: 0 0 4px;">Your fuel spend for {month_label}</h2>
    <p style="color: #5a5a68; font-size: 13px; margin: 0 0 24px;">Hi {name}, here's your monthly fuel spending summary.</p>
    <div style="display:flex; gap:12px; margin-bottom:20px;">
      <div style="flex:1; background:#111; border-radius:8px; padding:14px 16px; border:1px solid #2a2a2a;">
        <div style="font-size:12px; color:#5a5a68; margin-bottom:4px;">Total spent</div>
        <div style="font-size:24px; font-weight:700; color:#f5a623;">£{total_spend_gbp:.2f}</div>
      </div>
      <div style="flex:1; background:#111; border-radius:8px; padding:14px 16px; border:1px solid #2a2a2a;">
        <div style="font-size:12px; color:#5a5a68; margin-bottom:4px;">Total litres</div>
        <div style="font-size:24px; font-weight:700; color:#e8e8e8;">{total_litres:.1f}L</div>
      </div>
      <div style="flex:1; background:#111; border-radius:8px; padding:14px 16px; border:1px solid #2a2a2a;">
        <div style="font-size:12px; color:#5a5a68; margin-bottom:4px;">Avg price</div>
        <div style="font-size:24px; font-weight:700; color:#e8e8e8;">{avg_ppl:.1f}p</div>
      </div>
    </div>
    {f'<div style="background:#111; border-radius:8px; padding:14px 16px; margin-bottom:16px; border:1px solid #2a2a2a;"><table style="width:100%; font-size:13px; border-collapse:collapse;"><thead><tr><th style="text-align:left; color:#5a5a68; padding-bottom:8px;">Vehicle</th><th style="text-align:right; color:#5a5a68; padding-bottom:8px;">Spent</th><th style="text-align:right; color:#5a5a68; padding-bottom:8px;">Litres</th><th style="text-align:right; color:#5a5a68; padding-bottom:8px;">Fill-ups</th><th style="text-align:right; color:#5a5a68; padding-bottom:8px;">MPG</th></tr></thead><tbody>{vehicle_rows}</tbody></table></div>' if vehicles else ''}
    {ytd_html}
    {prediction_html}
    <p style="font-size:13px; color:#5a5a68; margin:16px 0;">{fillup_count} fill-up{'s' if fillup_count != 1 else ''} logged this month.</p>
    <a href="https://pumpr.co.uk" style="display: inline-block; margin: 8px 0 24px; background: #f5a623; color: #000; font-weight: 700; padding: 12px 28px; border-radius: 8px; text-decoration: none; font-size: 15px;">View full tracker →</a>
    <hr style="border: none; border-top: 1px solid #2a2a2a; margin: 24px 0;" />
    <p style="color: #3a3a48; font-size: 12px; line-height: 1.6;">
      You're receiving this because you enabled monthly spending digests on Pumpr.<br/>
      <a href="https://pumpr.co.uk/profile" style="color: #5a5a68;">Manage email preferences</a>
    </p>
  </div>
</body>
</html>"""
    text = (
        f"Pumpr Monthly Spending Digest — {month_label}\n\n"
        f"Hi {name},\n\n"
        f"Total spent: £{total_spend_gbp:.2f}\n"
        f"Total litres: {total_litres:.1f}L\n"
        f"Average price: {avg_ppl:.1f}p/litre\n"
        f"Fill-ups logged: {fillup_count}\n"
    )
    if ytd_spend_gbp:
        text += f"Year to date: £{ytd_spend_gbp:.2f}\n"
    if predicted_monthly:
        text += f"Predicted next month: £{predicted_monthly:.2f}\n"
    text += "\nView your full tracker: https://pumpr.co.uk\nManage preferences: https://pumpr.co.uk/profile"
    _send(email, f"Pumpr: Your fuel spend for {month_label}", html, text)


async def send_monthly_spending_digests() -> int:
    """Send monthly spending digest to all opted-in Pro users with fillups last month. Returns send count."""
    from calendar import month_name
    from datetime import date, timedelta

    from sqlalchemy import select, text

    from app.db.session import AsyncSessionLocal
    from app.models.user import User

    today = date.today()
    # Last month's date range
    first_of_this_month = today.replace(day=1)
    last_month_end = first_of_this_month - timedelta(days=1)
    last_month_start = last_month_end.replace(day=1)
    month_label = f"{month_name[last_month_end.month]} {last_month_end.year}"

    sent = 0
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(User).where(
                User.spending_digest.is_(True),
                User.is_verified.is_(True),
                User.role.in_(("pro", "admin")),
                User.email.is_not(None),
            )
        )
        users = result.scalars().all()
        logger.info("Sending spending digest for %s to %d eligible users", month_label, len(users))

        for user in users:
            try:
                # Overall stats for last month
                overall = await db.execute(
                    text("""
                        SELECT
                            COUNT(*) as fillup_count,
                            ROUND(SUM(litres)::numeric, 2) as total_litres,
                            ROUND(SUM(total_cost_pence)::numeric / 100, 2) as total_spend_gbp,
                            ROUND(AVG(price_pence_per_litre)::numeric, 2) as avg_ppl
                        FROM fuel_fillups
                        WHERE user_id = :uid
                          AND filled_at >= :start AND filled_at <= :end
                    """),
                    {"uid": user.id, "start": last_month_start, "end": last_month_end},
                )
                o = overall.fetchone()
                if not o or not o.fillup_count:
                    continue  # No fillups last month, skip

                # Per-vehicle breakdown
                veh_result = await db.execute(
                    text("""
                        SELECT
                            v.id as vehicle_id, v.nickname, v.make, v.model,
                            ROUND(SUM(f.total_cost_pence)::numeric / 100, 2) as spend_gbp,
                            ROUND(SUM(f.litres)::numeric, 2) as litres,
                            COUNT(*) as fillups
                        FROM fuel_fillups f
                        JOIN user_vehicles v ON f.vehicle_id = v.id
                        WHERE f.user_id = :uid
                          AND f.filled_at >= :start AND f.filled_at <= :end
                        GROUP BY v.id, v.nickname, v.make, v.model
                        ORDER BY spend_gbp DESC
                    """),
                    {"uid": user.id, "start": last_month_start, "end": last_month_end},
                )
                vehicles = []
                for r in veh_result.fetchall():
                    name = r.nickname or f"{r.make or ''} {r.model or ''}".strip() or "Vehicle"
                    # Compute MPG for this vehicle using odometer data
                    mpg_result = await db.execute(
                        text("""
                            SELECT litres, odometer_miles,
                                LAG(odometer_miles) OVER (ORDER BY filled_at, created_at) as prev_odo
                            FROM fuel_fillups
                            WHERE user_id = :uid AND vehicle_id = :vid
                              AND odometer_miles IS NOT NULL
                            ORDER BY filled_at, created_at
                        """),
                        {"uid": user.id, "vid": r.vehicle_id},
                    )
                    mpg_values = []
                    for mr in mpg_result.fetchall():
                        if mr.prev_odo and mr.odometer_miles > mr.prev_odo and mr.litres > 0:
                            miles = mr.odometer_miles - mr.prev_odo
                            actual_mpg = (miles / mr.litres) * 4.54609
                            if 10 < actual_mpg < 200:
                                mpg_values.append(actual_mpg)
                    avg_mpg = round(sum(mpg_values) / len(mpg_values), 1) if mpg_values else None
                    vehicles.append({
                        "name": name,
                        "spend_gbp": float(r.spend_gbp),
                        "litres": float(r.litres),
                        "fillups": int(r.fillups),
                        "mpg": avg_mpg,
                    })

                # Year to date spend
                year_start = last_month_end.replace(month=1, day=1)
                ytd_result = await db.execute(
                    text("""
                        SELECT ROUND(SUM(total_cost_pence)::numeric / 100, 2) as ytd_spend
                        FROM fuel_fillups
                        WHERE user_id = :uid AND filled_at >= :year_start AND filled_at <= :end
                    """),
                    {"uid": user.id, "year_start": year_start, "end": last_month_end},
                )
                ytd_row = ytd_result.fetchone()
                ytd_spend_gbp = float(ytd_row.ytd_spend) if ytd_row and ytd_row.ytd_spend else None

                # Predicted monthly spend (last 3 months avg)
                monthly_result = await db.execute(
                    text("""
                        SELECT ROUND(SUM(total_cost_pence)::numeric / 100, 2) as spend_gbp
                        FROM fuel_fillups
                        WHERE user_id = :uid
                          AND filled_at >= :start3 AND filled_at < :start
                        GROUP BY TO_CHAR(filled_at, 'YYYY-MM')
                        ORDER BY 1
                    """),
                    {
                        "uid": user.id,
                        "start3": last_month_start.replace(year=last_month_start.year if last_month_start.month > 3 else last_month_start.year - 1,
                                                           month=(last_month_start.month - 3) % 12 or 12),
                        "start": last_month_start,
                    },
                )
                monthly_rows = [float(r.spend_gbp) for r in monthly_result.fetchall()]
                predicted_monthly = round(sum(monthly_rows) / len(monthly_rows), 2) if monthly_rows else None

                await send_spending_digest_email(
                    email=user.email,
                    username=user.username,
                    month_label=month_label,
                    total_spend_gbp=float(o.total_spend_gbp),
                    total_litres=float(o.total_litres),
                    avg_ppl=float(o.avg_ppl),
                    fillup_count=int(o.fillup_count),
                    predicted_monthly=predicted_monthly,
                    ytd_spend_gbp=ytd_spend_gbp,
                    vehicles=vehicles,
                )
                sent += 1
            except Exception as e:
                logger.error("Spending digest send failed for %s: %s", user.email, e)

    logger.info("Spending digest sent to %d/%d eligible users", sent, len(users))
    return sent
