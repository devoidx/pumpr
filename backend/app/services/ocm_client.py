import logging

import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)

OCM_BASE = "https://api.openchargemap.io/v3"


async def get_chargers_near(lat: float, lng: float, radius_km: float = 10.0, max_results: int = 50) -> list[dict]:
    """Fetch EV chargers near a location from Open Charge Map."""
    params = {
        "output": "json",
        "countrycode": "GB",
        "latitude": lat,
        "longitude": lng,
        "distance": radius_km,
        "maxresults": max_results,
        "compact": "false",
        "verbose": "false",
        "key": settings.ocm_api_key,
    }
    async with httpx.AsyncClient(timeout=15.0) as client:
        response = await client.get(f"{OCM_BASE}/poi/", params=params)  # type: ignore[arg-type]
        response.raise_for_status()
        return response.json()


def parse_charger(raw: dict) -> dict:
    """Normalise OCM response into our format."""
    addr = raw.get("AddressInfo", {})
    operator = raw.get("OperatorInfo") or {}
    status = raw.get("StatusType") or {}
    usage = raw.get("UsageType") or {}

    connections = []
    for c in raw.get("Connections", []):
        conn_type = c.get("ConnectionType") or {}
        level = c.get("Level") or {}
        conn_status = c.get("StatusType") or {}
        connections.append({
            "id": c.get("ID"),
            "type": conn_type.get("Title", "Unknown"),
            "power_kw": c.get("PowerKW"),
            "amps": c.get("Amps"),
            "voltage": c.get("Voltage"),
            "is_fast_charge": level.get("IsFastChargeCapable", False),
            "level": level.get("Title", ""),
            "is_operational": conn_status.get("IsOperational", True),
        })

    return {
        "id": raw.get("ID"),
        "uuid": raw.get("UUID"),
        "name": addr.get("Title", ""),
        "address": ", ".join(filter(None, [
            addr.get("AddressLine1"),
            addr.get("Town"),
        ])),
        "postcode": addr.get("Postcode"),
        "latitude": addr.get("Latitude"),
        "longitude": addr.get("Longitude"),
        "distance_km": round(addr.get("Distance") or 0, 2),
        "network": operator.get("Title", "Unknown"),
        "operator_id": raw.get("OperatorID"),
        "is_operational": status.get("IsOperational", True),
        "status": status.get("Title", "Unknown"),
        "usage_cost": raw.get("UsageCost"),
        "is_pay_at_location": usage.get("IsPayAtLocation", False),
        "is_membership_required": usage.get("IsMembershipRequired", False),
        "usage_type_id": usage.get("ID", 0),
        "usage_type": usage.get("Title", "Unknown"),
        "connections": connections,
        "total_points": len(connections),
        "max_power_kw": max((c.get("power_kw") or 0 for c in connections), default=None),
        "connector_types": list({c["type"] for c in connections}),
        "date_last_verified": raw.get("DateLastVerified"),
    }
