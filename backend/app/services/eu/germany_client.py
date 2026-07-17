"""
Client for Germany fuel prices via Tankerkönig (TK) API.
Unlike France/Italy/Spain which have bulk feeds, TK is radius-based.

Two-phase approach:
1. Corridor seeding (one-time): query radius API along UK-traveller routes,
   store station UUIDs in eu_stations.
2. Daily price refresh: use bulk /prices.php endpoint (10 IDs per request)
   to refresh prices for stored stations.

Rate limit: TK will 503 under sustained sequential load and can escalate to
outright connection refusal (observed 16 July 2026 from the VPS IP after an
unpaced ~140-batch run). Requests are now paced and the run aborts early on
repeated consecutive failures rather than running to completion regardless.
API key stored in settings.tankerkoenig_api_key.
"""
import asyncio
import logging
from datetime import datetime, timezone

import httpx

from app.core.config import settings
from app.services.eu.fuel_type_map import FUEL_TYPE_MAP

logger = logging.getLogger(__name__)

TK_BASE = "https://creativecommons.tankerkoenig.de/json"

# Pacing / backoff for the bulk prices endpoint.
# Confirmed via TK support (17 July 2026): free-tier key limit is a 40
# request burst, then 1 request/minute steady state, per key. A full
# refresh of ~1,064 stations (107 batches) therefore takes ~68 minutes:
# ~40 batches at BURST_DELAY_SECONDS, then the remainder at
# STEADY_STATE_DELAY_SECONDS. Do not reduce STEADY_STATE_DELAY_SECONDS
# below 60 — this is TK's stated limit, not an empirically-tuned guess.
BURST_LIMIT = 40
BURST_DELAY_SECONDS = 1.5
STEADY_STATE_DELAY_SECONDS = 60
MAX_CONSECUTIVE_FAILURES = 5

# Corridor waypoints along main UK-traveller routes through Germany
# Spaced ~40km apart — 25km radius queries overlap to avoid gaps
GERMANY_CORRIDORS = [
    # A3/A61 — Belgian border → Cologne → Frankfurt
    (50.776, 6.084),   # Aachen
    (50.938, 6.960),   # Cologne
    (50.775, 7.194),   # Bonn
    (50.359, 7.599),   # Koblenz
    (49.998, 8.274),   # Mainz
    (50.110, 8.682),   # Frankfurt
    (49.872, 8.651),   # Darmstadt
    # A5 south — Frankfurt → Basel
    (49.494, 8.470),   # Heidelberg
    (48.992, 8.403),   # Karlsruhe
    (48.523, 7.735),   # Offenburg
    (47.998, 7.842),   # Freiburg
    # A8 east — Stuttgart → Munich → Austrian border
    (48.775, 9.182),   # Stuttgart
    (48.565, 9.678),   # Ulm
    (48.136, 10.898),  # Augsburg area
    (48.137, 11.575),  # Munich
    (47.799, 12.633),  # Rosenheim
    # A7 north — Hamburg → Hanover → Kassel
    (53.550, 10.000),  # Hamburg
    (52.375, 9.732),   # Hanover
    (51.512, 9.408),   # Kassel
]

# Germany bounding box
LAT_MIN, LAT_MAX = 47.3, 55.1
LON_MIN, LON_MAX = 5.9, 15.1


async def fetch_corridor_stations() -> list[dict]:
    """
    One-time seeder: query each corridor point and return all unique stations.
    Deduplicates by station UUID.
    """
    seen: set[str] = set()
    rows = []
    consecutive_failures = 0

    async with httpx.AsyncClient(timeout=30) as client:
        for lat, lng in GERMANY_CORRIDORS:
            try:
                resp = await client.get(f"{TK_BASE}/list.php", params={
                    "lat": lat,
                    "lng": lng,
                    "rad": 25,
                    "type": "all",
                    "sort": "dist",
                    "apikey": settings.tankerkoenig_api_key,
                })
                resp.raise_for_status()
                data = resp.json()
                consecutive_failures = 0

                if not data.get("ok"):
                    logger.warning("TK corridor query failed at %.3f,%.3f: %s", lat, lng, data.get("message"))
                    continue

                for s in data.get("stations", []):
                    station_id = s.get("id")
                    if not station_id or station_id in seen:
                        continue
                    seen.add(station_id)

                    s_lat = s.get("lat")
                    s_lng = s.get("lng")
                    if not s_lat or not s_lng:
                        continue
                    if not (LAT_MIN <= s_lat <= LAT_MAX and LON_MIN <= s_lng <= LON_MAX):
                        continue

                    now = datetime.now(timezone.utc)
                    for fuel_raw, mapped in FUEL_TYPE_MAP["DE"].items():
                        if mapped is None:
                            continue
                        price = s.get(fuel_raw)
                        if price is None or price <= 0:
                            continue
                        rows.append({
                            "external_id": station_id,
                            "country": "DE",
                            "name": s.get("name", ""),
                            "brand": s.get("brand") or None,
                            "address": f"{s.get('street', '')} {s.get('houseNumber', '')}".strip(),
                            "postcode": str(s.get("postCode", "")),
                            "city": s.get("place", ""),
                            "latitude": s_lat,
                            "longitude": s_lng,
                            "is_motorway": False,
                            "fuel_type": mapped,
                            "price_eur": price,
                            "recorded_at": now,
                        })

                logger.info("TK corridor %.3f,%.3f: %d stations found, %d unique so far",
                           lat, lng, len(data.get("stations", [])), len(seen))

            except Exception:
                logger.exception("TK corridor query failed at %.3f,%.3f", lat, lng)
                consecutive_failures += 1
                if consecutive_failures >= MAX_CONSECUTIVE_FAILURES:
                    logger.error(
                        "TK corridor seeding: %d consecutive failures — aborting early to avoid escalating a rate limit block",
                        consecutive_failures,
                    )
                    break

            await asyncio.sleep(BURST_DELAY_SECONDS)

    logger.info("TK corridor seeding complete: %d unique stations, %d price rows", len(seen), len(rows))
    return rows


