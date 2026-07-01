
from sqlalchemy import (
    Column,
    Date,
    Double,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import TIMESTAMP
from sqlalchemy.orm import relationship

from app.db.session import Base


class EUStation(Base):
    __tablename__ = "eu_stations"

    id = Column(Integer, primary_key=True)
    external_id = Column(String, nullable=False)
    country = Column(String(2), nullable=False)
    name = Column(String, nullable=False)
    brand = Column(String)
    address = Column(String)
    postcode = Column(String)
    city = Column(String)
    latitude = Column(Double, nullable=False)
    longitude = Column(Double, nullable=False)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())

    prices = relationship("EULatestPrice", back_populates="station", cascade="all, delete-orphan")

    __table_args__ = (
        UniqueConstraint("country", "external_id", name="uq_eu_station_country_external"),
        Index("idx_eu_stations_country_city", "country", "city"),
        Index("idx_eu_stations_coords", "latitude", "longitude"),
    )


class EULatestPrice(Base):
    __tablename__ = "eu_latest_prices"

    id = Column(Integer, primary_key=True)
    eu_station_id = Column(Integer, ForeignKey("eu_stations.id", ondelete="CASCADE"), nullable=False)
    fuel_type = Column(String, nullable=False)
    price_eur = Column(Numeric(6, 3), nullable=False)
    recorded_at = Column(TIMESTAMP(timezone=True), nullable=False)

    station = relationship("EUStation", back_populates="prices")

    __table_args__ = (
        UniqueConstraint("eu_station_id", "fuel_type", name="uq_eu_latest_price_station_fuel"),
        Index("idx_eu_latest_prices_station", "eu_station_id"),
    )


class ExchangeRate(Base):
    __tablename__ = "exchange_rates"

    rate_date = Column(Date, primary_key=True)
    eur_to_gbp = Column(Numeric(8, 6), nullable=False)
    fetched_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
