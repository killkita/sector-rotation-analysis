# scripts/ingest.py

import os
import pandas as pd
import yfinance as yf
from fredapi import Fred
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

load_dotenv()

engine = create_engine(
    f"sqlite:///{os.path.expanduser('~/sector-rotation-analysis/data/sector_data.db')}"
)

# ── 1. Populate SECTORS table ─────────────────────────────────────────────────
print("Populating sectors table...")

sectors_data = pd.DataFrame([
    {"sector_id": 1,  "ticker": "XLF",  "name": "Financials",             "category": "cyclical"},
    {"sector_id": 2,  "ticker": "XLE",  "name": "Energy",                 "category": "cyclical"},
    {"sector_id": 3,  "ticker": "XLK",  "name": "Technology",             "category": "cyclical"},
    {"sector_id": 4,  "ticker": "XLY",  "name": "Consumer Discretionary", "category": "cyclical"},
    {"sector_id": 5,  "ticker": "XLI",  "name": "Industrials",            "category": "cyclical"},
    {"sector_id": 6,  "ticker": "XLB",  "name": "Materials",              "category": "cyclical"},
    {"sector_id": 7,  "ticker": "XLV",  "name": "Healthcare",             "category": "defensive"},
    {"sector_id": 8,  "ticker": "XLP",  "name": "Consumer Staples",       "category": "defensive"},
    {"sector_id": 9,  "ticker": "XLU",  "name": "Utilities",              "category": "defensive"},
    {"sector_id": 10, "ticker": "XLRE", "name": "Real Estate",            "category": "defensive"},
    {"sector_id": 11, "ticker": "XLC",  "name": "Communication Services", "category": "cyclical"},
])

sectors_data.to_sql("sectors", con=engine, if_exists="replace", index=False)
print(f"  ✓ {len(sectors_data)} sectors inserted")

# ── 2. Populate PRICES table ──────────────────────────────────────────────────
print("\nDownloading sector price data from Yahoo Finance...")

all_prices = []

for _, row in sectors_data.iterrows():
    ticker = row["ticker"]
    sector_id = row["sector_id"]
    print(f"  Fetching {ticker}...")

    data = yf.download(ticker, start="2000-01-01", auto_adjust=True, progress=False)
    data = data[["Close", "Volume"]].copy()
    data.columns = ["close", "volume"]
    data.index.name = "date"
    data = data.resample("MS").first()
    data["return_1m"] = data["close"].pct_change() * 100
    data["sector_id"] = sector_id
    data = data.reset_index()
    all_prices.append(data)

prices_df = pd.concat(all_prices, ignore_index=True)
prices_df["date"] = pd.to_datetime(prices_df["date"]).dt.date
prices_df = prices_df[["sector_id", "date", "close", "volume", "return_1m"]]
prices_df.to_sql("prices", con=engine, if_exists="replace", index=False)
print(f"  ✓ {len(prices_df)} price rows inserted")

# ── 3. Populate INDICATORS table ──────────────────────────────────────────────
print("\nDownloading macro indicators from FRED...")

fred = Fred(api_key=os.getenv("FRED_API_KEY"))

series = {
    "fed_funds_rate": "FEDFUNDS",
    "unemployment":   "UNRATE",
    "cpi":            "CPIAUCSL",
}

frames = []
for col, series_id in series.items():
    print(f"  Fetching {series_id}...")
    data = fred.get_series(series_id, observation_start="2000-01-01")
    frames.append(data.rename(col))

print("  Fetching yield curve...")
t10 = fred.get_series("GS10", observation_start="2000-01-01").rename("t10")
t2  = fred.get_series("GS2",  observation_start="2000-01-01").rename("t2")
frames.extend([t10, t2])

indicators_df = pd.concat(frames, axis=1)
indicators_df = indicators_df.resample("MS").mean()
indicators_df["yield_curve"] = indicators_df["t10"] - indicators_df["t2"]
indicators_df = indicators_df.drop(columns=["t10", "t2"])
indicators_df.index.name = "date"
indicators_df = indicators_df.reset_index()
indicators_df["date"] = pd.to_datetime(indicators_df["date"]).dt.date
indicators_df.to_sql("indicators", con=engine, if_exists="replace", index=False)
print(f"  ✓ {len(indicators_df)} indicator rows inserted")

# ── 4. Populate RECESSIONS table ──────────────────────────────────────────────
print("\nPopulating recessions table...")

recessions_data = pd.DataFrame([
    {"start_date": "2001-03-01", "end_date": "2001-11-01", "label": "Dot-Com Recession"},
    {"start_date": "2007-12-01", "end_date": "2009-06-01", "label": "Global Financial Crisis"},
    {"start_date": "2020-02-01", "end_date": "2020-04-01", "label": "COVID-19 Recession"},
])

recessions_data.to_sql("recessions", con=engine, if_exists="replace", index=False)
print(f"  ✓ {len(recessions_data)} recession periods inserted")

print("\n✓ All tables populated successfully")