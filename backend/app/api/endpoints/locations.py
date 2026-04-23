from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user, require_verified
from app.db.session import get_db
from app.models.location import UserFavouriteCharger, UserLocation
from app.models.user import User
from app.schemas.location import FavouriteChargerOut, LocationCreate, LocationOut, LocationUpdate

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/locations", tags=["locations"])

MAX_LOCATIONS = 10


def _require_pro(user: User) -> None:
    if user.role not in ("pro", "admin"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Pro subscription required")


# ── Saved locations ───────────────────────────────────────────────────────

@router.get("", response_model=list[LocationOut])
async def list_locations(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[LocationOut]:
    _require_pro(current_user)
    result = await db.execute(
        select(UserLocation)
        .where(UserLocation.user_id == current_user.id)
        .order_by(UserLocation.created_at)
    )
    return [LocationOut.model_validate(r) for r in result.scalars().all()]


@router.post("", response_model=LocationOut, status_code=status.HTTP_201_CREATED)
async def create_location(
    body: LocationCreate,
    current_user: User = Depends(require_verified),
    db: AsyncSession = Depends(get_db),
) -> LocationOut:
    _require_pro(current_user)

    # Enforce max locations
    count_result = await db.execute(
        select(UserLocation).where(UserLocation.user_id == current_user.id)
    )
    existing = count_result.scalars().all()
    if len(existing) >= MAX_LOCATIONS:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Maximum {MAX_LOCATIONS} saved locations allowed")

    # Enforce single home/work
    if body.type in ("home", "work"):
        for loc in existing:
            if loc.type == body.type:
                raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=f"You already have a {body.type} location. Delete it first.")

    loc = UserLocation(
        user_id=current_user.id,
        label=body.label,
        type=body.type,
        lat=body.lat,
        lng=body.lng,
        postcode=body.postcode,
        has_home_charger=body.has_home_charger,
    )
    db.add(loc)
    await db.commit()
    await db.refresh(loc)
    return LocationOut.model_validate(loc)


@router.patch("/{location_id}", response_model=LocationOut)
async def update_location(
    location_id: str,
    body: LocationUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> LocationOut:
    _require_pro(current_user)
    import uuid as _uuid
    result = await db.execute(
        select(UserLocation).where(
            UserLocation.id == _uuid.UUID(location_id),
            UserLocation.user_id == current_user.id,
        )
    )
    loc = result.scalar_one_or_none()
    if not loc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Location not found")

    for field, value in body.model_dump(exclude_none=True).items():
        setattr(loc, field, value)
    await db.commit()
    await db.refresh(loc)
    return LocationOut.model_validate(loc)


@router.delete("/{location_id}")
async def delete_location(
    location_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    _require_pro = current_user.role in ("pro", "admin")
    if not _require_pro:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Pro subscription required")
    import uuid as _uuid
    await db.execute(
        delete(UserLocation).where(
            UserLocation.id == _uuid.UUID(location_id),
            UserLocation.user_id == current_user.id,
        )
    )
    await db.commit()
    return {"message": "Deleted"}


# ── Favourite chargers ────────────────────────────────────────────────────

@router.get("/chargers/favourites", response_model=list[FavouriteChargerOut])
async def list_favourite_chargers(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[FavouriteChargerOut]:
    _require_pro(current_user)
    result = await db.execute(
        select(UserFavouriteCharger)
        .where(UserFavouriteCharger.user_id == current_user.id)
        .order_by(UserFavouriteCharger.created_at)
    )
    return [FavouriteChargerOut.model_validate(r) for r in result.scalars().all()]


@router.post("/chargers/favourites/{charger_id}", status_code=status.HTTP_201_CREATED)
async def add_favourite_charger(
    charger_id: str,
    current_user: User = Depends(require_verified),
    db: AsyncSession = Depends(get_db),
) -> dict:
    _require_pro(current_user)
    existing = await db.execute(
        select(UserFavouriteCharger).where(
            UserFavouriteCharger.user_id == current_user.id,
            UserFavouriteCharger.charger_id == charger_id,
        )
    )
    if existing.scalar_one_or_none():
        return {"message": "Already favourited"}
    db.add(UserFavouriteCharger(user_id=current_user.id, charger_id=charger_id))
    await db.commit()
    return {"message": "Added to favourites"}


@router.delete("/chargers/favourites/{charger_id}")
async def remove_favourite_charger(
    charger_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    _require_pro(current_user)
    await db.execute(
        delete(UserFavouriteCharger).where(
            UserFavouriteCharger.user_id == current_user.id,
            UserFavouriteCharger.charger_id == charger_id,
        )
    )
    await db.commit()
    return {"message": "Removed"}
