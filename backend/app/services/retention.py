import logging
from datetime import datetime, timedelta

from sqlalchemy import text

from app.db.session import AsyncSessionLocal

logger = logging.getLogger(__name__)


async def apply_retention_policy() -> None:
    """
    Retention policy:
    - 0–7 days:   keep all records (30-min granularity)
    - 7–90 days:  keep one record per day per station/fuel (earliest of the day)
    - 90+ days:   delete all

    Processes one day at a time with separate committed transactions to avoid
    long-running locks that caused deadlocks when the June 6-10 spike data
    entered the thinning window simultaneously.
    """
    now = datetime.utcnow()
    cutoff_thin = now - timedelta(days=7)
    cutoff_delete = now - timedelta(days=90)

    # Step 1: Delete records older than 90 days (fast range delete)
    async with AsyncSessionLocal() as session:
        await session.execute(text("""
            DELETE FROM price_history
            WHERE recorded_at < :cutoff_delete
        """), {"cutoff_delete": cutoff_delete})
        await session.commit()
        logger.info("Retention: deleted records older than 90 days")

    # Step 2: Thin 7-90 day window one day at a time
    import time as _time
    job_start = _time.time()
    MAX_RUNTIME_SECONDS = 7200  # 2 hours max — prevents overlap with next night's run
    current = cutoff_delete.date()
    thin_end = cutoff_thin.date()
    days_thinned = 0
    rows_deleted = 0

    while current < thin_end:
        if _time.time() - job_start > MAX_RUNTIME_SECONDS:
            logger.warning(f"Retention: 2-hour limit reached, stopping at {current} — will continue tomorrow")
            break
        day_start = datetime.combine(current, datetime.min.time())
        day_end = day_start + timedelta(days=1)

        async with AsyncSessionLocal() as session:
            # Check if this day needs thinning (more than one record per station/fuel)
            check = await session.execute(text("""
                SELECT COUNT(*) FROM price_history
                WHERE recorded_at >= :day_start
                  AND recorded_at < :day_end
            """), {"day_start": day_start, "day_end": day_end})
            day_count = check.scalar() or 0

            if day_count > 0:
                import time as _t
                t0 = _t.time()
                result = await session.execute(text("""
                    DELETE FROM price_history
                    WHERE recorded_at >= :day_start
                      AND recorded_at < :day_end
                      AND id NOT IN (
                          SELECT MIN(id)
                          FROM price_history
                          WHERE recorded_at >= :day_start
                            AND recorded_at < :day_end
                          GROUP BY station_id, fuel_type
                      )
                """), {"day_start": day_start, "day_end": day_end})
                await session.commit()
                elapsed = _t.time() - t0
                day_deleted = result.rowcount if hasattr(result, 'rowcount') else 0
                rows_deleted += day_deleted
                days_thinned += 1
                logger.info(f"Retention: thinned {current} — {day_count} rows → deleted {day_deleted} in {elapsed:.1f}s")

        current += timedelta(days=1)

    logger.info(f"Retention: thinned {days_thinned} days, removed {rows_deleted} records")

    # Report current table size
    async with AsyncSessionLocal() as session:
        count_result = await session.execute(text("SELECT COUNT(*) FROM price_history"))
        total = count_result.scalar()
        logger.info(f"Retention: price_history now has {total:,} records")
