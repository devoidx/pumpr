import math
from collections import defaultdict
from datetime import datetime

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_optional_user
from app.core.limiter import limiter
from app.db.session import get_db
from app.models.user import User
from app.schemas.schemas import StatsOut
from app.services.osrm import get_driving_distances

router = APIRouter(prefix="/prices", tags=["prices"])


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    R = 6371.0
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = (
        math.sin(dphi / 2) ** 2
        + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    )
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


@router.get("/feed-health")
async def feed_health(db: AsyncSession = Depends(get_db)) -> dict:
    """Returns age of most recent price data."""
    result = await db.execute(text("""
        SELECT MAX(recorded_at) as latest FROM price_history
    """))
    latest = result.scalar()
    if not latest:
        return {"status": "red", "message": "No data available", "minutes_ago": None}

    from datetime import datetime, timezone
    now = datetime.now(timezone.utc)
    # Make latest timezone-aware if it isn't
    if latest.tzinfo is None:
        from datetime import timezone
        latest = latest.replace(tzinfo=timezone.utc)
    minutes_ago = (now - latest).total_seconds() / 60

    if minutes_ago <= 30:
        status = "green"
        message = f"Data updated {int(minutes_ago)} mins ago"
    elif minutes_ago <= 120:
        status = "amber"
        message = f"Data updated {int(minutes_ago)} mins ago — may be slightly stale"
    else:
        status = "red"
        message = f"Data not updated for {int(minutes_ago // 60)}h {int(minutes_ago % 60)}m — feed may be down"

    return {"status": status, "message": message, "minutes_ago": round(minutes_ago, 1)}


