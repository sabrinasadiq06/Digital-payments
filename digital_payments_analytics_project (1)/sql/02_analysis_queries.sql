-- =============================================================
-- 02_analysis_queries.sql
-- Core analytical SQL for the Digital Payments Analytics Dashboard.
-- Each block is a standalone, runnable query against `transactions`.
-- Grouped by the 8 analysis dimensions requested.
-- =============================================================

-- -------------------------------------------------------------
-- 1. TRANSACTION VOLUME  (overall + monthly trend)
-- -------------------------------------------------------------
-- 1a. Headline KPIs
SELECT
    COUNT(*)                                   AS total_transactions,
    SUM(CASE WHEN status = 'Success' THEN 1 ELSE 0 END) AS successful_transactions,
    ROUND(SUM(amount_inr), 2)                  AS total_value_inr,
    ROUND(AVG(amount_inr), 2)                  AS avg_ticket_size_inr,
    COUNT(DISTINCT customer_id)                AS active_customers,
    COUNT(DISTINCT merchant_id)                AS active_merchants
FROM transactions;

-- 1b. Monthly transaction volume & value trend
SELECT
    strftime('%Y-%m', ts)             AS month,
    COUNT(*)                          AS txn_count,
    ROUND(SUM(amount_inr), 2)         AS txn_value_inr
FROM transactions
GROUP BY month
ORDER BY month;

-- -------------------------------------------------------------
-- 2. TRANSACTION VALUE  (distribution by category / channel)
-- -------------------------------------------------------------
SELECT
    merchant_category,
    COUNT(*)                                   AS txn_count,
    ROUND(SUM(amount_inr), 2)                  AS total_value_inr,
    ROUND(AVG(amount_inr), 2)                  AS avg_value_inr,
    ROUND(100.0 * SUM(amount_inr) / (SELECT SUM(amount_inr) FROM transactions), 2) AS pct_of_total_value
FROM transactions
GROUP BY merchant_category
ORDER BY total_value_inr DESC;

-- -------------------------------------------------------------
-- 3. MERCHANT CATEGORY PERFORMANCE (volume, value, failure, fraud)
-- -------------------------------------------------------------
SELECT
    merchant_category,
    COUNT(*)                                                             AS txn_count,
    ROUND(AVG(amount_inr), 2)                                            AS avg_amount_inr,
    ROUND(100.0 * SUM(CASE WHEN status='Failed' THEN 1 ELSE 0 END) / COUNT(*), 2) AS failure_rate_pct,
    ROUND(100.0 * SUM(is_fraud) / COUNT(*), 3)                           AS fraud_rate_pct
FROM transactions
GROUP BY merchant_category
ORDER BY txn_count DESC;

-- -------------------------------------------------------------
-- 4. GEOGRAPHY  (state-level volume, value, failure & fraud rates)
-- -------------------------------------------------------------
SELECT
    customer_state,
    COUNT(*)                                                             AS txn_count,
    ROUND(SUM(amount_inr), 2)                                            AS total_value_inr,
    ROUND(100.0 * SUM(CASE WHEN status='Failed' THEN 1 ELSE 0 END) / COUNT(*), 2) AS failure_rate_pct,
    ROUND(100.0 * SUM(is_fraud) / COUNT(*), 3)                           AS fraud_rate_pct
FROM transactions
GROUP BY customer_state
ORDER BY txn_count DESC;

-- Top 10 cities by transaction value
SELECT
    customer_city, customer_state,
    COUNT(*) AS txn_count,
    ROUND(SUM(amount_inr), 2) AS total_value_inr
FROM transactions
GROUP BY customer_city, customer_state
ORDER BY total_value_inr DESC
LIMIT 10;

-- -------------------------------------------------------------
-- 5. FAILURE RATE  (by channel, and failure trend over time)
-- -------------------------------------------------------------
SELECT
    payment_channel,
    COUNT(*)                                                              AS txn_count,
    SUM(CASE WHEN status='Failed' THEN 1 ELSE 0 END)                      AS failed_count,
    ROUND(100.0 * SUM(CASE WHEN status='Failed' THEN 1 ELSE 0 END) / COUNT(*), 2) AS failure_rate_pct
FROM transactions
GROUP BY payment_channel
ORDER BY failure_rate_pct DESC;

-- Daily failure-rate trend (surfaces the simulated outage spike)
SELECT
    date(ts)                                                              AS txn_date,
    COUNT(*)                                                              AS txn_count,
    ROUND(100.0 * SUM(CASE WHEN status='Failed' THEN 1 ELSE 0 END) / COUNT(*), 2) AS failure_rate_pct
