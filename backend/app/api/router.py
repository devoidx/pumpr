from fastapi import APIRouter

from app.api.endpoints import ev, prices, stations, stats

api_router = APIRouter()
api_router.include_router(stations.router)
api_router.include_router(prices.router)
api_router.include_router(ev.router)
api_router.include_router(stats.router)
