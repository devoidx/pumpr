from __future__ import annotations

import json
import logging
from datetime import date

from sqlalchemy import text

from app.db.session import AsyncSessionLocal

logger = logging.getLogger(__name__)

FUEL_TYPES = ["E10", "B7", "E5", "SDV"]

COUNTY_TO_REGION = {
    # England - London
    "GREATER LONDON": "Greater London",
    # England - South East
    "KENT": "South East", "SURREY": "South East", "EAST SUSSEX": "South East",
    "WEST SUSSEX": "South East", "HAMPSHIRE": "South East", "BERKSHIRE": "South East",
    "OXFORDSHIRE": "South East", "BUCKINGHAMSHIRE": "South East",
    "ISLE OF WIGHT": "South East",
    # England - South West
    "CORNWALL": "South West", "DEVON": "South West", "DORSET": "South West",
    "SOMERSET": "South West", "WILTSHIRE": "South West", "GLOUCESTERSHIRE": "South West",
    "BRISTOL": "South West", "AVON": "South West",
    # England - East of England
    "NORFOLK": "East of England", "SUFFOLK": "East of England", "CAMBRIDGESHIRE": "East of England",
    "BEDFORDSHIRE": "East of England", "HERTFORDSHIRE": "East of England",
    "ESSEX": "East of England",
    # England - East Midlands
    "LEICESTERSHIRE": "East Midlands", "NOTTINGHAMSHIRE": "East Midlands",
    "DERBYSHIRE": "East Midlands", "LINCOLNSHIRE": "East Midlands",
    "NORTHAMPTONSHIRE": "East Midlands", "RUTLAND": "East Midlands",
    # England - West Midlands
    "WEST MIDLANDS": "West Midlands", "WARWICKSHIRE": "West Midlands",
    "STAFFORDSHIRE": "West Midlands", "SHROPSHIRE": "West Midlands",
    "HEREFORDSHIRE": "West Midlands", "WORCESTERSHIRE": "West Midlands",
    # England - Yorkshire
    "WEST YORKSHIRE": "Yorkshire and the Humber", "SOUTH YORKSHIRE": "Yorkshire and the Humber",
    "NORTH YORKSHIRE": "Yorkshire and the Humber", "EAST RIDING OF YORKSHIRE": "Yorkshire and the Humber",
    "CITY OF KINGSTON UPON HULL": "Yorkshire and the Humber",
    # England - North West
    "GREATER MANCHESTER": "North West", "LANCASHIRE": "North West", "CHESHIRE": "North West",
    "MERSEYSIDE": "North West", "CUMBRIA": "North West",
    # England - North East
    "TYNE AND WEAR": "North East", "COUNTY DURHAM": "North East",
    "NORTHUMBERLAND": "North East", "CLEVELAND": "North East",
    # Scotland
    "ABERDEENSHIRE": "Scotland", "ANGUS": "Scotland", "ARGYLL AND BUTE": "Scotland",
    "AYRSHIRE": "Scotland", "DUNBARTONSHIRE": "Scotland", "DUMFRIES AND GALLOWAY": "Scotland",
    "FIFE": "Scotland", "GLASGOW CITY": "Scotland", "INVERNESS-SHIRE": "Scotland",
    "LANARKSHIRE": "Scotland", "LOTHIAN": "Scotland", "MORAY": "Scotland",
    "ORKNEY": "Scotland", "PERTHSHIRE": "Scotland", "RENFREWSHIRE": "Scotland",
    "SCOTTISH BORDERS": "Scotland", "SHETLAND": "Scotland", "STIRLINGSHIRE": "Scotland",
    # Wales
    "CLWYD": "Wales", "DYFED": "Wales", "GWENT": "Wales", "GWYNEDD": "Wales",
    "MID GLAMORGAN": "Wales", "POWYS": "Wales", "SOUTH GLAMORGAN": "Wales",
    "WEST GLAMORGAN": "Wales",
    # Northern Ireland
    "COUNTY ANTRIM": "Northern Ireland", "COUNTY ARMAGH": "Northern Ireland",
    "COUNTY DOWN": "Northern Ireland", "COUNTY FERMANAGH": "Northern Ireland",
    "COUNTY LONDONDERRY": "Northern Ireland", "COUNTY TYRONE": "Northern Ireland",
}

