from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base


class Station(Base):
    __tablename__ = "stations"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    brand: Mapped[str | None] = mapped_column(String, nullable=True)
    operator: Mapped[str | None] = mapped_column(String, nullable=True)
    address: Mapped[str | None] = mapped_column(String, nullable=True)
    postcode: Mapped[str | None] = mapped_column(String, nullable=True)
    latitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    longitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    country: Mapped[str | None] = mapped_column(String, nullable=True)
    county: Mapped[str | None] = mapped_column(String, nullable=True)
    phone: Mapped[str | None] = mapped_column(String, nullable=True)
    amenities: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    opening_times: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    fuel_types: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    is_motorway: Mapped[bool] = mapped_column(Boolean, default=False)
    is_supermarket: Mapped[bool] = mapped_column(Boolean, default=False)
    temporary_closure: Mapped[bool] = mapped_column(Boolean, default=False)
    permanent_closure: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())

    prices: Mapped[list["PriceRecord"]] = relationship("PriceRecord", back_populates="station")


class PriceRecord(Base):
    __tablename__ = "price_history"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    station_id: Mapped[str] = mapped_column(String, ForeignKey("stations.id"), nullable=False, index=True)
    fuel_type: Mapped[str] = mapped_column(String, nullable=False)
    price_pence: Mapped[float] = mapped_column(Float, nullable=False)
    recorded_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, index=True)
    source_updated_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    price_flagged: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    station: Mapped["Station"] = relationship("Station", back_populates="prices")
