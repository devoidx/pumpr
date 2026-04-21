from collections import defaultdict

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.limiter import limiter
from app.db.session import get_db

router = APIRouter(prefix="/stats", tags=["stats"])


async def _get_regional_prices(db: AsyncSession, group_field: str, filter_sql: str = "", params: dict = {}) -> list[dict]:
    sql = text(f"""
        WITH latest AS (
            SELECT DISTINCT ON (station_id, fuel_type)
                station_id, fuel_type, price_pence
            FROM price_history
            ORDER BY station_id, fuel_type, recorded_at DESC
        )
        SELECT
            s.{group_field} as region,
            l.fuel_type,
            ROUND(AVG(l.price_pence)::numeric, 1) as avg_price,
            MIN(l.price_pence) as min_price,
            MAX(l.price_pence) as max_price,
            COUNT(DISTINCT l.station_id) as station_count
        FROM latest l
        JOIN stations s ON l.station_id = s.id
        WHERE s.permanent_closure = FALSE
          AND s.{group_field} IS NOT NULL
          AND s.{group_field} != ''
          {filter_sql}
        GROUP BY s.{group_field}, l.fuel_type
        ORDER BY s.{group_field}, l.fuel_type
    """)
    result = await db.execute(sql, params)
    rows = result.fetchall()

    by_region: dict = defaultdict(dict)
    for row in rows:
        if not row.region:
            continue
        by_region[row.region][row.fuel_type] = {
            "avg": float(row.avg_price),
            "min": row.min_price,
            "max": row.max_price,
            "stations": row.station_count,
        }

    return [{"region": region, "fuels": fuels} for region, fuels in sorted(by_region.items())]


async def _get_cheapest_per_region(db: AsyncSession, group_field: str, fuel: str, filter_sql: str = "", params: dict = {}) -> list[dict]:
    sql = text(f"""
        WITH latest AS (
            SELECT DISTINCT ON (station_id, fuel_type)
                station_id, fuel_type, price_pence
            FROM price_history
            WHERE fuel_type = :fuel
            ORDER BY station_id, fuel_type, recorded_at DESC
        ),
        regional_min AS (
            SELECT s.{group_field} as region, MIN(l.price_pence) as min_price
            FROM latest l
            JOIN stations s ON l.station_id = s.id
            WHERE s.permanent_closure = FALSE
              AND s.{group_field} IS NOT NULL
              AND s.{group_field} != ''
              {filter_sql}
            GROUP BY s.{group_field}
        ),
        cheapest AS (
            SELECT
                s.{group_field} as region,
                s.name as station_name,
                s.postcode,
                s.brand,
                l.price_pence,
                COUNT(*) OVER (PARTITION BY s.{group_field}) as ties
            FROM latest l
            JOIN stations s ON l.station_id = s.id
            JOIN regional_min rm ON s.{group_field} = rm.region AND l.price_pence = rm.min_price
            WHERE s.permanent_closure = FALSE
              AND s.{group_field} IS NOT NULL
              AND s.{group_field} != ''
              {filter_sql}
        )
        SELECT DISTINCT ON (region) region, station_name, postcode, brand, price_pence, ties
        FROM cheapest
        ORDER BY region, price_pence
    """)
    result = await db.execute(sql, {"fuel": fuel, **params})
    rows = result.fetchall()

    return sorted([
        {
            "region": row.region,
            "price_pence": row.price_pence,
            "station_name": row.station_name if row.ties == 1 else None,
            "postcode": row.postcode if row.ties == 1 else None,
            "brand": row.brand if row.ties == 1 else None,
            "tied_stations": row.ties,
        }
        for row in rows
    ], key=lambda x: x["price_pence"])


@router.get("/countries")
@limiter.limit("30/minute")
async def get_country_stats(
    request: Request,
    fuel: str = Query("E10"),
    db: AsyncSession = Depends(get_db)
) -> list[dict]:
    return await _get_regional_prices(
        db, "country",
        "AND s.country IN ('England', 'Scotland', 'Wales', 'Northern Ireland')"
    )


@router.get("/countries/cheapest")
@limiter.limit("30/minute")
async def get_cheapest_by_country(
    request: Request,
    fuel: str = Query("E10"),
    db: AsyncSession = Depends(get_db)
) -> list[dict]:
    return await _get_cheapest_per_region(
        db, "country", fuel,
        "AND s.country IN ('England', 'Scotland', 'Wales', 'Northern Ireland')"
    )


@router.get("/counties")
@limiter.limit("30/minute")
async def get_county_stats(
    request: Request,
    fuel: str = Query("E10"),
    country: str | None = Query(None),
    db: AsyncSession = Depends(get_db)
) -> list[dict]:
    filter_sql = "AND s.country = :country" if country else ""
    params = {"country": country} if country else {}
    return await _get_regional_prices(db, "county", filter_sql, params)


@router.get("/counties/cheapest")
@limiter.limit("30/minute")
async def get_cheapest_by_county(
    request: Request,
    fuel: str = Query("E10"),
    country: str | None = Query(None),
    db: AsyncSession = Depends(get_db)
) -> list[dict]:
    filter_sql = "AND s.country = :country" if country else ""
    params = {"country": country} if country else {}
    return await _get_cheapest_per_region(db, "county", fuel, filter_sql, params)
