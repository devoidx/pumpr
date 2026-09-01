"""Membership-required brand matching (e.g. Costco).

stations.brand is free text with inconsistent suffixes (e.g.
"COSTCO WHOLESALE ABERDEEN"), so exact matching against brands.name
misses variants. We match by substring instead: a station is
membership-required if its brand text contains a brands.name value
flagged membership_required = TRUE.

To add another membership-required brand: flag it in the brands table.
    UPDATE brands SET membership_required = TRUE WHERE name = 'SOME BRAND';
No code changes needed — this module picks it up automatically.
"""
import time

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

_cache: list[str] | None = None
_cache_ts: float = 0.0
_CACHE_TTL = 300  # 5 min — membership flags change rarely, avoid a query per request


async def get_membership_required_names(db: AsyncSession) -> list[str]:
    """Canonical brand names (brands.name) currently flagged membership_required."""
    global _cache, _cache_ts
    if _cache is not None and time.time() - _cache_ts < _CACHE_TTL:
        return _cache
    result = await db.execute(
        text("SELECT name FROM brands WHERE membership_required = TRUE")
    )
    _cache = [r.name for r in result.fetchall()]
    _cache_ts = time.time()
    return _cache


def brand_requires_membership(station_brand: str | None, membership_names: list[str]) -> bool:
    """Substring match against station.brand, which may carry extra suffixes."""
    if not station_brand:
        return False
    upper = station_brand.upper()
    return any(name in upper for name in membership_names)
