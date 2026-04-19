import logging

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.triggers.cron import CronTrigger

from app.core.config import settings
from app.services.ingestion import ingest_prices, sync_stations
from app.services.retention import apply_retention_policy

logger = logging.getLogger(__name__)

scheduler = AsyncIOScheduler()


async def poll_prices() -> None:
    logger.info("Scheduler: polling prices")
    try:
        count = await ingest_prices()
        logger.info(f"Scheduler: ingested {count} price records")
    except Exception as e:
        logger.error(f"Scheduler: price poll failed: {e}")


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


async def post_county_e10_job() -> None:
    try:
        from app.services.social import post_cheapest_by_county
        await post_cheapest_by_county("E10", dry_run=False)
    except Exception as e:
        logger.error(f"Scheduler: county E10 post failed: {e}")


async def post_county_diesel_job() -> None:
    try:
        from app.services.social import post_cheapest_by_county
        await post_cheapest_by_county("B7", dry_run=False)
    except Exception as e:
        logger.error(f"Scheduler: county diesel post failed: {e}")


def start_scheduler() -> None:
    from apscheduler.triggers.cron import CronTrigger as CT2
    scheduler.add_job(
        run_county_fix,
        trigger=CT2(day_of_week="sun", hour=4, minute=0, timezone="Europe/London"),
        id="county_fix",
        replace_existing=True,
    )
    scheduler.add_job(
        post_daily_averages_job,
        trigger=CronTrigger(hour=8, timezone="Europe/London", minute=0),
        id="post_daily_averages_am",
        replace_existing=True,
    )
    scheduler.add_job(
        post_cheapest_job,
        trigger=CronTrigger(hour=8, timezone="Europe/London", minute=5),
        id="post_cheapest_am",
        replace_existing=True,
    )
    scheduler.add_job(
        post_cheapest_diesel_job,
        trigger=CronTrigger(hour=8, timezone="Europe/London", minute=15),
        id="post_cheapest_diesel_am",
        replace_existing=True,
    )
    scheduler.add_job(
        post_by_country_job,
        trigger=CronTrigger(hour=8, timezone="Europe/London", minute=20),
        id="post_by_country_am",
        replace_existing=True,
    )
    scheduler.add_job(
        post_daily_averages_job,
        trigger=CronTrigger(hour=16, timezone="Europe/London", minute=0),
        id="post_daily_averages_pm",
        replace_existing=True,
    )
    scheduler.add_job(
        post_cheapest_job,
        trigger=CronTrigger(hour=16, timezone="Europe/London", minute=5),
        id="post_cheapest_pm",
        replace_existing=True,
    )
    scheduler.add_job(
        post_cheapest_diesel_job,
        trigger=CronTrigger(hour=16, timezone="Europe/London", minute=15),
        id="post_cheapest_diesel_pm",
        replace_existing=True,
    )
    scheduler.add_job(
        post_by_country_job,
        trigger=CronTrigger(hour=16, timezone="Europe/London", minute=20),
        id="post_by_country_pm",
        replace_existing=True,
    )
    scheduler.add_job(
        post_county_e10_job,
        trigger=CronTrigger(hour=10, timezone="Europe/London", minute=0),
        id="post_county_e10",
        replace_existing=True,
    )
    scheduler.add_job(
        post_county_diesel_job,
        trigger=CronTrigger(hour=10, timezone="Europe/London", minute=30),
        id="post_county_diesel",
        replace_existing=True,
    )
    scheduler.add_job(
        poll_prices,
        trigger=IntervalTrigger(minutes=settings.poll_interval_minutes),
        id="poll_prices",
        replace_existing=True,
    )
    scheduler.add_job(
        run_retention,
        trigger=CronTrigger(hour=3, minute=0, timezone="Europe/London"),
        id="retention",
        replace_existing=True,
    )
    scheduler.start()
    logger.info(f"Scheduler started — polling every {settings.poll_interval_minutes} minutes, retention daily at 03:00")


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