FROM transactions
GROUP BY txn_date
ORDER BY failure_rate_pct DESC
LIMIT 10;

-- -------------------------------------------------------------
-- 6. FRAUD RATE  (by channel, amount bucket, and hour of day)
-- -------------------------------------------------------------
SELECT
    payment_channel,
    COUNT(*)                                    AS txn_count,
    SUM(is_fraud)                               AS fraud_count,
    ROUND(100.0 * SUM(is_fraud) / COUNT(*), 3)  AS fraud_rate_pct
FROM transactions
GROUP BY payment_channel
ORDER BY fraud_rate_pct DESC;

-- Fraud rate by amount bucket
SELECT
    CASE
        WHEN amount_inr < 500   THEN '1. <500'
        WHEN amount_inr < 2000  THEN '2. 500-2000'
        WHEN amount_inr < 5000  THEN '3. 2000-5000'
        WHEN amount_inr < 10000 THEN '4. 5000-10000'
        ELSE '5. 10000+'
    END AS amount_bucket,
    COUNT(*)                                    AS txn_count,
    ROUND(100.0 * SUM(is_fraud) / COUNT(*), 3)  AS fraud_rate_pct
FROM transactions
GROUP BY amount_bucket
ORDER BY amount_bucket;

-- Fraud rate by hour of day (fraud tends to cluster late night)
SELECT
    CAST(strftime('%H', ts) AS INTEGER)         AS hour_of_day,
    COUNT(*)                                    AS txn_count,
    ROUND(100.0 * SUM(is_fraud) / COUNT(*), 3)  AS fraud_rate_pct
FROM transactions
GROUP BY hour_of_day
ORDER BY hour_of_day;

-- -------------------------------------------------------------
-- 7. PEAK TRANSACTION PERIODS  (hour-of-day and day-of-week heatmap)
-- -------------------------------------------------------------
SELECT
    CASE CAST(strftime('%w', ts) AS INTEGER)
        WHEN 0 THEN '0-Sun' WHEN 1 THEN '1-Mon' WHEN 2 THEN '2-Tue'
        WHEN 3 THEN '3-Wed' WHEN 4 THEN '4-Thu' WHEN 5 THEN '5-Fri'
        WHEN 6 THEN '6-Sat'
    END                                          AS day_of_week,
    CAST(strftime('%H', ts) AS INTEGER)          AS hour_of_day,
    COUNT(*)                                     AS txn_count
FROM transactions
GROUP BY day_of_week, hour_of_day
ORDER BY day_of_week, hour_of_day;

-- -------------------------------------------------------------
-- 8. CUSTOMER BEHAVIOUR  (frequency segmentation + age-group spend)
-- -------------------------------------------------------------
-- Customer transaction-frequency segments
WITH customer_txns AS (
    SELECT customer_id, COUNT(*) AS txn_count, SUM(amount_inr) AS total_spend
    FROM transactions
    GROUP BY customer_id
)
SELECT
    CASE
        WHEN txn_count = 1          THEN '1. One-time (1 txn)'
        WHEN txn_count BETWEEN 2 AND 5  THEN '2. Occasional (2-5)'
        WHEN txn_count BETWEEN 6 AND 15 THEN '3. Regular (6-15)'
        ELSE '4. Power user (16+)'
    END                                          AS customer_segment,
    COUNT(*)                                     AS num_customers,
    ROUND(AVG(total_spend), 2)                   AS avg_spend_inr,
    SUM(txn_count)                               AS total_txns_in_segment
FROM customer_txns
GROUP BY customer_segment
ORDER BY customer_segment;

-- Spend by customer age group
SELECT
    customer_age_group,
    COUNT(*)                          AS txn_count,
    ROUND(AVG(amount_inr), 2)         AS avg_amount_inr,
    ROUND(SUM(amount_inr), 2)         AS total_value_inr
FROM transactions
GROUP BY customer_age_group
ORDER BY customer_age_group;

-- -------------------------------------------------------------
-- 9. PAYMENT-CHANNEL PERFORMANCE  (share, success rate, avg ticket)
-- -------------------------------------------------------------
SELECT
    payment_channel,
    COUNT(*)                                                              AS txn_count,
    ROUND(100.0 * COUNT(*) / (SELECT COUNT(*) FROM transactions), 2)      AS volume_share_pct,
    ROUND(SUM(amount_inr), 2)                                             AS total_value_inr,
    ROUND(AVG(amount_inr), 2)                                             AS avg_ticket_size_inr,
    ROUND(100.0 * SUM(CASE WHEN status='Success' THEN 1 ELSE 0 END) / COUNT(*), 2) AS success_rate_pct
FROM transactions
GROUP BY payment_channel
ORDER BY txn_count DESC;
