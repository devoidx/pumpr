-- Migration: 003_add_stripe
-- Run: docker exec -i pumpr_db psql -U pumpr pumpr < postgres/003_add_stripe.sql

ALTER TABLE users
  ADD COLUMN IF NOT EXISTS stripe_customer_id    TEXT,
  ADD COLUMN IF NOT EXISTS subscription_status   TEXT NOT NULL DEFAULT 'inactive',
  ADD COLUMN IF NOT EXISTS subscription_id       TEXT,
  ADD COLUMN IF NOT EXISTS price_id              TEXT,
  ADD COLUMN IF NOT EXISTS current_period_end    TIMESTAMPTZ;

CREATE INDEX IF NOT EXISTS idx_users_stripe_customer_id ON users (stripe_customer_id);
