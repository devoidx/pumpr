import logging
import httpx

logger = logging.getLogger(__name__)

POSTCODES_API = "https://api.postcodes.io/postcodes"

COUNTRY_MAP = {
    "England": "England",
    "Scotland": "Scotland",
    "Wales": "Wales",
    "Northern Ireland": "Northern Ireland",
}


async def lookup_postcodes_batch(postcodes: list[str]) -> dict[str, dict]:
    """Batch lookup postcodes via postcodes.io. Returns dict of clean_postcode -> {county, country}."""
    if not postcodes:
        return {}
    clean = [p.replace(" ", "").upper() for p in postcodes if p]
    if not clean:
        return {}
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.post(POSTCODES_API, json={"postcodes": clean})
            resp.raise_for_status()
            results = {}
            for item in resp.json().get("result", []):
                if item and item.get("result"):
                    r = item["result"]
                    pc = r.get("postcode", "").replace(" ", "").upper()
                    country = COUNTRY_MAP.get(r.get("country", ""))
                    county = (r.get("admin_county") or r.get("admin_district") or "").upper().strip()
                    results[pc] = {
                        "county": county or None,
                        "country": country,
                    }
            return results
    except Exception as e:
        logger.warning(f"postcodes.io lookup failed: {e}")
        return {}
