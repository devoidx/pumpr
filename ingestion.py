import logging
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import AsyncSessionLocal
from app.models.models import PriceRecord, Station
from app.services.fuel_finder_client import fuel_finder_client

logger = logging.getLogger(__name__)


async def sync_stations() -> int:
    """Fetch station metadata from API and upsert into DB. Returns count."""
    stations = await fuel_finder_client.get_stations()
    if not stations:
        logger.warning("No stations returned from API")
        return 0

    async with AsyncSessionLocal() as session:
        for raw in stations:
            stmt = insert(Station).values(
                id=raw["id"],
                name=raw.get("name", ""),
                brand=raw.get("brand"),
                operator=raw.get("operator"),
                address=raw.get("address"),
                postcode=raw.get("postcode"),
                latitude=raw.get("latitude"),
                longitude=raw.get("longitude"),
                amenities=str(raw.get("amenities", {})),
                opening_hours=str(raw.get("openingHours", {})),
            ).on_conflict_do_update(
                index_elements=["id"],
                set_={
                    "name": raw.get("name", ""),
                    "brand": raw.get("brand"),
                    "operator": raw.get("operator"),
                    "address": raw.get("address"),
                    "postcode": raw.get("postcode"),
                    "latitude": raw.get("latitude"),
                    "longitude": raw.get("longitude"),
                    "amenities": str(raw.get("amenities", {})),
                    "opening_hours": str(raw.get("openingHours", {})),
                    "updated_at": datetime.utcnow(),
                },
            )
            await session.execute(stmt)
        await session.commit()

    logger.info(f"Synced {len(stations)} stations")
    return len(stations)


async def ingest_prices() -> int:
    """Fetch current prices from API and write to price_history. Returns count."""
    prices = await fuel_finder_client.get_prices()
    if not prices:
        logger.warning("No prices returned from API")
        return 0

    now = datetime.utcnow()
    records: list[PriceRecord] = []

    for raw in prices:
        station_id = raw.get("stationId") or raw.get("id")
        for fuel_type in ("E10", "E5", "B7", "SDV"):
            price = raw.get(fuel_type.lower()) or raw.get(fuel_type)
            if price is not None:
                records.append(
                    PriceRecord(
                        station_id=station_id,
                        fuel_type=fuel_type,
                        price_pence=float(price),
                        recorded_at=now,
                        source_updated_at=_parse_dt(raw.get("lastUpdated")),
                    )
                )

    async with AsyncSessionLocal() as session:
        session.add_all(records)
        await session.commit()

    logger.info(f"Ingested {len(records)} price records")
    return len(records)


def _parse_dt(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except (ValueError, AttributeError):
        return None
