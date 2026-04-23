from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class LocationCreate(BaseModel):
    label:            str   = Field(min_length=1, max_length=50)
    type:             str   = Field(pattern=r"^(home|work|custom)$")
    lat:              float
    lng:              float
    postcode:         str | None = None
    has_home_charger: bool  = False


class LocationUpdate(BaseModel):
    label:            str | None  = Field(default=None, min_length=1, max_length=50)
    lat:              float | None = None
    lng:              float | None = None
    postcode:         str | None   = None
    has_home_charger: bool | None  = None


class LocationOut(BaseModel):
    id:               uuid.UUID
    label:            str
    type:             str
    lat:              float
    lng:              float
    postcode:         str | None
    has_home_charger: bool
    created_at:       datetime

    model_config = {"from_attributes": True}


class FavouriteChargerOut(BaseModel):
    id:         uuid.UUID
    charger_id: str
    created_at: datetime

    model_config = {"from_attributes": True}
