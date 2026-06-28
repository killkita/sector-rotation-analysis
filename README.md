# S&P 500 Sector Rotation & Recession Prediction (2000–2026)

**Tools:** Python · SQL · SQLite · pandas · scikit-learn · matplotlib · seaborn · yfinance · FRED API  
**Domain:** Macroeconomics · Equity Markets · Predictive Modelling · Monetary Policy

---

## Project Overview

This project investigates whether sector rotation patterns — the tendency for defensive 
sectors to outperform cyclicals ahead of recessions — can be used to predict economic 
regime changes. Using 26 years of S&P 500 sector ETF price data combined with Federal 
Reserve macroeconomic indicators, I designed a relational SQLite database, engineered 
predictive features using SQL window functions and CTEs, and trained a logistic regression 
model to classify recession vs non-recession periods.

---

## The Core Question

**Can the relative performance of defensive versus cyclical sectors predict whether the 
economy is heading into recession — and does this signal hold across different types 
of economic downturns?**

---

## Key Findings

### 1. Defensive Sectors Consistently Outperform Cyclicals During Recessions
Across all three recession periods, a clear rotation pattern emerged — but with important 
differences by crisis type:

- **Dot-Com Recession (2001):** Technology (XLK) lost over 80% of its value while 
  defensive sectors held close to their starting levels — a textbook sector rotation signal
- **Global Financial Crisis (2008):** The most severe drawdown in the dataset. All sectors 
  fell simultaneously, but defensives fell less and recovered faster. XLF (Financials) 
  dropped to 40% of its pre-crisis value — the worst performance of any sector in any recession
- **COVID-19 Recession (2020):** The shortest recession in the dataset (2 months) triggered 
  a sharp universal crash followed by the fastest recovery on record, with technology 
  sectors inverting the usual defensive outperformance pattern entirely

### 2. The Logistic Regression Model Successfully Detected Structural Recessions
A logistic regression model trained on four features — sector rotation signal, yield curve, 
unemployment, and Fed funds rate — produced the following results:

| Recession | Model Signal | Notes |
|---|---|---|
| Dot-Com (2001) | ✅ Detected | Probability above 0.5 throughout 2000–2003 |
| Financial Crisis (2008) | ✅ Detected | Strongest signal, probability peaked above 0.7 |
| COVID-19 (2020) | ❌ Missed | Probability near historic low at onset |

### 3. COVID-19 Was Fundamentally Unpredictable From Market Signals
The model's failure to detect COVID is itself a finding — not a flaw. The pandemic was 
an exogenous shock with no macroeconomic precursors. The yield curve was not inverted, 
unemployment was at historic lows, and cyclicals were outperforming defensives in the 
months before the crash. No model trained on structural recession patterns could have 
anticipated it.

### 4. The Model Flags Rising Recession Risk in 2024–2026
The predicted recession probability has risen from near zero in 2021 back toward 0.5 
by mid-2026, driven by rising unemployment and yield curve movements — an interesting 
live signal that warrants monitoring.

### 5. Long-Run Sector Performance (2000–2026)
| Sector | Category | Avg Monthly Return |
|---|---|---|
| XLC (Communication Services) | Cyclical | 1.122% |
| XLE (Energy) | Cyclical | 0.967% |
| XLK (Technology) | Cyclical | 0.953% |
| XLY (Consumer Discretionary) | Cyclical | 0.929% |
| XLF (Financials) | Cyclical | Lowest — never fully recovered from 2008 |

---

## Technical Implementation

### Database Design
Rather than a single flat table, this project uses a normalised relational schema 
with four linked tables:

```
sectors          prices              indicators          recessions
---------        --------            ----------          ----------
sector_id  ←─── sector_id           date                recession_id
ticker           date                fed_funds_rate      start_date
name             close               yield_curve         end_date
category         volume              unemployment        label
                 return_1m           cpi
```

### Feature Engineering in SQL
The core analytical dataset was built entirely in SQL using:
- **CTEs** to calculate average monthly returns by sector category
- **CASE/PIVOT logic** to create cyclical vs defensive return columns
- **Subquery existence checks** to label recession months
- **Three-table JOINs** across prices, sectors, and indicators

