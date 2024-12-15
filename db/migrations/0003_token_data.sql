-- +goose Up
CREATE TABLE IF NOT EXISTS data_wallet(
    id INTEGER PRIMARY KEY,
    wallet TEXT UNIQUE,
    pnl TEXT,
    wr TEXT
);

-- +goose Down
DROP TABLE IF EXISTS data_wallet;