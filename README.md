# S&P 500 Sector Rotation & Recession Prediction (2000–2026)

**Tools:** Python · SQL · SQLite · pandas · scikit-learn · matplotlib · seaborn · yfinance · FRED API  
**Domain:** Macroeconomics · Equity Markets · Predictive Modelling · Monetary Policy

---

## Overview

This project looks at whether sector rotation patterns can be used to predict recessions. The idea is that investors tend to move money from cyclical sectors like technology and financials into defensive sectors like utilities and consumer staples when they sense a downturn coming. If that signal is consistent enough, it should show up in the data before a recession officially begins.

I pulled 26 years of S&P 500 sector ETF price data from Yahoo Finance, combined it with Federal Reserve macroeconomic indicators via the FRED API, and stored everything in a normalised relational SQLite database. From there I used SQL to engineer the features and built a logistic regression model to classify recession versus non-recession periods.

---

## The Question

Can the relative performance of defensive versus cyclical sectors predict whether the economy is heading into recession, and does this signal hold across different types of downturns?

---

## What I Found

### Defensive sectors rotate ahead of recessions, but each crisis is different

The pattern showed up across all three recessions in the dataset but each one played out differently.

During the dot-com crash, technology (XLK) lost over 80% of its value while defensives barely moved. That is the textbook rotation signal working exactly as expected. The 2008 financial crisis was more severe with everything falling simultaneously, but defensives held up better and recovered faster. XLF (Financials) was the standout casualty, dropping to 40% of its pre-crisis value and never fully recovering even by 2026.

COVID was the outlier. It lasted just two months officially, recovery was almost immediate, and technology sectors massively outperformed defensives in the aftermath. The usual recession playbook did not apply.

### The model correctly identified the two structural recessions

A logistic regression model trained on sector rotation signals, the yield curve, unemployment, and the Fed funds rate produced clear signals for the dot-com and 2008 recessions, with predicted probability staying above 0.5 throughout both periods. The 2008 signal was the strongest, peaking above 0.7 at the height of the crisis.

| Recession | Model Signal | Notes |
|---|---|---|
| Dot-Com (2001) | Detected | Probability above 0.5 throughout 2000 to 2003 |
| Financial Crisis (2008) | Detected | Strongest signal, probability peaked above 0.7 |
| COVID-19 (2020) | Missed | Probability near historic low at onset |

### Missing COVID is a finding, not a flaw

The model had no chance of detecting COVID because there were no precursors. The yield curve was not inverted, unemployment was at historic lows, and cyclicals were outperforming defensives in the months before the crash. It was an exogenous shock and no model trained on structural recession patterns could have anticipated it. That distinction matters when interpreting any recession prediction model.

### The model is currently signalling rising risk

By mid-2026 the predicted recession probability has climbed back toward 0.5 after sitting near zero following the COVID recovery. Rising unemployment and yield curve movements are driving the signal, which is worth monitoring.

### Long run sector performance since 2000

Cyclical sectors dominated long run returns despite their recession vulnerability. Technology was the worst performer through the dot-com era but became the strongest over the full 26 year period. Financials were the clear underperformer, weighed down by the 2008 collapse they never fully recovered from.

| Sector | Category | Avg Monthly Return |
|---|---|---|
| XLC Communication Services | Cyclical | 1.122% |
| XLE Energy | Cyclical | 0.967% |
| XLK Technology | Cyclical | 0.953% |
| XLY Consumer Discretionary | Cyclical | 0.929% |
| XLF Financials | Cyclical | Lowest across all sectors |

---

## How It Was Built

### Database design

Instead of dumping everything into one flat table I designed a normalised schema with four linked tables. This made the SQL analysis cleaner and more realistic as a structure you would actually see in a production environment.

```
sectors       prices          indicators        recessions
--------      --------        ----------        ----------
sector_id     sector_id       date              recession_id
ticker        date            fed_funds_rate    start_date
name          close           yield_curve       end_date
category      volume          unemployment      label
              return_1m       cpi
```

### Feature engineering in SQL

The core analytical dataset was built entirely in SQL using CTEs to calculate average monthly returns by sector category, CASE logic to pivot cyclical and defensive returns into separate columns, subquery existence checks to label recession months, and three table JOINs across prices, sectors, and indicators.

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
```

### Model

Logistic regression with balanced class weights via scikit-learn. Features were scaled using StandardScaler before training. The train and test split was time based, training on 2000 to 2018 and testing on 2019 to 2026, to avoid data leakage. Class imbalance was handled with balanced class weights given only 31 recession months out of 316 total observations.

---

## Project Structure

```
sector-rotation-analysis/
├── data/                              
│   ├── sector_data.db
│   ├── chart_sector_performance.png
│   ├── chart_recession_comparison.png
│   ├── chart_model_evaluation.png
│   └── chart_recession_probability.png
├── notebooks/
│   ├── 01_verify_data.ipynb           
│   ├── 02_exploratory_analysis.ipynb  
│   └── 03_feature_engineering.ipynb   
├── scripts/
│   ├── create_schema.py               
│   └── ingest.py                      
├── requirements.txt
└── README.md
```

---

## Data Sources

Yahoo Finance via yfinance for 11 S&P 500 sector ETFs from 2000 to 2026: XLF, XLE, XLK, XLY, XLI, XLB, XLV, XLP, XLU, XLRE, XLC

FRED API for macroeconomic indicators:

| Series ID | Description |
|---|---|
| FEDFUNDS | Federal Funds Effective Rate |
| UNRATE | Unemployment Rate |
| CPIAUCSL | Consumer Price Index |
| GS10 | 10-Year Treasury Yield |
| GS2 | 2-Year Treasury Yield |

NBER official US recession dates encoded manually.

---

## How to Run

```bash
git clone https://github.com/killkita/sector-rotation-analysis.git
cd sector-rotation-analysis

/opt/homebrew/bin/python3.11 -m venv venv
source venv/bin/activate

pip install -r requirements.txt

echo "FRED_API_KEY=your_key_here" > .env

python scripts/create_schema.py
python scripts/ingest.py

jupyter notebook
```

---

## Limitations

Only three recession periods in the dataset limits the statistical power of the model. Logistic regression assumes linear relationships between features and outcomes so a more flexible model like Random Forest or XGBoost would likely improve detection of complex patterns. XLRE and XLC have shorter histories which creates slight unequal weighting in the rotation signal. And as COVID demonstrated, no model trained on structural recessions can anticipate exogenous shocks.

---

## Author

**kita** | ~ Aspiring data analyst experimenting with Python ~
[GitHub](https://github.com/killkita)