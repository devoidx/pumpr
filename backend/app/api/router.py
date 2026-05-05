from fastapi import APIRouter

from app.api.endpoints import (
    auth,
    blog,
    ev,
    locations,
    prices,
    stations,
    stats,
    stripe_routes,
    vehicles,
)

api_router = APIRouter()
api_router.include_router(auth.router)
api_router.include_router(stripe_routes.router)
api_router.include_router(locations.router)
api_router.include_router(stations.router)
api_router.include_router(prices.router)
api_router.include_router(ev.router)
api_router.include_router(vehicles.router)
api_router.include_router(stats.router)
api_router.include_router(blog.router)
