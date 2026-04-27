-- Migration: 005_add_driving_distance
-- Run: docker exec -i pumpr_db psql -U pumpr pumpr < postgres/005_add_driving_distance.sql

ALTER TABLE users
  ADD COLUMN IF NOT EXISTS use_driving_distance BOOLEAN NOT NULL DEFAULT FALSE;

CREATE TABLE IF NOT EXISTS driving_distance_cache (
    id              UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    origin_lat      FLOAT       NOT NULL,
    origin_lng      FLOAT       NOT NULL,
    station_id      TEXT        NOT NULL REFERENCES stations (id) ON DELETE CASCADE,
    driving_km      FLOAT       NOT NULL,
    driving_mins    FLOAT       NOT NULL,
    cached_at       TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (origin_lat, origin_lng, station_id)
);

CREATE INDEX IF NOT EXISTS idx_ddc_origin ON driving_distance_cache (origin_lat, origin_lng);
CREATE INDEX IF NOT EXISTS idx_ddc_station ON driving_distance_cache (station_id);
CREATE INDEX IF NOT EXISTS idx_ddc_cached_at ON driving_distance_cache (cached_at);
