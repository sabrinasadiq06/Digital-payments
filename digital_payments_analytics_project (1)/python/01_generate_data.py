"""
01_generate_data.py
--------------------
Generates a synthetic digital-payments transaction dataset that mimics
real-world patterns you'd see in a UPI/card/wallet payments system
(volume seasonality, channel-specific failure & fraud rates, geography,
merchant categories, time-of-day peaks, repeat-customer behaviour).

Output: ../data/synthetic_transactions.csv
"""

import numpy as np
import pandas as pd
from datetime import datetime, timedelta

RNG = np.random.default_rng(42)
N_TXNS = 60000
N_CUSTOMERS = 5000
N_MERCHANTS = 800

# ---------------------------------------------------------------------------
# 1. Reference data (dimensions)
# ---------------------------------------------------------------------------
MERCHANT_CATEGORIES = {
    # category: (weight, mean_amount, std_amount)
    "Grocery":          (0.18,  650,  350),
    "Food Delivery":    (0.15,  350,  200),
    "E-commerce":       (0.16, 1800, 1600),
    "Fuel":             (0.08, 1200,  500),
    "Utilities":        (0.09,  950,  450),
    "Travel":           (0.05, 4200, 3200),
    "Entertainment":    (0.08,  500,  300),
    "Healthcare":       (0.06, 1600, 1200),
    "Fashion":          (0.08, 1900, 1400),
    "Education":        (0.03, 5200, 3800),
    "Financial Services":(0.04, 3000, 2500),
}

PAYMENT_CHANNELS = {
    # channel: (weight, base_failure_rate, base_fraud_rate)
    "UPI":            (0.46, 0.035, 0.0020),
    "Debit Card":     (0.18, 0.055, 0.0028),
    "Credit Card":    (0.16, 0.045, 0.0045),
    "Net Banking":    (0.10, 0.070, 0.0012),
    "Wallet":         (0.10, 0.040, 0.0022),
}

CITIES = {
    # city: (weight, state)
    "Mumbai":     (0.11, "Maharashtra"),
    "Pune":       (0.06, "Maharashtra"),
    "Sangli":     (0.02, "Maharashtra"),
    "Delhi":      (0.10, "Delhi"),
    "Bengaluru":  (0.11, "Karnataka"),
    "Hyderabad":  (0.07, "Telangana"),
    "Chennai":    (0.07, "Tamil Nadu"),
    "Kolkata":    (0.06, "West Bengal"),
    "Ahmedabad":  (0.06, "Gujarat"),
    "Jaipur":     (0.04, "Rajasthan"),
    "Lucknow":    (0.04, "Uttar Pradesh"),
    "Chandigarh": (0.03, "Punjab"),
    "Kochi":      (0.04, "Kerala"),
    "Indore":     (0.04, "Madhya Pradesh"),
    "Nagpur":     (0.03, "Maharashtra"),
    "Surat":      (0.03, "Gujarat"),
    "Bhopal":     (0.02, "Madhya Pradesh"),
    "Patna":      (0.03, "Bihar"),
    "Coimbatore": (0.02, "Tamil Nadu"),
    "Guwahati":   (0.02, "Assam"),
}

DEVICE_TYPES = {"Mobile App": 0.68, "Mobile Web": 0.12, "Desktop Web": 0.14, "POS Terminal": 0.06}
AGE_GROUPS = {"18-24": 0.16, "25-34": 0.34, "35-44": 0.24, "45-54": 0.15, "55+": 0.11}

START_DATE = datetime(2025, 9, 1)
END_DATE = datetime(2026, 8, 31, 23, 59, 59)
TOTAL_DAYS = (END_DATE - START_DATE).days + 1

def weighted_choice(d, size):
    keys = list(d.keys())
    weights = np.array([v[0] if isinstance(v, tuple) else v for v in d.values()], dtype=float)
    weights = weights / weights.sum()
    idx = RNG.choice(len(keys), size=size, p=weights)
    return np.array(keys)[idx]

# ---------------------------------------------------------------------------
# 2. Customers & merchants (with skewed activity -> some customers/merchants
#    transact far more than others, like real payment platforms)
# ---------------------------------------------------------------------------
customer_ids = [f"CUST{str(i).zfill(6)}" for i in range(1, N_CUSTOMERS + 1)]
customer_activity_weight = RNG.pareto(a=1.8, size=N_CUSTOMERS) + 0.1
customer_activity_weight = customer_activity_weight / customer_activity_weight.sum()
customer_age = weighted_choice(AGE_GROUPS, N_CUSTOMERS)
customer_signup_offset = RNG.integers(0, 900, size=N_CUSTOMERS)  # days before window start
customer_home_city = weighted_choice(CITIES, N_CUSTOMERS)

merchant_ids = [f"MERCH{str(i).zfill(5)}" for i in range(1, N_MERCHANTS + 1)]
merchant_category_assign = weighted_choice(MERCHANT_CATEGORIES, N_MERCHANTS)
merchant_activity_weight = RNG.pareto(a=1.5, size=N_MERCHANTS) + 0.1
merchant_activity_weight = merchant_activity_weight / merchant_activity_weight.sum()

# ---------------------------------------------------------------------------
# 3. Day-level seasonality: weekday/weekend + festive season bump (Oct-Nov)
#    + a payments-outage incident day (illustrates failure-rate spike analysis)
# ---------------------------------------------------------------------------
day_dates = [START_DATE + timedelta(days=i) for i in range(TOTAL_DAYS)]
day_weight = []
for d in day_dates:
    w = 1.0
    if d.weekday() >= 5:          # weekend
        w *= 1.20
    if d.month in (10, 11):       # festive season (Diwali shopping window)
        w *= 1.45
    if d.month == 12 and d.day <= 5:
        w *= 1.15                 # month-start salary/utility bills
    if d.month == 1 and d.day == 1:
        w *= 1.3                  # New Year spend
    day_weight.append(w)
