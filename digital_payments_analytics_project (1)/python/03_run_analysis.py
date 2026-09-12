"""
03_run_analysis.py
--------------------
Executes the SQL analysis layer (mirrors ../sql/02_analysis_queries.sql)
against the SQLite database, and:
  1. Saves each result as a CSV in ../outputs/tables/
  2. Assembles everything into one dashboard_data.json consumed by the
     HTML dashboard
  3. Prints a plain-language summary of key findings to the console
"""

import json
import sqlite3
import pandas as pd
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DB_PATH = PROJECT_ROOT / "data" / "payments.db"
OUT_DIR = PROJECT_ROOT / "outputs"
TABLES_DIR = OUT_DIR / "tables"
TABLES_DIR.mkdir(parents=True, exist_ok=True)

conn = sqlite3.connect(DB_PATH)

QUERIES = {

    "kpis": """
        SELECT
            COUNT(*) AS total_transactions,
            SUM(CASE WHEN status='Success' THEN 1 ELSE 0 END) AS successful_transactions,
            ROUND(SUM(amount_inr),2) AS total_value_inr,
            ROUND(AVG(amount_inr),2) AS avg_ticket_size_inr,
            COUNT(DISTINCT customer_id) AS active_customers,
            COUNT(DISTINCT merchant_id) AS active_merchants,
            ROUND(100.0*SUM(CASE WHEN status='Failed' THEN 1 ELSE 0 END)/COUNT(*),2) AS failure_rate_pct,
            ROUND(100.0*SUM(is_fraud)/COUNT(*),3) AS fraud_rate_pct
        FROM transactions;
    """,

    "monthly_trend": """
        SELECT strftime('%Y-%m', ts) AS month, COUNT(*) AS txn_count,
               ROUND(SUM(amount_inr),2) AS txn_value_inr
        FROM transactions GROUP BY month ORDER BY month;
    """,

    "category_value": """
        SELECT merchant_category, COUNT(*) AS txn_count,
               ROUND(SUM(amount_inr),2) AS total_value_inr,
               ROUND(AVG(amount_inr),2) AS avg_value_inr,
               ROUND(100.0*SUM(amount_inr)/(SELECT SUM(amount_inr) FROM transactions),2) AS pct_of_total_value
        FROM transactions GROUP BY merchant_category ORDER BY total_value_inr DESC;
    """,

    "category_performance": """
        SELECT merchant_category, COUNT(*) AS txn_count,
               ROUND(AVG(amount_inr),2) AS avg_amount_inr,
               ROUND(100.0*SUM(CASE WHEN status='Failed' THEN 1 ELSE 0 END)/COUNT(*),2) AS failure_rate_pct,
               ROUND(100.0*SUM(is_fraud)/COUNT(*),3) AS fraud_rate_pct
        FROM transactions GROUP BY merchant_category ORDER BY txn_count DESC;
    """,

    "geography_state": """
        SELECT customer_state, COUNT(*) AS txn_count,
               ROUND(SUM(amount_inr),2) AS total_value_inr,
               ROUND(100.0*SUM(CASE WHEN status='Failed' THEN 1 ELSE 0 END)/COUNT(*),2) AS failure_rate_pct,
               ROUND(100.0*SUM(is_fraud)/COUNT(*),3) AS fraud_rate_pct
        FROM transactions GROUP BY customer_state ORDER BY txn_count DESC;
    """,

    "geography_top_cities": """
        SELECT customer_city, customer_state, COUNT(*) AS txn_count,
               ROUND(SUM(amount_inr),2) AS total_value_inr
        FROM transactions GROUP BY customer_city, customer_state
        ORDER BY total_value_inr DESC LIMIT 10;
    """,

    "failure_by_channel": """
        SELECT payment_channel, COUNT(*) AS txn_count,
               SUM(CASE WHEN status='Failed' THEN 1 ELSE 0 END) AS failed_count,
               ROUND(100.0*SUM(CASE WHEN status='Failed' THEN 1 ELSE 0 END)/COUNT(*),2) AS failure_rate_pct
        FROM transactions GROUP BY payment_channel ORDER BY failure_rate_pct DESC;
    """,

    "failure_worst_days": """
        SELECT date(ts) AS txn_date, COUNT(*) AS txn_count,
               ROUND(100.0*SUM(CASE WHEN status='Failed' THEN 1 ELSE 0 END)/COUNT(*),2) AS failure_rate_pct
        FROM transactions GROUP BY txn_date ORDER BY failure_rate_pct DESC LIMIT 10;
    """,

    "fraud_by_channel": """
        SELECT payment_channel, COUNT(*) AS txn_count, SUM(is_fraud) AS fraud_count,
               ROUND(100.0*SUM(is_fraud)/COUNT(*),3) AS fraud_rate_pct
        FROM transactions GROUP BY payment_channel ORDER BY fraud_rate_pct DESC;
    """,

    "fraud_by_amount_bucket": """
        SELECT CASE
                WHEN amount_inr < 500 THEN '1. <500'
                WHEN amount_inr < 2000 THEN '2. 500-2000'
                WHEN amount_inr < 5000 THEN '3. 2000-5000'
                WHEN amount_inr < 10000 THEN '4. 5000-10000'
                ELSE '5. 10000+' END AS amount_bucket,
               COUNT(*) AS txn_count,
               ROUND(100.0*SUM(is_fraud)/COUNT(*),3) AS fraud_rate_pct
        FROM transactions GROUP BY amount_bucket ORDER BY amount_bucket;
    """,

    "fraud_by_hour": """
        SELECT CAST(strftime('%H', ts) AS INTEGER) AS hour_of_day,
               COUNT(*) AS txn_count,
               ROUND(100.0*SUM(is_fraud)/COUNT(*),3) AS fraud_rate_pct
        FROM transactions GROUP BY hour_of_day ORDER BY hour_of_day;
    """,

    "peak_heatmap": """
        SELECT CASE CAST(strftime('%w', ts) AS INTEGER)
                WHEN 0 THEN '0-Sun' WHEN 1 THEN '1-Mon' WHEN 2 THEN '2-Tue'
                WHEN 3 THEN '3-Wed' WHEN 4 THEN '4-Thu' WHEN 5 THEN '5-Fri'
                WHEN 6 THEN '6-Sat' END AS day_of_week,
               CAST(strftime('%H', ts) AS INTEGER) AS hour_of_day,
               COUNT(*) AS txn_count
        FROM transactions GROUP BY day_of_week, hour_of_day ORDER BY day_of_week, hour_of_day;
    """,

    "customer_segments": """
        WITH customer_txns AS (
            SELECT customer_id, COUNT(*) AS txn_count, SUM(amount_inr) AS total_spend
            FROM transactions GROUP BY customer_id
        )
        SELECT CASE
                WHEN txn_count = 1 THEN '1. One-time (1 txn)'
                WHEN txn_count BETWEEN 2 AND 5 THEN '2. Occasional (2-5)'
                WHEN txn_count BETWEEN 6 AND 15 THEN '3. Regular (6-15)'
                ELSE '4. Power user (16+)' END AS customer_segment,
               COUNT(*) AS num_customers,
               ROUND(AVG(total_spend),2) AS avg_spend_inr,
               SUM(txn_count) AS total_txns_in_segment
        FROM customer_txns GROUP BY customer_segment ORDER BY customer_segment;
    """,

    "spend_by_age_group": """
        SELECT customer_age_group, COUNT(*) AS txn_count,
               ROUND(AVG(amount_inr),2) AS avg_amount_inr,
               ROUND(SUM(amount_inr),2) AS total_value_inr
        FROM transactions GROUP BY customer_age_group ORDER BY customer_age_group;
    """,

    "channel_performance": """
        SELECT payment_channel, COUNT(*) AS txn_count,
               ROUND(100.0*COUNT(*)/(SELECT COUNT(*) FROM transactions),2) AS volume_share_pct,
               ROUND(SUM(amount_inr),2) AS total_value_inr,
               ROUND(AVG(amount_inr),2) AS avg_ticket_size_inr,
               ROUND(100.0*SUM(CASE WHEN status='Success' THEN 1 ELSE 0 END)/COUNT(*),2) AS success_rate_pct
        FROM transactions GROUP BY payment_channel ORDER BY txn_count DESC;
    """,
}

