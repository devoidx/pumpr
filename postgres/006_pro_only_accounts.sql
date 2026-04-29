-- Migration 006: Pro-only accounts
-- Make username optional, add setup_password token purpose

ALTER TABLE users
  ALTER COLUMN username DROP NOT NULL,
  ALTER COLUMN username SET DEFAULT NULL;

-- Allow null usernames (existing users keep theirs)
UPDATE users SET username = NULL WHERE username = '';

-- Add setup_password purpose to user_tokens
ALTER TABLE user_tokens DROP CONSTRAINT IF EXISTS user_tokens_purpose_check;
ALTER TABLE user_tokens ADD CONSTRAINT user_tokens_purpose_check
  CHECK (purpose = ANY (ARRAY['verify_email', 'reset_password', 'setup_password']));
