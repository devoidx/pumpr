CREATE TABLE market_intelligence (
    id SERIAL PRIMARY KEY,
    computed_at TIMESTAMP NOT NULL DEFAULT NOW(),
    date DATE NOT NULL UNIQUE,
    national JSONB NOT NULL,
    regional JSONB NOT NULL,
    brands JSONB NOT NULL,
    postcode_sectors JSONB NOT NULL,
    narrative TEXT
);

CREATE INDEX idx_market_intelligence_date ON market_intelligence(date DESC);