results = {}
for name, query in QUERIES.items():
    df = pd.read_sql_query(query, conn)
    results[name] = df
    df.to_csv(TABLES_DIR / f"{name}.csv", index=False, encoding="utf-8")

conn.close()

# ---------------------------------------------------------------------------
# Assemble dashboard JSON (records orientation, easy to consume in JS)
# ---------------------------------------------------------------------------
dashboard_data = {name: df.to_dict(orient="records") for name, df in results.items()}
with open(OUT_DIR / "dashboard_data.json", "w", encoding="utf-8") as f:
    json.dump(dashboard_data, f, indent=2, default=str)

# ---------------------------------------------------------------------------
# Console summary — plain-language headline findings
# ---------------------------------------------------------------------------
k = results["kpis"].iloc[0]
print("=" * 60)
print("HEADLINE KPIs")
print("=" * 60)
print(f"Total transactions      : {int(k.total_transactions):,}")
print(f"Successful transactions : {int(k.successful_transactions):,}")
print(f"Total value (INR)       : {k.total_value_inr:,.2f}")
print(f"Avg ticket size (INR)   : {k.avg_ticket_size_inr:,.2f}")
print(f"Active customers        : {int(k.active_customers):,}")
print(f"Active merchants        : {int(k.active_merchants):,}")
print(f"Overall failure rate    : {k.failure_rate_pct}%")
print(f"Overall fraud rate      : {k.fraud_rate_pct}%")

print("\nTop merchant category by value:",
      results["category_value"].iloc[0]["merchant_category"])
print("Worst channel by failure rate:",
      results["failure_by_channel"].iloc[0]["payment_channel"],
      f"({results['failure_by_channel'].iloc[0]['failure_rate_pct']}%)")
print("Worst channel by fraud rate:",
      results["fraud_by_channel"].iloc[0]["payment_channel"],
      f"({results['fraud_by_channel'].iloc[0]['fraud_rate_pct']}%)")
print("Worst single day for failures:",
      results["failure_worst_days"].iloc[0]["txn_date"],
      f"({results['failure_worst_days'].iloc[0]['failure_rate_pct']}% failure rate — simulated outage)")

peak = results["peak_heatmap"].sort_values("txn_count", ascending=False).iloc[0]
print(f"Peak transaction slot: {peak['day_of_week']} at {int(peak['hour_of_day'])}:00 "
      f"({int(peak['txn_count'])} txns)")

print(f"\nAll table CSVs written to {TABLES_DIR}")
print(f"Dashboard JSON written to {OUT_DIR / 'dashboard_data.json'}")
