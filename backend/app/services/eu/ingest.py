"""
EU price ingestion — upserts rows from any country client into
eu_stations + eu_latest_prices. Intentionally separate from the
UK ingestion.py to avoid any risk to the GB pipeline.
"""
import logging

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import AsyncSessionLocal
from app.services.eu.france_client import fetch_and_parse_france

logger = logging.getLogger(__name__)


async def upsert_eu_rows(rows: list[dict], db: AsyncSession) -> tuple[int, int]:
    """
    Upserts a list of normalized station+price dicts.
    Returns (stations_upserted, prices_upserted).
    """
    if not rows:
        return 0, 0

    # Deduplicate rows by (external_id, country, fuel_type) — keep the most
    # recent recorded_at per combination in case the feed has duplicates.
    seen: dict[tuple, dict] = {}
    for row in rows:
        key = (row["external_id"], row["country"], row["fuel_type"])
        if key not in seen or row["recorded_at"] > seen[key]["recorded_at"]:
            seen[key] = row
    deduped = list(seen.values())

    # Upsert stations first, get back id per (country, external_id).
    station_keys = {(r["country"], r["external_id"]) for r in deduped}
    station_rows = [
        {
            "external_id": ext_id,
            "country": country,
            # name/address/city/postcode/lat/lon from the first matching row
            **next(
                {
                    "name": r["name"],
                    "address": r["address"],
                    "postcode": r["postcode"],
                    "city": r["city"],
                    "latitude": r["latitude"],
                    "longitude": r["longitude"],
                    "is_motorway": r.get("is_motorway", False),
                }
                for r in deduped
                if r["external_id"] == ext_id and r["country"] == country
            ),
        }
        for country, ext_id in station_keys
    ]

    await db.execute(
        text("""
            INSERT INTO eu_stations
                (external_id, country, name, address, postcode, city, latitude, longitude, is_motorway)
            VALUES
                (:external_id, :country, :name, :address, :postcode, :city, :latitude, :longitude, :is_motorway)
            ON CONFLICT (country, external_id) DO UPDATE SET
                name     = EXCLUDED.name,
                address  = EXCLUDED.address,
                postcode = EXCLUDED.postcode,
                city     = EXCLUDED.city,
                latitude = EXCLUDED.latitude,
                longitude = EXCLUDED.longitude,
                is_motorway = EXCLUDED.is_motorway,
                updated_at = now()
        """),
        station_rows,
    )

    stations_upserted = len(station_rows)

    # Fetch station id map: (country, external_id) -> id
    result = await db.execute(
        text("""
            SELECT id, country, external_id FROM eu_stations
            WHERE (country, external_id) = ANY(
                SELECT country, external_id FROM eu_stations
                WHERE country = ANY(CAST(:countries AS varchar[]))
            )
        """),
        {"countries": list({r["country"] for r in deduped})},
    )
    station_id_map = {(row.country, row.external_id): row.id for row in result}

    # Upsert prices.
    price_rows = []
    for row in deduped:
        station_id = station_id_map.get((row["country"], row["external_id"]))
        if station_id is None:
            continue
        price_rows.append({
            "eu_station_id": station_id,
            "fuel_type": row["fuel_type"],
            "price_eur": row["price_eur"],
            "recorded_at": row["recorded_at"],
        })

    if price_rows:
        await db.execute(
            text("""
                INSERT INTO eu_latest_prices
                    (eu_station_id, fuel_type, price_eur, recorded_at)
                VALUES
                    (:eu_station_id, :fuel_type, :price_eur, :recorded_at)
                ON CONFLICT (eu_station_id, fuel_type) DO UPDATE SET
                    price_eur   = EXCLUDED.price_eur,
                    recorded_at = EXCLUDED.recorded_at
                WHERE EXCLUDED.recorded_at >= eu_latest_prices.recorded_at
            """),
            price_rows,
        )

    await db.commit()
    return stations_upserted, len(price_rows)


async def ingest_france() -> None:
    """Fetch and upsert France station prices. Called by the scheduler."""
    logger.info("eu_ingest: starting France ingestion")
    try:
        rows = await fetch_and_parse_france()
        logger.info("eu_ingest: parsed %d France rows", len(rows))
    except Exception:
        logger.exception("eu_ingest: failed to fetch/parse France feed — aborting")
        return

    try:
        async with AsyncSessionLocal() as db:
            stations, prices = await upsert_eu_rows(rows, db)
        logger.info(
            "eu_ingest: France done — %d stations, %d prices upserted",
            stations,
            prices,
        )
    except Exception:
        logger.exception("eu_ingest: failed to upsert France rows")


async def ingest_italy() -> None:
    """Fetch and upsert Italy station prices. Called by the scheduler."""
    logger.info("eu_ingest: starting Italy ingestion")
    try:
        from app.services.eu.italy_client import fetch_and_parse_italy
        rows = await fetch_and_parse_italy()
        logger.info("eu_ingest: parsed %d Italy rows", len(rows))
    except Exception:
        logger.exception("eu_ingest: failed to fetch/parse Italy feed — aborting")
        return

    try:
        async with AsyncSessionLocal() as db:
            stations, prices = await upsert_eu_rows(rows, db)
        logger.info(
            "eu_ingest: Italy done — %d stations, %d prices upserted",
            stations,
            prices,
        )
    except Exception:
        logger.exception("eu_ingest: failed to upsert Italy rows")


async def ingest_spain() -> None:
    """Fetch and upsert Spain station prices. Called by the scheduler."""
    logger.info("eu_ingest: starting Spain ingestion")
    try:
        from app.services.eu.spain_client import fetch_and_parse_spain
        rows = await fetch_and_parse_spain()
        logger.info("eu_ingest: parsed %d Spain rows", len(rows))
    except Exception:
        logger.exception("eu_ingest: failed to fetch/parse Spain feed — aborting")
        return

    try:
        async with AsyncSessionLocal() as db:
            stations, prices = await upsert_eu_rows(rows, db)
        logger.info(
            "eu_ingest: Spain done — %d stations, %d prices upserted",
            stations,
            prices,
        )
    except Exception:
        logger.exception("eu_ingest: failed to upsert Spain rows")


async def ingest_germany() -> None:
    """Fetch and upsert Germany station prices. Called by the scheduler."""
    logger.info("eu_ingest: starting Germany ingestion")
    try:
        from app.services.eu.germany_client import fetch_and_parse_germany
        rows = await fetch_and_parse_germany()
        logger.info("eu_ingest: parsed %d Germany rows", len(rows))
    except Exception:
        logger.exception("eu_ingest: failed to fetch/parse Germany feed — aborting")
        return

    if not rows:
        return

    try:
        async with AsyncSessionLocal() as db:
            stations, prices = await upsert_eu_rows(rows, db)
        logger.info(
            "eu_ingest: Germany done — %d stations, %d prices upserted",
            stations,
            prices,
        )
    except Exception:
        logger.exception("eu_ingest: failed to upsert Germany rows")
