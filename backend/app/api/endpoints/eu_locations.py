"""
EU fuel price endpoints — /api/v1/eu/cheap-fuel/{country}/{city}
Serves station-level prices from eu_stations + eu_latest_prices.
Currency: EUR stored natively; GBP conversion via exchange_rates table
(falls back to None if no rate available yet).
"""
from __future__ import annotations

import logging
import math
import time as _time

from fastapi import APIRouter, HTTPException
from sqlalchemy import text

from app.db.session import AsyncSessionLocal

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/eu", tags=["eu-locations"])

# Simple in-memory cache — same pattern as locations_seo.py
_cache: dict = {}
_CACHE_TTL = 3600  # 1 hour — EU data updates daily, no need for 10-min TTL


def _cache_get(key: str):
    if key in _cache:
        val, ts = _cache[key]
        if _time.time() - ts < _CACHE_TTL:
            return val
        del _cache[key]
    return None


def _cache_set(key: str, val) -> None:
    _cache[key] = (val, _time.time())


# Curated city list — France first. Used for SEO snapshot generation.
# Coordinates are city centres used for radius search.
EU_CITIES: dict[str, dict[str, float | str]] = {
    "calais":            {"lat": 50.9513, "lon": 1.8587,  "country": "FR", "name": "Calais"},
    "boulogne-sur-mer":  {"lat": 50.7264, "lon": 1.6141,  "country": "FR", "name": "Boulogne-sur-Mer"},
    "dunkirk":           {"lat": 51.0343, "lon": 2.3769,  "country": "FR", "name": "Dunkirk"},
    "lille":             {"lat": 50.6292, "lon": 3.0573,  "country": "FR", "name": "Lille"},
    "rouen":             {"lat": 49.4431, "lon": 1.0993,  "country": "FR", "name": "Rouen"},
    "paris":             {"lat": 48.8566, "lon": 2.3522,  "country": "FR", "name": "Paris"},
    "reims":             {"lat": 49.2583, "lon": 4.0317,  "country": "FR", "name": "Reims"},
    "le-havre":          {"lat": 49.4944, "lon": 0.1079,  "country": "FR", "name": "Le Havre"},
    "caen":              {"lat": 49.1829, "lon": -0.3707, "country": "FR", "name": "Caen"},
    "rennes":            {"lat": 48.1173, "lon": -1.6778, "country": "FR", "name": "Rennes"},
    "saint-malo":        {"lat": 48.6493, "lon": -2.0258, "country": "FR", "name": "Saint-Malo"},
    "bordeaux":          {"lat": 44.8378, "lon": -0.5792, "country": "FR", "name": "Bordeaux"},
    "toulouse":          {"lat": 43.6047, "lon": 1.4442,  "country": "FR", "name": "Toulouse"},
    "lyon":              {"lat": 45.7640, "lon": 4.8357,  "country": "FR", "name": "Lyon"},
    "nice":              {"lat": 43.7102, "lon": 7.2620,  "country": "FR", "name": "Nice"},
    "marseille":         {"lat": 43.2965, "lon": 5.3698,  "country": "FR", "name": "Marseille"},
    # Spain
    "madrid":     {"lat": 40.4146, "lon": -3.6701, "country": "ES", "name": "Madrid"},
    "barcelona":  {"lat": 41.4010, "lon":  2.1672, "country": "ES", "name": "Barcelona"},
    "malaga":     {"lat": 36.7067, "lon": -4.4591, "country": "ES", "name": "Malaga"},
    "alicante":   {"lat": 38.3575, "lon": -0.4996, "country": "ES", "name": "Alicante"},
    "valencia":   {"lat": 39.4684, "lon": -0.3780, "country": "ES", "name": "Valencia"},
    "seville":    {"lat": 37.3904, "lon": -5.9573, "country": "ES", "name": "Seville"},
    "palma":      {"lat": 39.5788, "lon":  2.6643, "country": "ES", "name": "Palma"},
    "las-palmas": {"lat": 28.1058, "lon": -15.4372, "country": "ES", "name": "Las Palmas"},
    "bilbao":     {"lat": 43.2623, "lon": -2.9271, "country": "ES", "name": "Bilbao"},
    "murcia":     {"lat": 37.9833, "lon": -1.1297, "country": "ES", "name": "Murcia"},
    "girona":     {"lat": 41.9760, "lon":  2.8163, "country": "ES", "name": "Girona"},
    "marbella":   {"lat": 36.5078, "lon": -4.8628, "country": "ES", "name": "Marbella"},
    # Italy
    "rome":              {"lat": 41.8851, "lon": 12.4969, "country": "IT", "name": "Rome"},
    "milan":             {"lat": 45.4729, "lon": 9.1754,  "country": "IT", "name": "Milan"},
    "turin":             {"lat": 45.0724, "lon": 7.6662,  "country": "IT", "name": "Turin"},
    "naples":            {"lat": 40.8542, "lon": 14.2491, "country": "IT", "name": "Naples"},
    "palermo":           {"lat": 38.1275, "lon": 13.3444, "country": "IT", "name": "Palermo"},
    "genoa":             {"lat": 44.4236, "lon": 8.9260,  "country": "IT", "name": "Genoa"},
    "florence":          {"lat": 43.7788, "lon": 11.2396, "country": "IT", "name": "Florence"},
    "bologna":           {"lat": 44.5017, "lon": 11.3461, "country": "IT", "name": "Bologna"},
    "catania":           {"lat": 37.5128, "lon": 15.0779, "country": "IT", "name": "Catania"},
    "verona":            {"lat": 45.4328, "lon": 10.9818, "country": "IT", "name": "Verona"},
    "venice":            {"lat": 45.4818, "lon": 12.2541, "country": "IT", "name": "Venice"},
    "bari":              {"lat": 41.1085, "lon": 16.8629, "country": "IT", "name": "Bari"},
}