@router.get("/cheapest")
@limiter.limit("60/minute")
async def get_cheapest(
    request: Request,
    current_user: User | None = Depends(get_optional_user),
    fuel: str = Query(...),
    lat: float | None = Query(None),
    lng: float | None = Query(None),
    radius_km: float = Query(10.0),
    limit: int = Query(20, le=100),
    brand: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
) -> list[dict]:
    brand_filter = ""
    if lat is not None and lng is not None:
        lat_margin = radius_km / 111.0
        lng_margin = radius_km / (111.0 * math.cos(math.radians(lat)))
        geo_filter = """
            AND s.latitude BETWEEN :lat_min AND :lat_max
            AND s.longitude BETWEEN :lng_min AND :lng_max
        """
        params = {
            "fuel": fuel,
            "lat_min": lat - lat_margin,
            "lat_max": lat + lat_margin,
            "lng_min": lng - lng_margin,
            "lng_max": lng + lng_margin,
        }
    else:
        geo_filter = ""
        params = {"fuel": fuel}

    if brand:
        params["brand"] = brand
        brand_filter = "AND UPPER(s.brand) = UPPER(:brand)"

    sql = text(f"""
        SELECT DISTINCT ON (ph.station_id)
            ph.station_id,
            ph.price_pence,
            ph.recorded_at,
            ph.source_updated_at,
            ph.price_flagged,
            s.name,
            s.brand,
            s.address,
            s.postcode,
            s.latitude,
            s.longitude,
            s.is_motorway,
            s.is_supermarket,
            s.temporary_closure,
            s.amenities,
            s.opening_times,
            s.county,
            prev.price_pence as prev_price_pence
        FROM price_history ph
        JOIN stations s ON ph.station_id = s.id
        LEFT JOIN LATERAL (
            SELECT price_pence FROM price_history
            WHERE station_id = ph.station_id
              AND fuel_type = :fuel
              AND recorded_at BETWEEN NOW() - INTERVAL '26 hours' AND NOW() - INTERVAL '22 hours'
            ORDER BY recorded_at DESC
            LIMIT 1
        ) prev ON true
        WHERE ph.fuel_type = :fuel
          AND (s.permanent_closure = FALSE OR s.permanent_closure IS NULL)
          AND s.latitude IS NOT NULL
          AND s.longitude IS NOT NULL
          {geo_filter}
          {brand_filter}
        ORDER BY ph.station_id, ph.recorded_at DESC
    """)

    result = await db.execute(sql, params)
    rows = result.fetchall()

    output = []
    for row in rows:
        if lat is not None and lng is not None:
            dist = haversine_km(lat, lng, row.latitude, row.longitude)
            if dist > radius_km:
                continue
        else:
            dist = None

        output.append({
            "station_id": row.station_id,
            "station_name": row.name,
            "brand": row.brand,
            "address": row.address,
            "postcode": row.postcode,
            "latitude": row.latitude,
            "longitude": row.longitude,
            "is_motorway": row.is_motorway or False,
            "is_supermarket": row.is_supermarket or False,
            "temporary_closure": row.temporary_closure or False,
            "amenities": row.amenities or [],
            "opening_times": row.opening_times,
            "fuel_type": fuel,
            "price_pence": row.price_pence,
            "price_flagged": bool(row.price_flagged) if row.price_flagged is not None else False,
            "recorded_at": row.recorded_at,
            "source_updated_at": row.source_updated_at,
            "distance_km": round(dist, 2) if dist is not None else None,
            "county": row.county,
            "is_county_cheapest": False,
            "price_change_pence": round(row.price_pence - float(row.prev_price_pence), 1) if row.prev_price_pence is not None else None,
        })

    output.sort(key=lambda x: (x["price_pence"], x["distance_km"] if x["distance_km"] is not None else 9999))

    # Add driving distances for Pro users who have enabled it
    if current_user and current_user.role in ("pro", "admin") and getattr(current_user, "use_driving_distance", False) and lat and lng:
        top10 = output[:10]
        driving = await get_driving_distances(lat, lng, top10, db)
        for s in output[:10]:
            d = driving.get(s["station_id"])
            if d:
                s["driving_km"] = d["driving_km"]
                s["driving_mins"] = d["driving_mins"]

    # Flag cheapest non-flagged station per county (whole county, not just search radius)
    counties = list(set(s["county"] for s in output if s.get("county") and not s["price_flagged"]))
    county_cheapest: dict[str, float] = {}
    if counties:
        placeholders = ",".join(f":c{i}" for i in range(len(counties)))
        county_params = {f"c{i}": c for i, c in enumerate(counties)}
        county_params["fuel"] = fuel
        cp_result = await db.execute(text(f"""
            SELECT s.county, MIN(ph.price_pence) as min_price
            FROM price_history ph
            JOIN stations s ON ph.station_id = s.id
            WHERE s.county IN ({placeholders})
              AND ph.fuel_type = :fuel
              AND ph.price_flagged = FALSE
              AND ph.recorded_at > NOW() - INTERVAL '2 hours'
            GROUP BY s.county
        """), county_params)
        county_cheapest = {r.county: float(r.min_price) for r in cp_result.fetchall()}

    for s in output:
        county = s.get("county")
        if county and not s["price_flagged"] and county_cheapest.get(county) == s["price_pence"]:
            s["is_county_cheapest"] = True

    return output[:limit]


@router.get("/stats", response_model=list[StatsOut])
async def get_stats(db: AsyncSession = Depends(get_db)) -> list[StatsOut]:
    sql = text("""
        SELECT DISTINCT ON (ph.station_id, ph.fuel_type)
            ph.fuel_type,
            ph.price_pence
        FROM price_history ph
        JOIN stations s ON ph.station_id = s.id
        WHERE (s.permanent_closure = FALSE OR s.permanent_closure IS NULL)
          AND (ph.price_flagged = FALSE OR ph.price_flagged IS NULL)
          AND ph.recorded_at > NOW() - INTERVAL '2 hours'
        ORDER BY ph.station_id, ph.fuel_type, ph.recorded_at DESC
    """)
    result = await db.execute(sql)
    rows = result.fetchall()

    by_fuel: dict = defaultdict(list)
    for row in rows:
        by_fuel[row.fuel_type].append(row.price_pence)

    now = datetime.utcnow()
    return [
        StatsOut(
            fuel_type=fuel,
            avg_price_pence=round(sum(prices) / len(prices), 2),
            min_price_pence=min(prices),
            max_price_pence=max(prices),
            station_count=len(prices),
            as_of=now,
        )
        for fuel, prices in sorted(by_fuel.items())
    ]
