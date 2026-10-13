import logging

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import require_admin
from app.db.session import get_db
from app.models.user import User
from app.services.market_intelligence import compute_brand_stats


class ContactIn(BaseModel):
    station_id: str
    note: str | None = Field(None, max_length=2000)


class BrandContactEmailIn(BaseModel):
    brand_name: str
    contact_email: str | None = Field(None, max_length=255)
    notes: str | None = Field(None, max_length=2000)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/admin/brand-stats", tags=["admin"])


@router.get("")
async def get_brand_stats(
    admin: User = Depends(require_admin),
) -> dict:
    """Brand league table with staleness metrics (admin only).

    Uses the lightweight compute_brand_stats() (not the full
    compute_market_intelligence(), which was taking ~19s on production due
    to an expensive national-average query this endpoint never needed).
    """
    brands = await compute_brand_stats()
    return {"brands": brands}


@router.get("/stations")
async def get_brand_stale_stations(
    brand: str = Query(..., description="Brand name exactly as shown in the league table"),
    days: int = Query(21, ge=1, le=365),
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Stations under a brand whose freshest fuel is older than `days` (admin only).

    Fuels update independently, so a station only qualifies when nothing at all has
    changed. Each station's E10/B7 is compared with the median of live stations (updated
    in the last 14 days) in the same brand, country and motorway/non-motorway group,
    needing at least 3 such peers. Rows sort by the largest gap, so stations whose frozen
    price differs from their peers come first; stations without enough peers come last,
    oldest first. Closed stations, and stations the feed no longer returns (the sync flags
    those as temporarily closed), are excluded.
    """
    result = await db.execute(
        text("""
            WITH st AS (
                SELECT s.id, s.name, s.brand AS raw_brand, s.postcode, s.county, s.phone,
                       COALESCE(s.country, '') AS country,
                       COALESCE(s.is_motorway, FALSE) AS motorway,
                       COALESCE(b.display_name, s.brand) AS brand,
                       MAX(lp.source_updated_at) AS freshest,
                       MAX(lp.price_pence) FILTER (WHERE lp.fuel_type = 'E10') AS e10,
                       MAX(lp.price_pence) FILTER (WHERE lp.fuel_type = 'B7') AS b7
                FROM latest_prices lp
                JOIN stations s ON s.id = lp.station_id
                LEFT JOIN LATERAL (
                    SELECT display_name FROM brands
                    WHERE s.brand ILIKE '%' || name || '%'
                    ORDER BY LENGTH(name) DESC
                    LIMIT 1
                ) b ON true
                WHERE s.brand IS NOT NULL
                  AND (s.permanent_closure = FALSE OR s.permanent_closure IS NULL)
                  AND (s.temporary_closure = FALSE OR s.temporary_closure IS NULL)
                GROUP BY s.id, s.name, s.brand, s.postcode, s.county, s.phone, s.country,
                         s.is_motorway, COALESCE(b.display_name, s.brand)
            ), peers AS (
                SELECT country, motorway,
                       COUNT(e10) AS n_e10,
                       PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY e10) AS med_e10,
                       COUNT(b7) AS n_b7,
                       PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY b7) AS med_b7
                FROM st
                WHERE brand = :brand AND freshest > NOW() - INTERVAL '14 days'
                GROUP BY country, motorway
            )
            SELECT st.id AS station_id, st.name, st.raw_brand, st.postcode, st.county, st.phone,
                   st.freshest, EXTRACT(DAY FROM NOW() - st.freshest)::int AS days_since,
                   st.e10, st.b7, p.n_e10, p.med_e10, p.n_b7, p.med_b7
            FROM st
            LEFT JOIN peers p ON p.country = st.country AND p.motorway = st.motorway
            WHERE st.brand = :brand
              AND st.freshest < NOW() - make_interval(days => :days)
            ORDER BY st.freshest ASC
        """),
        {"brand": brand, "days": days},
    )
    rows = result.fetchall()

    min_peers = 3

    def gap(price: float | None, med: float | None, n: int | None) -> float | None:
        if price is None or med is None or n is None or n < min_peers:
            return None
        return round(float(price) - float(med), 1)

    stations: list[dict] = []
    for r in rows:
        g10 = gap(r.e10, r.med_e10, r.n_e10)
        g7 = gap(r.b7, r.med_b7, r.n_b7)
        gaps = [abs(g) for g in (g10, g7) if g is not None]
        stations.append({
            "station_id": r.station_id,
            "name": r.name,
            "brand": r.raw_brand,
            "postcode": r.postcode,
            "county": r.county,
            "phone": r.phone,
            "last_update": r.freshest.isoformat() if r.freshest else None,
            "days_since_update": r.days_since,
            "e10": r.e10,
            "e10_vs_peers": g10,
            "b7": r.b7,
            "b7_vs_peers": g7,
            "worst_gap": max(gaps) if gaps else None,
        })
    stations.sort(key=lambda s: (s["worst_gap"] is None, -(s["worst_gap"] or 0.0), s["last_update"] or ""))
    return {
        "brand": brand,
        "days_threshold": days,
        "count": len(stations),
        "sorted_by": "gap vs live peers (same brand, country, motorway/not), largest first; no peers last, oldest first",
        "stations": stations,
    }


@router.post("/contact")
async def log_brand_contact(
    payload: ContactIn,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Record that this station's brand has been contacted about stale
    reporting (admin only). Feeds the public "we've flagged this" badge
    on the station detail page until resolved.
    """
    station_check = await db.execute(
        text("SELECT id FROM stations WHERE id = :station_id"),
        {"station_id": payload.station_id},
    )
    if station_check.fetchone() is None:
        raise HTTPException(status_code=404, detail="Station not found")

    result = await db.execute(
        text("""
            INSERT INTO station_reporting_contacts (station_id, contacted_by, note)
            VALUES (:station_id, :contacted_by, :note)
            RETURNING id, contacted_at
        """),
        {"station_id": payload.station_id, "contacted_by": admin.email, "note": payload.note},
    )
    row = result.fetchone()
    assert row is not None  # RETURNING always yields a row on successful INSERT
    await db.commit()
    logger.info(f"Brand contact logged for station {payload.station_id} by {admin.email}")
    return {"id": row.id, "station_id": payload.station_id, "contacted_at": row.contacted_at.isoformat()}


