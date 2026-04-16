import logging
from datetime import datetime

from sqlalchemy.dialects.postgresql import insert

from app.db.session import AsyncSessionLocal
from app.models.models import PriceRecord, Station
from app.services.fuel_finder_client import fuel_finder_client

logger = logging.getLogger(__name__)

FUEL_TYPE_MAP = {
    "E10":        "E10",
    "E5":         "E5",
    "B7_STANDARD": "B7",
    "B7_Standard": "B7",  # fallback for old casing
    "B7_PREMIUM":  "SDV",
    "B7_Premium":  "SDV",  # fallback
    "B10":        "B10",
    "HVO":        "HVO",
}


async def sync_stations() -> int:
    """Fetch station metadata from API and upsert into DB. Returns count."""
    stations = await fuel_finder_client.get_stations()
    if not stations:
        logger.warning("No stations returned from API")
        return 0

    async with AsyncSessionLocal() as session:
        for raw in stations:
            location = raw.get("location", {})
            stmt = insert(Station).values(
                id=raw["node_id"],
                name=raw.get("trading_name", ""),
                brand=raw.get("brand_name"),
                operator=raw.get("brand_name"),
                address=", ".join(filter(None, [
                    location.get("address_line_1"),
                    location.get("address_line_2"),
                    location.get("city"),
                ])),
                postcode=location.get("postcode"),
                latitude=location.get("latitude"),
                longitude=location.get("longitude"),
                amenities=str(raw.get("amenities", [])),
                opening_hours=str(raw.get("opening_times", {})),
            ).on_conflict_do_update(
                index_elements=["id"],
                set_={
                    "name": raw.get("trading_name", ""),
                    "brand": raw.get("brand_name"),
                    "operator": raw.get("brand_name"),
                    "address": ", ".join(filter(None, [
                        location.get("address_line_1"),
                        location.get("address_line_2"),
                        location.get("city"),
                    ])),
                    "postcode": location.get("postcode"),
                    "latitude": location.get("latitude"),
                    "longitude": location.get("longitude"),
                    "amenities": str(raw.get("amenities", [])),
                    "opening_hours": str(raw.get("opening_times", {})),
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
        station_id = raw.get("node_id")
        if not station_id:
            continue
        for fuel_entry in raw.get("fuel_prices", []):
            api_fuel_type = fuel_entry.get("fuel_type")
            internal_fuel_type = FUEL_TYPE_MAP.get(api_fuel_type)
            if not internal_fuel_type:
                logger.debug(f"Unknown fuel type: {api_fuel_type}")
                continue
            price = fuel_entry.get("price")
            if price is not None:
                records.append(
                    PriceRecord(
                        station_id=station_id,
                        fuel_type=internal_fuel_type,
                        price_pence=float(price),
                        recorded_at=now,
                        source_updated_at=_parse_dt(fuel_entry.get("price_last_updated")),
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
        dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
        return dt.replace(tzinfo=None)
    except (ValueError, AttributeError):
        return None
