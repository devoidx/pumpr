-- Old Fuel Finder registrations replaced by a new one at the same forecourt
-- (operator changes create a new station ID; the old one is rarely closed).
-- Set nightly by mark_superseded_stations(); never written by sync_stations.
ALTER TABLE stations ADD COLUMN IF NOT EXISTS superseded_by VARCHAR REFERENCES stations(id) ON DELETE SET NULL;
ALTER TABLE stations ADD COLUMN IF NOT EXISTS superseded_at TIMESTAMP;
