CREATE TABLE fuel_fillups (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    vehicle_id UUID NOT NULL REFERENCES user_vehicles(id) ON DELETE CASCADE,
    filled_at DATE NOT NULL,
    station_id VARCHAR REFERENCES stations(id) ON DELETE SET NULL,
    station_name VARCHAR,
    fuel_type VARCHAR NOT NULL,
    litres DOUBLE PRECISION NOT NULL,
    price_pence_per_litre DOUBLE PRECISION NOT NULL,
    total_cost_pence DOUBLE PRECISION NOT NULL,
    odometer_miles DOUBLE PRECISION,
    notes TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_fuel_fillups_user ON fuel_fillups(user_id);
CREATE INDEX idx_fuel_fillups_vehicle ON fuel_fillups(vehicle_id);
CREATE INDEX idx_fuel_fillups_date ON fuel_fillups(filled_at DESC);
