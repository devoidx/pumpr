from datetime import datetime

from pydantic import BaseModel


class PriceOut(BaseModel):
    fuel_type: str
    price_pence: float
    recorded_at: datetime
    model_config = {"from_attributes": True}


class StationLatestPrices(BaseModel):
    fuel_type: str
    price_pence: float
    recorded_at: datetime
    source_updated_at: datetime | None = None
    price_flagged: bool = False
    model_config = {"from_attributes": True}


class StationOut(BaseModel):
    id: str
    name: str
    brand: str | None
    operator: str | None
    address: str | None
    postcode: str | None
    latitude: float | None
    longitude: float | None
    country: str | None = None
    county: str | None = None
    is_motorway: bool = False
    is_supermarket: bool = False
    temporary_closure: bool = False
    amenities: list | None = None
    fuel_types: list | None = None
    latest_prices: list[StationLatestPrices] = []
    model_config = {"from_attributes": True}


class StationDetail(StationOut):
    phone: str | None = None
    opening_times_data: dict | None = None
    created_at: datetime
    updated_at: datetime


class PriceHistoryPoint(BaseModel):
    recorded_at: datetime
    price_pence: float
    model_config = {"from_attributes": True}


class PriceHistoryOut(BaseModel):
    station_id: str
    fuel_type: str
    history: list[PriceHistoryPoint]


class StatsOut(BaseModel):
    fuel_type: str
    avg_price_pence: float
    min_price_pence: float
    max_price_pence: float
    station_count: int
    as_of: datetime
