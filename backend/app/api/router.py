from fastapi import APIRouter

from app.api.endpoints import prices, stations

api_router = APIRouter()
api_router.include_router(stations.router)
api_router.include_router(prices.router)
