"""
Computes day-of-week price patterns from price_history and stores in price_day_patterns.
Run weekly — data changes slowly enough that daily refresh is unnecessary.
"""
import logging

from sqlalchemy import text

from app.db.session import AsyncSessionLocal

logger = logging.getLogger(__name__)


async def compute_price_day_patterns() -> int:
    """
    Recomputes day-of-week average prices from the last 84 days of price_history.
    Returns number of rows upserted.
    """
    async with AsyncSessionLocal() as db:
        await db.execute(text("""
            INSERT INTO price_day_patterns
                (fuel_type, is_supermarket, day_of_week, avg_price_pence, station_count, computed_at)
            SELECT
                ph.fuel_type,
                s.is_supermarket,
                EXTRACT(DOW FROM ph.recorded_at)::integer as day_of_week,
                ROUND(AVG(ph.price_pence)::numeric, 2) as avg_price_pence,
                COUNT(DISTINCT ph.station_id) as station_count,
                now() as computed_at
            FROM price_history ph
            JOIN stations s ON ph.station_id = s.id
            WHERE ph.fuel_type IN ('E10', 'B7', 'E5')
            AND ph.price_flagged = false
            AND ph.recorded_at > NOW() - INTERVAL '84 days'
            GROUP BY ph.fuel_type, s.is_supermarket, day_of_week
            ON CONFLICT (fuel_type, is_supermarket, day_of_week) DO UPDATE SET
                avg_price_pence = EXCLUDED.avg_price_pence,
                station_count = EXCLUDED.station_count,
                computed_at = EXCLUDED.computed_at
        """))
        await db.commit()
        # Count rows inserted
        count_result = await db.execute(text("SELECT COUNT(*) FROM price_day_patterns"))
        rows = count_result.scalar() or 0
        logger.info("price_patterns: %d day-of-week pattern rows in table", rows)
        return rows
