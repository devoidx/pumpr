import logging

from fastapi import APIRouter, Depends, Query
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import require_admin
from app.db.session import get_db
from app.models.user import User
from app.services.market_intelligence import compute_market_intelligence

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/admin/brand-stats", tags=["admin"])


@router.get("")
async def get_brand_stats(
    admin: User = Depends(require_admin),
) -> dict:
    """Brand league table with staleness metrics (admin only).

    Reuses compute_market_intelligence()'s brand computation rather than a
    parallel query — same canonicalized brand grouping, same
    source_updated_at-based freshness/staleness figures.
    """
    data = await compute_market_intelligence()
    brands = sorted(
        data["brands"],
        key=lambda b: b.get("stale_rate_21d", 0),
        reverse=True,
    )
    return {"brands": brands}


@router.get("/stations")
async def get_brand_stale_stations(
    brand: str = Query(..., description="Brand display_name or raw brand text to match"),
    days: int = Query(21, ge=1, le=90),
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Individual stations for a brand, stalest first (admin only).

    Matches the same canonicalized-brand logic as the league table: a station
    is included if its raw stations.brand text contains the given brand name
    (case-insensitive), OR if it resolves via the curated brands table to a
    display_name matching the given brand — so "Valero" also picks up
    "CARNAGH HOUSE VALERO" etc.
    """
    result = await db.execute(
        text("""
            SELECT
                s.id as station_id,
                s.name,
                s.brand,
                s.postcode,
                s.county,
                lp.fuel_type,
                lp.price_pence,
                lp.source_updated_at,
                EXTRACT(DAY FROM NOW() - lp.source_updated_at)::int as days_stale
            FROM latest_prices lp
            JOIN stations s ON lp.station_id = s.id
            LEFT JOIN LATERAL (
                SELECT display_name FROM brands
                WHERE s.brand ILIKE '%' || name || '%'
                ORDER BY LENGTH(name) DESC
                LIMIT 1
            ) b ON true
            WHERE lp.price_flagged = false
              AND (s.permanent_closure = FALSE OR s.permanent_closure IS NULL)
              AND (
                  s.brand ILIKE '%' || :brand || '%'
                  OR b.display_name ILIKE :brand
              )
              AND lp.source_updated_at < NOW() - make_interval(days => :days)
            ORDER BY lp.source_updated_at ASC
        """),
        {"brand": brand, "days": days},
    )
    rows = result.fetchall()

    # Collapse to one row per station — a station can have several stale
    # fuel types (E10, B7, etc.), and counting each as a separate "station"
    # overstates how many physical sites actually need chasing.
    by_station: dict = {}
    for r in rows:
        entry = by_station.setdefault(r.station_id, {
            "station_id": r.station_id,
            "name": r.name,
            "brand": r.brand,
            "postcode": r.postcode,
            "county": r.county,
            "stale_fuels": [],
        })
        entry["stale_fuels"].append({
            "fuel_type": r.fuel_type,
            "price_pence": float(r.price_pence),
            "source_updated_at": r.source_updated_at.isoformat() if r.source_updated_at else None,
            "days_stale": r.days_stale,
        })

    stations = list(by_station.values())
    # Sort stations by their stalest fuel type, worst first
    stations.sort(key=lambda s: max(f["days_stale"] for f in s["stale_fuels"]), reverse=True)

    return {"brand": brand, "days_threshold": days, "count": len(stations), "stations": stations}
