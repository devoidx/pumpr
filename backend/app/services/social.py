import logging
from datetime import datetime, timedelta
from sqlalchemy import text
from app.db.session import AsyncSessionLocal
from app.core.config import settings

logger = logging.getLogger(__name__)

FUEL_EMOJI = {
    "E10": "⛽",
    "E5": "⛽",
    "B7": "🚛",
    "SDV": "🚛",
    "B10": "🌿",
    "HVO": "🌿",
}

FUEL_LABEL = {
    "E10": "Unleaded (E10)",
    "E5": "Super Unleaded (E5)",
    "B7": "Diesel (B7)",
    "SDV": "Super Diesel",
    "B10": "Biodiesel (B10)",
    "HVO": "HVO",
}


def _bsky_client():
    from atproto import Client
    client = Client()
    client.login(settings.bsky_handle, settings.bsky_app_password)
    return client


async def _get_uk_averages() -> list[dict]:
    async with AsyncSessionLocal() as session:
        result = await session.execute(text("""
            WITH latest AS (
                SELECT DISTINCT ON (station_id, fuel_type)
                    station_id, fuel_type, price_pence
                FROM price_history
                ORDER BY station_id, fuel_type, recorded_at DESC
            )
            SELECT fuel_type, ROUND(AVG(price_pence)::numeric, 1) as avg_price
            FROM latest l
            JOIN stations s ON l.station_id = s.id
            WHERE s.permanent_closure = FALSE
            GROUP BY fuel_type
            ORDER BY fuel_type
        """))
        return [{"fuel_type": r.fuel_type, "avg_price": float(r.avg_price)} for r in result.fetchall()]


async def _get_cheapest_uk(fuel: str) -> dict | None:
    async with AsyncSessionLocal() as session:
        result = await session.execute(text("""
            WITH latest AS (
                SELECT DISTINCT ON (station_id, fuel_type)
                    station_id, fuel_type, price_pence
                FROM price_history
                WHERE fuel_type = :fuel
                ORDER BY station_id, fuel_type, recorded_at DESC
            )
            SELECT s.name, s.postcode, s.county, s.country, l.price_pence
            FROM latest l
            JOIN stations s ON l.station_id = s.id
            WHERE s.permanent_closure = FALSE
            ORDER BY l.price_pence ASC
            LIMIT 1
        """), {"fuel": fuel})
        row = result.fetchone()
        if row:
            return {
                "name": row.name,
                "postcode": row.postcode,
                "county": row.county,
                "country": row.country,
                "price_pence": row.price_pence,
            }
        return None


async def _get_cheapest_by_country(fuel: str) -> list[dict]:
    async with AsyncSessionLocal() as session:
        result = await session.execute(text("""
            WITH latest AS (
                SELECT DISTINCT ON (station_id, fuel_type)
                    station_id, fuel_type, price_pence
                FROM price_history
                WHERE fuel_type = :fuel
                ORDER BY station_id, fuel_type, recorded_at DESC
            ),
            regional_min AS (
                SELECT s.country as region, MIN(l.price_pence) as min_price
                FROM latest l
                JOIN stations s ON l.station_id = s.id
                WHERE s.permanent_closure = FALSE
                  AND s.country IN ('England', 'Scotland', 'Wales', 'Northern Ireland')
                GROUP BY s.country
            )
            SELECT DISTINCT ON (s.country)
                s.country, s.name, s.postcode, s.county, l.price_pence
            FROM latest l
            JOIN stations s ON l.station_id = s.id
            JOIN regional_min rm ON s.country = rm.region AND l.price_pence = rm.min_price
            WHERE s.permanent_closure = FALSE
            ORDER BY s.country, l.price_pence
        """), {"fuel": fuel})
        return [
            {"country": r.country, "name": r.name, "postcode": r.postcode, "county": r.county, "price_pence": r.price_pence}
            for r in result.fetchall()
        ]


async def post_daily_averages(dry_run: bool = False) -> str:
    """Post UK average fuel prices to Bluesky."""
    averages = await _get_uk_averages()
    if not averages:
        logger.warning("No averages data for daily post")
        return ""

    # Only post E10, B7, E5
    key_fuels = {a["fuel_type"]: a["avg_price"] for a in averages if a["fuel_type"] in ("E10", "B7", "E5")}

    today = datetime.utcnow().strftime("%a %d %b")
    text = f"⛽ UK Average Fuel Prices — {today}\n\n"
    text += f"Unleaded E10: {key_fuels.get('E10', '—')}p/L\n"
    text += f"Super Unleaded: {key_fuels.get('E5', '—')}p/L\n"
    text += f"Diesel: {key_fuels.get('B7', '—')}p/L\n\n"
    text += "Prices from 7,600+ UK stations 🇬🇧\n"
    text += "#UKFuel #FuelPrices #Pumpr"

    logger.info(f"Daily averages post:\n{text}")

    if not dry_run:
        try:
            client = _bsky_client()
            client.send_post(text=text)
            logger.info("Posted daily averages to Bluesky")
        except Exception as e:
            logger.error(f"Bluesky post failed: {e}")
            return ""

    return text


