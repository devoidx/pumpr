-- Migration: 004_add_saved_locations
-- Run: docker exec -i pumpr_db psql -U pumpr pumpr < postgres/004_add_saved_locations.sql

CREATE TABLE IF NOT EXISTS user_locations (
    id              UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id         UUID        NOT NULL REFERENCES users (id) ON DELETE CASCADE,
    label           TEXT        NOT NULL,
    type            TEXT        NOT NULL DEFAULT 'custom'
                                CHECK (type IN ('home', 'work', 'custom')),
    lat             FLOAT       NOT NULL,
    lng             FLOAT       NOT NULL,
    postcode        TEXT,
    has_home_charger BOOLEAN    NOT NULL DEFAULT FALSE,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_user_locations_user_id ON user_locations (user_id);

CREATE TABLE IF NOT EXISTS user_favourite_chargers (
    id          UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id     UUID        NOT NULL REFERENCES users (id) ON DELETE CASCADE,
    charger_id  TEXT        NOT NULL,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (user_id, charger_id)
);

CREATE INDEX IF NOT EXISTS idx_user_fav_chargers_user_id ON user_favourite_chargers (user_id);
