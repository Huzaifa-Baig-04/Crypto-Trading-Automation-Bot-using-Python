import pandas as pd
import numpy as np
from binance.client import Client
from datetime import datetime
import ta

# === CONFIG ===
SYMBOL = "PENGUUSDT"
INTERVAL = Client.KLINE_INTERVAL_5MINUTE
LIMIT = 1000
PAGES = 5
API_KEY = "YOUR_API_KEY"
API_SECRET = "YOUR_API_SECRET"

RSI_THRESHOLD = 30
ADX_THRESHOLD = 20
STOP_LOSS = 0.02
TAKE_PROFIT = 0.03

# === INIT CLIENT ===
client = Client(api_key=API_KEY, api_secret=API_SECRET)

# === PAGINATED FETCH ===
def fetch_historical_ohlcv(symbol, interval, limit, pages):
    all_data = []
    end_time = None
    for _ in range(pages):
        klines = client.futures_klines(symbol=symbol, interval=interval, limit=limit, endTime=end_time)
        if not klines:
            break
        all_data += klines
        end_time = klines[0][0]
    df = pd.DataFrame(all_data, columns=[
        'timestamp', 'open', 'high', 'low', 'close', 'volume',
        'close_time', 'quote_asset_volume', 'number_of_trades',
        'taker_buy_base_asset_volume', 'taker_buy_quote_asset_volume', 'ignore'
    ])
    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
    df.set_index('timestamp', inplace=True)
    df = df[['open', 'high', 'low', 'close', 'volume']].astype(float)
    return df.sort_index()

# === STRATEGY ===
def apply_indicators(df):
    df['rsi'] = ta.momentum.RSIIndicator(df['close'], window=14).rsi()
    macd = ta.trend.MACD(df['close'])
    df['macd'] = macd.macd_diff()
    df['vwap'] = (df['close'] * df['volume']).cumsum() / df['volume'].cumsum()
    adx = ta.trend.ADXIndicator(df['high'], df['low'], df['close'], window=14)
    df['adx'] = adx.adx()
    return df.dropna()

# === BACKTEST ===
def backtest(df):
    balance = 1000
    position = None
    entry_price = 0
    wins, losses = 0, 0
    returns = []
    logs = []

    for i in range(1, len(df)):
        row, prev = df.iloc[i], df.iloc[i - 1]
        score = 0

        if prev['macd'] > 0: score += 1
        if prev['rsi'] < RSI_THRESHOLD: score += 1
        if prev['close'] < prev['vwap']: score += 1
        if prev['adx'] > ADX_THRESHOLD: score += 1

        if position is None and score >= 3:
            position = 'LONG'
            entry_price = row['close']
            logs.append(f"[BUY] @ {entry_price:.4f} on {df.index[i]}")
        elif position == 'LONG':
            change = (row['close'] - entry_price) / entry_price
            if change >= TAKE_PROFIT or change <= -STOP_LOSS or i == len(df) - 1:
                pnl = change
                balance *= (1 + pnl)
                result = "✅ WIN" if pnl > 0 else "❌ LOSS"
                logs.append(f"[SELL] @ {row['close']:.4f} | PNL: {pnl*100:.2f}% | Balance: ${balance:.2f} | {result}")
                returns.append(pnl)
                wins += pnl > 0
                losses += pnl <= 0
                position = None

    # === STATS ===
    win_rate = (wins / (wins + losses)) * 100 if wins + losses > 0 else 0
    avg_return = np.mean([r * 100 for r in returns]) if returns else 0

    print("\n".join(logs))
    print(f"\nFinal Balance: ${balance:.2f}")
    print(f"Win Rate: {win_rate:.2f}%")
    print(f"Average Return: {avg_return:.2f}%")

# === RUN ===
if __name__ == "__main__":
    df = fetch_historical_ohlcv(SYMBOL, INTERVAL, LIMIT, PAGES)
    df = apply_indicators(df)
    backtest(df)


