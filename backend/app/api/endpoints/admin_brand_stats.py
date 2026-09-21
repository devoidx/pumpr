import logging

from fastapi import APIRouter, Depends

from app.auth.dependencies import require_admin
from app.models.user import User
from app.services.market_intelligence import compute_market_intelligence

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/admin/brand-stats", tags=["admin"])


@router.get("")
async def get_brand_stats(
    admin: User = Depends(require_admin),
) -> dict:
    """Brand league table with staleness metrics (admin only).

    Reuses compute_market_intelligence()'s brand computation rather than a
    parallel query — same canonicalized brand grouping, same
    source_updated_at-based freshness/staleness figures.
    """
    data = await compute_market_intelligence()
    brands = sorted(
        data["brands"],
        key=lambda b: b.get("stale_rate_21d", 0),
        reverse=True,
    )
    return {"brands": brands}
