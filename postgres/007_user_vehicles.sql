-- Migration 007: User vehicles
CREATE TABLE user_vehicles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    registration TEXT NOT NULL,
    nickname TEXT,
    make TEXT,
    model TEXT,
    year INTEGER,
    colour TEXT,
    fuel_type TEXT,
    tank_litres FLOAT,
    mpg FLOAT,
    miles_per_kwh FLOAT,
    is_active BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_user_vehicles_user_id ON user_vehicles(user_id);
