from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db

router = APIRouter(prefix="/intelligence", tags=["intelligence"])

@router.get("/latest")
async def get_latest_intelligence(db: AsyncSession = Depends(get_db)) -> dict:
    result = await db.execute(
        text("""
        SELECT date, computed_at, national, regional, brands, postcode_sectors, narrative
        FROM market_intelligence
        ORDER BY date DESC
        LIMIT 1
    """)
    )
    row = result.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="No market intelligence data available yet")
    stats = await db.execute(text("SELECT MIN(date), COUNT(*) FROM market_intelligence"))
    stats_row = stats.fetchone()
    first_date = stats_row[0].isoformat() if stats_row and stats_row[0] else row.date.isoformat()
    day_count = stats_row[1] if stats_row and stats_row[1] else 1
    return {
        "date": row.date.isoformat(),
        "computed_at": row.computed_at.isoformat(),
        "national": row.national,
        "regional": row.regional,
        "brands": row.brands,
        "postcode_sectors": row.postcode_sectors,
        "narrative": row.narrative,
        "first_date": first_date,
        "day_count": day_count,
    }

@router.get("/trends")
async def get_intelligence_trends(db: AsyncSession = Depends(get_db)) -> dict:
    result = await db.execute(text("""
        SELECT
            date,
            (national->'E10'->>'avg')::float as e10_avg,
            (national->'E10'->>'supermarket_avg')::float as e10_supermarket_avg,
            (national->'E10'->>'motorway_avg')::float as e10_motorway_avg,
            (national->'B7'->>'avg')::float as b7_avg,
            (national->'B7'->>'supermarket_avg')::float as b7_supermarket_avg,
            (national->'B7'->>'motorway_avg')::float as b7_motorway_avg
        FROM market_intelligence
        ORDER BY date ASC
    """))
    rows = result.fetchall()
    if not rows:
        raise HTTPException(status_code=404, detail="No trend data available yet")
    return {
        "days": [
            {
                "date": r.date.isoformat(),
                "e10_avg": r.e10_avg,
                "e10_supermarket_avg": r.e10_supermarket_avg,
                "e10_motorway_avg": r.e10_motorway_avg,
                "b7_avg": r.b7_avg,
                "b7_supermarket_avg": r.b7_supermarket_avg,
                "b7_motorway_avg": r.b7_motorway_avg,
            }
            for r in rows
        ]
    }
