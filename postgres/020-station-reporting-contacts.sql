-- Tracks admin outreach to brands about stations that have stopped
-- reporting/updating prices — feeds a "we've flagged this with <brand>"
-- badge on the station page, and lets the badge auto-clear once the
-- station starts reporting again (resolved_at set once source_updated_at
-- moves past contacted_at).
CREATE TABLE station_reporting_contacts (
    id SERIAL PRIMARY KEY,
    station_id VARCHAR NOT NULL REFERENCES stations(id),
    contacted_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    contacted_by VARCHAR,
    note TEXT,
    resolved_at TIMESTAMPTZ
);

CREATE INDEX idx_station_reporting_contacts_station ON station_reporting_contacts(station_id);

-- Manually-maintained contact details per brand, for the admin draft-email
-- tool. Populated as needed, not pre-filled for all 30 brands up front.
CREATE TABLE brand_contacts (
    id SERIAL PRIMARY KEY,
    brand_name VARCHAR NOT NULL UNIQUE,  -- matches brands.name
    contact_email VARCHAR,
    notes TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
