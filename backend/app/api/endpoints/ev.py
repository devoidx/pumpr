from fastapi import APIRouter, HTTPException, Query

from app.services.ocm_client import get_chargers_near, parse_charger

router = APIRouter(prefix="/ev", tags=["ev"])


@router.get("/chargers")
async def list_chargers(
    lat: float = Query(...),
    lng: float = Query(...),
    radius_km: float = Query(10.0),
    limit: int = Query(50, le=100),
    min_power_kw: float | None = Query(None),
    connector_type: str | None = Query(None),
) -> list[dict]:
    """Return EV chargers near a location from Open Charge Map."""
    raw = await get_chargers_near(lat, lng, radius_km, limit)
    chargers = [parse_charger(r) for r in raw]

    if min_power_kw:
        chargers = [c for c in chargers if c["max_power_kw"] and c["max_power_kw"] >= min_power_kw]

    if connector_type:
        chargers = [c for c in chargers if any(connector_type.lower() in t.lower() for t in c["connector_types"])]

    chargers.sort(key=lambda c: c["distance_km"])
    return chargers[:limit]


@router.get("/chargers/{charger_id}")
async def get_charger(charger_id: int) -> dict:
    """Get a specific charger by OCM ID."""
    import httpx

    from app.core.config import settings
    async with httpx.AsyncClient(timeout=15.0) as client:
        r = await client.get(
            "https://api.openchargemap.io/v3/poi/",
            params={"output": "json", "chargepointid": charger_id, "key": settings.ocm_api_key}
        )
        r.raise_for_status()
        data = r.json()
    if not data:
        raise HTTPException(status_code=404, detail="Charger not found")
    return parse_charger(data[0])
