from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models.models import PriceRecord, Station
from app.schemas.schemas import PriceHistoryOut, PriceHistoryPoint, StationDetail, StationLatestPrices, StationOut

router = APIRouter(prefix="/stations", tags=["stations"])


@router.get("/", response_model=list[StationOut])
async def list_stations(
    fuel: str | None = Query(None, description="Filter by fuel type: E10, E5, B7, SDV"),
    brand: str | None = Query(None),
    lat: float | None = Query(None),
    lng: float | None = Query(None),
    radius_km: float | None = Query(None),
    limit: int = Query(100, le=500),
    db: AsyncSession = Depends(get_db),
) -> list[StationOut]:
    stmt = select(Station).limit(limit)
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
            latest_prices=latest,
        ))
    return out


@router.get("/{station_id}", response_model=StationDetail)
async def get_station(station_id: str, db: AsyncSession = Depends(get_db)) -> StationDetail:
    result = await db.execute(select(Station).where(Station.id == station_id))
    station = result.scalar_one_or_none()
    if not station:
        raise HTTPException(status_code=404, detail="Station not found")
    latest = await _get_latest_prices(db, station_id)
    return StationDetail(
        id=station.id,
        name=station.name,
        brand=station.brand,
        operator=station.operator,
        address=station.address,
        postcode=station.postcode,
        latitude=station.latitude,
        longitude=station.longitude,
        amenities=station.amenities,
        opening_hours=station.opening_hours,
        created_at=station.created_at,
        updated_at=station.updated_at,
        latest_prices=latest,
    )


@router.get("/{station_id}/history", response_model=PriceHistoryOut)
async def get_price_history(
    station_id: str,
    fuel: str = Query(..., description="Fuel type: E10, E5, B7, SDV"),
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
    return [StationLatestPrices(fuel_type=r.fuel_type, price_pence=r.price_pence, recorded_at=r.recorded_at) for r in records]
