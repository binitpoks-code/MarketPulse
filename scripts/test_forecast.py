import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

print("step 1: importing prophet...", flush=True)
from prophet import Prophet
print("step 1: done", flush=True)

print("step 2: fitting a tiny prophet model...", flush=True)
import pandas as pd
import numpy as np
df = pd.DataFrame({
    "ds": pd.date_range("2024-01-01", periods=60, freq="D"),
    "y": np.random.randn(60).cumsum() + 100,
    "sentiment": np.random.randn(60) * 0.1,
})
m = Prophet(weekly_seasonality=True, yearly_seasonality=False, daily_seasonality=False)
m.add_regressor("sentiment")
m.fit(df)
print("step 2: done", flush=True)

print("step 3: fetching yahoo history...", flush=True)
from ingestion.yahoo import fetch_history_all
data = fetch_history_all(tickers=["AAPL"], period="3mo")
print(f"step 3: done - {len(data.get('AAPL', []))} rows", flush=True)

print("ALL GOOD - forecast pipeline is functional", flush=True)
