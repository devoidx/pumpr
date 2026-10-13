import asyncio
import logging
import re
import sys

sys.path.insert(0, '/app')

import httpx
from sqlalchemy import text
from app.db.session import AsyncSessionLocal
from app.services.geocoding import DISTRICT_TO_COUNTY, lookup_postcodes_batch

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s: %(message)s")
logger = logging.getLogger(__name__)


REVERSE_COUNTRIES = {"England", "Scotland", "Wales", "Northern Ireland"}


def _outcode(postcode):
    p = re.sub(r"\s+", "", (postcode or "").upper())
    return p[:-3] if len(p) > 3 else p


async def reverse_geocode_blanks(session) -> None:
    """Second pass for stations still without a county after the postcode lookup
    (postcodes the feed still carries but postcodes.io has retired). Finds the
    nearest postcode to the station's own coordinates and accepts it only when its
    outcode matches the stored postcode's, so a wrong coordinate cannot quietly
    assign the wrong county. Only fills blanks, never overwrites a value."""
    result = await session.execute(text("""
        SELECT id, postcode, latitude, longitude, country FROM stations
        WHERE (county IS NULL OR county = '')
          AND latitude IS NOT NULL AND longitude IS NOT NULL
          AND (permanent_closure = FALSE OR permanent_closure IS NULL)
    """))
    blanks = result.fetchall()
    logger.info(f"Reverse-geocode pass: {len(blanks)} stations without a county")
    filled = skipped = errors = 0
    async with httpx.AsyncClient(timeout=60) as client:
        for i in range(0, len(blanks), 100):
            batch = blanks[i:i + 100]
            body = {"geolocations": [
                {"longitude": s.longitude, "latitude": s.latitude, "radius": 1000, "limit": 1}
                for s in batch
            ]}
            try:
                resp = await client.post("https://api.postcodes.io/postcodes", json=body)
                resp.raise_for_status()
                items = resp.json()["result"]
            except Exception as e:
                logger.error(f"Reverse batch {i // 100 + 1} failed: {e}")
                errors += 1
                continue
            for station, item in zip(batch, items):
                hits = item.get("result") or []
                if not hits:
                    skipped += 1
                    continue
                hit = hits[0]
                if _outcode(hit.get("postcode")) != _outcode(station.postcode):
                    skipped += 1
                    continue
                county = (hit.get("admin_county") or "").upper().strip()
                if not county:
                    district = (hit.get("admin_district") or "").upper().strip()
                    county = DISTRICT_TO_COUNTY.get(district, "")
                if not county:
                    skipped += 1
                    continue
                updates = ["county = :county"]
                params = {"id": station.id, "county": county}
                country = hit.get("country")
                if not (station.country or "").strip() and country in REVERSE_COUNTRIES:
                    updates.append("country = :country")
                    params["country"] = country
                await session.execute(
                    text(f"UPDATE stations SET {', '.join(updates)} WHERE id = :id AND (county IS NULL OR county = '')"),
                    params,
                )
                filled += 1
            await session.commit()
            await asyncio.sleep(0.3)
    logger.info(f"Reverse-geocode pass complete. Filled: {filled}, Left blank: {skipped}, Errors: {errors}")


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

        await reverse_geocode_blanks(session)

        result = await session.execute(text("""
            SELECT country, COUNT(DISTINCT county) as counties, COUNT(*) as stations
            FROM stations WHERE county IS NOT NULL AND county != ''
            GROUP BY country ORDER BY stations DESC
        """))
        for row in result.fetchall():
            logger.info(f"  {row.country}: {row.counties} counties, {row.stations} stations")


if __name__ == "__main__":
    asyncio.run(fix_counties())
