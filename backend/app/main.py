import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.router import api_router
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

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="/api/v1")


@app.on_event("startup")
async def startup() -> None:
    logger.info("Creating database tables...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    logger.info("Running initial station sync...")
    try:
        await sync_stations()
        await ingest_prices()
    except Exception as e:
        logger.error(f"Initial sync failed (API credentials may not be set): {e}")

    start_scheduler()


@app.on_event("shutdown")
async def shutdown() -> None:
    stop_scheduler()
    await fuel_finder_client.close()


@app.get("/health")
async def health() -> dict:
    return {"status": "ok"}
