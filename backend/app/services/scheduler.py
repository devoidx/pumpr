import logging

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger

from app.core.config import settings
from app.services.ingestion import ingest_prices, sync_stations
from app.services.retention import apply_retention_policy

logger = logging.getLogger(__name__)

scheduler = AsyncIOScheduler()


async def sync_stations_job() -> None:
    logger.info("Scheduler: syncing stations")
    try:
        await sync_stations()
        logger.info("Scheduler: station sync complete")
    except Exception as e:
        logger.error(f"Scheduler: station sync failed: {e}")


async def poll_prices() -> None:
    logger.info("Scheduler: polling prices")
    try:
        count = await ingest_prices()
        logger.info(f"Scheduler: ingested {count} price records")
        # Warm city cache in background after poll (delayed to avoid DB contention)
        import asyncio
        async def _delayed_warmup():
            await asyncio.sleep(60)
            await warm_city_cache_job()
        asyncio.ensure_future(_delayed_warmup())
    except Exception as e:
        logger.exception(f"Scheduler: price poll failed: {e}")


async def run_retention() -> None:
    logger.info("Scheduler: running retention policy")
    try:
        await apply_retention_policy()
    except Exception as e:
        logger.error(f"Scheduler: retention failed: {e}")


async def post_daily_averages_job() -> None:
    try:
        from app.services.social import post_daily_averages
        await post_daily_averages(dry_run=False)
    except Exception as e:
        logger.error(f"Scheduler: daily averages post failed: {e}")


async def post_cheapest_job() -> None:
    try:
        from app.services.social import post_cheapest_station
        await post_cheapest_station("E10", dry_run=False)
    except Exception as e:
        logger.error(f"Scheduler: cheapest post failed: {e}")


async def post_cheapest_diesel_job() -> None:
    try:
        from app.services.social import post_cheapest_diesel
        await post_cheapest_diesel(dry_run=False)
    except Exception as e:
        logger.error(f"Scheduler: cheapest diesel post failed: {e}")


async def post_by_country_job() -> None:
    try:
        from app.services.social import post_cheapest_by_country
        await post_cheapest_by_country("E10", dry_run=False)
    except Exception as e:
        logger.error(f"Scheduler: by country post failed: {e}")


async def post_by_country_diesel_job() -> None:
    try:
        from app.services.social import post_cheapest_by_country
        await post_cheapest_by_country("B7", dry_run=False)
    except Exception as e:
        logger.error(f"Scheduler: by country diesel post failed: {e}")


async def post_county_e10_job() -> None:
    try:
        from app.services.social import post_cheapest_by_county
        await post_cheapest_by_county("E10", dry_run=False)
    except Exception as e:
        logger.error(f"Scheduler: county E10 post failed: {e}")


async def check_blog_sources_job() -> None:
    try:
        from app.services.source_monitor import check_sources
        posts = await check_sources()
        logger.info(f"Scheduler: blog source check complete — {len(posts)} new posts")
        if posts:
            from app.services.email import send_blog_newsletter
            for post in posts:
                sent = await send_blog_newsletter(str(post.id))
                logger.info(f"Newsletter sent to {sent} subscribers for '{post.title}'")
    except Exception as e:
        logger.error(f"Scheduler: blog source check failed: {e}")


async def generate_weekly_blog_post_job() -> None:
    try:
        import datetime

        from app.services.blog_generator import generate_weekly_post
        week_num = datetime.datetime.now().isocalendar()[1]
        post = await generate_weekly_post(style_index=week_num)
        if post:
            logger.info(f"Weekly blog post generated: {post.title}")
            from app.services.email import send_blog_newsletter
            sent = await send_blog_newsletter(str(post.id))
            logger.info(f"Newsletter sent to {sent} subscribers")
    except Exception as e:
        logger.error(f"Scheduler: weekly blog post generation failed: {e}")


async def refresh_threads_token_job() -> None:
    try:
        from app.services.social import refresh_threads_token
        await refresh_threads_token()
    except Exception as e:
        logger.error(f"Scheduler: Threads token refresh failed: {e}")


async def post_county_diesel_job() -> None:
    try:
        from app.services.social import post_cheapest_by_county
        await post_cheapest_by_county("B7", dry_run=False)
    except Exception as e:
        logger.error(f"Scheduler: county diesel post failed: {e}")


