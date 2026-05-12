from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db

router = APIRouter(prefix="/intelligence", tags=["intelligence"])


@router.get("/latest")
async def get_latest_intelligence(db: AsyncSession = Depends(get_db)) -> dict:
    result = await db.execute(text("""
        SELECT date, computed_at, national, regional, brands, postcode_sectors, narrative
        FROM market_intelligence
        ORDER BY date DESC
        LIMIT 1
    """))
    row = result.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="No market intelligence data available yet")
    return {
        "date": row.date.isoformat(),
        "computed_at": row.computed_at.isoformat(),
        "national": row.national,
        "regional": row.regional,
        "brands": row.brands,
        "postcode_sectors": row.postcode_sectors,
        "narrative": row.narrative,
    }
