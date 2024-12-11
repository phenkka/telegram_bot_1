-- +goose Up
ALTER TABLE users
ADD COLUMN IF NOT EXISTS notify_smart BOOLEAN DEFAULT TRUE;

ALTER TABLE users
ADD COLUMN IF NOT EXISTS notify_infl BOOLEAN DEFAULT TRUE;

-- +goose Down
ALTER TABLE users
DROP COLUMN notify_smart;

ALTER TABLE users
DROP COLUMN notify_infl;