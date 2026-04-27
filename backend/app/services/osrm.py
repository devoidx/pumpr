"""
OSRM driving distance service.
Uses the public OSRM demo API with DB caching.
Falls back gracefully if OSRM is unavailable.

OSRM table endpoint: returns a matrix of distances/durations.
We send origin + up to 10 destinations in one request.
"""
from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone

import httpx
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.driving_cache import DrivingDistanceCache

logger = logging.getLogger(__name__)

OSRM_BASE = "http://router.project-osrm.org"
CACHE_TTL_HOURS = 24
ROUND_PRECISION = 4  # ~11m precision for cache key


def _round_coord(val: float) -> float:
    return round(val, ROUND_PRECISION)


async def get_driving_distances(
    origin_lat: float,
    origin_lng: float,
    stations: list[dict],
    db: AsyncSession,
) -> dict[str, dict]:
    """
    Get driving distances from origin to each station.
    Returns dict of station_id -> {driving_km, driving_mins}
    Uses cache, falls back to straight-line on OSRM failure.
    """
    if not stations:
        return {}

    olat = _round_coord(origin_lat)
    olng = _round_coord(origin_lng)

    station_ids = [s["station_id"] for s in stations]

    # Check cache
    cached = await _get_cached(db, olat, olng, station_ids)
    missing = [s for s in stations if s["station_id"] not in cached]

    if missing:
        fresh = await _fetch_from_osrm(olat, olng, missing)
        if fresh:
            await _save_cache(db, olat, olng, fresh)
            cached.update(fresh)

    return cached


async def _get_cached(
    db: AsyncSession,
    olat: float,
    olng: float,
    station_ids: list[str],
) -> dict[str, dict]:
    cutoff = datetime.now(timezone.utc) - timedelta(hours=CACHE_TTL_HOURS)
    result = await db.execute(
        select(DrivingDistanceCache).where(
            DrivingDistanceCache.origin_lat == olat,
            DrivingDistanceCache.origin_lng == olng,
            DrivingDistanceCache.station_id.in_(station_ids),
            DrivingDistanceCache.cached_at > cutoff,
        )
    )
    return {
        row.station_id: {"driving_km": row.driving_km, "driving_mins": row.driving_mins}
        for row in result.scalars().all()
    }


async def _fetch_from_osrm(
    olat: float,
    olng: float,
    stations: list[dict],
) -> dict[str, dict]:
    """Call OSRM table API. Returns driving distances or empty dict on failure."""
    # Build coordinate string: origin first, then destinations
    coords = f"{olng},{olat}"
    for s in stations:
        if s.get("latitude") and s.get("longitude"):
            coords += f";{s['longitude']},{s['latitude']}"

    # destinations=1;2;3... (indices of destination coords, skipping 0=origin)
    dest_indices = ";".join(str(i + 1) for i in range(len(stations)))

    url = (
        f"{OSRM_BASE}/table/v1/driving/{coords}"
        f"?sources=0&destinations={dest_indices}"
        f"&annotations=distance,duration"
    )

    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.get(url)
            resp.raise_for_status()
            data = resp.json()

        if data.get("code") != "Ok":
            logger.warning("OSRM returned non-Ok code: %s", data.get("code"))
            return {}

        distances = data["distances"][0]   # distances from source 0
        durations = data["durations"][0]   # durations from source 0

        result = {}
        for i, s in enumerate(stations):
            dist_m = distances[i]
            dur_s  = durations[i]
            if dist_m is None or dur_s is None:
                continue
            result[s["station_id"]] = {
                "driving_km":   round(dist_m / 1000, 2),
                "driving_mins": round(dur_s / 60, 1),
            }
        return result

    except Exception as e:
        logger.warning("OSRM request failed: %s", e)
        return {}


async def _save_cache(
    db: AsyncSession,
    olat: float,
    olng: float,
    distances: dict[str, dict],
) -> None:
    for station_id, vals in distances.items():
        stmt = insert(DrivingDistanceCache).values(
            origin_lat=olat,
            origin_lng=olng,
            station_id=station_id,
            driving_km=vals["driving_km"],
            driving_mins=vals["driving_mins"],
            cached_at=datetime.now(timezone.utc),
        ).on_conflict_do_update(
            index_elements=["origin_lat", "origin_lng", "station_id"],
            set_={
                "driving_km": vals["driving_km"],
                "driving_mins": vals["driving_mins"],
                "cached_at": datetime.now(timezone.utc),
            }
        )
        await db.execute(stmt)
    await db.commit()
