import logging
from datetime import datetime, timedelta

from sqlalchemy import text

from app.db.session import AsyncSessionLocal

logger = logging.getLogger(__name__)


async def apply_retention_policy() -> None:
    """
    Retention policy: delete price_history records older than 90 days.
    Thinning (keeping one record per day in 7-90 day window) was removed —
    the NOT IN / self-join approaches were too slow at 9M+ rows.
    At current polling rates, 90 days of history = ~9M rows which Postgres
    handles fine with proper indexes.
    """
    async with AsyncSessionLocal() as session:
        cutoff_delete = datetime.utcnow() - timedelta(days=90)

        await session.execute(text("""
            DELETE FROM price_history
            WHERE recorded_at < :cutoff_delete
        """), {"cutoff_delete": cutoff_delete})
        await session.commit()

        count_result = await session.execute(text("SELECT COUNT(*) FROM price_history"))
        total = count_result.scalar()
        logger.info(f"Retention: price_history now has {total:,} records")
