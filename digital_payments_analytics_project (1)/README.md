# Digital Payments Analytics Dashboard

A complete, end-to-end analytics project on a synthetic digital-payments
transaction dataset (UPI, cards, net banking, wallets — modelled on the
Indian payments ecosystem). Demonstrates the full stack:

**Synthetic Data → SQL (SQLite) → Python (pandas) → Interactive Dashboard**

---

## 1. What's inside

```
payments_project/
├── data/
│   ├── synthetic_transactions.csv   # 60,000 generated transactions
│   └── payments.db                  # same data loaded into SQLite
├── sql/
│   ├── 01_schema.sql                # table + indexes
│   └── 02_analysis_queries.sql      # all analysis queries, documented
├── python/
│   ├── 01_generate_data.py          # builds the synthetic dataset
│   ├── 02_load_to_sqlite.py         # CSV -> SQLite using the schema
│   ├── 03_run_analysis.py           # runs every SQL query, exports CSV + JSON
│   ├── 04_visualize.py              # matplotlib charts (static PNGs)
│   └── 05_build_dashboard.py        # injects data into the HTML dashboard
├── outputs/
│   ├── tables/                      # one CSV per analysis query
│   ├── charts/                      # 8 PNG charts
│   ├── dashboard_data.json          # all query results, machine-readable
│   └── dashboard.html               # the final interactive dashboard
├── dashboard/
│   └── template.html                # dashboard HTML/CSS/JS (pre-data-injection)
└── run_all.sh                       # runs the whole pipeline in order
```

Run everything with:
```bash
bash run_all.sh
```

---

## 2. Step-by-step walkthrough

### Step 1 — Generate a realistic synthetic dataset (`01_generate_data.py`)
60,000 transactions across 5,000 customers and 800 merchants, Sep 2025–Aug 2026.
Built so the *patterns* are realistic, not just the row count:
- **Merchant categories** (Grocery, E-commerce, Food Delivery, Travel, etc.) each
  have their own typical ticket size.
- **Payment channels** (UPI, Debit Card, Credit Card, Net Banking, Wallet) each
  have their own base failure rate and fraud rate — UPI is high-volume/low-failure,
  Net Banking is lower-volume/higher-failure, Credit Card carries the highest
  fraud rate.
- **Time patterns**: hour-of-day weighting gives lunchtime and evening peaks;
  day-of-week weighting gives a weekend lift; month weighting gives an
  Oct–Nov festive-season spike.
- **A simulated gateway outage** on one specific day (failure rate jumps to
  ~45%) — deliberately injected so the failure-rate analysis has a real
  anomaly to detect, the way a production dashboard would need to.
- **Fraud logic**: probability increases with transaction amount, late-night
  hours (12am–4am), and certain channels/devices — mirroring how real
  fraud-risk models are reasoned about.
- **Customer skew**: transaction frequency follows a Pareto (power-law)
  distribution, so a small number of customers transact far more than most —
  realistic for any payments platform.

### Step 2 — Load into SQL (`sql/01_schema.sql`, `02_load_to_sqlite.py`)
The CSV is loaded into a single `transactions` fact table in SQLite, indexed
on the columns you'd actually filter/group by in a dashboard (timestamp,
channel, category, state, status, customer). SQLite is used so the whole
project runs with zero external services — the schema and queries are
standard ANSI SQL and port to Postgres/MySQL with minimal changes.

### Step 3 — SQL analysis layer (`sql/02_analysis_queries.sql`, `03_run_analysis.py`)
One query per analysis dimension you asked for:

| # | Dimension | What the query returns |
|---|---|---|
| 1 | Transaction volume | Headline KPIs + monthly count trend |
| 2 | Transaction value | Value by merchant category (total, avg, % share) |
| 3 | Merchant category | Volume, avg ticket, failure %, fraud % per category |
| 4 | Geography | Value/failure/fraud by state; top 10 cities by value |
| 5 | Failure rate | By channel; worst 10 single days (surfaces the outage) |
| 6 | Fraud rate | By channel, by amount bucket, by hour of day |
| 7 | Peak periods | Day-of-week × hour-of-day transaction density |
| 8 | Customer behaviour | Frequency segments (one-time → power user); spend by age group |
| 9 | Channel performance | Volume share, value, avg ticket, success rate per channel |

`03_run_analysis.py` executes each query against SQLite, saves each result
as a CSV under `outputs/tables/`, and assembles everything into one
`dashboard_data.json` — this is the hand-off point from SQL to the
visualization layer.

### Step 4 — Python analysis & visualization (`04_visualize.py`)
Reads the query-result CSVs with pandas and renders 8 static matplotlib
charts (monthly trend, category value, channel failure rate, hourly fraud
curve, peak-period heatmap, customer segmentation, channel share,
geography) — the kind of chart set you'd drop into a slide deck or PDF
report, independent of the interactive dashboard.

### Step 5 — Interactive dashboard (`05_build_dashboard.py`, `dashboard/template.html`)
A single self-contained HTML file (Chart.js for charts, no build step, no
server) that embeds `dashboard_data.json` directly, so it opens and works
offline in any browser. Sections mirror the 9 analyses above: KPI strip,
volume/value trend, category breakdown, geography, failure rate (with the
simulated-outage callout), fraud rate (channel/amount/hour), a peak-period
heatmap, customer segmentation, and a full channel scorecard table.

---

## 3. Key findings from this run

- **~87.3M** total transaction value across **60,000** transactions, avg
  ticket **₹1,456**.
- **Overall failure rate 5.33%**, overall **fraud rate 0.275%**.
- **Net Banking** has the highest failure rate (~7.7%); **UPI** the lowest.
- **Credit Card** has the highest fraud rate — consistent with it carrying
  the largest average ticket size.
- **E-commerce** is the top merchant category by total value.
- Transaction volume peaks **Sunday/Saturday evenings around 7–8pm**, with a
  secondary lunchtime bump.
- One day (a simulated outage) spikes to **~45% failure rate**, clearly
  visible against a normal ~5% baseline — this is the kind of anomaly a
  production dashboard needs to surface immediately.
- Customer base is skewed: a small "power user" segment (16+ transactions)
  accounts for a disproportionate share of total transactions — typical of
  payment-platform usage.

*(All numbers are from the synthetic dataset — a stand-in for a real
transaction warehouse. The pipeline and dashboard are built to be dropped
onto a real dataset with the same column names.)*
