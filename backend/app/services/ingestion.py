import logging
from datetime import datetime

from sqlalchemy.dialects.postgresql import insert
from sqlalchemy import text, case, literal

from app.db.session import AsyncSessionLocal
from app.models.models import PriceRecord, Station
from app.services.fuel_finder_client import fuel_finder_client
from app.services.geocoding import lookup_postcodes_batch

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

COUNTRY_MAP = {
    'ENGLAND': 'England', 'E': 'England',
    'SCOTLAND': 'Scotland', 'S': 'Scotland',
    'WALES': 'Wales', 'W': 'Wales',
    'NORTHERN IRELAND': 'Northern Ireland', 'N. IRELAND': 'Northern Ireland',
    'N': 'Northern Ireland', 'UNITED KINGDOM': 'England', 'UK': 'England',
}

SUPERMARKET_BRANDS = {
    'tesco', 'morrisons', 'sainsbury', 'asda', 'aldi', 'lidl',
    'waitrose', 'marks & spencer', 'm&s', 'co-op', 'cooperative'
}


def _normalise_country(raw: dict) -> str | None:
    country = (raw.get("location", {}).get("country") or "").strip().upper()
    return COUNTRY_MAP.get(country, raw.get("location", {}).get("country"))


def _is_supermarket(raw: dict) -> bool:
    brand = (raw.get('brand_name') or '').lower()
    return any(s in brand for s in SUPERMARKET_BRANDS)



BRAND_NORMALISE = {
    "esso": "ESSO",
    "bp": "BP",
    "shell": "SHELL",
    "tesco": "TESCO",
    "morrisons": "MORRISONS",
    "asda": "ASDA",
    "asda express": "ASDA",
    "sainsbury's": "SAINSBURY'S",
    "sainsburys": "SAINSBURY'S",
    "texaco": "TEXACO",
    "jet": "JET",
    "eg on the move": "EG ON THE MOVE",
    "gulf": "GULF",
    "valero": "VALERO",
    "murco": "MURCO",
    "maxol": "MAXOL",
    "applegreen": "APPLEGREEN",
    "certas": "CERTAS",
    "harvest energy": "HARVEST ENERGY",
}

def _normalise_brand(brand: str | None) -> str | None:
    if not brand:
        return None
    return BRAND_NORMALISE.get(brand.lower().strip(), brand.upper().strip())

async def sync_stations() -> int:
    """Fetch station metadata from API and upsert into DB. Returns count."""
    stations = await fuel_finder_client.get_stations()
    if not stations:
        logger.warning("No stations returned from API")
        return 0

    # Only geocode stations we haven't seen before (no county data yet)
    from sqlalchemy import text, select, text
    async with AsyncSessionLocal() as check_session:
        result = await check_session.execute(
            text("SELECT id FROM stations WHERE county IS NOT NULL")
        )
        known_ids = {row[0] for row in result.fetchall()}

    new_stations = [s for s in stations if s.get("node_id") not in known_ids]
    postcodes = [
        s.get("location", {}).get("postcode", "")
        for s in new_stations
        if s.get("location", {}).get("postcode")
    ]
    postcode_data: dict = {}
    if postcodes:
        for i in range(0, len(postcodes), 100):
            batch_result = await lookup_postcodes_batch(postcodes[i:i + 100])
            postcode_data.update(batch_result)
        logger.info(f"Geocoded {len(postcode_data)} new postcodes")

    async with AsyncSessionLocal() as session:
        for raw in stations:
            if raw.get("permanent_closure"):
                continue
            # Filter out test/dummy stations
            name = raw.get("trading_name", "").upper()
            if any(x in name for x in ["DUMMY", "PRE PROD", "WB 0749"]):
                continue

            location = raw.get("location", {})
            postcode = location.get("postcode") or ""
            clean_pc = postcode.replace(" ", "").upper()
            geo = postcode_data.get(clean_pc, {})

            county = geo.get("county") or None
            country = geo.get("country") or _normalise_country(raw)

            stmt = insert(Station).values(
                id=raw["node_id"],
                name=raw.get("trading_name", ""),
                brand=_normalise_brand(raw.get("brand_name")),
                operator=_normalise_brand(raw.get("brand_name")),
                address=", ".join(filter(None, [
                    location.get("address_line_1"),
                    location.get("address_line_2"),
                    location.get("city"),
                ])),
                postcode=postcode or None,
                latitude=location.get("latitude"),
                longitude=location.get("longitude"),
                country=country,
                county=county,
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
                    "brand": _normalise_brand(raw.get("brand_name")),
                    "operator": _normalise_brand(raw.get("brand_name")),
                    "address": ", ".join(filter(None, [
                        location.get("address_line_1"),
                        location.get("address_line_2"),
                        location.get("city"),
                    ])),
                    "postcode": postcode or None,
                    "latitude": location.get("latitude"),
                    "longitude": location.get("longitude"),
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


# Fallback hard limits per fuel type (pence)
FUEL_HARD_LIMITS = {
    "E10":  (100, 300),
    "E5":   (100, 320),
    "B7":   (100, 320),
    "SDV":  (100, 350),
    "B10":  (100, 350),
    "HVO":  (100, 400),
}

# Cache for median prices, refreshed each ingest run
_median_cache: dict[str, float] = {}


async def _get_median_prices(session) -> dict[str, float]:
    """Get median price per fuel type from recent price history."""
    result = await session.execute(text("""
        SELECT fuel_type, PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY price_pence) as median
        FROM price_history
        WHERE recorded_at > NOW() - INTERVAL '24 hours'
        GROUP BY fuel_type
    """))
    return {row.fuel_type: float(row.median) for row in result.fetchall()}


def _is_valid_price(fuel_type: str, price: float, medians: dict[str, float]) -> bool:
    """Validate price using dynamic median-based limits with hard floor/ceiling."""
    hard_min, hard_max = FUEL_HARD_LIMITS.get(fuel_type, (100, 400))
    if not (hard_min <= price <= hard_max):
        return False
    # If we have median data, also check within 40% of median
    if fuel_type in medians:
        median = medians[fuel_type]
        if price < median * 0.6 or price > median * 1.4:
            logger.warning(f"Price outlier: {fuel_type} {price}p (median {median}p)")
            return False
    return True


async def ingest_prices() -> int:
    """Fetch current prices from API and write to price_history. Returns count."""
    prices = await fuel_finder_client.get_prices()
    if not prices:
        logger.warning("No prices returned from API")
        return 0

    # Get median prices for outlier detection
    async with AsyncSessionLocal() as session:
        medians = await _get_median_prices(session)

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
            if price is None:
                continue
            price = float(price)
            if price < 100:
                logger.warning(f"Rejected price {price}p for {internal_fuel_type} at {station_id}")
                continue
            flagged = False
            if internal_fuel_type in medians and price < medians[internal_fuel_type] * 0.6:
                logger.warning(f"Flagged suspicious price {price}p for {internal_fuel_type} at {station_id}")
                flagged = True
            records.append(
                PriceRecord(
                    station_id=station_id,
                    fuel_type=internal_fuel_type,
                    price_pence=price,
                    recorded_at=now,
                    source_updated_at=_parse_dt(fuel_entry.get("price_last_updated")),
                    price_flagged=flagged,
                )
            )

    async with AsyncSessionLocal() as session:
        session.add_all(records)
        await session.commit()

    flagged_count = sum(1 for r in records if r.price_flagged)
    logger.info(f"Ingested {len(records)} price records ({flagged_count} flagged)")
    return len(records)

def _parse_dt(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00")).replace(tzinfo=None)
    except (ValueError, AttributeError):
        return None
