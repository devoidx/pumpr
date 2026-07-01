"""
Client for Italy's official fuel price feed (MIMIT — Ministero delle Imprese e del Made in Italy).
Two files, joined on idImpianto:
  - anagrafica_impianti_attivi.csv — station reference (name, brand, coordinates)
  - prezzo_alle_8.csv — daily prices (as of 08:00 previous day)
Both are pipe-delimited (|), UTF-8, with extraction date on line 1 and header on line 2.
Self-service only (isSelf=1) — served prices excluded to avoid confusing UK users.
"""
import logging
from datetime import datetime, timezone

import httpx

from app.services.eu.fuel_type_map import FUEL_TYPE_MAP

logger = logging.getLogger(__name__)

ITALY_PRICES_URL = "https://www.mimit.gov.it/images/exportCSV/prezzo_alle_8.csv"
ITALY_STATIONS_URL = "https://www.mimit.gov.it/images/exportCSV/anagrafica_impianti_attivi.csv"

# Italy bounding box — mainland + Sicily + Sardinia
LAT_MIN, LAT_MAX = 36.0, 47.5
LON_MIN, LON_MAX = 6.5, 18.5


async def fetch_italy_raw() -> tuple[bytes, bytes]:
    async with httpx.AsyncClient(timeout=60) as client:
        prices_resp = await client.get(ITALY_PRICES_URL)
        prices_resp.raise_for_status()
        stations_resp = await client.get(ITALY_STATIONS_URL)
        stations_resp.raise_for_status()
    return prices_resp.content, stations_resp.content


def parse_italy_csv(prices_bytes: bytes, stations_bytes: bytes) -> list[dict]:
    """
    Parses both MIMIT CSV files and returns normalized station+price rows.
    One dict per (station, fuel_type) — matches the eu_latest_prices upsert shape.
    Self-service prices only (isSelf=1).
    """
    # Parse stations — skip line 0 (extraction date), line 1 is header
    stations: dict[str, dict] = {}
    stations_text = stations_bytes.decode("utf-8", errors="replace")
    station_lines = stations_text.splitlines()
    skipped_coords = 0

    for line in station_lines[2:]:  # skip extraction date + header
        parts = line.split("|")
        if len(parts) < 10:
            continue
        id_impianto = parts[0].strip()
        brand = parts[2].strip()       # Bandiera
        name = parts[4].strip()        # Nome Impianto
        address = parts[5].strip()     # Indirizzo
        city = parts[6].strip()        # Comune

        try:
            lat = float(parts[8].strip().replace(",", "."))
            lon = float(parts[9].strip().replace(",", "."))
        except ValueError:
            skipped_coords += 1
            continue

        if not (LAT_MIN <= lat <= LAT_MAX and LON_MIN <= lon <= LON_MAX):
            skipped_coords += 1
            continue

        tipo = parts[3].strip()  # Tipo Impianto: Stradale or Autostradale
        stations[id_impianto] = {
            "external_id": id_impianto,
            "country": "IT",
            "name": name or address,
            "brand": brand or None,
            "address": address,
            "postcode": "",
            "city": city,
            "latitude": lat,
            "longitude": lon,
            "is_motorway": tipo == "Autostradale",
        }

    if skipped_coords:
        logger.warning("italy_client: skipped %d stations with invalid/out-of-bounds coordinates", skipped_coords)

    # Parse prices — skip line 0 (extraction date), line 1 is header
    prices_text = prices_bytes.decode("ascii", errors="replace")
    price_lines = prices_text.splitlines()

    # Extract extraction date from line 0 for use as recorded_at
    extraction_date_str = price_lines[0].replace("Estrazione del", "").strip() if price_lines else ""
    try:
        recorded_at = datetime.strptime(extraction_date_str, "%Y-%m-%d").replace(
            hour=8, tzinfo=timezone.utc
        )
    except ValueError:
        recorded_at = datetime.now(timezone.utc)

    rows = []
    for line in price_lines[2:]:  # skip extraction date + header
        parts = line.split("|")
        if len(parts) < 5:
            continue

        id_impianto = parts[0].strip()
        fuel_raw = parts[1].strip()
        is_self = parts[3].strip()

        # Self-service only
        if is_self != "1":
            continue

        mapped_fuel = FUEL_TYPE_MAP["IT"].get(fuel_raw)
        if mapped_fuel is None:
            continue

        station = stations.get(id_impianto)
        if station is None:
            continue

        try:
            price = float(parts[2].strip())
        except ValueError:
            continue

        rows.append({
            **station,
            "fuel_type": mapped_fuel,
            "price_eur": price,
            "recorded_at": recorded_at,
        })

    return rows


async def fetch_and_parse_italy() -> list[dict]:
    prices_bytes, stations_bytes = await fetch_italy_raw()
    return parse_italy_csv(prices_bytes, stations_bytes)
