from datetime import datetime

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models.models import PriceRecord, Station
from app.schemas.schemas import StatsOut

router = APIRouter(prefix="/prices", tags=["prices"])


@router.get("/cheapest")
async def get_cheapest(
    fuel: str = Query(..., description="Fuel type: E10, E5, B7, SDV"),
    lat: float | None = Query(None),
    lng: float | None = Query(None),
    radius_km: float = Query(10.0),
    limit: int = Query(20, le=100),
    db: AsyncSession = Depends(get_db),
) -> list[dict]:
    """Return cheapest stations for a given fuel type, optionally within a radius."""
    subq = (
        select(PriceRecord.station_id, func.max(PriceRecord.recorded_at).label("max_ts"))
        .where(PriceRecord.fuel_type == fuel)
        .group_by(PriceRecord.station_id)
        .subquery()
    )
    stmt = (
        select(PriceRecord, Station)
        .join(subq, (PriceRecord.station_id == subq.c.station_id) & (PriceRecord.recorded_at == subq.c.max_ts))
        .join(Station, PriceRecord.station_id == Station.id)
        .where(PriceRecord.fuel_type == fuel)
        .order_by(PriceRecord.price_pence.asc())
        .limit(limit)
    )
    result = await db.execute(stmt)
    rows = result.all()

    return [
        {
            "station_id": price.station_id,
            "station_name": station.name,
            "brand": station.brand,
            "address": station.address,
            "postcode": station.postcode,
            "latitude": station.latitude,
            "longitude": station.longitude,
            "fuel_type": fuel,
            "price_pence": price.price_pence,
            "recorded_at": price.recorded_at,
        }
        for price, station in rows
    ]


@router.get("/stats", response_model=list[StatsOut])
async def get_stats(db: AsyncSession = Depends(get_db)) -> list[StatsOut]:
    """UK-wide average, min, max price per fuel type based on latest readings."""
    subq = (
        select(PriceRecord.station_id, PriceRecord.fuel_type, func.max(PriceRecord.recorded_at).label("max_ts"))
        .group_by(PriceRecord.station_id, PriceRecord.fuel_type)
        .subquery()
    )
    stmt = (
        select(
            PriceRecord.fuel_type,
            func.avg(PriceRecord.price_pence).label("avg_price"),
            func.min(PriceRecord.price_pence).label("min_price"),
            func.max(PriceRecord.price_pence).label("max_price"),
            func.count(PriceRecord.station_id).label("station_count"),
        )
        .join(
            subq,
            (PriceRecord.station_id == subq.c.station_id)
            & (PriceRecord.fuel_type == subq.c.fuel_type)
            & (PriceRecord.recorded_at == subq.c.max_ts),
        )
        .group_by(PriceRecord.fuel_type)
    )
    result = await db.execute(stmt)
    rows = result.all()
    now = datetime.utcnow()
    return [
        StatsOut(
            fuel_type=row.fuel_type,
            avg_price_pence=round(row.avg_price, 2),
            min_price_pence=row.min_price,
            max_price_pence=row.max_price,
            station_count=row.station_count,
            as_of=now,
        )
        for row in rows
    ]
