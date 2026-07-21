"""
Client for Germany fuel prices via Tankerkönig (TK) API.
Unlike France/Italy/Spain which have bulk feeds, TK is radius-based.

Two-phase approach:
1. Corridor seeding (one-time, but re-runnable — see fetch_corridor_stations):
   query radius API along UK-traveller routes, store station UUIDs in eu_stations.
2. Price refresh: use bulk /prices.php endpoint (10 IDs per request) to
   refresh prices for stored stations. As of 21 July 2026 this is a ROTATING
   THIRD, not a full daily refresh — see fetch_and_parse_germany(). Station
   count roughly tripled (1,064 -> 3,039) after a corridor-seeding gap was
   found and fixed 21 July 2026 (the original 18 July seed silently aborted
   after 7 of 19 waypoints, leaving 8 of 12 published cities with zero
   stations for three days without anyone noticing). A full refresh at that
   scale would take ~5 hours against TK's rate limit, no longer fitting
   safely in one scheduled window — hence the 3-way rotation, run as its
   own standalone scheduler job (see scheduler.py: ingest_germany_job).

Rate limit: TK will 503 under sustained sequential load and can escalate to
outright connection refusal (observed 16 July 2026 from the VPS IP after an
unpaced ~140-batch run). Requests are now paced and the run aborts early on
repeated consecutive failures rather than running to completion regardless.
Confirmed directly by TK support (17 July 2026): free-tier key limit is an
nginx token bucket, 40-request burst then 1 request/minute steady state,
shared across all endpoints on the key (list.php and prices.php both draw
from the same bucket).
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
# TK's rate limit is fixed at their end (40 burst + 1/min) — do not reduce
# STEADY_STATE_DELAY_SECONDS below 60, this is not an empirically-tuned
# guess. With ~3,039 total DE stations split into 3 rotating groups
# (~1,013 each), one day's refresh is ~102 batches — close to the
# originally-validated 107-batch/~74-minute run (21 July 2026, zero
# failures at 65s steady-state), so this pacing should hold without
# further tuning. Do not attempt to refresh all stations in one run —
# see fetch_and_parse_germany()'s rotation logic.
BURST_LIMIT = 40
BURST_DELAY_SECONDS = 1.5
STEADY_STATE_DELAY_SECONDS = 65
MAX_CONSECUTIVE_FAILURES = 5
ROTATION_GROUPS = 3

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
    Called by ingest_germany_job (its own standalone scheduler job as of
    21 July 2026 — previously part of the shared ingest_eu_job, split out
    once station count tripled and a full refresh no longer fit one window).

    If DE stations exist in DB, refresh prices for TODAY'S ROTATION GROUP
    ONLY (roughly 1/ROTATION_GROUPS of all stations) rather than the full
    set — each station refreshes roughly once every ROTATION_GROUPS days,
    not daily. If no DE stations exist at all, run corridor seeding first
    (this also re-seeds correctly if re-run after a partial/aborted seed —
    see fetch_corridor_stations, which upserts via ON CONFLICT DO UPDATE
    so re-running against existing stations is always safe).
    """
    from datetime import datetime, timezone

    from sqlalchemy import text

    from app.db.session import AsyncSessionLocal

    async with AsyncSessionLocal() as db:
        result = await db.execute(text(
            "SELECT id, external_id FROM eu_stations WHERE country = 'DE'"
        ))
        all_stations = [(row.id, row.external_id) for row in result]

    if not all_stations:
        logger.info("germany_client: no DE stations found — running corridor seeding")
        return await fetch_corridor_stations()

    # Stable rotation by day-of-year — no stored counter needed, survives
    # container restarts, and any newly-seeded station just falls into
    # whichever group its DB id naturally lands in.
    today_group = datetime.now(timezone.utc).timetuple().tm_yday % ROTATION_GROUPS
    todays_station_ids = [
        ext_id for db_id, ext_id in all_stations
        if db_id % ROTATION_GROUPS == today_group
    ]

    logger.info(
        "germany_client: refreshing %d/%d DE stations (rotation group %d/%d)",
        len(todays_station_ids), len(all_stations), today_group, ROTATION_GROUPS,
    )

    # For price-only refresh we need to merge with existing station data
    # The bulk prices endpoint doesn't return station metadata
    # So we return price rows with only external_id + fuel_type + price_eur
    # ingest.py upsert will only update eu_latest_prices, not eu_stations
    price_rows = await fetch_corridor_prices(todays_station_ids)
    return price_rows
