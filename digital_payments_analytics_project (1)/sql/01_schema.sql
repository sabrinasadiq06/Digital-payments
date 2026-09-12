-- =============================================================
-- 01_schema.sql
-- Schema for the Digital Payments Analytics Dashboard project.
-- Designed as one clean fact table (transactions) — realistic for
-- how a payments warehouse table typically looks after ETL from
-- an OLTP switch/gateway. Written for SQLite (also valid ANSI SQL
-- with trivial changes for Postgres/MySQL, noted inline).
-- =============================================================

DROP TABLE IF EXISTS transactions;

CREATE TABLE transactions (
    transaction_id      TEXT PRIMARY KEY,
    ts                   TIMESTAMP NOT NULL,        -- transaction timestamp
    customer_id          TEXT NOT NULL,
    customer_age_group   TEXT NOT NULL,
    customer_city        TEXT NOT NULL,
    customer_state       TEXT NOT NULL,
    merchant_id           TEXT NOT NULL,
    merchant_category     TEXT NOT NULL,
    payment_channel        TEXT NOT NULL,            -- UPI / Debit Card / Credit Card / Net Banking / Wallet
    device_type             TEXT NOT NULL,
    amount_inr              REAL NOT NULL,
    status                   TEXT NOT NULL,            -- Success / Failed
    is_fraud                 INTEGER NOT NULL           -- 0/1 (boolean)
);

-- Helpful indexes for the analytical queries below (mirrors how you'd
-- index a real payments fact table for dashboard-style filtering).
CREATE INDEX idx_txn_ts        ON transactions (ts);
CREATE INDEX idx_txn_channel   ON transactions (payment_channel);
CREATE INDEX idx_txn_category  ON transactions (merchant_category);
CREATE INDEX idx_txn_state     ON transactions (customer_state);
CREATE INDEX idx_txn_status    ON transactions (status);
CREATE INDEX idx_txn_customer  ON transactions (customer_id);
