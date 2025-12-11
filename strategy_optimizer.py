
import pandas as pd
import numpy as np
import ta
from binance.client import Client
from datetime import datetime

# === CONFIG ===
SYMBOL = "PENGUUSDT"
INTERVAL = Client.KLINE_INTERVAL_5MINUTE
LIMIT = 1000
API_KEY = "YOUR_API_KEY"
API_SECRET = "YOUR_API_SECRET"

STOP_LOSS_PCT = -2
TAKE_PROFIT_PCT = 3

client = Client(api_key=API_KEY, api_secret=API_SECRET)

def fetch_historical_ohlcv(symbol, interval, limit):
    klines = client.futures_klines(symbol=symbol, interval=interval, limit=limit)
    df = pd.DataFrame(klines, columns=[
        'timestamp', 'open', 'high', 'low', 'close', 'volume',
        'close_time', 'quote_asset_volume', 'number_of_trades',
        'taker_buy_base_asset_volume', 'taker_buy_quote_asset_volume', 'ignore'
    ])
    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
    df.set_index('timestamp', inplace=True)
    df = df[['open', 'high', 'low', 'close', 'volume']].astype(float)
    return df

def apply_indicators(df):
    df['rsi'] = ta.momentum.RSIIndicator(df['close'], window=14).rsi()
    df['macd'] = ta.trend.MACD(df['close']).macd_diff()
    return df

def backtest_strategy(df, rsi_threshold, macd_threshold):
    df = apply_indicators(df)
    balance = 1000
    position = None
    entry_price = 0
    wins = 0
    losses = 0
    returns = []

    for i in range(30, len(df)):
        row = df.iloc[i]
        score = 0
        if row['macd'] > macd_threshold:
            score += 1
        if row['rsi'] < rsi_threshold:
            score += 1

        decision = None
        if score >= 2:
            decision = 'BUY'
        elif score <= 0:
            decision = 'SELL'

        if decision == 'BUY' and position is None:
            position = 'LONG'
            entry_price = row['close']

        elif decision == 'SELL' and position == 'LONG':
            exit_price = row['close']
            profit_pct = (exit_price - entry_price) / entry_price * 100

            if profit_pct >= TAKE_PROFIT_PCT:
                profit_pct = TAKE_PROFIT_PCT
                wins += 1
            elif profit_pct <= STOP_LOSS_PCT:
                profit_pct = STOP_LOSS_PCT
                losses += 1
            else:
                if profit_pct > 0:
                    wins += 1
                else:
                    losses += 1

            balance *= (1 + profit_pct / 100)
            returns.append(profit_pct)
            position = None

    win_rate = wins / (wins + losses) * 100 if (wins + losses) > 0 else 0
    avg_return = np.mean(returns) if returns else 0
    return balance, win_rate, avg_return

def optimize_strategy(df):
    best_result = None
    results = []

    for rsi in range(25, 50, 5):
        for macd in np.arange(0.0, 0.05, 0.01):
            final_balance, win_rate, avg_return = backtest_strategy(df.copy(), rsi, macd)
            results.append((rsi, macd, final_balance, win_rate, avg_return))

            if not best_result or final_balance > best_result[2]:
                best_result = (rsi, macd, final_balance, win_rate, avg_return)

    results_df = pd.DataFrame(results, columns=["RSI", "MACD", "Balance", "Win Rate", "Avg Return"])
    results_df.sort_values(by="Balance", ascending=False, inplace=True)
    print("\nTop 5 Results:")
    print(results_df.head())
    return best_result

if __name__ == "__main__":
    df = fetch_historical_ohlcv(SYMBOL, INTERVAL, LIMIT)
    best_config = optimize_strategy(df)
    print(f"\n🔥 Best Config => RSI: {best_config[0]}, MACD: {best_config[1]}")
    print(f"📊 Final Balance: ${best_config[2]:.2f} | Win Rate: {best_config[3]:.2f}% | Avg Return: {best_config[4]:.2f}%")