RADIUS_KM = 25  # broader than UK 16km — city centres in France are more spread out


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    R = 6371
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (
        math.sin(dlat / 2) ** 2
        + math.cos(math.radians(lat1))
        * math.cos(math.radians(lat2))
        * math.sin(dlon / 2) ** 2
    )
    return R * 2 * math.asin(math.sqrt(a))


async def get_eur_to_gbp() -> float | None:
    """Fetch the most recent EUR→GBP rate from exchange_rates table."""
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            text("SELECT eur_to_gbp FROM exchange_rates ORDER BY rate_date DESC LIMIT 1")
        )
        row = result.fetchone()
        return float(row.eur_to_gbp) if row else None


@router.get("/cheap-fuel/{country}/{city}")
async def eu_cheap_fuel(country: str, city: str) -> dict:
    country = country.upper()
    city_key = city.lower()

    city_meta = EU_CITIES.get(city_key)
    if city_meta is None or city_meta["country"] != country:
        raise HTTPException(status_code=404, detail="City not found")

    cache_key = f"eu_cheap_fuel_{country}_{city_key}"
    cached = _cache_get(cache_key)
    if cached:
        return cached

    lat = float(city_meta["lat"])
    lon = float(city_meta["lon"])
    lat_margin = RADIUS_KM / 111.0
    lon_margin = RADIUS_KM / (111.0 * math.cos(math.radians(lat)))

    eur_to_gbp = await get_eur_to_gbp()

    async with AsyncSessionLocal() as db:
        result = await db.execute(
            text("""
                SELECT
                    s.external_id,
                    s.name,
                    s.address,
                    s.city,
                    s.postcode,
                    s.latitude,
                    s.longitude,
                    s.is_motorway,
                    p.fuel_type,
                    p.price_eur,
                    p.recorded_at
                FROM eu_stations s
                JOIN eu_latest_prices p ON p.eu_station_id = s.id
                WHERE s.country = :country
                  AND s.latitude  BETWEEN :lat_min AND :lat_max
                  AND s.longitude BETWEEN :lon_min AND :lon_max
            """),
            {
                "country": country,
                "lat_min": lat - lat_margin,
                "lat_max": lat + lat_margin,
                "lon_min": lon - lon_margin,
                "lon_max": lon + lon_margin,
            },
        )
        rows = result.fetchall()

    # Group by fuel type, filter to radius, sort by price
    by_fuel: dict[str, list[dict]] = {}
    for row in rows:
        dist = haversine_km(lat, lon, row.latitude, row.longitude)
        if dist > RADIUS_KM:
            continue
        station: dict = {
            "external_id": row.external_id,
            "name": row.name,
            "address": row.address,
            "city": row.city,
            "postcode": row.postcode,
            "latitude": row.latitude,
            "longitude": row.longitude,
            "fuel_type": row.fuel_type,
            "price_eur": float(row.price_eur),
            "price_gbp": round(float(row.price_eur) * eur_to_gbp, 3) if eur_to_gbp else None,
            "distance_km": round(dist, 2),
            "recorded_at": row.recorded_at.isoformat() if row.recorded_at else None,
            "is_motorway": row.is_motorway or False,
        }
        by_fuel.setdefault(row.fuel_type, []).append(station)

    for fuel in by_fuel:
        by_fuel[fuel].sort(key=lambda x: x["price_eur"])

    # Per-fuel stats
    stats: dict[str, dict] = {}
    for fuel, stations in by_fuel.items():
        prices = [s["price_eur"] for s in stations]
        stats[fuel] = {
            "min": round(min(prices), 3),
            "max": round(max(prices), 3),
            "avg": round(sum(prices) / len(prices), 3),
            "count": len(prices),
        }

    result_data = {
        "city": city_meta["name"],
        "country": country,
        "eur_to_gbp": eur_to_gbp,
        "cheapest": {fuel: stations[:10] for fuel, stations in by_fuel.items()},
        "stats": stats,
    }
    _cache_set(cache_key, result_data)
    return result_data