SUPERMARKET_BRANDS = {"TESCO", "ASDA", "MORRISONS", "SAINSBURY'S", "COSTCO WHOLESALE"}
MOTORWAY_BRANDS = {"WELCOME BREAK", "MOTO", "ROADCHEF", "EXTRA MSA", "APPLEGREEN"}


async def compute_market_intelligence() -> dict:
    """Compute comprehensive market intelligence stats from latest price data."""
    async with AsyncSessionLocal() as db:
        logger.info("Computing market intelligence...")

        # ── National averages ──────────────────────────────────────────────
        nat_result = await db.execute(text("""
            SELECT
                ph.fuel_type,
                ROUND(AVG(ph.price_pence)::numeric, 2) as avg_price,
                ROUND(MIN(ph.price_pence)::numeric, 2) as min_price,
                ROUND(MAX(ph.price_pence)::numeric, 2) as max_price,
                ROUND(PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY ph.price_pence)::numeric, 2) as median_price,
                COUNT(DISTINCT ph.station_id) as station_count
            FROM (
                SELECT DISTINCT ON (station_id, fuel_type)
                    station_id, fuel_type, price_pence
                FROM price_history
                WHERE fuel_type = ANY(:fuels)
                  AND price_flagged = false
                  AND price_pence BETWEEN 50 AND 350
                ORDER BY station_id, fuel_type, recorded_at DESC
            ) ph
            GROUP BY ph.fuel_type
        """), {"fuels": FUEL_TYPES})
        national_rows = nat_result.fetchall()
        national = {
            row.fuel_type: {
                "avg": float(row.avg_price),
                "min": float(row.min_price),
                "max": float(row.max_price),
                "median": float(row.median_price),
                "stations": int(row.station_count),
            }
            for row in national_rows
        }

        # ── Supermarket vs branded discount ───────────────────────────────
        super_result = await db.execute(text("""
            SELECT
                ph.fuel_type,
                ROUND(AVG(CASE WHEN s.is_supermarket THEN ph.price_pence END)::numeric, 2) as supermarket_avg,
                ROUND(AVG(CASE WHEN NOT s.is_supermarket AND NOT s.is_motorway THEN ph.price_pence END)::numeric, 2) as branded_avg,
                ROUND(AVG(CASE WHEN s.is_motorway THEN ph.price_pence END)::numeric, 2) as motorway_avg
            FROM (
                SELECT DISTINCT ON (ph.station_id, ph.fuel_type)
                    ph.station_id, ph.fuel_type, ph.price_pence
                FROM price_history ph
                WHERE ph.fuel_type = ANY(:fuels)
                  AND ph.price_flagged = false
                  AND ph.price_pence BETWEEN 50 AND 350
                ORDER BY ph.station_id, ph.fuel_type, ph.recorded_at DESC
            ) ph
            JOIN stations s ON ph.station_id = s.id
            GROUP BY ph.fuel_type
        """), {"fuels": ["E10", "B7", "E5", "SDV"]})
        for row in super_result.fetchall():
            if row.fuel_type in national:
                national[row.fuel_type]["supermarket_avg"] = float(row.supermarket_avg) if row.supermarket_avg else 0.0
                national[row.fuel_type]["branded_avg"] = float(row.branded_avg) if row.branded_avg else 0.0
                national[row.fuel_type]["motorway_avg"] = float(row.motorway_avg) if row.motorway_avg else 0.0
                if row.supermarket_avg and row.branded_avg:
                    national[row.fuel_type]["supermarket_discount"] = round(float(row.branded_avg) - float(row.supermarket_avg), 2)
                if row.motorway_avg and national[row.fuel_type].get("avg"):
                    national[row.fuel_type]["motorway_premium"] = round(float(row.motorway_avg) - national[row.fuel_type]["avg"], 2)

        # ── Regional breakdown ─────────────────────────────────────────────
        regional_result = await db.execute(text("""
            SELECT
                s.county,
                s.country,
                ph.fuel_type,
                ROUND(AVG(ph.price_pence)::numeric, 2) as avg_price,
                COUNT(DISTINCT ph.station_id) as station_count
            FROM (
                SELECT DISTINCT ON (station_id, fuel_type)
                    station_id, fuel_type, price_pence
                FROM price_history
                WHERE fuel_type = ANY(:fuels)
                  AND price_flagged = false
                  AND price_pence BETWEEN 50 AND 350
                ORDER BY station_id, fuel_type, recorded_at DESC
            ) ph
            JOIN stations s ON ph.station_id = s.id
            WHERE s.county IS NOT NULL
            GROUP BY s.county, s.country, ph.fuel_type
        """), {"fuels": ["E10", "B7"]})

        # Aggregate by region
        region_data: dict = {}
        for row in regional_result.fetchall():
            region = COUNTY_TO_REGION.get(row.county, row.country or "Other")
            if region not in region_data:
                region_data[region] = {"E10": [], "B7": [], "stations": set()}
            if row.fuel_type in region_data[region]:
                region_data[region][row.fuel_type].append((float(row.avg_price), int(row.station_count)))
            region_data[region]["stations"].add(row.county)

        regional = []
        for region, data in region_data.items():
            entry = {"region": region}
            for fuel in ["E10", "B7"]:
                if data[fuel]:
                    total_stations = sum(s for _, s in data[fuel])
                    weighted_avg = sum(p * s for p, s in data[fuel]) / total_stations
                    entry[fuel] = round(weighted_avg, 2)
                    entry[f"{fuel}_stations"] = total_stations
            regional.append(entry)

        regional.sort(key=lambda x: x.get("E10", 999))

        # ── Brand league table ─────────────────────────────────────────────
        brand_result = await db.execute(text("""
            SELECT
                s.brand,
                ph.fuel_type,
                ROUND(AVG(ph.price_pence)::numeric, 2) as avg_price,
                COUNT(DISTINCT ph.station_id) as station_count,
                ROUND(
                    100.0 * COUNT(CASE WHEN ph.recorded_at >= NOW() - INTERVAL '7 days' THEN 1 END)::numeric
                    / COUNT(*)::numeric, 1
                ) as update_rate_7d
            FROM (
                SELECT DISTINCT ON (station_id, fuel_type)
                    station_id, fuel_type, price_pence, recorded_at
                FROM price_history
                WHERE fuel_type = ANY(:fuels)
                  AND price_flagged = false
                  AND price_pence BETWEEN 50 AND 350
                ORDER BY station_id, fuel_type, recorded_at DESC
            ) ph
            JOIN stations s ON ph.station_id = s.id
            WHERE s.brand IS NOT NULL
            GROUP BY s.brand, ph.fuel_type
            HAVING COUNT(DISTINCT ph.station_id) >= 5
        """), {"fuels": ["E10", "B7"]})

        brand_data: dict = {}
        for row in brand_result.fetchall():
            if row.brand not in brand_data:
                brand_data[row.brand] = {"brand": row.brand}
            brand_data[row.brand][row.fuel_type] = float(row.avg_price)
            brand_data[row.brand][f"{row.fuel_type}_stations"] = int(row.station_count)
            brand_data[row.brand]["update_rate_7d"] = float(row.update_rate_7d)

        # Add vs national average
        nat_e10 = national.get("E10", {}).get("avg", 0)
        nat_b7 = national.get("B7", {}).get("avg", 0)
        brands = []
        for b in brand_data.values():
            if "E10" in b:
                b["E10_vs_national"] = round(b["E10"] - nat_e10, 2)
            if "B7" in b:
                b["B7_vs_national"] = round(b["B7"] - nat_b7, 2)
            brands.append(b)

        brands.sort(key=lambda x: x.get("E10", 999))

        # ── Postcode sector analysis ───────────────────────────────────────
        postcode_result = await db.execute(text("""
            SELECT
                SUBSTRING(s.postcode FROM '^[A-Z]{1,2}[0-9]{1,2}') as sector,
                ROUND(AVG(ph.price_pence)::numeric, 2) as avg_price,
                ROUND(MIN(ph.price_pence)::numeric, 2) as min_price,
                ROUND(MAX(ph.price_pence)::numeric, 2) as max_price,
                ROUND((MAX(ph.price_pence) - MIN(ph.price_pence))::numeric, 2) as price_range,
                COUNT(DISTINCT ph.station_id) as station_count,
                MODE() WITHIN GROUP (ORDER BY s.brand) as price_leader_brand
            FROM (
                SELECT DISTINCT ON (station_id, fuel_type)
                    station_id, fuel_type, price_pence
                FROM price_history
                WHERE fuel_type = 'E10'
                  AND price_flagged = false
                  AND price_pence BETWEEN 50 AND 350
                ORDER BY station_id, fuel_type, recorded_at DESC
            ) ph
            JOIN stations s ON ph.station_id = s.id
            WHERE s.postcode IS NOT NULL
            GROUP BY sector
            HAVING COUNT(DISTINCT ph.station_id) >= 3
            ORDER BY avg_price ASC
        """))

        postcode_sectors = []
        for row in postcode_result.fetchall():
            price_range = float(row.price_range)
            market_type = "Competitive" if price_range >= 10 else "Concentrated"
            postcode_sectors.append({
                "sector": row.sector,
                "avg_e10": float(row.avg_price),
                "min_e10": float(row.min_price),
                "max_e10": float(row.max_price),
                "price_range": price_range,
                "stations": int(row.station_count),
                "market_type": market_type,
                "price_leader": row.price_leader_brand,
            })

        logger.info(f"Market intelligence computed: {len(brands)} brands, {len(regional)} regions, {len(postcode_sectors)} postcode sectors")

        return {
            "national": national,
            "regional": regional,
            "brands": brands,
            "postcode_sectors": postcode_sectors,
        }


