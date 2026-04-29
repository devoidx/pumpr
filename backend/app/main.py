import asyncio
import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from app.api.router import api_router
from app.core.limiter import limiter
from app.db.session import Base, engine
from app.services.fuel_finder_client import fuel_finder_client
from app.services.ingestion import ingest_prices, sync_stations
from app.services.scheduler import start_scheduler, stop_scheduler

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s", datefmt="%Y-%m-%d %H:%M:%S")
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Pumpr API",
    description="UK fuel price tracker using GOV.UK Fuel Finder data",
    version="0.1.0",
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)  # type: ignore[arg-type]
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="/api/v1")


async def _background_sync() -> None:
    """Run initial sync in background so app starts immediately."""
    import os
    if os.getenv("ENABLE_PRICE_POLLING", "true").lower() != "true":
        logger.info("Background sync skipped — ENABLE_PRICE_POLLING=false")
        return
    await asyncio.sleep(2)  # let the app finish starting
    try:
        logger.info("Background sync: starting station sync...")
        try:
            await sync_stations()
        except Exception as e:
            logger.warning(f"Background sync: station sync failed (will retry later): {e}")
        logger.info("Background sync: starting price ingest...")
        await ingest_prices()
        logger.info("Background sync: complete")
    except Exception as e:
        logger.exception(f"Background sync failed: {e}")


@app.on_event("startup")
async def startup() -> None:
    logger.info("Creating database tables...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Start scheduler immediately
    start_scheduler()

    # Run initial sync in background — app is available straight away
    asyncio.create_task(_background_sync())

    logger.info("App ready — background sync running")


@app.on_event("shutdown")
async def shutdown() -> None:
    stop_scheduler()
    await fuel_finder_client.close()


@app.get("/health")
async def health() -> dict:
    return {"status": "ok"}
