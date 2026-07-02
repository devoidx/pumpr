"""
Client for Spain's official fuel price feed (Geoportal Gasolineras).
Source: https://sedeaplicaciones.minetur.gob.es/ServiciosRESTCarburantes/PreciosCarburantes/EstacionesTerrestres/
Returns JSON with all stations and current prices in a single call.
Coordinates use comma as decimal separator. No separate station/price files — everything in one response.
"""
import logging
from datetime import datetime, timezone

import httpx

from app.services.eu.fuel_type_map import FUEL_TYPE_MAP

logger = logging.getLogger(__name__)

SPAIN_URL = "https://sedeaplicaciones.minetur.gob.es/ServiciosRESTCarburantes/PreciosCarburantes/EstacionesTerrestres/"

# Spain bounding box — mainland + Balearics + Canaries
LAT_MIN, LAT_MAX = 27.5, 43.8
LON_MIN, LON_MAX = -18.2, 4.4


async def fetch_spain_raw() -> dict:
    async with httpx.AsyncClient(timeout=60) as client:
        resp = await client.get(SPAIN_URL)
        resp.raise_for_status()
        return resp.json()


def parse_spain_json(data: dict) -> list[dict]:
    """
    Parses the Geoportal JSON into normalized station+price rows.
    One dict per (station, fuel_type) — matches the eu_latest_prices upsert shape.
    """
    stations_raw = data.get("ListaEESSPrecio", [])

    # Feed-level timestamp — same for all stations
    fecha_str = data.get("Fecha", "")
    try:
        recorded_at = datetime.strptime(fecha_str, "%d/%m/%Y %H:%M:%S").replace(
            tzinfo=timezone.utc
        )
    except ValueError:
        recorded_at = datetime.now(timezone.utc)

    rows = []
    skipped_coords = 0

    for s in stations_raw:
        external_id = s.get("IDEESS", "")

        lat_str = s.get("Latitud", "").replace(",", ".")
        lon_str = s.get("Longitud (WGS84)", "").replace(",", ".")

        try:
            lat = float(lat_str)
            lon = float(lon_str)
        except ValueError:
            skipped_coords += 1
            continue

        if not (LAT_MIN <= lat <= LAT_MAX and LON_MIN <= lon <= LON_MAX):
            skipped_coords += 1
            continue

        name = s.get("Rótulo", "").strip() or s.get("Dirección", "").strip()
        address = s.get("Dirección", "").strip()
        city = s.get("Localidad", "").strip()
        postcode = s.get("C.P.", "").strip()

        for fuel_raw, mapped_fuel in FUEL_TYPE_MAP["ES"].items():
            if mapped_fuel is None:
                continue
            price_str = s.get(fuel_raw, "").replace(",", ".")
            if not price_str:
                continue
            try:
                price = float(price_str)
            except ValueError:
                continue
            if price <= 0:
                continue

            rotulo = s.get("Rótulo", "").strip()
            # Only use Rótulo as brand if it looks like a real brand name
            # (not a registration number like "Nº 10.935")
            brand = rotulo if rotulo and not rotulo.startswith("Nº") else None
            rows.append({
                "external_id": external_id,
                "country": "ES",
                "name": name,
                "brand": brand,
                "address": address,
                "postcode": postcode,
                "city": city,
                "latitude": lat,
                "longitude": lon,
                "is_motorway": False,  # Spain feed doesn't distinguish
                "fuel_type": mapped_fuel,
                "price_eur": price,
                "recorded_at": recorded_at,
            })

    if skipped_coords:
        logger.warning(
            "spain_client: skipped %d stations with invalid/out-of-bounds coordinates",
            skipped_coords,
        )

    return rows


async def fetch_and_parse_spain() -> list[dict]:
    data = await fetch_spain_raw()
    return parse_spain_json(data)