async def fetch_corridor_prices(station_ids: list[str]) -> list[dict]:
    """
    Daily price refresh: fetch current prices for stored station UUIDs
    using the bulk /prices.php endpoint (10 IDs per request).

    Respects TK's confirmed free-tier limit: BURST_LIMIT requests at
    BURST_DELAY_SECONDS spacing, then STEADY_STATE_DELAY_SECONDS between
    each subsequent batch. Aborts early if MAX_CONSECUTIVE_FAILURES batches
    fail in a row rather than running through the full ID list regardless.
    A full run over ~107 batches takes roughly an hour — this is expected,
    not a bug; do not shorten STEADY_STATE_DELAY_SECONDS to speed it up.
    """
    rows = []
    now = datetime.now(timezone.utc)
    batch_size = 10
    consecutive_failures = 0
    total_batches = (len(station_ids) + batch_size - 1) // batch_size

    async with httpx.AsyncClient(timeout=30) as client:
        for batch_num, i in enumerate(range(0, len(station_ids), batch_size), start=1):
            batch = station_ids[i:i + batch_size]
            if batch_num % 10 == 0 or batch_num == total_batches:
                logger.info("TK price refresh: batch %d/%d in progress", batch_num, total_batches)
            try:
                resp = await client.get(f"{TK_BASE}/prices.php", params={
                    "ids": ",".join(batch),
                    "apikey": settings.tankerkoenig_api_key,
                })
                resp.raise_for_status()
                data = resp.json()
                consecutive_failures = 0

                if not data.get("ok"):
                    logger.warning("TK prices batch failed: %s", data.get("message"))
                    continue

                for station_id, prices in data.get("prices", {}).items():
                    if prices.get("status") != "open":
                        continue
                    for fuel_raw, mapped in FUEL_TYPE_MAP["DE"].items():
                        if mapped is None:
                            continue
                        price = prices.get(fuel_raw)
                        if price is None or price is False or price <= 0:
                            continue
                        rows.append({
                            "external_id": station_id,
                            "country": "DE",
                            "fuel_type": mapped,
                            "price_eur": float(price),
                            "recorded_at": now,
                        })

            except Exception:
                logger.exception("TK prices batch failed for batch starting %s", batch[0])
                consecutive_failures += 1
                if consecutive_failures >= MAX_CONSECUTIVE_FAILURES:
                    logger.error(
                        "TK price refresh: %d consecutive batch failures — aborting early to avoid escalating a rate limit block. Processed %d/%d stations.",
                        consecutive_failures, i, len(station_ids),
                    )
                    break

            delay = BURST_DELAY_SECONDS if batch_num <= BURST_LIMIT else STEADY_STATE_DELAY_SECONDS
            await asyncio.sleep(delay)

    logger.info("TK price refresh: %d price rows from %d stations", len(rows), len(station_ids))
    return rows


async def fetch_and_parse_germany() -> list[dict]:
    """
    Called by ingest_eu_job. If DE stations exist in DB, refresh prices.
    If not, run corridor seeding first.
    """
    from sqlalchemy import text

    from app.db.session import AsyncSessionLocal

    async with AsyncSessionLocal() as db:
        result = await db.execute(text(
            "SELECT external_id FROM eu_stations WHERE country = 'DE'"
        ))
        station_ids = [row.external_id for row in result]

    if not station_ids:
        logger.info("germany_client: no DE stations found — running corridor seeding")
        return await fetch_corridor_stations()

    logger.info("germany_client: refreshing prices for %d DE stations", len(station_ids))

    # For price-only refresh we need to merge with existing station data
    # The bulk prices endpoint doesn't return station metadata
    # So we return price rows with only external_id + fuel_type + price_eur
    # ingest.py upsert will only update eu_latest_prices, not eu_stations
    price_rows = await fetch_corridor_prices(station_ids)
    return price_rows