@router.get("/nearby")
async def eu_nearby(
    lat: float,
    lng: float,
    radius_km: float = 25,
    country: str = "FR",
    fuel_type: str | None = None,
) -> dict:
    country = country.upper()
    lat_margin = radius_km / 111.0
    lng_margin = radius_km / (111.0 * math.cos(math.radians(lat)))

    eur_to_gbp = await get_eur_to_gbp()

    fuel_filter = "AND p.fuel_type = :fuel_type" if fuel_type else ""

    async with AsyncSessionLocal() as db:
        result = await db.execute(
            text(f"""
                SELECT
                    s.id,
                    s.external_id,
                    s.name,
                    s.address,
                    s.city,
                    s.postcode,
                    s.latitude,
                    s.longitude,
                    s.is_motorway,
                    p.fuel_type,
                    p.price_eur,
                    p.recorded_at
                FROM eu_stations s
                JOIN eu_latest_prices p ON p.eu_station_id = s.id
                WHERE s.country = :country
                  AND s.latitude  BETWEEN :lat_min AND :lat_max
                  AND s.longitude BETWEEN :lng_min AND :lng_max
                  {fuel_filter}
            """),
            {
                "country": country,
                "lat_min": lat - lat_margin,
                "lat_max": lat + lat_margin,
                "lng_min": lng - lng_margin,
                "lng_max": lng + lng_margin,
                **({"fuel_type": fuel_type} if fuel_type else {}),
            },
        )
        rows = result.fetchall()

    stations = []
    for row in rows:
        dist = haversine_km(lat, lng, row.latitude, row.longitude)
        if dist > radius_km:
            continue
        stations.append({
            "id": row.id,
            "external_id": row.external_id,
            "name": row.name,
            "address": row.address,
            "city": row.city,
            "postcode": row.postcode,
            "latitude": row.latitude,
            "longitude": row.longitude,
            "fuel_type": row.fuel_type,
            "price_eur": float(row.price_eur),
            "price_gbp": round(float(row.price_eur) * eur_to_gbp, 4) if eur_to_gbp else None,
            "distance_km": round(dist, 2),
            "recorded_at": row.recorded_at.isoformat() if row.recorded_at else None,
            "is_motorway": row.is_motorway or False,
        })

    stations.sort(key=lambda x: (x["fuel_type"], x["price_eur"]))

    return {
        "stations": stations,
        "eur_to_gbp": eur_to_gbp,
        "country": country,
        "center": {"lat": lat, "lng": lng},
        "radius_km": radius_km,
    }
# Italy cities added to EU_CITIES dict — paste after existing FR entries
