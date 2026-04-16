import logging
from datetime import datetime, timedelta

from sqlalchemy import delete, select, func, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import AsyncSessionLocal
from app.models.models import PriceRecord

logger = logging.getLogger(__name__)


async def apply_retention_policy() -> None:
    """
    Retention policy:
    - 0–7 days:   keep all records (30-min granularity)
    - 7–90 days:  keep one record per day per station/fuel (earliest of the day)
    - 90+ days:   delete all
    """
    async with AsyncSessionLocal() as session:
        now = datetime.utcnow()
        cutoff_thin = now - timedelta(days=7)
        cutoff_delete = now - timedelta(days=90)

        # Delete records older than 90 days
        result = await session.execute(
            delete(PriceRecord).where(PriceRecord.recorded_at < cutoff_delete)
        )
        deleted_old = result.rowcount
        logger.info(f"Retention: deleted {deleted_old} records older than 90 days")

        # For 7–90 day range, keep only the earliest record per station/fuel/day
        # Find IDs to keep (min id per station/fuel/date in the thinning window)
        keep_subq = (
            select(func.min(PriceRecord.id).label("keep_id"))
            .where(
                PriceRecord.recorded_at >= cutoff_delete,
                PriceRecord.recorded_at < cutoff_thin,
            )
            .group_by(
                PriceRecord.station_id,
                PriceRecord.fuel_type,
                func.date_trunc("day", PriceRecord.recorded_at),
            )
            .subquery()
        )

        # Delete records in the thinning window that aren't the daily keeper
        result = await session.execute(
            delete(PriceRecord).where(
                PriceRecord.recorded_at >= cutoff_delete,
                PriceRecord.recorded_at < cutoff_thin,
                PriceRecord.id.not_in(select(keep_subq.c.keep_id)),
            )
        )
        deleted_thin = result.rowcount
        logger.info(f"Retention: thinned {deleted_thin} records in 7–90 day window")

        await session.commit()

        # Report current table size
        result = await session.execute(
            select(func.count()).select_from(PriceRecord)
        )
        total = result.scalar()
        logger.info(f"Retention: price_history now has {total:,} records")
