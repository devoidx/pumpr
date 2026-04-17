import asyncio
import logging
import sys

sys.path.insert(0, '/app')

from sqlalchemy import text
from app.db.session import AsyncSessionLocal
from app.services.geocoding import lookup_postcodes_batch

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s: %(message)s")
logger = logging.getLogger(__name__)


async def fix_counties():
    async with AsyncSessionLocal() as session:
        result = await session.execute(text("""
            SELECT id, postcode FROM stations
            WHERE postcode IS NOT NULL AND postcode != ''
            ORDER BY id
        """))
        stations = result.fetchall()
        logger.info(f"Found {len(stations)} stations with postcodes")

        updated = 0
        errors = 0
        total_batches = (len(stations) + 99) // 100

        for i in range(0, len(stations), 100):
            batch = stations[i:i + 100]
            postcodes = [s.postcode for s in batch]

            try:
                lookup = await lookup_postcodes_batch(postcodes)
            except Exception as e:
                logger.error(f"Batch {i//100 + 1} failed: {e}")
                errors += 1
                await asyncio.sleep(1.0)
                continue

            for station in batch:
                clean_pc = station.postcode.replace(" ", "").upper()
                data = lookup.get(clean_pc)
                if not data:
                    continue

                county = data.get("county")
                country = data.get("country")

                # Only update fields we have good data for
                updates = []
                params = {"id": station.id}

                if county is not None:
                    updates.append("county = :county")
                    params["county"] = county

                if country is not None:
                    updates.append("country = :country")
                    params["country"] = country

                if updates:
                    await session.execute(
                        text(f"UPDATE stations SET {', '.join(updates)} WHERE id = :id"),
                        params
                    )
                    updated += 1

            await session.commit()
            logger.info(f"Batch {i//100 + 1}/{total_batches} done — {updated} updated")
            await asyncio.sleep(0.2)

        logger.info(f"Complete. Updated: {updated}, Errors: {errors}")

        result = await session.execute(text("""
            SELECT country, COUNT(DISTINCT county) as counties, COUNT(*) as stations
            FROM stations WHERE county IS NOT NULL AND county != ''
            GROUP BY country ORDER BY stations DESC
        """))
        for row in result.fetchall():
            logger.info(f"  {row.country}: {row.counties} counties, {row.stations} stations")


if __name__ == "__main__":
    asyncio.run(fix_counties())
