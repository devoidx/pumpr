-- Migration 006: Pro-only accounts
-- Make username optional, add setup_password token purpose

ALTER TABLE users
  ALTER COLUMN username DROP NOT NULL,
  ALTER COLUMN username SET DEFAULT NULL;

-- Allow null usernames (existing users keep theirs)
UPDATE users SET username = NULL WHERE username = '';
