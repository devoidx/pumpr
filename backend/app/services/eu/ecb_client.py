"""
Fetches the daily EUR→GBP reference rate from the ECB's free XML feed.
No API key required. Updates once per working day ~16:00 CET.
Feed: https://www.ecb.europa.eu/stats/eurofxref/eurofxref-daily.xml
"""
import logging
from datetime import date, datetime

import httpx
from sqlalchemy import text

from app.db.session import AsyncSessionLocal

logger = logging.getLogger(__name__)

ECB_URL = "https://www.ecb.europa.eu/stats/eurofxref/eurofxref-daily.xml"
ECB_NS = "http://www.ecb.int/vocabulary/2002-08-01/eurofxref"


async def fetch_ecb_eur_to_gbp() -> tuple[date, float] | None:
    """
    Fetches today's ECB EUR→GBP rate.
    Returns (rate_date, rate) or None if the feed is unavailable or GBP not present.
    """
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.get(ECB_URL)
            resp.raise_for_status()
            xml = resp.content
    except Exception:
        logger.exception("ecb_client: failed to fetch ECB feed")
        return None

    try:
        from xml.etree import ElementTree as ET
        root = ET.fromstring(xml)
        # ECB XML structure:
        # <gesmes:Envelope>
        #   <Cube>
        #     <Cube time="2026-07-01">
        #       <Cube currency="GBP" rate="0.85120"/>
        #       ...
        #     </Cube>
        #   </Cube>
        # </gesmes:Envelope>
        ns = {"ecb": ECB_NS}
        outer = root.find(".//ecb:Cube/ecb:Cube", ns)
        if outer is None:
            logger.error("ecb_client: could not find date Cube element in ECB feed")
            return None

        rate_date_str = outer.get("time")
        if rate_date_str is None:
            logger.error("ecb_client: date Cube element has no time attribute")
            return None
        rate_date = datetime.strptime(rate_date_str, "%Y-%m-%d").date()

        for cube in outer.findall("ecb:Cube", ns):
            if cube.get("currency") == "GBP":
                rate_str = cube.get("rate")
                if rate_str is None:
                    logger.error("ecb_client: GBP Cube has no rate attribute")
                    return None
                return rate_date, float(rate_str)

        logger.error("ecb_client: GBP not found in ECB feed")
        return None

    except Exception:
        logger.exception("ecb_client: failed to parse ECB feed")
        return None


async def upsert_ecb_rate() -> bool:
    """
    Fetches and stores today's EUR→GBP rate. Returns True on success.
    Safe to call repeatedly — ON CONFLICT DO UPDATE is idempotent.
    """
    result = await fetch_ecb_eur_to_gbp()
    if result is None:
        return False

    rate_date, rate = result
    try:
        async with AsyncSessionLocal() as db:
            await db.execute(
                text("""
                    INSERT INTO exchange_rates (rate_date, eur_to_gbp)
                    VALUES (:rate_date, :eur_to_gbp)
                    ON CONFLICT (rate_date) DO UPDATE SET
                        eur_to_gbp = EXCLUDED.eur_to_gbp,
                        fetched_at = now()
                """),
                {"rate_date": rate_date, "eur_to_gbp": rate},
            )
            await db.commit()
        logger.info("ecb_client: upserted EUR→GBP rate %s = %s", rate_date, rate)
        return True
    except Exception:
        logger.exception("ecb_client: failed to upsert ECB rate")
        return False
