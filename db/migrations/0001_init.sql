-- +goose Up
CREATE TABLE IF NOT EXISTS sol_wallet (
    id SERIAL PRIMARY KEY,
    wallet VARCHAR(255) UNIQUE,
    "user" TEXT,
    link TEXT
);

CREATE TABLE IF NOT EXISTS token_data (
    id SERIAL PRIMARY KEY,
    wallet VARCHAR(255),
    token_address VARCHAR(255),
    token_name VARCHAR(255),
    token_amount NUMERIC,
    total_in_sol NUMERIC,
    FOREIGN KEY (wallet) REFERENCES sol_wallet (wallet) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS stats_wallets (
    id SERIAL PRIMARY KEY,
    wallet VARCHAR(255) UNIQUE,
    win_rate NUMERIC,
    total_pnl NUMERIC,
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS users (
    user_id BIGINT PRIMARY KEY,
    payment_status VARCHAR(50),
    payment_date TIMESTAMP,
    notify_status BOOLEAN DEFAULT FALSE
);

CREATE TABLE IF NOT EXISTS infl_buys (
    wallet TEXT,
    token TEXT,
    amount_token REAL,
    timestamp TIMESTAMP,
    operation_type TEXT
);

CREATE TABLE IF NOT EXISTS notified_tokens (
    token TEXT PRIMARY KEY
);

-- +goose Down
DROP TABLE IF EXISTS sol_wallet CASCADE;
DROP TABLE IF EXISTS token_data CASCADE;
DROP TABLE IF EXISTS stats_wallets CASCADE;
DROP TABLE IF EXISTS users CASCADE;
DROP TABLE IF EXISTS infl_buys CASCADE;
DROP TABLE IF EXISTS notified_tokens CASCADE;