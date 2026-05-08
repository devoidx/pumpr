CREATE TABLE brands (
    name VARCHAR PRIMARY KEY,
    display_name VARCHAR NOT NULL,
    logo_b64 TEXT,
    logo_updated_at TIMESTAMP
);
