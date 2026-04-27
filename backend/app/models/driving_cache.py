from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base


class DrivingDistanceCache(Base):
    __tablename__ = "driving_distance_cache"

    id:          Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    origin_lat:  Mapped[float]     = mapped_column(Float, nullable=False)
    origin_lng:  Mapped[float]     = mapped_column(Float, nullable=False)
    station_id:  Mapped[str]       = mapped_column(Text, ForeignKey("stations.id", ondelete="CASCADE"), nullable=False)
    driving_km:  Mapped[float]     = mapped_column(Float, nullable=False)
    driving_mins: Mapped[float]    = mapped_column(Float, nullable=False)
    cached_at:   Mapped[datetime]  = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
