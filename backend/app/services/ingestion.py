import logging
from datetime import datetime

from sqlalchemy.dialects.postgresql import insert

from app.db.session import AsyncSessionLocal
from app.models.models import PriceRecord, Station
from app.services.fuel_finder_client import fuel_finder_client

logger = logging.getLogger(__name__)

FUEL_TYPE_MAP = {
    "E10":         "E10",
    "E5":          "E5",
    "B7_STANDARD": "B7",
    "B7_Standard": "B7",
    "B7_PREMIUM":  "SDV",
    "B7_Premium":  "SDV",
    "B10":         "B10",
    "HVO":         "HVO",
}


async def sync_stations() -> int:
    stations = await fuel_finder_client.get_stations()
    if not stations:
        logger.warning("No stations returned from API")
        return 0

    async with AsyncSessionLocal() as session:
        for raw in stations:
            # Skip permanently closed stations
            if raw.get("permanent_closure"):
                continue

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
                country=_normalise_country(raw),
                county=location.get("county"),
                phone=raw.get("public_phone_number"),
                amenities=raw.get("amenities", []),
                opening_times=raw.get("opening_times", {}),
                fuel_types=raw.get("fuel_types", []),
                is_motorway=bool(raw.get("is_motorway_service_station") or False),
                is_supermarket=_is_supermarket(raw),
                temporary_closure=bool(raw.get("temporary_closure") or False),
                permanent_closure=bool(raw.get("permanent_closure") or False),
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
                    "country": _normalise_country(raw),
                    "county": location.get("county"),
                    "phone": raw.get("public_phone_number"),
                    "amenities": raw.get("amenities", []),
                    "opening_times": raw.get("opening_times", {}),
                    "fuel_types": raw.get("fuel_types", []),
                    "is_motorway": bool(raw.get("is_motorway_service_station") or False),
                    "is_supermarket": _is_supermarket(raw),
                    "temporary_closure": bool(raw.get("temporary_closure") or False),
                    "permanent_closure": bool(raw.get("permanent_closure") or False),
                    "updated_at": datetime.utcnow(),
                },
            )
            await session.execute(stmt)
        await session.commit()

    logger.info(f"Synced {len(stations)} stations")
    return len(stations)


async def ingest_prices() -> int:
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
                continue
            price = fuel_entry.get("price")
            if price is not None and 50 <= float(price) <= 300:
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
        return datetime.fromisoformat(value.replace("Z", "+00:00")).replace(tzinfo=None)
    except (ValueError, AttributeError):
        return None



COUNTRY_MAP = {
    'ENGLAND': 'England', 'E': 'England',
    'SCOTLAND': 'Scotland', 'S': 'Scotland',
    'WALES': 'Wales', 'W': 'Wales',
    'NORTHERN IRELAND': 'Northern Ireland', 'N. IRELAND': 'Northern Ireland',
    'N': 'Northern Ireland', 'UNITED KINGDOM': 'England', 'UK': 'England',
}

def _normalise_country(raw: dict) -> str | None:
    country = (raw.get("location", {}).get("country") or "").strip().upper()
    return COUNTRY_MAP.get(country, raw.get("location", {}).get("country"))

SUPERMARKET_BRANDS = {
    'tesco', 'morrisons', 'sainsbury', 'asda', 'aldi', 'lidl',
    'waitrose', 'marks & spencer', 'm&s', 'co-op', 'cooperative'
}


def _is_supermarket(raw: dict) -> bool:
    if False:  # API field unreliable, use brand-based logic only
        return True
    brand = (raw.get('brand_name') or '').lower()
    return any(s in brand for s in SUPERMARKET_BRANDS)
