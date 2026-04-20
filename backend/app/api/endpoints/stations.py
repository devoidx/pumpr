from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models.models import PriceRecord, Station
from app.schemas.schemas import PriceHistoryOut, PriceHistoryPoint, StationDetail, StationLatestPrices, StationOut
from app.services.opening_hours import is_open_now, get_week_hours

router = APIRouter(prefix="/stations", tags=["stations"])


@router.get("/", response_model=list[StationOut])
async def list_stations(
    fuel: str | None = Query(None),
    brand: str | None = Query(None),
    limit: int = Query(100, le=500),
    db: AsyncSession = Depends(get_db),
) -> list[StationOut]:
    stmt = select(Station).where((Station.permanent_closure == False) | Station.permanent_closure.is_(None)).limit(limit)
    if brand:
        stmt = stmt.where(Station.brand.ilike(f"%{brand}%"))
    result = await db.execute(stmt)
    stations = result.scalars().all()

    out = []
    for station in stations:
        latest = await _get_latest_prices(db, station.id)
        if fuel and not any(p.fuel_type == fuel for p in latest):
            continue
        out.append(StationOut(
            id=station.id,
            name=station.name,
            brand=station.brand,
            operator=station.operator,
            address=station.address,
            postcode=station.postcode,
            latitude=station.latitude,
            longitude=station.longitude,
            country=station.country,
            county=station.county,
            is_motorway=station.is_motorway or False,
            is_supermarket=station.is_supermarket or False,
            temporary_closure=station.temporary_closure or False,
            amenities=station.amenities,
            fuel_types=station.fuel_types,
            latest_prices=latest,
        ))
    return out


@router.get("/{station_id}")
async def get_station(station_id: str, db: AsyncSession = Depends(get_db)) -> dict:
    result = await db.execute(select(Station).where(Station.id == station_id))
    station = result.scalar_one_or_none()
    if not station:
        raise HTTPException(status_code=404, detail="Station not found")
    latest = await _get_latest_prices(db, station_id)

    open_now = is_open_now(station.opening_times)
    week_hours = get_week_hours(station.opening_times)

    return {
        "id": station.id,
        "name": station.name,
        "brand": station.brand,
        "operator": station.operator,
        "address": station.address,
        "postcode": station.postcode,
        "latitude": station.latitude,
        "longitude": station.longitude,
        "country": station.country,
        "county": station.county,
        "phone": station.phone,
        "is_motorway": station.is_motorway or False,
        "is_supermarket": station.is_supermarket or False,
        "temporary_closure": station.temporary_closure or False,
        "amenities": station.amenities or [],
        "fuel_types": station.fuel_types or [],
        "opening_times": station.opening_times,
        "is_open_now": open_now,
        "week_hours": week_hours,
        "latest_prices": [{"fuel_type": p.fuel_type, "price_pence": p.price_pence, "recorded_at": p.recorded_at, "source_updated_at": p.source_updated_at, "price_flagged": getattr(p, "price_flagged", False)} for p in latest],
        "created_at": station.created_at,
        "updated_at": station.updated_at,
    }


@router.get("/{station_id}/history", response_model=PriceHistoryOut)
async def get_price_history(
    station_id: str,
    fuel: str = Query(...),
    from_dt: datetime | None = Query(None),
    to_dt: datetime | None = Query(None),
    db: AsyncSession = Depends(get_db),
) -> PriceHistoryOut:
    stmt = (
        select(PriceRecord)
        .where(PriceRecord.station_id == station_id, PriceRecord.fuel_type == fuel)
        .order_by(PriceRecord.recorded_at.asc())
    )
    if from_dt:
        stmt = stmt.where(PriceRecord.recorded_at >= from_dt)
    if to_dt:
        stmt = stmt.where(PriceRecord.recorded_at <= to_dt)
    result = await db.execute(stmt)
    records = result.scalars().all()
    return PriceHistoryOut(
        station_id=station_id,
        fuel_type=fuel,
        history=[PriceHistoryPoint(recorded_at=r.recorded_at, price_pence=r.price_pence) for r in records],
    )


async def _get_latest_prices(db: AsyncSession, station_id: str) -> list[StationLatestPrices]:
    subq = (
        select(PriceRecord.fuel_type, func.max(PriceRecord.recorded_at).label("max_ts"))
        .where(PriceRecord.station_id == station_id)
        .group_by(PriceRecord.fuel_type)
        .subquery()
    )
    stmt = select(PriceRecord).join(
        subq,
        (PriceRecord.fuel_type == subq.c.fuel_type) & (PriceRecord.recorded_at == subq.c.max_ts),
    ).where(PriceRecord.station_id == station_id)
    result = await db.execute(stmt)
    records = result.scalars().all()
    return [StationLatestPrices(fuel_type=r.fuel_type, price_pence=r.price_pence, recorded_at=r.recorded_at, source_updated_at=r.source_updated_at, price_flagged=r.price_flagged or False) for r in records]


@router.get("/{station_id}/price-changes")
async def get_price_changes(
    station_id: str,
    db: AsyncSession = Depends(get_db),
) -> list[dict]:
    """Return current prices vs 24h ago for a station."""
    from datetime import timedelta
    from sqlalchemy import func

    now = datetime.utcnow()
    day_ago = now - timedelta(hours=24)

    # Latest prices
    latest_sql = text("""
        SELECT DISTINCT ON (fuel_type)
            fuel_type, price_pence, recorded_at
        FROM price_history
        WHERE station_id = :station_id
        ORDER BY fuel_type, recorded_at DESC
    """)

    # Prices ~24h ago
    old_sql = text("""
        SELECT DISTINCT ON (fuel_type)
            fuel_type, price_pence, recorded_at
        FROM price_history
        WHERE station_id = :station_id
          AND recorded_at <= :day_ago
        ORDER BY fuel_type, recorded_at DESC
    """)

    latest_result = await db.execute(latest_sql, {"station_id": station_id})
    old_result = await db.execute(old_sql, {"station_id": station_id, "day_ago": day_ago})

    latest = {r.fuel_type: r for r in latest_result.fetchall()}
    old = {r.fuel_type: r for r in old_result.fetchall()}

    changes = []
    for fuel_type, current in latest.items():
        prev = old.get(fuel_type)
        change = None
        if prev:
            change = round(current.price_pence - prev.price_pence, 1)
        changes.append({
            "fuel_type": fuel_type,
            "price_pence": current.price_pence,
            "prev_price_pence": prev.price_pence if prev else None,
            "change_pence": change,
            "recorded_at": current.recorded_at,
        })

    return sorted(changes, key=lambda x: x["fuel_type"])