def start_scheduler() -> None:
    import os
    enable_social  = os.getenv("ENABLE_SOCIAL_POSTS",  "true").lower() == "true"
    enable_polling = os.getenv("ENABLE_PRICE_POLLING", "true").lower() == "true"

    if not enable_social and not enable_polling:
        logger.info("Scheduler fully disabled")
        return

    from apscheduler.triggers.cron import CronTrigger as CT2

    if enable_social:
        scheduler.add_job(run_county_fix, trigger=CT2(day_of_week="sun", hour=4, minute=0, timezone="Europe/London"), id="county_fix", replace_existing=True)
        scheduler.add_job(post_daily_averages_job, trigger=CronTrigger(hour=8,  minute=0,  timezone="Europe/London"), id="post_daily_averages_am",      replace_existing=True)
        scheduler.add_job(post_cheapest_job,        trigger=CronTrigger(hour=8,  minute=5,  timezone="Europe/London"), id="post_cheapest_am",            replace_existing=True)
        scheduler.add_job(post_cheapest_diesel_job, trigger=CronTrigger(hour=8,  minute=15, timezone="Europe/London"), id="post_cheapest_diesel_am",     replace_existing=True)
        scheduler.add_job(post_by_country_job,      trigger=CronTrigger(hour=8,  minute=20, timezone="Europe/London"), id="post_by_country_am",          replace_existing=True)
        scheduler.add_job(post_by_country_diesel_job, trigger=CronTrigger(hour=8, minute=25, timezone="Europe/London"), id="post_by_country_diesel_am",  replace_existing=True)
        scheduler.add_job(post_daily_averages_job,  trigger=CronTrigger(hour=16, minute=0,  timezone="Europe/London"), id="post_daily_averages_pm",      replace_existing=True)
        scheduler.add_job(post_cheapest_job,        trigger=CronTrigger(hour=16, minute=5,  timezone="Europe/London"), id="post_cheapest_pm",            replace_existing=True)
        scheduler.add_job(post_cheapest_diesel_job, trigger=CronTrigger(hour=16, minute=15, timezone="Europe/London"), id="post_cheapest_diesel_pm",     replace_existing=True)
        scheduler.add_job(post_by_country_job,      trigger=CronTrigger(hour=16, minute=20, timezone="Europe/London"), id="post_by_country_pm",          replace_existing=True)
        scheduler.add_job(post_by_country_diesel_job, trigger=CronTrigger(hour=16, minute=25, timezone="Europe/London"), id="post_by_country_diesel_pm", replace_existing=True)
        scheduler.add_job(post_county_e10_job,      trigger=CronTrigger(hour=10, minute=0,  timezone="Europe/London"), id="post_county_e10",             replace_existing=True)
        scheduler.add_job(post_county_diesel_job,   trigger=CronTrigger(hour=10, minute=30, timezone="Europe/London"), id="post_county_diesel",          replace_existing=True)
        scheduler.add_job(refresh_threads_token_job, trigger=IntervalTrigger(days=45), id="refresh_threads_token", replace_existing=True)
        scheduler.add_job(generate_weekly_blog_post_job, trigger=CronTrigger(day_of_week="tue", hour=9, minute=30, timezone="Europe/London"), id="weekly_blog_post", replace_existing=True)
        scheduler.add_job(check_blog_sources_job, trigger=CronTrigger(day_of_week="wed", hour=10, minute=0, timezone="Europe/London"), id="check_blog_sources", replace_existing=True)

    if enable_polling:
        scheduler.add_job(sync_stations_job, trigger=CronTrigger(hour=4, minute=30, timezone="Europe/London"), id="sync_stations", replace_existing=True)
        scheduler.add_job(poll_prices,   trigger=IntervalTrigger(minutes=settings.poll_interval_minutes), id="poll_prices", replace_existing=True)
        scheduler.add_job(generate_sitemap_job, trigger=CronTrigger(hour=2, minute=0, timezone="Europe/London"), id="generate_sitemap", replace_existing=True)
        scheduler.add_job(market_intelligence_job, trigger=CronTrigger(hour=4, minute=30, timezone="Europe/London"), id="market_intelligence", replace_existing=True)
        scheduler.add_job(check_price_alerts_job, trigger=IntervalTrigger(minutes=settings.poll_interval_minutes, start_date='2026-01-01 00:10:00'), id="check_price_alerts", replace_existing=True)
        scheduler.add_job(run_retention, trigger=CronTrigger(hour=3, minute=0, timezone="Europe/London"), id="retention",   replace_existing=True)

    scheduler.start()
    logger.info(f"Scheduler started — social={enable_social} polling={enable_polling}")


def stop_scheduler() -> None:
    scheduler.shutdown(wait=False)


async def run_county_fix() -> None:
    logger.info("Scheduler: running weekly county normalisation")
    try:
        import subprocess
        result = subprocess.run(
            ["python3", "/app/scripts/fix_counties.py"],
            capture_output=True, text=True, timeout=300
        )
        if result.returncode == 0:
            logger.info("County fix complete")
        else:
            logger.error(f"County fix failed: {result.stderr}")
    except Exception as e:
        logger.error(f"County fix error: {e}")


