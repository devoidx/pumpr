from fastapi import APIRouter

from app.api.endpoints import (
    alerts,
    auth,
    blog,
    eu_locations,
    ev,
    feedback,
    fillups,
    intelligence,
    locations,
    locations_seo,
    prices,
    sitemap,
    stations,
    stats,
    stripe_routes,
    vehicles,
)

api_router = APIRouter()
api_router.include_router(eu_locations.router)
api_router.include_router(auth.router)
api_router.include_router(stripe_routes.router)
api_router.include_router(locations.router)
api_router.include_router(locations_seo.router)
api_router.include_router(stations.router)
api_router.include_router(prices.router)
api_router.include_router(ev.router)
api_router.include_router(vehicles.router)
api_router.include_router(fillups.router)
api_router.include_router(stats.router)
api_router.include_router(alerts.router)
api_router.include_router(intelligence.router)
api_router.include_router(sitemap.router)
api_router.include_router(blog.router)
api_router.include_router(feedback.router)
