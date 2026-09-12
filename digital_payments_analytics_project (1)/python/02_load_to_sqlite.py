"""
02_load_to_sqlite.py
---------------------
Loads the synthetic transactions CSV into a SQLite database using the
schema in ../sql/01_schema.sql. This mimics the "load" step of an
ETL pipeline feeding a payments analytics warehouse.
"""

import sqlite3
import pandas as pd
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
CSV_PATH = PROJECT_ROOT / "data" / "synthetic_transactions.csv"
DB_PATH = PROJECT_ROOT / "data" / "payments.db"
SCHEMA_PATH = PROJECT_ROOT / "sql" / "01_schema.sql"

df = pd.read_csv(CSV_PATH, parse_dates=["timestamp"], encoding="utf-8")
df["is_fraud"] = df["is_fraud"].astype(int)
df = df.rename(columns={"timestamp": "ts"})

conn = sqlite3.connect(DB_PATH)
with open(SCHEMA_PATH, encoding="utf-8") as f:
    conn.executescript(f.read())

df.to_sql("transactions", conn, if_exists="append", index=False)
conn.commit()

count = conn.execute("SELECT COUNT(*) FROM transactions").fetchone()[0]
print(f"Loaded {count:,} rows into {DB_PATH}")

conn.close()
