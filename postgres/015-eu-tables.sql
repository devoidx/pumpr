CREATE TABLE eu_stations (
    id SERIAL PRIMARY KEY,
    external_id VARCHAR NOT NULL,
    country VARCHAR(2) NOT NULL,
    name VARCHAR NOT NULL,
    brand VARCHAR,
    address VARCHAR,
    postcode VARCHAR,
    city VARCHAR,
    latitude DOUBLE PRECISION NOT NULL,
    longitude DOUBLE PRECISION NOT NULL,
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now(),
    UNIQUE (country, external_id)
);

CREATE TABLE eu_latest_prices (
    id SERIAL PRIMARY KEY,
    eu_station_id INTEGER REFERENCES eu_stations(id) ON DELETE CASCADE,
    fuel_type VARCHAR NOT NULL,
    price_eur NUMERIC(6,3) NOT NULL,
    recorded_at TIMESTAMPTZ NOT NULL,
    UNIQUE (eu_station_id, fuel_type)
);

CREATE TABLE exchange_rates (
    rate_date DATE PRIMARY KEY,
    eur_to_gbp NUMERIC(8,6) NOT NULL,
    fetched_at TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX idx_eu_stations_country_city ON eu_stations(country, city);
CREATE INDEX idx_eu_stations_coords ON eu_stations(latitude, longitude);
CREATE INDEX idx_eu_latest_prices_station ON eu_latest_prices(eu_station_id);

-- Added post-initial-creation: motorway flag for Italy (and future countries)
ALTER TABLE eu_stations ADD COLUMN IF NOT EXISTS is_motorway BOOLEAN DEFAULT FALSE;