```sql
WITH monthly_category_returns AS (
    SELECT p.date, s.category, AVG(p.return_1m) AS avg_return
    FROM prices p
    JOIN sectors s ON p.sector_id = s.sector_id
    WHERE p.return_1m IS NOT NULL
    GROUP BY p.date, s.category
),
category_pivot AS (
    SELECT date,
        MAX(CASE WHEN category = 'cyclical'  THEN avg_return END) AS cyclical_return,
        MAX(CASE WHEN category = 'defensive' THEN avg_return END) AS defensive_return
    FROM monthly_category_returns
    GROUP BY date
)
...
```

### Model Architecture
- **Algorithm:** Logistic Regression with balanced class weights (scikit-learn)
- **Features:** Rotation signal, yield curve, unemployment rate, Fed funds rate
- **Scaling:** StandardScaler applied before training
- **Train/test split:** Time-based — trained on 2000–2018, tested on 2019–2026
- **Key limitation:** Only 31 recession months in 316 total observations creates 
  class imbalance, addressed via `class_weight="balanced"`

### Environment Notes
- Built on Python 3.11 installed via Homebrew on macOS (system Python 3.9 has 
  a known broken pip on Apple Developer Command Line Tools)
- SQLite absolute paths resolved using `os.path.expanduser()` to avoid 
  notebook-relative path issues
- yfinance multi-level column output handled by explicit column selection 
  and hardcoded sector IDs to avoid foreign key mapping errors

---

## Project Structure

```
sector-rotation-analysis/
├── data/                              # SQLite database and saved charts
│   ├── sector_data.db
│   ├── chart_sector_performance.png
│   ├── chart_recession_comparison.png
│   ├── chart_model_evaluation.png
│   └── chart_recession_probability.png
├── notebooks/
│   ├── 01_verify_data.ipynb           # SQL verification and multi-table joins
│   ├── 02_exploratory_analysis.ipynb  # Sector performance visualisation
│   └── 03_feature_engineering.ipynb   # SQL feature engineering + ML model
├── scripts/
│   ├── create_schema.py               # Relational database schema definition
│   └── ingest.py                      # Data pipeline (yfinance + FRED API)
├── requirements.txt
└── README.md
```

---

## Data Sources

**Yahoo Finance** via `yfinance` — 11 S&P 500 sector ETFs from 2000 to 2026:
XLF, XLE, XLK, XLY, XLI, XLB, XLV, XLP, XLU, XLRE, XLC

**FRED API** — Federal Reserve Economic Data:

| Series ID | Description |
|---|---|
| FEDFUNDS | Federal Funds Effective Rate |
| UNRATE | Unemployment Rate |
| CPIAUCSL | Consumer Price Index |
| GS10 | 10-Year Treasury Yield |
| GS2 | 2-Year Treasury Yield |

**NBER** — Official US recession dates (manually encoded)

---

## How to Run

```bash
# Clone the repo
git clone https://github.com/YOURUSERNAME/sector-rotation-analysis.git
cd sector-rotation-analysis

# Create virtual environment using Python 3.11
/opt/homebrew/bin/python3.11 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Add your FRED API key
echo "FRED_API_KEY=your_key_here" > .env

# Build the database schema
python scripts/create_schema.py

# Run the data pipeline
python scripts/ingest.py

# Open notebooks in order
jupyter notebook
```

---

## Limitations

- Only three recession periods in the dataset limits statistical power
- COVID-19 demonstrates that exogenous shock recessions are inherently 
  unpredictable from market signals alone
- Logistic regression assumes linear relationships between features and 
  recession probability — a more flexible model (Random Forest, XGBoost) 
  may improve detection
- XLRE and XLC have shorter histories (post-2015 and post-2018 respectively) 
  which creates unequal weighting in the rotation signal calculation

---

## Author

**kita** | ~ Data Analyst experimenting with Python ~ 
[GitHub](https://github.com/killkita)