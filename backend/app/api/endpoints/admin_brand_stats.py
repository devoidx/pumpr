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
