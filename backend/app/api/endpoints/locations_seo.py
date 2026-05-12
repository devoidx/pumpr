from __future__ import annotations

import logging
import math
import time as _time

import httpx
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db

PRECOMPUTE_CITIES = [
    "london", "manchester", "birmingham", "leeds", "glasgow", "liverpool",
    "edinburgh", "bristol", "sheffield", "newcastle", "nottingham", "cardiff",
    "leicester", "coventry", "bradford", "belfast", "wolverhampton", "plymouth",
    "derby", "reading", "southampton", "portsmouth", "exeter", "cambridge",
    "oxford", "york", "norwich", "swansea", "aberdeen", "dundee",
]

router = APIRouter(prefix="/locations", tags=["locations-seo"])
logger = logging.getLogger(__name__)

# Simple in-memory cache with 10 minute TTL
_cache: dict = {}
_CACHE_TTL = 600  # 10 minutes


def _cache_get(key: str):
    if key in _cache:
        val, ts = _cache[key]
        if _time.time() - ts < _CACHE_TTL:
            return val
        del _cache[key]
    return None


def _cache_set(key: str, val) -> None:
    _cache[key] = (val, _time.time())

FUEL_TYPES = ["E10", "B7", "E5"]


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    R = 6371
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat/2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon/2)**2
    return R * 2 * math.asin(math.sqrt(a))


PLACE_OVERRIDES = {
    "belfast": {"name": "Belfast", "lat": 54.5973, "lng": -5.9301, "region": "Northern Ireland", "country": "Northern Ireland"},
    "derry": {"name": "Derry", "lat": 54.9966, "lng": -7.3086, "region": "Northern Ireland", "country": "Northern Ireland"},
    "lisburn": {"name": "Lisburn", "lat": 54.5162, "lng": -6.0580, "region": "Northern Ireland", "country": "Northern Ireland"},
}


async def geocode_place(place: str) -> dict | None:
    """Geocode a city/place name using postcodes.io places API."""
    place_lower = place.lower().replace("-", " ")
    if place_lower in PLACE_OVERRIDES:
        return PLACE_OVERRIDES[place_lower]
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            r = await client.get(f"https://api.postcodes.io/places?q={place}&limit=1")
            if r.status_code == 200:
                results = r.json().get("result") or []
                if results:
                    p = results[0]
                    return {
                        "name": p["name_1"],
                        "lat": p["latitude"],
                        "lng": p["longitude"],
                        "region": p.get("region"),
                        "country": p.get("country"),
                    }
    except Exception as e:
        logger.warning(f"Geocode failed for {place}: {e}")
    return None


@router.get("/cheap-fuel/{location}")
async def cheap_fuel_location(
    location: str,
    db: AsyncSession = Depends(get_db),
) -> dict:
    # Check cache
    cache_key = f"cheap_fuel_{location}"
    cached = _cache_get(cache_key)
    if cached:
        return cached

    # Try to geocode
    place = await geocode_place(location.replace("-", " "))
    if not place:
        raise HTTPException(status_code=404, detail="Location not found")

    lat, lng = place["lat"], place["lng"]
    radius_km = 16  # ~10 miles

    lat_margin = radius_km / 111.0
    lng_margin = radius_km / (111.0 * math.cos(math.radians(lat)))

    async def fetch_fuel(fuel: str) -> tuple:
        result = await db.execute(text("""
            SELECT DISTINCT ON (ph.station_id)
                ph.station_id,
                ph.price_pence,
                ph.source_updated_at,
                s.name,
                s.brand,
                s.address,
                s.postcode,
                s.latitude,
                s.longitude,
                s.is_motorway,
                s.is_supermarket
            FROM price_history ph
            JOIN stations s ON ph.station_id = s.id
            WHERE ph.fuel_type = :fuel
              AND ph.price_flagged = false
              AND (s.permanent_closure = FALSE OR s.permanent_closure IS NULL)
              AND s.latitude BETWEEN :lat_min AND :lat_max
              AND s.longitude BETWEEN :lng_min AND :lng_max
            ORDER BY ph.station_id, ph.recorded_at DESC
        """), {
            "fuel": fuel,
            "lat_min": lat - lat_margin,
            "lat_max": lat + lat_margin,
            "lng_min": lng - lng_margin,
            "lng_max": lng + lng_margin,
        })
        rows = result.fetchall()
        stations = []
        prices = []
        for row in rows:
            dist = haversine_km(lat, lng, row.latitude, row.longitude)
            if dist <= radius_km:
                stations.append({
                    "station_id": row.station_id,
                    "name": row.name,
                    "brand": row.brand,
                    "address": row.address,
                    "postcode": row.postcode,
                    "latitude": row.latitude,
                    "longitude": row.longitude,
                    "price_pence": row.price_pence,
                    "is_motorway": row.is_motorway or False,
                    "is_supermarket": row.is_supermarket or False,
                    "distance_km": round(dist, 2),
                    "source_updated_at": row.source_updated_at.isoformat() if row.source_updated_at else None,
                })
                prices.append(row.price_pence)
        stations.sort(key=lambda x: x["price_pence"])
        fuel_stats = {"min": round(min(prices), 1), "max": round(max(prices), 1), "avg": round(sum(prices) / len(prices), 1), "count": len(prices)} if prices else None
        return fuel, stations[:10], fuel_stats

    async def fetch_national() -> dict:
        nat_result = await db.execute(text("""
            SELECT fuel_type, ROUND(AVG(price_pence)::numeric, 1) as avg_price
            FROM price_history
            WHERE fuel_type = ANY(:fuels)
              AND price_flagged = false
              AND recorded_at >= NOW() - INTERVAL '48 hours'
            GROUP BY fuel_type
        """), {"fuels": FUEL_TYPES})
        return {row.fuel_type: float(row.avg_price) for row in nat_result.fetchall()}

    import asyncio
    results = await asyncio.gather(
        fetch_fuel("E10"),
        fetch_fuel("B7"),
        fetch_fuel("E5"),
        fetch_national(),
    )

    cheapest = {}
    stats = {}
    for fuel, stations, fuel_stats in results[:3]:
        cheapest[fuel] = stations
        if fuel_stats:
            stats[fuel] = fuel_stats
    national = results[3]

    result = {
        "location": place,
        "cheapest": cheapest,
        "stats": stats,
        "national": national,
    }
    _cache_set(cache_key, result)
    return result
