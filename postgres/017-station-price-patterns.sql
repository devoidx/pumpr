CREATE TABLE IF NOT EXISTS station_price_patterns (
    station_id VARCHAR NOT NULL REFERENCES stations(id) ON DELETE CASCADE,
    fuel_type VARCHAR NOT NULL,
    day_of_week INTEGER NOT NULL,  -- 0=Sunday, 1=Monday ... 6=Saturday
    avg_price_pence NUMERIC(6,2) NOT NULL,
    reading_count INTEGER NOT NULL,
    computed_at TIMESTAMPTZ DEFAULT now(),
    PRIMARY KEY (station_id, fuel_type, day_of_week)
);

CREATE INDEX IF NOT EXISTS idx_station_price_patterns_station ON station_price_patterns(station_id, fuel_type);
