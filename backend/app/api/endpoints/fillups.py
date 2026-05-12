from __future__ import annotations

import uuid
from datetime import date, datetime

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user
from app.db.session import get_db
from app.models.user import User

router = APIRouter(prefix="/fillups", tags=["fillups"])


def _require_pro(user: User) -> None:
    if user.role not in ("pro", "admin"):
        raise HTTPException(status_code=403, detail="Pro subscription required")


class FillupCreate(BaseModel):
    vehicle_id: uuid.UUID
    filled_at: date
    station_id: str | None = None
    station_name: str | None = None
    fuel_type: str
    litres: float
    price_pence_per_litre: float
    odometer_miles: float | None = None
    notes: str | None = None


class FillupOut(BaseModel):
    id: uuid.UUID
    vehicle_id: uuid.UUID
    vehicle_name: str | None
    filled_at: date
    station_id: str | None
    station_name: str | None
    fuel_type: str
    litres: float
    price_pence_per_litre: float
    total_cost_pence: float
    odometer_miles: float | None
    notes: str | None
    created_at: datetime


@router.get("/", response_model=list[FillupOut])
async def list_fillups(
    vehicle_id: uuid.UUID | None = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[FillupOut]:
    _require_pro(current_user)
    query = """
        SELECT f.*, v.nickname, v.make, v.model
        FROM fuel_fillups f
        JOIN user_vehicles v ON f.vehicle_id = v.id
        WHERE f.user_id = :user_id
    """
    params: dict = {"user_id": current_user.id}
    if vehicle_id:
        query += " AND f.vehicle_id = :vehicle_id"
        params["vehicle_id"] = vehicle_id
    query += " ORDER BY f.filled_at DESC, f.created_at DESC"
    result = await db.execute(text(query), params)
    rows = result.fetchall()
    return [FillupOut(
        id=r.id,
        vehicle_id=r.vehicle_id,
        vehicle_name=r.nickname or f"{r.make or ''} {r.model or ''}".strip() or None,
        filled_at=r.filled_at,
        station_id=r.station_id,
        station_name=r.station_name,
        fuel_type=r.fuel_type,
        litres=r.litres,
        price_pence_per_litre=r.price_pence_per_litre,
        total_cost_pence=r.total_cost_pence,
        odometer_miles=r.odometer_miles,
        notes=r.notes,
        created_at=r.created_at,
    ) for r in rows]


@router.post("/", response_model=FillupOut, status_code=status.HTTP_201_CREATED)
async def create_fillup(
    body: FillupCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> FillupOut:
    _require_pro(current_user)
    if body.litres <= 0:
        raise HTTPException(status_code=400, detail="Litres must be positive")
    if body.price_pence_per_litre <= 0:
        raise HTTPException(status_code=400, detail="Price must be positive")

    # Verify vehicle belongs to user
    veh = await db.execute(
        text("SELECT id, nickname, make, model FROM user_vehicles WHERE id = :id AND user_id = :uid"),
        {"id": body.vehicle_id, "uid": current_user.id}
    )
    v = veh.fetchone()
    if not v:
        raise HTTPException(status_code=404, detail="Vehicle not found")

    total_cost = body.litres * body.price_pence_per_litre

    result = await db.execute(text("""
        INSERT INTO fuel_fillups
            (user_id, vehicle_id, filled_at, station_id, station_name,
             fuel_type, litres, price_pence_per_litre, total_cost_pence,
             odometer_miles, notes)
        VALUES
            (:user_id, :vehicle_id, :filled_at, :station_id, :station_name,
             :fuel_type, :litres, :ppl, :total, :odo, :notes)
        RETURNING id, created_at
    """), {
        "user_id": current_user.id,
        "vehicle_id": body.vehicle_id,
        "filled_at": body.filled_at,
        "station_id": body.station_id,
        "station_name": body.station_name,
        "fuel_type": body.fuel_type,
        "litres": body.litres,
        "ppl": body.price_pence_per_litre,
        "total": total_cost,
        "odo": body.odometer_miles,
        "notes": body.notes,
    })
    row = result.fetchone()
    if not row:
        raise HTTPException(status_code=500, detail="Insert failed")
    await db.commit()

    return FillupOut(
        id=row.id,
        vehicle_id=body.vehicle_id,
        vehicle_name=v.nickname or f"{v.make or ''} {v.model or ''}".strip() or None,
        filled_at=body.filled_at,
        station_id=body.station_id,
        station_name=body.station_name,
        fuel_type=body.fuel_type,
        litres=body.litres,
        price_pence_per_litre=body.price_pence_per_litre,
        total_cost_pence=total_cost,
        odometer_miles=body.odometer_miles,
        notes=body.notes,
        created_at=row.created_at,
    )


@router.delete("/{fillup_id}", status_code=status.HTTP_204_NO_CONTENT, response_model=None)
async def delete_fillup(
    fillup_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    _require_pro(current_user)
    result = await db.execute(
        text("DELETE FROM fuel_fillups WHERE id = :id AND user_id = :uid RETURNING id"),
        {"id": fillup_id, "uid": current_user.id}
    )
    if not result.fetchone():
        raise HTTPException(status_code=404, detail="Fill-up not found")
    await db.commit()


@router.get("/stats")
async def get_fillup_stats(
    vehicle_id: uuid.UUID | None = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    _require_pro(current_user)

    params: dict = {"user_id": current_user.id}
    vehicle_filter = ""
    if vehicle_id:
        vehicle_filter = "AND f.vehicle_id = :vehicle_id"
        params["vehicle_id"] = vehicle_id

    # Overall stats
    overall = await db.execute(text(f"""
        SELECT
            COUNT(*) as fillup_count,
            ROUND(SUM(litres)::numeric, 2) as total_litres,
            ROUND(SUM(total_cost_pence)::numeric / 100, 2) as total_spend_gbp,
            ROUND(AVG(price_pence_per_litre)::numeric, 2) as avg_ppl,
            MIN(filled_at) as first_fillup,
            MAX(filled_at) as last_fillup
        FROM fuel_fillups f
        WHERE f.user_id = :user_id {vehicle_filter}
    """), params)
    o = overall.fetchone()
    if not o:
        raise HTTPException(status_code=500, detail="Stats query failed")

    # Monthly breakdown (last 12 months)
    monthly = await db.execute(text(f"""
        SELECT
            TO_CHAR(filled_at, 'YYYY-MM') as month,
            ROUND(SUM(total_cost_pence)::numeric / 100, 2) as spend_gbp,
            ROUND(SUM(litres)::numeric, 2) as litres,
            COUNT(*) as fillups
        FROM fuel_fillups f
        WHERE f.user_id = :user_id {vehicle_filter}
          AND filled_at >= NOW() - INTERVAL '12 months'
        GROUP BY month
        ORDER BY month ASC
    """), params)
    monthly_data = [{"month": r.month, "spend_gbp": float(r.spend_gbp), "litres": float(r.litres), "fillups": int(r.fillups)} for r in monthly.fetchall()]

    # MPG calculations (only where odometer provided)
    mpg_result = await db.execute(text(f"""
        SELECT
            filled_at,
            litres,
            odometer_miles,
            LAG(odometer_miles) OVER (PARTITION BY vehicle_id ORDER BY filled_at, created_at) as prev_odo
        FROM fuel_fillups f
        WHERE f.user_id = :user_id {vehicle_filter}
          AND odometer_miles IS NOT NULL
        ORDER BY vehicle_id, filled_at, created_at
    """), params)
    mpg_rows = mpg_result.fetchall()
    mpg_data = []
    for r in mpg_rows:
        if r.prev_odo and r.odometer_miles > r.prev_odo and r.litres > 0:
            miles = r.odometer_miles - r.prev_odo
            litres_used = r.litres
            actual_mpg = round((miles / litres_used) * 4.54609, 1)
            if 10 < actual_mpg < 200:  # sanity check
                mpg_data.append({"date": r.filled_at.isoformat(), "mpg": actual_mpg})

    # Predicted monthly spend based on last 3 months average
    predicted_monthly = None
    if monthly_data and len(monthly_data) >= 1:
        recent = monthly_data[-3:]
        predicted_monthly = round(sum(m["spend_gbp"] for m in recent) / len(recent), 2)

    # Vehicle spec MPG for comparison
    spec_mpg = None
    if vehicle_id:
        veh = await db.execute(
            text("SELECT mpg FROM user_vehicles WHERE id = :id AND user_id = :uid"),
            {"id": vehicle_id, "uid": current_user.id}
        )
        v = veh.fetchone()
        if v and v.mpg:
            spec_mpg = v.mpg

    return {
        "fillup_count": int(o.fillup_count) if o.fillup_count else 0,
        "total_litres": float(o.total_litres) if o.total_litres else 0,
        "total_spend_gbp": float(o.total_spend_gbp) if o.total_spend_gbp else 0,
        "avg_ppl": float(o.avg_ppl) if o.avg_ppl else 0,
        "first_fillup": o.first_fillup.isoformat() if o.first_fillup else None,
        "last_fillup": o.last_fillup.isoformat() if o.last_fillup else None,
        "monthly": monthly_data,
        "mpg_history": mpg_data,
        "predicted_monthly_spend": predicted_monthly,
        "predicted_annual_spend": round(predicted_monthly * 12, 2) if predicted_monthly else None,
        "spec_mpg": spec_mpg,
        "avg_actual_mpg": round(sum(m["mpg"] for m in mpg_data) / len(mpg_data), 1) if mpg_data else None,
    }


class FillupUpdate(BaseModel):
    vehicle_id: uuid.UUID | None = None
    filled_at: date | None = None
    station_id: str | None = None
    station_name: str | None = None
    fuel_type: str | None = None
    litres: float | None = None
    price_pence_per_litre: float | None = None
    odometer_miles: float | None = None
    notes: str | None = None


@router.patch("/{fillup_id}", response_model=FillupOut)
async def update_fillup(
    fillup_id: uuid.UUID,
    body: FillupUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> FillupOut:
    _require_pro(current_user)

    # Fetch existing
    result = await db.execute(
        text("SELECT * FROM fuel_fillups WHERE id = :id AND user_id = :uid"),
        {"id": fillup_id, "uid": current_user.id}
    )
    row = result.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Fill-up not found")

    # If changing vehicle, verify it belongs to user
    vehicle_id = body.vehicle_id or row.vehicle_id
    veh = await db.execute(
        text("SELECT id, nickname, make, model FROM user_vehicles WHERE id = :id AND user_id = :uid"),
        {"id": vehicle_id, "uid": current_user.id}
    )
    v = veh.fetchone()
    if not v:
        raise HTTPException(status_code=404, detail="Vehicle not found")

    litres = body.litres if body.litres is not None else row.litres
    ppl = body.price_pence_per_litre if body.price_pence_per_litre is not None else row.price_pence_per_litre
    total_cost = litres * ppl

    await db.execute(text("""
        UPDATE fuel_fillups SET
            vehicle_id = :vehicle_id,
            filled_at = :filled_at,
            station_id = :station_id,
            station_name = :station_name,
            fuel_type = :fuel_type,
            litres = :litres,
            price_pence_per_litre = :ppl,
            total_cost_pence = :total,
            odometer_miles = :odo,
            notes = :notes
        WHERE id = :id AND user_id = :uid
    """), {
        "id": fillup_id,
        "uid": current_user.id,
        "vehicle_id": vehicle_id,
        "filled_at": body.filled_at or row.filled_at,
        "station_id": body.station_id if body.station_id is not None else row.station_id,
        "station_name": body.station_name if body.station_name is not None else row.station_name,
        "fuel_type": body.fuel_type or row.fuel_type,
        "litres": litres,
        "ppl": ppl,
        "total": total_cost,
        "odo": body.odometer_miles if body.odometer_miles is not None else row.odometer_miles,
        "notes": body.notes if body.notes is not None else row.notes,
    })
    await db.commit()

    return FillupOut(
        id=fillup_id,
        vehicle_id=vehicle_id,
        vehicle_name=v.nickname or f"{v.make or ''} {v.model or ''}".strip() or None,
        filled_at=body.filled_at or row.filled_at,
        station_id=body.station_id if body.station_id is not None else row.station_id,
        station_name=body.station_name if body.station_name is not None else row.station_name,
        fuel_type=body.fuel_type or row.fuel_type,
        litres=litres,
        price_pence_per_litre=ppl,
        total_cost_pence=total_cost,
        odometer_miles=body.odometer_miles if body.odometer_miles is not None else row.odometer_miles,
        notes=body.notes if body.notes is not None else row.notes,
        created_at=row.created_at,
    )
