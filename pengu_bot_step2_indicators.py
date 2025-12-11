# Step 2: Technical Indicator Engine for PENGU Futures Bot

import pandas as pd
import numpy as np
import ta
from binance.client import Client
from datetime import datetime
import time

# Initialize Binance Client
client = Client()

symbol = "PENGUUSDT"

def fetch_ohlcv(symbol, interval, limit=200):
    klines = client.futures_klines(symbol=symbol, interval=interval, limit=limit)
    df = pd.DataFrame(klines, columns=[
        'timestamp', 'open', 'high', 'low', 'close', 'volume',
        'close_time', 'quote_asset_volume', 'number_of_trades',
        'taker_buy_base_asset_volume', 'taker_buy_quote_asset_volume', 'ignore'])
    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
    df.set_index('timestamp', inplace=True)
    df = df[['open', 'high', 'low', 'close', 'volume']].astype(float)
    return df

# Fetch OHLCV data
entry_df = fetch_ohlcv(symbol, Client.KLINE_INTERVAL_5MINUTE, limit=150)
filter_df = fetch_ohlcv(symbol, Client.KLINE_INTERVAL_15MINUTE, limit=150)
direction_df = fetch_ohlcv(symbol, Client.KLINE_INTERVAL_1HOUR, limit=150)

# --- Entry Indicators (5m) ---
entry_df['rsi'] = ta.momentum.RSIIndicator(entry_df['close'], window=14).rsi()
entry_df['macd'] = ta.trend.MACD(entry_df['close']).macd_diff()
bb = ta.volatility.BollingerBands(entry_df['close'], window=20, window_dev=2)
entry_df['bb_upper'] = bb.bollinger_hband()
entry_df['bb_lower'] = bb.bollinger_lband()

# --- VWAP (15m) ---
filter_df['vwap'] = (filter_df['close'] * filter_df['volume']).cumsum() / filter_df['volume'].cumsum()

# --- ADX (1h) ---
adx = ta.trend.ADXIndicator(direction_df['high'], direction_df['low'], direction_df['close'], window=14)
direction_df['adx'] = adx.adx()

# --- Combine Last N Rows ---
rows_to_export = 50  # INCREASED for better analysis
combined_df = pd.concat([
    entry_df[['open', 'high', 'low', 'close', 'rsi', 'macd', 'bb_upper', 'bb_lower']].tail(rows_to_export).rename(columns=lambda x: f'entry_{x}'),
    filter_df[['vwap']].tail(rows_to_export).rename(columns=lambda x: f'filter_{x}'),
    direction_df[['adx']].tail(rows_to_export).rename(columns=lambda x: f'direction_{x}')
], axis=1)

# Export preview
print("\n✅ Exported Combined Data Preview:")
print(combined_df.tail())

# Save to CSV
combined_df.to_csv("pengu_data_indicators.csv")
print("✅ pengu_data_indicators.csv saved successfully with", len(combined_df), "rows.")