@router.get("/contact/{station_id}")
async def get_brand_contact_status(
    station_id: str,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Current unresolved contact record for a station, if any (admin only)."""
    result = await db.execute(
        text("""
            SELECT id, contacted_at, contacted_by, note, resolved_at
            FROM station_reporting_contacts
            WHERE station_id = :station_id
            ORDER BY contacted_at DESC
            LIMIT 1
        """),
        {"station_id": station_id},
    )
    row = result.fetchone()
    if row is None:
        return {"contacted": False}
    return {
        "contacted": True,
        "id": row.id,
        "contacted_at": row.contacted_at.isoformat(),
        "contacted_by": row.contacted_by,
        "note": row.note,
        "resolved_at": row.resolved_at.isoformat() if row.resolved_at else None,
    }


@router.get("/contacts")
async def list_brand_contacts(
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """All brand contact records (admin only)."""
    result = await db.execute(
        text("SELECT brand_name, contact_email, notes FROM brand_contacts ORDER BY brand_name")
    )
    contacts = [dict(row._mapping) for row in result.fetchall()]
    return {"contacts": contacts}


@router.put("/contacts")
async def upsert_brand_contact(
    payload: BrandContactEmailIn,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Create or update a brand's contact email (admin only)."""
    result = await db.execute(
        text("""
            INSERT INTO brand_contacts (brand_name, contact_email, notes)
            VALUES (:brand_name, :contact_email, :notes)
            ON CONFLICT (brand_name) DO UPDATE
            SET contact_email = EXCLUDED.contact_email,
                notes = EXCLUDED.notes
            RETURNING brand_name, contact_email, notes
        """),
        {"brand_name": payload.brand_name, "contact_email": payload.contact_email, "notes": payload.notes},
    )
    row = result.fetchone()
    assert row is not None
    await db.commit()
    logger.info(f"Brand contact upserted: {payload.brand_name} by {admin.email}")
    return dict(row._mapping)
