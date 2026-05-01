import logging
from datetime import datetime

from sqlalchemy import text

from app.core.config import settings
from app.db.session import AsyncSessionLocal

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
    "E5": "Unleaded (E5)",
    "B7": "Diesel (B7)",
    "SDV": "Super Diesel",
    "B10": "Biodiesel",
    "HVO": "HVO",
}


def _bsky_client():
    from atproto import Client
    client = Client()
    client.login(settings.bsky_handle, settings.bsky_app_password)
    return client


def _mastodon_post(content: str) -> bool:
    """Post to Mastodon. Returns True on success."""
    if not settings.mastodon_access_token:
        return False
    try:
        import httpx
        resp = httpx.post(
            f"{settings.mastodon_instance}/api/v1/statuses",
            headers={"Authorization": f"Bearer {settings.mastodon_access_token}"},
            data={"status": content, "visibility": "public"},
            timeout=10,
        )
        resp.raise_for_status()
        logger.info("Posted to Mastodon")
        return True
    except Exception as e:
        logger.error(f"Mastodon post failed: {e}")
        return False


def _threads_post(text: str) -> bool:
    """Post to Threads. Returns True on success."""
    if not settings.threads_user_id:
        return False
    try:
        import os

        import httpx
        user_id = settings.threads_user_id
        # Prefer token from file (refreshed), fall back to env var
        token_file = os.getenv("THREADS_TOKEN_FILE", "/app/data/threads_token.txt")
        if os.path.exists(token_file):
            with open(token_file) as f:
                token = f.read().strip()
        else:
            token = settings.threads_access_token
        if not token:
            return False
        # Step 1: create media container
        create = httpx.post(
            f"https://graph.threads.net/v1.0/{user_id}/threads",
            params={"media_type": "TEXT", "text": text, "access_token": token},
            timeout=10,
        )
        create.raise_for_status()
        creation_id = create.json().get("id")
        if not creation_id:
            logger.error(f"Threads: no creation_id in response: {create.text}")
            return False
        # Step 2: publish
        publish = httpx.post(
            f"https://graph.threads.net/v1.0/{user_id}/threads_publish",
            params={"creation_id": creation_id, "access_token": token},
            timeout=10,
        )
        publish.raise_for_status()
        logger.info("Posted to Threads")
        return True
    except Exception as e:
        logger.error(f"Threads post failed: {e}")
        return False


async def refresh_threads_token() -> bool:
    """Refresh the Threads long-lived token and persist to file."""
    try:
        import os

        import httpx
        token_file = os.getenv("THREADS_TOKEN_FILE", "/app/data/threads_token.txt")
        if os.path.exists(token_file):
            with open(token_file) as f:
                current_token = f.read().strip()
        else:
            current_token = settings.threads_access_token
        if not current_token:
            logger.warning("No Threads token to refresh")
            return False
        resp = httpx.get(
            "https://graph.threads.net/access_token",
            params={
                "grant_type": "th_refresh_token",
                "access_token": current_token,
            },
            timeout=10,
        )
        resp.raise_for_status()
        new_token = resp.json().get("access_token")
        if not new_token:
            logger.error(f"Threads refresh: no token in response: {resp.text}")
            return False

        # Write new token to file for persistence across restarts
        token_file = os.getenv("THREADS_TOKEN_FILE", "/app/data/threads_token.txt")
        try:
            os.makedirs(os.path.dirname(token_file), exist_ok=True)
            with open(token_file, "w") as f:
                f.write(new_token)
            logger.info(f"Threads token refreshed and written to {token_file}")
        except Exception as write_err:
            logger.warning(f"Threads token refreshed but could not write to file: {write_err}")

        return True
    except Exception as e:
        logger.error(f"Threads token refresh failed: {e}")
        return False


async def _get_uk_averages() -> list[dict]:
    async with AsyncSessionLocal() as session:
        result = await session.execute(text("""
            WITH latest AS (
                SELECT DISTINCT ON (station_id, fuel_type)
                    station_id, fuel_type, price_pence, price_flagged
                FROM price_history
                ORDER BY station_id, fuel_type, recorded_at DESC
            )
            SELECT fuel_type, ROUND(AVG(price_pence)::numeric, 1) as avg_price
            FROM latest l
            JOIN stations s ON l.station_id = s.id
            WHERE s.permanent_closure = FALSE
              AND (l.price_flagged = FALSE OR l.price_flagged IS NULL)
            GROUP BY fuel_type
            ORDER BY fuel_type
        """))
        return [{"fuel_type": r.fuel_type, "avg_price": float(r.avg_price)} for r in result.fetchall()]


