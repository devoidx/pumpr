-- Membership-required brands (e.g. Costco). Reuses the existing curated
-- brands table rather than a new one — stations.brand is matched via
-- ILIKE '%' || brands.name || '%' since station brand text has suffixes
-- (e.g. "COSTCO WHOLESALE ABERDEEN") that brands.name ("COSTCO WHOLESALE")
-- is a substring of.
--
-- To add another membership-required brand later:
--   UPDATE brands SET membership_required = TRUE WHERE name = 'SOME BRAND';
-- No code changes needed.

ALTER TABLE brands ADD COLUMN membership_required BOOLEAN NOT NULL DEFAULT FALSE;

UPDATE brands SET membership_required = TRUE WHERE name = 'COSTCO WHOLESALE';
