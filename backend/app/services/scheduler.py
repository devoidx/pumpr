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
