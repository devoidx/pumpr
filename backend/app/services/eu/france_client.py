"""
Client for France's official open fuel price feed (data.gouv.fr / roulez-eco.fr).
Source: https://donnees.roulez-eco.fr/opendata/instantane
Returns a ZIP archive containing ISO-8859-1 XML. ~10k stations.
Each <prix> has its own per-fuel `maj` (last-updated) timestamp.
"""
import io
import logging
import zipfile
from datetime import datetime, timezone
from xml.etree import ElementTree as ET

import httpx

from app.services.eu.fuel_type_map import FUEL_TYPE_MAP

logger = logging.getLogger(__name__)

FRANCE_FEED_URL = "https://donnees.roulez-eco.fr/opendata/instantane"
COORD_SCALE = 100_000  # lat/lon are *1e5 integers in the feed — confirmed via live sample

LAT_MIN, LAT_MAX = 41.0, 51.5
LON_MIN, LON_MAX = -6.0, 10.0


async def fetch_france_raw() -> bytes:
    async with httpx.AsyncClient(timeout=60) as client:
        resp = await client.get(FRANCE_FEED_URL)
        resp.raise_for_status()
        return resp.content


def parse_france_xml(raw_zip_bytes: bytes) -> list[dict]:
    """
    Unpacks the ZIP and parses the XML into normalized station+price rows.
    One dict per (station, fuel_type) — matches the eu_latest_prices upsert shape.
    """
    with zipfile.ZipFile(io.BytesIO(raw_zip_bytes)) as zf:
        xml_filename = zf.namelist()[0]
        xml_bytes = zf.read(xml_filename)

    root = ET.fromstring(xml_bytes)

    rows = []
    skipped_coords = 0

    for pdv in root.findall("pdv"):
        external_id = pdv.get("id")
        lat_raw = pdv.get("latitude")
        lon_raw = pdv.get("longitude")

        if lat_raw is None or lon_raw is None:
            skipped_coords += 1
            continue

        try:
            lat = float(lat_raw) / COORD_SCALE
            lon = float(lon_raw) / COORD_SCALE
        except ValueError:
            skipped_coords += 1
            continue

        if not (LAT_MIN <= lat <= LAT_MAX and LON_MIN <= lon <= LON_MAX):
            skipped_coords += 1
            continue

        adresse = pdv.findtext("adresse", default="")
        ville = pdv.findtext("ville", default="")
        cp = pdv.get("cp", "")

        for prix in pdv.findall("prix"):
            fuel_raw = prix.get("nom")
            if fuel_raw is None:
                continue
            mapped_fuel = FUEL_TYPE_MAP["FR"].get(fuel_raw)
            if mapped_fuel is None:
                continue

            valeur = prix.get("valeur")
            if valeur is None:
                continue
            try:
                price = float(valeur)
            except ValueError:
                continue

            maj_raw = prix.get("maj")
            if maj_raw is not None:
                try:
                    recorded_at = datetime.strptime(maj_raw, "%Y-%m-%d %H:%M:%S").replace(
                        tzinfo=timezone.utc
                    )
                except ValueError:
                    recorded_at = datetime.now(timezone.utc)
            else:
                recorded_at = datetime.now(timezone.utc)

            rows.append({
                "external_id": external_id,
                "country": "FR",
                "name": adresse or ville,
                "address": adresse,
                "postcode": cp,
                "city": ville,
                "latitude": lat,
                "longitude": lon,
                "fuel_type": mapped_fuel,
                "price_eur": price,
                "recorded_at": recorded_at,
            })

    if skipped_coords:
        logger.warning(
            "france_client: skipped %d stations with invalid/out-of-bounds coordinates",
            skipped_coords,
        )

    return rows


async def fetch_and_parse_france() -> list[dict]:
    raw = await fetch_france_raw()
    return parse_france_xml(raw)