async def post_cheapest_station(fuel: str = "E10", dry_run: bool = False) -> str:
    """Post cheapest UK station for a fuel type."""
    station = await _get_cheapest_uk(fuel)
    if not station:
        return ""

    parts = []
    if station["county"]:
        parts.append(station["county"].title())
    if station["country"] and station["country"] != "England":
        parts.append(station["country"])
    if station["postcode"]:
        parts.append(station["postcode"])
    location = ", ".join(parts) if parts else "UK"

    text = f"💰 Cheapest {FUEL_LABEL.get(fuel, fuel)} in the UK today:\n\n"
    text += f"📍 {station['name']}\n"
    text += f"📌 {location}\n"
    text += f"💷 {station['price_pence']}p/L\n\n"
    text += "#UKFuel #CheapFuel #Pumpr"

    logger.info(f"Cheapest station post:\n{text}")

    if not dry_run:
        try:
            client = _bsky_client()
            client.send_post(text=text)
            logger.info(f"Posted cheapest {fuel} to Bluesky")
        except Exception as e:
            logger.error(f"Bluesky post failed: {e}")
            return ""

    return text


async def post_cheapest_by_country(fuel: str = "E10", dry_run: bool = False) -> str:
    """Post cheapest station per country."""
    countries = await _get_cheapest_by_country(fuel)
    if not countries:
        return ""


    text = f"🗺️ Cheapest {FUEL_LABEL.get(fuel, fuel)} by nation today:\n\n"
    for c in countries:
        location_parts = [c["name"]]
        if c.get("county"):
            location_parts.append(c["county"].title())
        if c.get("postcode"):
            location_parts.append(c["postcode"])
        text += f"{c['country']}: {c['price_pence']}p — {', '.join(location_parts)}\n"
    text += "\n#UKFuel #FuelPrices #Pumpr"

    logger.info(f"Cheapest by country post:\n{text}")

    if not dry_run:
        try:
            client = _bsky_client()
            client.send_post(text=text)
            logger.info("Posted cheapest by country to Bluesky")
        except Exception as e:
            logger.error(f"Bluesky post failed: {e}")
            return ""

    return text


async def post_cheapest_diesel(dry_run: bool = False) -> str:
    """Post cheapest diesel (B7) station to Bluesky."""
    return await post_cheapest_station("B7", dry_run=dry_run)


async def _get_cheapest_by_county_all(fuel: str) -> list[dict]:
    async with AsyncSessionLocal() as session:
        result = await session.execute(text("""
            WITH latest AS (
                SELECT DISTINCT ON (station_id, fuel_type)
                    station_id, fuel_type, price_pence
                FROM price_history
                WHERE fuel_type = :fuel
                ORDER BY station_id, fuel_type, recorded_at DESC
            ),
            regional_min AS (
                SELECT s.county as region, s.country, MIN(l.price_pence) as min_price
                FROM latest l
                JOIN stations s ON l.station_id = s.id
                WHERE s.permanent_closure = FALSE
                  AND s.county IS NOT NULL AND s.county != ''
                  AND s.country IN ('England', 'Scotland', 'Wales', 'Northern Ireland')
                GROUP BY s.county, s.country
            )
            SELECT
                s.county as region,
                s.country,
                s.name,
                s.postcode,
                l.price_pence,
                COUNT(*) OVER (PARTITION BY s.county) as ties
            FROM latest l
            JOIN stations s ON l.station_id = s.id
            JOIN regional_min rm ON s.county = rm.region AND l.price_pence = rm.min_price
            WHERE s.permanent_closure = FALSE
              AND s.county IS NOT NULL AND s.county != ''
            ORDER BY s.county, RANDOM()
        """), {"fuel": fuel})

        rows = result.fetchall()
        seen = set()
        out = []
        for row in rows:
            if row.region in seen:
                continue
            seen.add(row.region)
            out.append({
                "region": row.region,
                "country": row.country,
                "name": row.name,
                "postcode": row.postcode,
                "price_pence": row.price_pence,
                "ties": row.ties,
            })
        return out


FUEL_FRIENDLY = {
    "E10": "unleaded petrol",
    "E5": "super unleaded petrol",
    "B7": "diesel",
    "SDV": "super diesel",
    "B10": "biodiesel",
    "HVO": "HVO",
}


async def post_cheapest_by_county(fuel: str = "E10", dry_run: bool = False) -> list[str]:
    import asyncio as aio
    counties = await _get_cheapest_by_county_all(fuel)
    if not counties:
        return []

    fuel_name = FUEL_FRIENDLY.get(fuel, fuel)
    posted = []

    for c in counties:
        region = c["region"].title()
        price = c["price_pence"]
        name = c["name"].title()
        postcode = c["postcode"] or ""
        ties = c["ties"]

        location = f"{name}, {postcode}" if postcode else name

        if ties > 1:
            text = f"⛽ {region.upper()}! Your cheapest {fuel_name} today is {price}p/L at {location} — and {ties - 1} other{'s' if ties - 1 > 1 else ''} at the same price!\n\n#UKFuel #Pumpr #{region.replace(' ', '')}"
        else:
            text = f"⛽ {region.upper()}! Your cheapest {fuel_name} today is {price}p/L at {location}!\n\n#UKFuel #Pumpr #{region.replace(' ', '')}"

        logger.info(f"County post ({region}): {text[:80]}")

        if not dry_run:
            try:
                client = _bsky_client()
                client.send_post(text=text)
                logger.info(f"Posted county cheapest for {region}")
                posted.append(region)
                await aio.sleep(2)
            except Exception as e:
                logger.error(f"Bluesky county post failed for {region}: {e}")
        else:
            posted.append(region)

    return posted
