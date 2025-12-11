# Step 1: Base Bot Setup - PENGU Futures Trading Bot

import pandas as pd
import numpy as np
import requests
import time
from datetime import datetime

# --------------- CONFIG -----------------
SYMBOL = "PENGUUSDT"
INTERVALS = {
    "entry": "5m",       # 5-minute for scalping entries
    "filter": "15m",      # 15-minute for trend filter
    "direction": "1h"     # 1-hour for macro trend
}
LIMIT = 500
DATA_SOURCE = "binance"

# --------------- DATA FETCH FUNCTION -----------------
def fetch_ohlcv(interval):
    api_url = f"https://api.binance.com/api/v3/klines?symbol={SYMBOL}&interval={interval}&limit={LIMIT}"
    try:
        response = requests.get(api_url)
        response.raise_for_status()
        data = response.json()

        df = pd.DataFrame(data, columns=[
            "timestamp", "open", "high", "low", "close", "volume",
            "close_time", "quote_asset_volume", "number_of_trades",
            "taker_buy_base_vol", "taker_buy_quote_vol", "ignore"
        ])

        df = df[["timestamp", "open", "high", "low", "close", "volume"]]
        df.columns = ["timestamp", "open", "high", "low", "close", "volume"]

        df[["open", "high", "low", "close", "volume"]] = df[["open", "high", "low", "close", "volume"]].astype(float)
        df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms")
        df.set_index("timestamp", inplace=True)

        return df

    except Exception as e:
        print(f"Error fetching OHLCV ({interval}) data: {e}")
        return pd.DataFrame()

# --------------- MAIN LOOP (Preview) -----------------
if __name__ == "__main__":
    while True:
        print("\nFetching OHLCV data for multi-timeframe analysis...")
        entry_df = fetch_ohlcv(INTERVALS["entry"])
        filter_df = fetch_ohlcv(INTERVALS["filter"])
        direction_df = fetch_ohlcv(INTERVALS["direction"])

        if not entry_df.empty:
            print("\nLatest ENTRY (5m) candles:")
            print(entry_df.tail(5))

        if not filter_df.empty:
            print("\nLatest FILTER (15m) candles:")
            print(filter_df.tail(2))

        if not direction_df.empty:
            print("\nLatest DIRECTION (1h) candles:")
            print(direction_df.tail(2))

        time.sleep(60)
