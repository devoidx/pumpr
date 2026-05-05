import logging
from datetime import datetime, timedelta

import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)


class FuelFinderClient:
    def __init__(self) -> None:
        self._token: str | None = None
        self._refresh_token: str | None = None
        self._token_expires_at: datetime | None = None
        self._client = httpx.AsyncClient(timeout=60.0, transport=httpx.AsyncHTTPTransport(local_address="0.0.0.0"))

    async def _get_token(self) -> str:
        if self._token and self._token_expires_at and datetime.utcnow() < self._token_expires_at:
            return self._token

        if self._refresh_token:
            try:
                return await self._refresh_access_token()
            except Exception:
                logger.warning("Refresh token failed, falling back to client credentials")

        return await self._fetch_new_token()

    async def _fetch_new_token(self) -> str:
        logger.info("Fetching new Fuel Finder OAuth token")
        response = await self._client.post(
            settings.fuel_finder_token_url,
            json={
                "client_id": settings.fuel_finder_client_id,
                "client_secret": settings.fuel_finder_client_secret,
            },
        )
        response.raise_for_status()
        data = response.json()
        token_data = data.get("data", data)
        self._token = token_data["access_token"]
        self._refresh_token = token_data.get("refresh_token")
        expires_in = token_data.get("expires_in", 3600)
        self._token_expires_at = datetime.utcnow() + timedelta(seconds=expires_in - 60)
        logger.info("OAuth token acquired successfully")
        return self._token  # type: ignore[return-value]

    async def _refresh_access_token(self) -> str:
        logger.info("Refreshing Fuel Finder OAuth token")
        refresh_url = settings.fuel_finder_token_url.replace(
            "generate_access_token", "regenerate_access_token"
        )
        response = await self._client.post(
            refresh_url,
            json={
                "client_id": settings.fuel_finder_client_id,
                "refresh_token": self._refresh_token,
            },
        )
        response.raise_for_status()
        data = response.json()
        self._token = data["access_token"]
        expires_in = data.get("expires_in", 3600)
        self._token_expires_at = datetime.utcnow() + timedelta(seconds=expires_in - 60)
        return self._token  # type: ignore[return-value]

    async def _get_paginated(self, path: str) -> list[dict]:
        """Fetch all batches from a paginated endpoint with retry logic."""
        import asyncio
        token = await self._get_token()
        all_records: list[dict] = []
        batch = 1
        max_retries = 3

        while True:
            for attempt in range(max_retries):
                try:
                    response = await self._client.get(
                        f"{settings.fuel_finder_api_url}{path}",
                        headers={"Authorization": f"Bearer {token}"},
                        params={"batch-number": batch},
                    )
                    break
                except Exception as e:
                    if attempt < max_retries - 1:
                        wait = 5 * (2 ** attempt)  # exponential backoff: 5s, 10s, 20s
                        logger.warning(f"Batch {batch} attempt {attempt + 1} failed: {type(e).__name__}: {e} — retrying in {wait}s")
                        await asyncio.sleep(wait)
                    else:
                        raise
            if response.status_code == 404:
                logger.info(f"Pagination complete at batch {batch - 1} ({len(all_records)} records)")
                break
            response.raise_for_status()
            data = response.json()
            records = data if isinstance(data, list) else data.get("data", [])
            if not records:
                break
            all_records.extend(records)
            logger.info(f"Fetched batch {batch} from {path} ({len(records)} records)")
            batch += 1

        return all_records

    async def get_stations(self) -> list[dict]:
        """Fetch all station metadata across all batches."""
        return await self._get_paginated("/api/v1/pfs")

    async def get_prices(self) -> list[dict]:
        """Fetch all fuel prices across all batches."""
        return await self._get_paginated("/api/v1/pfs/fuel-prices")

    async def close(self) -> None:
        await self._client.aclose()


fuel_finder_client = FuelFinderClient()
