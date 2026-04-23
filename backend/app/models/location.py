from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base


class UserLocation(Base):
    __tablename__ = "user_locations"

    id:               Mapped[uuid.UUID]      = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id:          Mapped[uuid.UUID]      = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    label:            Mapped[str]            = mapped_column(Text, nullable=False)
    type:             Mapped[str]            = mapped_column(String(10), nullable=False, default="custom")
    lat:              Mapped[float]          = mapped_column(Float, nullable=False)
    lng:              Mapped[float]          = mapped_column(Float, nullable=False)
    postcode:         Mapped[str | None]     = mapped_column(Text, nullable=True)
    has_home_charger: Mapped[bool]           = mapped_column(Boolean, nullable=False, default=False)
    created_at:       Mapped[datetime]       = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())


class UserFavouriteCharger(Base):
    __tablename__ = "user_favourite_chargers"

    id:         Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id:    Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    charger_id: Mapped[str]       = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime]  = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
