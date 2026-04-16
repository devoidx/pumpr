import logging

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger

from app.core.config import settings
from app.services.ingestion import ingest_prices, sync_stations

logger = logging.getLogger(__name__)

scheduler = AsyncIOScheduler()


async def poll_prices() -> None:
    logger.info("Scheduler: polling prices")
    try:
        count = await ingest_prices()
        logger.info(f"Scheduler: ingested {count} price records")
    except Exception as e:
        logger.error(f"Scheduler: price poll failed: {e}")


def start_scheduler() -> None:
    scheduler.add_job(
        poll_prices,
        trigger=IntervalTrigger(minutes=settings.poll_interval_minutes),
        id="poll_prices",
        replace_existing=True,
    )
    scheduler.start()
    logger.info(f"Scheduler started — polling every {settings.poll_interval_minutes} minutes")


def stop_scheduler() -> None:
    scheduler.shutdown(wait=False)
