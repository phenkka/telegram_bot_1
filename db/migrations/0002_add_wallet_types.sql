-- +goose Up
CREATE TYPE wallet_type_enum AS ENUM ('INFLUENCER', 'SMART', 'WHALE', 'INSIDER');

ALTER TABLE sol_wallet
ADD COLUMN wallet_type wallet_type_enum;

-- +goose Down
ALTER TABLE sol_wallet
DROP COLUMN wallet_type;

DROP TYPE wallet_type_enum;
