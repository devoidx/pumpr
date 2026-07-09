CREATE TABLE IF NOT EXISTS price_day_patterns (
    fuel_type VARCHAR NOT NULL,
    is_supermarket BOOLEAN NOT NULL,
    day_of_week INTEGER NOT NULL,  -- 0=Sunday, 1=Monday ... 6=Saturday
    avg_price_pence NUMERIC(6,2) NOT NULL,
    station_count INTEGER NOT NULL,
    computed_at TIMESTAMPTZ DEFAULT now(),
    PRIMARY KEY (fuel_type, is_supermarket, day_of_week)
);