async def generate_narrative(data: dict) -> str:
    """Generate a narrative summary using Claude API."""
    try:
        import httpx

        from app.core.config import settings

        nat = data["national"]
        e10 = nat.get("E10", {})
        b7 = nat.get("B7", {})
        regional = data["regional"]
        brands = data["brands"]

        cheapest_region = regional[0]["region"] if regional else "N/A"
        most_expensive_region = regional[-1]["region"] if regional else "N/A"
        cheapest_region_price = regional[0].get("E10", 0) if regional else 0
        most_expensive_region_price = regional[-1].get("E10", 0) if regional else 0

        prompt = f"""Write a concise market intelligence summary (3-4 paragraphs) for UK fuel prices today.
Use a professional, analytical tone. Include specific numbers. Do not use bullet points.

Data:
- National E10 average: {e10.get('avg')}p (range: {e10.get('min')}p - {e10.get('max')}p, {e10.get('stations')} stations)
- National B7 average: {b7.get('avg')}p (range: {b7.get('min')}p - {b7.get('max')}p)
- Diesel premium over petrol: {round(b7.get('avg', 0) - e10.get('avg', 0), 1)}p
- Supermarket E10 discount vs branded: {e10.get('supermarket_discount')}p
- Motorway E10 premium vs national: {e10.get('motorway_premium')}p
- Cheapest region: {cheapest_region} at {cheapest_region_price}p
- Most expensive region: {most_expensive_region} at {most_expensive_region_price}p
- Regional spread: {round(most_expensive_region_price - cheapest_region_price, 1)}p
- Cheapest brands: {', '.join([f"{b['brand']} ({b.get('E10', 'N/A')}p)" for b in brands[:3]])}

Write the summary now:"""

        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(
                "https://api.anthropic.com/v1/messages",
                headers={
                    "Content-Type": "application/json",
                    "x-api-key": settings.anthropic_api_key,
                    "anthropic-version": "2023-06-01",
                },
                json={
                    "model": "claude-sonnet-4-5",
                    "max_tokens": 600,
                    "messages": [{"role": "user", "content": prompt}],
                }
            )
            return response.json()["content"][0]["text"]
    except Exception as e:
        logger.error(f"Narrative generation failed: {e}")
        return ""


async def run_market_intelligence_job() -> None:
    """Compute and store market intelligence. Called by scheduler."""
    try:
        from app.db.session import AsyncSessionLocal

        data = await compute_market_intelligence()
        narrative = await generate_narrative(data)

        async with AsyncSessionLocal() as db:
            today = date.today()
            await db.execute(text("""
                INSERT INTO market_intelligence (date, national, regional, brands, postcode_sectors, narrative)
                VALUES (:date, :national, :regional, :brands, :postcode_sectors, :narrative)
                ON CONFLICT (date) DO UPDATE SET
                    computed_at = NOW(),
                    national = EXCLUDED.national,
                    regional = EXCLUDED.regional,
                    brands = EXCLUDED.brands,
                    postcode_sectors = EXCLUDED.postcode_sectors,
                    narrative = EXCLUDED.narrative
            """), {
                "date": today,
                "national": json.dumps(data["national"]),
                "regional": json.dumps(data["regional"]),
                "brands": json.dumps(data["brands"]),
                "postcode_sectors": json.dumps(data["postcode_sectors"]),
                "narrative": narrative,
            })
            await db.commit()

        logger.info(f"Market intelligence stored for {today}")
    except Exception as e:
        logger.error(f"Market intelligence job failed: {e}")
