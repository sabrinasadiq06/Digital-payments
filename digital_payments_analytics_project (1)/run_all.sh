#!/usr/bin/env bash
# Runs the full Digital Payments Analytics pipeline end-to-end:
# synthetic data -> SQLite (SQL) -> pandas analysis -> charts -> dashboard
set -e
cd "$(dirname "$0")/python"

echo "[1/5] Generating synthetic transaction data..."
python3 01_generate_data.py

echo "[2/5] Loading data into SQLite (SQL schema)..."
python3 02_load_to_sqlite.py

echo "[3/5] Running SQL analysis queries..."
python3 03_run_analysis.py

echo "[4/5] Generating matplotlib charts..."
python3 04_visualize.py

echo "[5/5] Building interactive HTML dashboard..."
python3 05_build_dashboard.py

echo ""
echo "Done. Open ../outputs/dashboard.html in a browser to view the dashboard."
