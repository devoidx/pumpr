-- Performance indexes added July 2026
CREATE INDEX IF NOT EXISTS idx_stations_county ON stations(county);
CREATE INDEX IF NOT EXISTS idx_stations_lat_lng ON stations(latitude, longitude);
CREATE INDEX IF NOT EXISTS idx_latest_prices_fuel_type ON latest_prices(fuel_type);
CREATE INDEX IF NOT EXISTS idx_latest_prices_station_fuel ON latest_prices(station_id, fuel_type);
CREATE INDEX IF NOT EXISTS idx_price_history_station_fuel_time ON price_history(station_id, fuel_type, recorded_at DESC);
ALTER TABLE stations ALTER COLUMN county SET STATISTICS 500;
