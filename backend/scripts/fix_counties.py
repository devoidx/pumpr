"""
One-off script to fix county data using postcodes.io reverse geocoding.
"""
import asyncio
import httpx
import logging
import sys
import os

sys.path.insert(0, '/app')
os.environ.setdefault('DATABASE_URL', os.environ.get('DATABASE_URL', ''))

from sqlalchemy import text
from app.db.session import AsyncSessionLocal

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

BATCH_SIZE = 100
POSTCODES_API = "https://api.postcodes.io/postcodes"


async def lookup_postcodes(postcodes: list[str]) -> dict[str, dict]:
    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.post(POSTCODES_API, json={"postcodes": postcodes})
        resp.raise_for_status()
        results = {}
        for item in resp.json().get("result", []):
            if item and item.get("result"):
                r = item["result"]
                postcode = r.get("postcode", "").replace(" ", "").upper()
                results[postcode] = {
                    "county": r.get("admin_county") or r.get("admin_district") or "",
                    "country": r.get("country", ""),
                }
        return results


async def fix_counties():
    async with AsyncSessionLocal() as session:
        result = await session.execute(text("""
            SELECT id, postcode, county, country
            FROM stations
            WHERE postcode IS NOT NULL AND postcode != ''
            ORDER BY id
        """))
        stations = result.fetchall()
        logger.info(f"Found {len(stations)} stations with postcodes")

        updated = 0
        errors = 0
        total_batches = (len(stations) + BATCH_SIZE - 1) // BATCH_SIZE

        for i in range(0, len(stations), BATCH_SIZE):
            batch = stations[i:i + BATCH_SIZE]
            postcodes = [s.postcode.replace(" ", "").upper() for s in batch]

            try:
                lookup = await lookup_postcodes(postcodes)
            except Exception as e:
                logger.error(f"Batch {i//BATCH_SIZE + 1} failed: {e}")
                errors += 1
                await asyncio.sleep(1.0)
                continue

            for station in batch:
                clean_pc = station.postcode.replace(" ", "").upper()
                data = lookup.get(clean_pc)
                if not data:
                    continue

                county = (data.get("county") or "").upper().strip()
                country_raw = data.get("country", "").strip()

                country_map = {
                    "England": "England",
                    "Scotland": "Scotland",
                    "Wales": "Wales",
                    "Northern Ireland": "Northern Ireland",
                }
                normalised_country = country_map.get(country_raw)

                await session.execute(text("""
                    UPDATE stations
                    SET county = :county,
                        country = COALESCE(:country, country)
                    WHERE id = :id
                """), {
                    "county": county if county else None,
                    "country": normalised_country,
                    "id": station.id,
                })
                updated += 1

            await session.commit()
            batch_num = i // BATCH_SIZE + 1
            logger.info(f"Batch {batch_num}/{total_batches} done — {updated} updated")
            await asyncio.sleep(0.2)

        logger.info(f"Complete. Updated: {updated}, Errors: {errors}")

        result = await session.execute(text("""
            SELECT country, COUNT(DISTINCT county) as counties, COUNT(*) as stations
            FROM stations
            WHERE county IS NOT NULL AND county != ''
            GROUP BY country ORDER BY stations DESC
        """))
        for row in result.fetchall():
            logger.info(f"  {row.country}: {row.counties} counties, {row.stations} stations")


if __name__ == "__main__":
    asyncio.run(fix_counties())