day_weight = np.array(day_weight)
day_weight = day_weight / day_weight.sum()

INCIDENT_DATE = datetime(2026, 3, 14).date()  # simulated gateway-outage day

# Hour-of-day weights: morning trickle, lunch peak, evening peak (typical UPI/food pattern)
hour_weight = np.array([
    0.3,0.2,0.15,0.1,0.1,0.2,0.5,1.0,      # 0-7
    1.6,1.9,1.7,1.6,2.1,2.3,1.8,1.5,       # 8-15
    1.6,1.9,2.4,2.8,2.6,2.1,1.4,0.7        # 16-23
])
hour_weight = hour_weight / hour_weight.sum()

# ---------------------------------------------------------------------------
# 4. Generate transactions
# ---------------------------------------------------------------------------
cust_idx = RNG.choice(N_CUSTOMERS, size=N_TXNS, p=customer_activity_weight)
merch_idx = RNG.choice(N_MERCHANTS, size=N_TXNS, p=merchant_activity_weight)
day_idx = RNG.choice(TOTAL_DAYS, size=N_TXNS, p=day_weight)
hour_idx = RNG.choice(24, size=N_TXNS, p=hour_weight)
minute = RNG.integers(0, 60, size=N_TXNS)
second = RNG.integers(0, 60, size=N_TXNS)

txn_dates = np.array(day_dates, dtype=object)[day_idx]
timestamps = [
    txn_dates[i] + timedelta(hours=int(hour_idx[i]), minutes=int(minute[i]), seconds=int(second[i]))
    for i in range(N_TXNS)
]

merch_categories = merchant_category_assign[merch_idx]
channels = weighted_choice(PAYMENT_CHANNELS, N_TXNS)
customer_cities = customer_home_city[cust_idx]

# amount depends on merchant category (log-normal-ish via normal-on-log)
cat_mean = np.array([MERCHANT_CATEGORIES[c][1] for c in merch_categories])
cat_std = np.array([MERCHANT_CATEGORIES[c][2] for c in merch_categories])
raw_amount = RNG.normal(loc=cat_mean, scale=cat_std)
amount = np.clip(raw_amount, 20, None).round(2)

device_type = weighted_choice(DEVICE_TYPES, N_TXNS)
age_group = customer_age[cust_idx]

# ---------------------------------------------------------------------------
# 5. Status (Success / Failed) — channel base rate + amount effect + incident day
# ---------------------------------------------------------------------------
base_fail = np.array([PAYMENT_CHANNELS[c][1] for c in channels])
amount_effect = np.clip((amount - 2000) / 40000, 0, 0.05)  # bigger txns fail slightly more
hour_effect = np.where((hour_idx >= 19) & (hour_idx <= 21), 0.01, 0.0)  # evening network load
is_incident_day = np.array([ts.date() == INCIDENT_DATE for ts in timestamps])
incident_effect = np.where(is_incident_day, 0.35, 0.0)  # simulated outage spike

fail_prob = np.clip(base_fail + amount_effect + hour_effect + incident_effect, 0, 0.9)
status = np.where(RNG.random(N_TXNS) < fail_prob, "Failed", "Success")

# ---------------------------------------------------------------------------
# 6. Fraud flag — only meaningful on transactions that *attempted* (mostly
#    tagged on Success/Failed both, as fraud systems screen all attempts)
#    Higher for: high amount, odd late-night hour, credit card, new device
# ---------------------------------------------------------------------------
base_fraud = np.array([PAYMENT_CHANNELS[c][2] for c in channels])
odd_hour_effect = np.where((hour_idx >= 0) & (hour_idx <= 4), 0.004, 0.0)
high_amount_effect = np.where(amount > 8000, 0.006, 0.0)
new_device_effect = np.where(device_type == "Desktop Web", 0.0008, 0.0)
fraud_prob = np.clip(base_fraud + odd_hour_effect + high_amount_effect + new_device_effect, 0, 0.2)
is_fraud = RNG.random(N_TXNS) < fraud_prob

txn_id = [f"TXN{str(i).zfill(8)}" for i in range(1, N_TXNS + 1)]

df = pd.DataFrame({
    "transaction_id": txn_id,
    "timestamp": timestamps,
    "customer_id": np.array(customer_ids)[cust_idx],
    "customer_age_group": age_group,
    "customer_city": customer_cities,
    "customer_state": [CITIES[c][1] for c in customer_cities],
    "merchant_id": np.array(merchant_ids)[merch_idx],
    "merchant_category": merch_categories,
    "payment_channel": channels,
    "device_type": device_type,
    "amount_inr": amount,
    "status": status,
    "is_fraud": is_fraud,
})

df = df.sort_values("timestamp").reset_index(drop=True)
df["timestamp"] = pd.to_datetime(df["timestamp"])

from pathlib import Path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)
out_path = DATA_DIR / "synthetic_transactions.csv"
df.to_csv(out_path, index=False, encoding="utf-8")

print(f"Generated {len(df):,} transactions -> {out_path}")
print(df["status"].value_counts(normalize=True).round(4))
print("Fraud rate:", round(df["is_fraud"].mean() * 100, 3), "%")
print(df.head(3).to_string())