async def _get_cheapest_uk(fuel: str) -> dict | None:
    async with AsyncSessionLocal() as session:
        result = await session.execute(text("""
            WITH latest AS (
                SELECT DISTINCT ON (station_id, fuel_type)
                    station_id, fuel_type, price_pence, price_flagged
                FROM price_history
                WHERE fuel_type = :fuel
                ORDER BY station_id, fuel_type, recorded_at DESC
            )
            SELECT s.name, s.postcode, s.county, s.country, l.price_pence
            FROM latest l
            JOIN stations s ON l.station_id = s.id
            WHERE s.permanent_closure = FALSE
              AND (l.price_flagged = FALSE OR l.price_flagged IS NULL)
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
                    station_id, fuel_type, price_pence, price_flagged
                FROM price_history
                WHERE fuel_type = :fuel
                ORDER BY station_id, fuel_type, recorded_at DESC
            ),
            regional_min AS (
                SELECT s.country as region, MIN(l.price_pence) as min_price
                FROM latest l
                JOIN stations s ON l.station_id = s.id
                WHERE s.permanent_closure = FALSE
                  AND (l.price_flagged = FALSE OR l.price_flagged IS NULL)
                  AND s.country IN ('England', 'Scotland', 'Wales', 'Northern Ireland')
                GROUP BY s.country
            )
            SELECT DISTINCT ON (s.country)
                s.country, s.name, s.postcode, s.county, l.price_pence
            FROM latest l
            JOIN stations s ON l.station_id = s.id
            JOIN regional_min rm ON s.country = rm.region AND l.price_pence = rm.min_price
            WHERE s.permanent_closure = FALSE
            AND (l.price_flagged = FALSE OR l.price_flagged IS NULL)
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
        _mastodon_post(text)
        _threads_post(text)

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
        _mastodon_post(text)
        _threads_post(text)

    return text


async def post_cheapest_by_country(fuel: str = "E10", dry_run: bool = False) -> str:
    """Post cheapest station per country."""
    countries = await _get_cheapest_by_country(fuel)
    if not countries:
        return ""


    text = f"🗺️ Cheapest {FUEL_LABEL.get(fuel, fuel)} by nation today:\n\n"
    for c in countries:
        name = c["name"][:35]
        postcode = c.get("postcode") or ""
        location = f"{name}, {postcode}" if postcode else name
        text += f"{c['country']}: {c['price_pence']}p — {location}\n"
    text += "\n#UKFuel #FuelPrices #Pumpr"

    logger.info(f"Cheapest by country post:\n{text}")

    if not dry_run:
        try:
            client = _bsky_client()
            client.send_post(text=text)
            logger.info("Posted cheapest by country to Bluesky")
        except Exception as e:
            logger.error(f"Bluesky post failed: {e}")
        _mastodon_post(text)
        _threads_post(text)

    return text


async def post_cheapest_diesel(dry_run: bool = False) -> str:
    """Post cheapest diesel (B7) station to Bluesky."""
    return await post_cheapest_station("B7", dry_run=dry_run)


async def _get_cheapest_by_county_all(fuel: str) -> list[dict]:
    async with AsyncSessionLocal() as session:
        result = await session.execute(text("""
            WITH latest AS (
                SELECT DISTINCT ON (station_id, fuel_type)
                    station_id, fuel_type, price_pence, price_flagged
                FROM price_history
                WHERE fuel_type = :fuel
                ORDER BY station_id, fuel_type, recorded_at DESC
            ),
            regional_min AS (
                SELECT s.county as region, s.country, MIN(l.price_pence) as min_price
                FROM latest l
                JOIN stations s ON l.station_id = s.id
                WHERE s.permanent_closure = FALSE
                AND (l.price_flagged = FALSE OR l.price_flagged IS NULL)
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
            AND (l.price_flagged = FALSE OR l.price_flagged IS NULL)
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
    "E10": "unleaded petrol (E10)",
    "E5": "unleaded petrol (E5)",
    "B7": "diesel (B7)",
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
                _mastodon_post(text)
                _threads_post(text)
                await aio.sleep(2)
            except Exception as e:
                logger.error(f"Bluesky county post failed for {region}: {e}")
                _mastodon_post(text)
        else:
            posted.append(region)

    return posted
