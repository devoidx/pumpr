import logging
from datetime import datetime, timedelta

import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)


class FuelFinderClient:
    def __init__(self) -> None:
        self._token: str | None = None
        self._token_expires_at: datetime | None = None
        self._client = httpx.AsyncClient(timeout=30.0)

    async def _get_token(self) -> str:
        if self._token and self._token_expires_at and datetime.utcnow() < self._token_expires_at:
            return self._token

        logger.info("Fetching new Fuel Finder OAuth token")
        response = await self._client.post(
            settings.fuel_finder_token_url,
            data={
                "grant_type": "client_credentials",
                "client_id": settings.fuel_finder_client_id,
                "client_secret": settings.fuel_finder_client_secret,
            },
        )
        response.raise_for_status()
        data = response.json()
        self._token = data["access_token"]
        expires_in = data.get("expires_in", 3600)
        self._token_expires_at = datetime.utcnow() + timedelta(seconds=expires_in - 60)
        return self._token

    async def _get(self, path: str, params: dict | None = None) -> dict | list:
        token = await self._get_token()
        response = await self._client.get(
            f"{settings.fuel_finder_api_url}{path}",
            headers={"Authorization": f"Bearer {token}"},
            params=params,
        )
        response.raise_for_status()
        return response.json()

    async def get_stations(self) -> list[dict]:
        """Fetch all station metadata."""
        data = await self._get("/stations")
        return data if isinstance(data, list) else data.get("stations", [])

    async def get_prices(self) -> list[dict]:
        """Fetch current prices for all stations."""
        data = await self._get("/prices")
        return data if isinstance(data, list) else data.get("prices", [])

    async def close(self) -> None:
        await self._client.aclose()


fuel_finder_client = FuelFinderClient()
