"""
04_visualize.py
-----------------
Produces a set of static charts (PNG) straight from pandas/matplotlib,
independent of the HTML dashboard — this is the "Python visualization"
deliverable you'd attach to a report or slide deck.
"""

import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
TABLES_DIR = PROJECT_ROOT / "outputs" / "tables"
CHARTS_DIR = PROJECT_ROOT / "outputs" / "charts"
CHARTS_DIR.mkdir(parents=True, exist_ok=True)

plt.rcParams.update({"figure.dpi": 110, "font.size": 10, "axes.spines.top": False, "axes.spines.right": False})

def savefig(name):
    plt.tight_layout()
    plt.savefig(CHARTS_DIR / name, bbox_inches="tight")
    plt.close()
    print("saved", name)

# 1. Monthly volume & value trend
df = pd.read_csv(TABLES_DIR / "monthly_trend.csv", encoding="utf-8")
fig, ax1 = plt.subplots(figsize=(8, 4))
ax2 = ax1.twinx()
ax1.bar(df["month"], df["txn_count"], color="#4C6EF5", alpha=0.75, label="Txn count")
ax2.plot(df["month"], df["txn_value_inr"] / 1e6, color="#F76707", marker="o", label="Value (₹ Mn)")
ax1.set_ylabel("Transaction count")
ax2.set_ylabel("Transaction value (₹ Millions)")
ax1.set_title("Monthly Transaction Volume & Value")
plt.xticks(rotation=45)
savefig("01_monthly_trend.png")

# 2. Value by merchant category
df = pd.read_csv(TABLES_DIR / "category_value.csv", encoding="utf-8").sort_values("total_value_inr")
plt.figure(figsize=(7, 4.5))
plt.barh(df["merchant_category"], df["total_value_inr"] / 1e6, color="#2F9E44")
plt.xlabel("Total value (₹ Millions)")
plt.title("Transaction Value by Merchant Category")
savefig("02_category_value.png")

# 3. Failure rate by payment channel
df = pd.read_csv(TABLES_DIR / "failure_by_channel.csv", encoding="utf-8").sort_values("failure_rate_pct")
plt.figure(figsize=(6, 4))
colors = ["#2F9E44" if v < 5 else "#F08C00" if v < 7 else "#E03131" for v in df["failure_rate_pct"]]
plt.barh(df["payment_channel"], df["failure_rate_pct"], color=colors)
plt.xlabel("Failure rate (%)")
plt.title("Failure Rate by Payment Channel")
savefig("03_failure_by_channel.png")

# 4. Fraud rate by hour of day
df = pd.read_csv(TABLES_DIR / "fraud_by_hour.csv", encoding="utf-8")
plt.figure(figsize=(8, 4))
plt.plot(df["hour_of_day"], df["fraud_rate_pct"], color="#E03131", marker="o")
plt.fill_between(df["hour_of_day"], df["fraud_rate_pct"], color="#E03131", alpha=0.15)
plt.xlabel("Hour of day")
plt.ylabel("Fraud rate (%)")
plt.title("Fraud Rate by Hour of Day (late-night spike)")
plt.xticks(range(0, 24, 2))
savefig("04_fraud_by_hour.png")

# 5. Peak period heatmap (day of week x hour)
df = pd.read_csv(TABLES_DIR / "peak_heatmap.csv", encoding="utf-8")
pivot = df.pivot(index="day_of_week", columns="hour_of_day", values="txn_count").sort_index()
plt.figure(figsize=(10, 4.5))
plt.imshow(pivot.values, aspect="auto", cmap="YlOrRd")
plt.colorbar(label="Transaction count")
plt.yticks(range(len(pivot.index)), [d.split("-")[1] for d in pivot.index])
plt.xticks(range(0, 24, 2), range(0, 24, 2))
plt.xlabel("Hour of day")
plt.title("Peak Transaction Periods — Day of Week x Hour Heatmap")
savefig("05_peak_heatmap.png")

# 6. Customer segments
df = pd.read_csv(TABLES_DIR / "customer_segments.csv", encoding="utf-8")
plt.figure(figsize=(6, 6))
plt.pie(df["num_customers"], labels=[s.split(". ")[1] for s in df["customer_segment"]],
        autopct="%1.1f%%", colors=["#adb5bd", "#748ffc", "#4263eb", "#1864ab"], startangle=90)
plt.title("Customer Segmentation by Transaction Frequency")
savefig("06_customer_segments.png")

# 7. Payment channel performance (volume share)
df = pd.read_csv(TABLES_DIR / "channel_performance.csv", encoding="utf-8")
plt.figure(figsize=(6, 6))
plt.pie(df["txn_count"], labels=df["payment_channel"], autopct="%1.1f%%",
        colors=["#4C6EF5", "#2F9E44", "#F08C00", "#E8590C", "#7048E8"], startangle=90)
plt.title("Payment Channel Volume Share")
savefig("07_channel_share.png")

# 8. Geography - top states by value
df = pd.read_csv(TABLES_DIR / "geography_state.csv", encoding="utf-8").sort_values("total_value_inr").tail(10)
plt.figure(figsize=(7, 4.5))
plt.barh(df["customer_state"], df["total_value_inr"] / 1e6, color="#1971C2")
plt.xlabel("Total value (₹ Millions)")
plt.title("Top 10 States by Transaction Value")
savefig("08_geography_states.png")

# 9. Fraud rate by channel
df = pd.read_csv(TABLES_DIR / "fraud_by_channel.csv", encoding="utf-8").sort_values("fraud_rate_pct")
plt.figure(figsize=(6, 4))
plt.barh(df["payment_channel"], df["fraud_rate_pct"], color="#E03131")
plt.xlabel("Fraud rate (%)")
plt.title("Fraud Rate by Payment Channel")
savefig("09_fraud_by_channel.png")

# 10. Fraud rate by amount bucket
df = pd.read_csv(TABLES_DIR / "fraud_by_amount_bucket.csv", encoding="utf-8")
plt.figure(figsize=(8, 4))
plt.bar(df["amount_bucket"], df["fraud_rate_pct"], color="#E03131", alpha=0.8)
plt.ylabel("Fraud rate (%)")
plt.title("Fraud Rate by Amount Bucket")
savefig("10_fraud_by_amount.png")

# 11. Avg transaction value by age group
df = pd.read_csv(TABLES_DIR / "spend_by_age_group.csv", encoding="utf-8")
plt.figure(figsize=(8, 4))
plt.bar(df["customer_age_group"], df["avg_amount_inr"], color="#4C6EF5", alpha=0.8)
plt.ylabel("Avg value (₹)")
plt.title("Average Transaction Value by Age Group")
savefig("11_spend_by_age.png")

print(f"\nAll charts saved to {CHARTS_DIR}")
