from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from jose import JWTError, jwt
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user
from app.core.config import settings
from app.db.session import get_db
from app.models.alert import PriceAlert
from app.models.models import Station
from app.models.user import User

router = APIRouter(prefix="/alerts", tags=["alerts"])

ALERT_TOKEN_EXPIRE_DAYS = 90
ALERT_TOKEN_PURPOSE = "disable_alert"


def _create_disable_token(alert_id: uuid.UUID) -> str:
    payload = {
        "sub": str(alert_id),
        "purpose": ALERT_TOKEN_PURPOSE,
        "exp": datetime.now(timezone.utc) + timedelta(days=ALERT_TOKEN_EXPIRE_DAYS),
    }
    return jwt.encode(payload, settings.secret_key, algorithm="HS256")


def _decode_disable_token(token: str) -> uuid.UUID:
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=["HS256"])
        if payload.get("purpose") != ALERT_TOKEN_PURPOSE:
            raise ValueError("Invalid token purpose")
        return uuid.UUID(payload["sub"])
    except (JWTError, ValueError, KeyError) as e:
        raise HTTPException(status_code=400, detail="Invalid or expired token") from e


class AlertCreate(BaseModel):
    station_id: str
    fuel_type: str
    alert_type: str  # below_pence | change_pct
    threshold: float


class AlertOut(BaseModel):
    id: uuid.UUID
    station_id: str
    station_name: str | None
    fuel_type: str
    alert_type: str
    threshold: float
    is_active: bool
    last_triggered_at: datetime | None
    triggered_count: int
    created_at: datetime

    model_config = {"from_attributes": True}


def _require_pro(user: User) -> None:
    if user.role not in ("pro", "admin"):
        raise HTTPException(status_code=403, detail="Pro subscription required")


@router.get("/", response_model=list[AlertOut])
async def list_alerts(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[AlertOut]:
    _require_pro(current_user)
    result = await db.execute(
        select(PriceAlert, Station.name)
        .join(Station, PriceAlert.station_id == Station.id)
        .where(PriceAlert.user_id == current_user.id)
        .order_by(PriceAlert.created_at.desc())
    )
    rows = result.all()
    out = []
    for alert, station_name in rows:
        out.append(AlertOut(
            id=alert.id,
            station_id=alert.station_id,
            station_name=station_name,
            fuel_type=alert.fuel_type,
            alert_type=alert.alert_type,
            threshold=alert.threshold,
            is_active=alert.is_active,
            last_triggered_at=alert.last_triggered_at,
            triggered_count=alert.triggered_count,
            created_at=alert.created_at,
        ))
    return out


@router.get("/station/{station_id}", response_model=list[AlertOut])
async def list_alerts_for_station(
    station_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[AlertOut]:
    _require_pro(current_user)
    result = await db.execute(
        select(PriceAlert, Station.name)
        .join(Station, PriceAlert.station_id == Station.id)
        .where(PriceAlert.user_id == current_user.id, PriceAlert.station_id == station_id)
        .order_by(PriceAlert.created_at.desc())
    )
    rows = result.all()
    return [AlertOut(
        id=a.id, station_id=a.station_id, station_name=sn,
        fuel_type=a.fuel_type, alert_type=a.alert_type, threshold=a.threshold,
        is_active=a.is_active, last_triggered_at=a.last_triggered_at,
        triggered_count=a.triggered_count, created_at=a.created_at,
    ) for a, sn in rows]


@router.post("/", response_model=AlertOut, status_code=status.HTTP_201_CREATED)
async def create_alert(
    body: AlertCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> AlertOut:
    _require_pro(current_user)
    if body.alert_type not in ("below_pence", "change_pct"):
        raise HTTPException(status_code=400, detail="Invalid alert_type")
    if body.threshold <= 0:
        raise HTTPException(status_code=400, detail="Threshold must be positive")

    station = await db.get(Station, body.station_id)
    if not station:
        raise HTTPException(status_code=404, detail="Station not found")

    alert = PriceAlert(
        user_id=current_user.id,
        station_id=body.station_id,
        fuel_type=body.fuel_type,
        alert_type=body.alert_type,
        threshold=body.threshold,
    )
    db.add(alert)
    await db.commit()
    await db.refresh(alert)
    return AlertOut(
        id=alert.id, station_id=alert.station_id, station_name=station.name,
        fuel_type=alert.fuel_type, alert_type=alert.alert_type, threshold=alert.threshold,
        is_active=alert.is_active, last_triggered_at=alert.last_triggered_at,
        triggered_count=alert.triggered_count, created_at=alert.created_at,
    )


@router.patch("/{alert_id}/toggle", response_model=AlertOut)
async def toggle_alert(
    alert_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> AlertOut:
    _require_pro(current_user)
    alert = await db.get(PriceAlert, alert_id)
    if not alert or alert.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Alert not found")
    alert.is_active = not alert.is_active
    await db.commit()
    await db.refresh(alert)
    station = await db.get(Station, alert.station_id)
    return AlertOut(
        id=alert.id, station_id=alert.station_id, station_name=station.name if station else None,
        fuel_type=alert.fuel_type, alert_type=alert.alert_type, threshold=alert.threshold,
        is_active=alert.is_active, last_triggered_at=alert.last_triggered_at,
        triggered_count=alert.triggered_count, created_at=alert.created_at,
    )


@router.delete("/{alert_id}", status_code=status.HTTP_204_NO_CONTENT, response_model=None)
async def delete_alert(
    alert_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    _require_pro(current_user)
    alert = await db.get(PriceAlert, alert_id)
    if not alert or alert.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Alert not found")
    await db.delete(alert)
    await db.commit()


@router.get("/disable", response_model=dict)
async def disable_alert_via_token(
    token: str,
    db: AsyncSession = Depends(get_db),
) -> dict:
    alert_id = _decode_disable_token(token)
    alert = await db.get(PriceAlert, alert_id)
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    alert.is_active = False
    await db.commit()
    return {"message": "Alert disabled successfully"}
