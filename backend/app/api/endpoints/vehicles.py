from __future__ import annotations

import logging
from uuid import UUID

import httpx
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user
from app.core.config import settings
from app.db.session import get_db
from app.models.user import User
from app.models.vehicle import UserVehicle

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/vehicles", tags=["vehicles"])

MAX_VEHICLES = 10

# Fuel type defaults: (tank_litres, mpg)
FUEL_DEFAULTS = {
    "PETROL":        (50.0, 45.0),
    "DIESEL":        (60.0, 55.0),
    "HYBRID ELECTRIC": (45.0, 60.0),
    "ELECTRIC":      (None, None),
    "PLUG-IN HYBRID ELECTRIC": (45.0, 50.0),
}


class VehicleCreate(BaseModel):
    registration: str
    nickname: str | None = None
    make: str | None = None
    model: str | None = None
    year: int | None = None
    colour: str | None = None
    fuel_type: str | None = None
    tank_litres: float | None = None
    mpg: float | None = None
    miles_per_kwh: float | None = None


class VehicleUpdate(BaseModel):
    nickname: str | None = None
    make: str | None = None
    model: str | None = None
    year: int | None = None
    colour: str | None = None
    fuel_type: str | None = None
    tank_litres: float | None = None
    mpg: float | None = None
    miles_per_kwh: float | None = None


def _vehicle_out(v: UserVehicle) -> dict:
    return {
        "id": str(v.id),
        "registration": v.registration,
        "nickname": v.nickname,
        "make": v.make,
        "model": v.model,
        "year": v.year,
        "colour": v.colour,
        "fuel_type": v.fuel_type,
        "tank_litres": v.tank_litres,
        "mpg": v.mpg,
        "miles_per_kwh": v.miles_per_kwh,
        "is_active": v.is_active,
        "created_at": v.created_at.isoformat(),
    }


@router.get("/lookup/{registration}")
async def lookup_vehicle(
    registration: str,
    current_user: User = Depends(get_current_user),
) -> dict:
    """Look up vehicle details from DVLA VES API."""
    reg = registration.upper().replace(" ", "")

    # If DVLA key is configured, use it
    if settings.dvla_api_key:
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.post(
                    "https://driver-vehicle-licensing.api.gov.uk/vehicle-enquiry/v1/vehicles",
                    headers={"x-api-key": settings.dvla_api_key, "Content-Type": "application/json"},
                    json={"registrationNumber": reg},
                )
                if resp.status_code == 200:
                    data = resp.json()
                    fuel = data.get("fuelType", "PETROL")
                    defaults = FUEL_DEFAULTS.get(fuel.upper(), (55.0, 45.0))
                    return {
                        "registration": reg,
                        "make": data.get("make"),
                        "model": None,  # VES doesn't return model
                        "year": data.get("yearOfManufacture"),
                        "colour": data.get("colour", "").title() or None,
                        "fuel_type": fuel,
                        "tank_litres": defaults[0],
                        "mpg": defaults[1],
                        "miles_per_kwh": 3.5 if "ELECTRIC" in fuel.upper() else None,
                        "source": "dvla",
                    }
        except Exception as e:
            logger.warning(f"DVLA lookup failed for {reg}: {e}")

    # Stub response — replace with real data when DVLA key arrives
    return {
        "registration": reg,
        "make": None,
        "model": None,
        "year": None,
        "colour": None,
        "fuel_type": "PETROL",
        "tank_litres": 50.0,
        "mpg": 45.0,
        "miles_per_kwh": None,
        "source": "manual",
    }


@router.get("")
async def list_vehicles(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[dict]:
    if current_user.role not in ("pro", "admin"):
        raise HTTPException(status_code=403, detail="Pro subscription required")
    result = await db.execute(
        select(UserVehicle)
        .where(UserVehicle.user_id == current_user.id)
        .order_by(UserVehicle.is_active.desc(), UserVehicle.created_at)
    )
    return [_vehicle_out(v) for v in result.scalars().all()]


@router.post("", status_code=status.HTTP_201_CREATED)
async def add_vehicle(
    body: VehicleCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    if current_user.role not in ("pro", "admin"):
        raise HTTPException(status_code=403, detail="Pro subscription required")

    count = await db.execute(
        select(UserVehicle).where(UserVehicle.user_id == current_user.id)
    )
    if len(count.scalars().all()) >= MAX_VEHICLES:
        raise HTTPException(status_code=400, detail=f"Maximum {MAX_VEHICLES} vehicles allowed")

    # If first vehicle, make it active
    existing = await db.execute(
        select(UserVehicle).where(UserVehicle.user_id == current_user.id)
    )
    is_first = len(existing.scalars().all()) == 0

    vehicle = UserVehicle(
        user_id=current_user.id,
        registration=body.registration.upper().replace(" ", ""),
        nickname=body.nickname,
        make=body.make,
        model=body.model,
        year=body.year,
        colour=body.colour,
        fuel_type=body.fuel_type,
        tank_litres=body.tank_litres,
        mpg=body.mpg,
        miles_per_kwh=body.miles_per_kwh,
        is_active=is_first,
    )
    db.add(vehicle)
    await db.commit()
    await db.refresh(vehicle)
    return _vehicle_out(vehicle)


@router.put("/{vehicle_id}")
async def update_vehicle(
    vehicle_id: UUID,
    body: VehicleUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    result = await db.execute(
        select(UserVehicle).where(
            UserVehicle.id == vehicle_id,
            UserVehicle.user_id == current_user.id,
        )
    )
    vehicle = result.scalar_one_or_none()
    if not vehicle:
        raise HTTPException(status_code=404, detail="Vehicle not found")

    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(vehicle, field, value)
    await db.commit()
    await db.refresh(vehicle)
    return _vehicle_out(vehicle)


@router.post("/{vehicle_id}/activate")
async def activate_vehicle(
    vehicle_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    result = await db.execute(
        select(UserVehicle).where(
            UserVehicle.id == vehicle_id,
            UserVehicle.user_id == current_user.id,
        )
    )
    vehicle = result.scalar_one_or_none()
    if not vehicle:
        raise HTTPException(status_code=404, detail="Vehicle not found")

    # Deactivate all others
    await db.execute(
        update(UserVehicle)
        .where(UserVehicle.user_id == current_user.id)
        .values(is_active=False)
    )
    vehicle.is_active = True
    await db.commit()
    return {"status": "ok"}


@router.delete("/{vehicle_id}")
async def delete_vehicle(
    vehicle_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    result = await db.execute(
        select(UserVehicle).where(
            UserVehicle.id == vehicle_id,
            UserVehicle.user_id == current_user.id,
        )
    )
    vehicle = result.scalar_one_or_none()
    if not vehicle:
        raise HTTPException(status_code=404, detail="Vehicle not found")

    was_active = vehicle.is_active
    await db.delete(vehicle)
    await db.commit()

    # If deleted vehicle was active, make the first remaining one active
    if was_active:
        remaining = await db.execute(
            select(UserVehicle)
            .where(UserVehicle.user_id == current_user.id)
            .order_by(UserVehicle.created_at)
            .limit(1)
        )
        first = remaining.scalar_one_or_none()
        if first:
            first.is_active = True
            await db.commit()
    return {"status": "deleted"}