async def warm_city_cache_job() -> None:
    """Pre-compute city landing page data after price poll. Runs in background."""
    try:
        import asyncio

        import httpx

        from app.api.endpoints.locations_seo import PRECOMPUTE_CITIES

        logger.info("Starting city cache warmup...")
        warmed = 0
        async with httpx.AsyncClient(timeout=30, base_url="http://localhost:8000") as client:
            for city in PRECOMPUTE_CITIES:
                try:
                    r = await client.get(f"/api/v1/locations/cheap-fuel/{city}")
                    if r.status_code == 200:
                        warmed += 1
                    else:
                        logger.warning(f"City cache warmup: {city} returned {r.status_code}: {r.text[:200]}")
                    await asyncio.sleep(5)
                except Exception as e:
                    logger.warning(f"City cache warmup failed for {city}: {e}")
        logger.info(f"City cache warmup complete — {warmed}/{len(PRECOMPUTE_CITIES)} cities cached")
    except Exception as e:
        logger.error(f"Scheduler: city cache warmup failed: {e}")


async def market_intelligence_job() -> None:
    try:
        from app.services.market_intelligence import run_market_intelligence_job
        await run_market_intelligence_job()
    except Exception as e:
        logger.error(f"Scheduler: market intelligence job failed: {e}")


async def generate_sitemap_job() -> None:
    try:
        import subprocess
        result = subprocess.run(
            ["python3", "/app/scripts/generate_sitemap.py"],
            capture_output=True, text=True
        )
        if result.returncode == 0:
            logger.info(f"Sitemap generated: {result.stdout.strip()}")
        else:
            logger.error(f"Sitemap generation failed: {result.stderr}")
    except Exception as e:
        logger.error(f"Scheduler: sitemap generation failed: {e}")


async def check_price_alerts_job() -> None:
    try:
        from datetime import datetime, timedelta, timezone

        from sqlalchemy import select

        from app.api.endpoints.alerts import _create_disable_token
        from app.db.session import AsyncSessionLocal
        from app.models.alert import PriceAlert
        from app.models.models import Station
        from app.models.user import User
        from app.services.email import send_price_alert_email

        COOLDOWN_HOURS = 24

        async with AsyncSessionLocal() as db:
            # Get all active alerts with user and latest price
            result = await db.execute(
                select(PriceAlert, User.email, Station.name)
                .join(User, PriceAlert.user_id == User.id)
                .join(Station, PriceAlert.station_id == Station.id)
                .where(PriceAlert.is_active == True)  # noqa: E712
            )
            rows = result.all()

            now = datetime.now(timezone.utc)
            triggered = 0

            for alert, user_email, station_name in rows:
                # Cooldown check
                if alert.last_triggered_at:
                    last = alert.last_triggered_at.replace(tzinfo=timezone.utc)
                    if now - last < timedelta(hours=COOLDOWN_HOURS):
                        continue

                # Get latest price for this station/fuel
                from sqlalchemy import text
                price_result = await db.execute(
                    text("""
                        SELECT price_pence FROM price_history
                        WHERE station_id = :sid AND fuel_type = :fuel AND price_flagged = false
                        ORDER BY recorded_at DESC LIMIT 1
                    """),
                    {"sid": alert.station_id, "fuel": alert.fuel_type}
                )
                row = price_result.fetchone()
                if not row:
                    continue
                current_price = row[0]

                should_trigger = False

                if alert.alert_type == "below_pence":
                    should_trigger = current_price <= alert.threshold
                elif alert.alert_type == "change_pct":
                    # Get price from 24h ago
                    prev_result = await db.execute(
                        text("""
                            SELECT price_pence FROM price_history
                            WHERE station_id = :sid AND fuel_type = :fuel AND price_flagged = false
                            AND recorded_at <= NOW() - INTERVAL '24 hours'
                            ORDER BY recorded_at DESC LIMIT 1
                        """),
                        {"sid": alert.station_id, "fuel": alert.fuel_type}
                    )
                    prev_row = prev_result.fetchone()
                    if prev_row and prev_row[0] > 0:
                        pct_change = abs((current_price - prev_row[0]) / prev_row[0] * 100)
                        should_trigger = pct_change >= alert.threshold

                if should_trigger:
                    disable_token = _create_disable_token(alert.id)
                    await send_price_alert_email(
                        email=user_email,
                        station_name=station_name,
                        station_id=alert.station_id,
                        fuel_type=alert.fuel_type,
                        alert_type=alert.alert_type,
                        threshold=alert.threshold,
                        current_price=current_price,
                        disable_token=disable_token,
                    )
                    alert.last_triggered_at = now.replace(tzinfo=None)
                    alert.triggered_count += 1
                    await db.commit()
                    triggered += 1

        logger.info(f"Price alert check complete — {triggered} alerts triggered")
    except Exception as e:
        logger.error(f"Scheduler: price alert check failed: {e}")
