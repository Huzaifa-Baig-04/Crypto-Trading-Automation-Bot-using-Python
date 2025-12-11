# 📌 Full Pengu Bot Code with Support & Resistance + Working Signal Output

import asyncio
import pandas as pd
import numpy as np
import ta
from datetime import datetime
from binance.client import Client
import os
import traceback
import mplfinance as mpf
import matplotlib.pyplot as plt
import warnings
import requests

warnings.filterwarnings("ignore")

# === CONFIG ===
TELEGRAM_BOT_TOKEN = "8340457173:AAHJF4IIR2cEzvAbJ9I_H3WCQng6WRmrVx0"
CHAT_ID = "5632818629"
SYMBOL = "PENGUUSDT"
LOG_FILE = "pengu_signal_log.csv"
FEEDBACK_POLL_INTERVAL = 5  # seconds

client = Client()
LAST_UPDATE_ID = None
BASE_URL = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}"


def send_telegram_alert_sync(message: str):
    payload = {"chat_id": CHAT_ID, "text": message, "parse_mode": "Markdown"}
    try:
        r = requests.post(f"{BASE_URL}/sendMessage", json=payload, timeout=10)
        r.raise_for_status()
        print("📨 Telegram alert sent.")
    except Exception as e:
        print(f"[❌ Telegram Alert Error] {e}")


def send_telegram_image_sync(image_path: str, caption="📊 Candlestick Chart"):
    try:
        with open(image_path, "rb") as f:
            files = {"photo": f}
            data = {"chat_id": CHAT_ID, "caption": caption}
            r = requests.post(f"{BASE_URL}/sendPhoto", files=files, data=data, timeout=15)
            r.raise_for_status()
            print("🖼️ Telegram image sent.")
    except Exception as e:
        print(f"[❌ Telegram Image Error] {e}")


def notify_self_learning(message: str):
    print("🧐 Self-learning:", message)


def notify_self_learning_update(message: str):
    print("🧠 Update:", message)


def send_trade_alert(score, decision, reasons, patterns):
    print("📣 Trade Alert:")
    print(f" Score: {score}\n Decision: {decision}\n Reasons: {reasons}\n Patterns: {patterns}")


def fetch_ohlcv(symbol, interval, limit=200):
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


def detect_candlestick_patterns(df):
    patterns = []
    open_ = df['entry_open'].iloc[-1]
    close = df['entry_close'].iloc[-1]
    low = df['entry_low'].iloc[-1]
    high = df['entry_high'].iloc[-1]
    body = abs(close - open_)
    range_ = high - low
    upper_shadow = high - max(open_, close)
    lower_shadow = min(open_, close) - low
    if body <= 0.3 * range_ and lower_shadow > 2 * body:
        patterns.append("🔨 Hammer")
    if body <= 0.3 * range_ and upper_shadow > 2 * body:
        patterns.append("📍 Inverted Hammer")
    if close > open_ and open_ < df['entry_open'].iloc[-2] and close > df['entry_close'].iloc[-2]:
        patterns.append("🟩 Bullish Engulfing")
    if close < open_ and open_ > df['entry_open'].iloc[-2] and close < df['entry_close'].iloc[-2]:
        patterns.append("🔵 Bearish Engulfing")
    return patterns if patterns else ["None"]


def plot_candlestick(df):
    chart_path = 'last_signal.png'
    try:
        last_20 = df.tail(20).copy()
        last_20.index.name = 'Date'
        mpf.plot(last_20, type='candle', style='charles', volume=True, mav=(3, 6), savefig=chart_path)
    except Exception as e:
        print("❌ Error plotting candlestick chart:", e)
    return chart_path


def log_signal(timestamp, score, decision, reasons, patterns):
    log_entry = pd.DataFrame([[timestamp, score, decision, ", ".join(reasons), ", ".join(patterns)]],
                             columns=['Time', 'Score', 'Decision', 'Reasons', 'Patterns'])
    if not os.path.exists(LOG_FILE):
        log_entry.to_csv(LOG_FILE, index=False)
    else:
        log_entry.to_csv(LOG_FILE, mode='a', index=False, header=False)


def self_learn_from_log():
    try:
        if not os.path.exists(LOG_FILE):
            return
        df = pd.read_csv(LOG_FILE)
        df['Time'] = pd.to_datetime(df['Time'])
        df['Outcome'] = "Unknown"
        for i in range(len(df) - 3):
            if df.loc[i, 'Decision'] == df.loc[i+3, 'Decision']:
                df.at[i, 'Outcome'] = "Correct"
            else:
                df.at[i, 'Outcome'] = "Incorrect"
        df.to_csv(LOG_FILE, index=False)
    except Exception as e:
        print(f"[❌ Self-learning error] {e}")


def find_support_resistance(df, window=5):
    df['support'] = df['low'].rolling(window, center=True).apply(
        lambda x: x[window//2] if all(x[window//2] <= i for i in x) else np.nan
    )
    df['resistance'] = df['high'].rolling(window, center=True).apply(
        lambda x: x[window//2] if all(x[window//2] >= i for i in x) else np.nan
    )
    return df


async def generate_signals():
    try:
        print("⚙️ Generating signal...")
        entry_df = fetch_ohlcv(SYMBOL, Client.KLINE_INTERVAL_5MINUTE, limit=100)
        filter_df = fetch_ohlcv(SYMBOL, Client.KLINE_INTERVAL_15MINUTE, limit=100)
        direction_df = fetch_ohlcv(SYMBOL, Client.KLINE_INTERVAL_1HOUR, limit=100)

        entry_df['rsi'] = ta.momentum.RSIIndicator(entry_df['close'], window=14).rsi()
        entry_df['macd'] = ta.trend.MACD(entry_df['close']).macd_diff()
        bb = ta.volatility.BollingerBands(entry_df['close'], window=20, window_dev=2)
        entry_df['bb_upper'] = bb.bollinger_hband()
        entry_df['bb_lower'] = bb.bollinger_lband()
        entry_df['entry_open'] = entry_df['open']
        entry_df['entry_close'] = entry_df['close']
        entry_df['entry_high'] = entry_df['high']
        entry_df['entry_low'] = entry_df['low']
        entry_df = find_support_resistance(entry_df)

        filter_df['vwap'] = (filter_df['close'] * filter_df['volume']).cumsum() / filter_df['volume'].cumsum()
        adx = ta.trend.ADXIndicator(direction_df['high'], direction_df['low'], direction_df['close'], window=14)
        direction_df['adx'] = adx.adx()

        candles = pd.concat([
            entry_df[['entry_open', 'entry_high', 'entry_low', 'entry_close', 'rsi', 'macd', 'bb_upper', 'bb_lower', 'support', 'resistance']].tail(2),
            filter_df[['vwap']].tail(2).rename(columns=lambda x: f'filter_{x}'),
            direction_df[['adx']].tail(2).rename(columns=lambda x: f'direction_{x}')
        ], axis=1).fillna(method='ffill')

        latest = candles.iloc[-1]
        score = 0
        reasons = []

        if latest['macd'] > 0:
            score += 1
            reasons.append("📈 MACD Bullish")
        elif latest['macd'] < 0:
            reasons.append("📉 MACD Bearish")

        if latest['rsi'] < 30:
            score += 1
            reasons.append("💧 RSI Oversold")
        elif latest['rsi'] > 70:
            reasons.append("🔥 RSI Overbought")

        if latest['entry_close'] < latest['filter_vwap']:
            score += 1
            reasons.append("🔻 Price Below VWAP (Buy Zone)")
        else:
            reasons.append("🔹 Price Above VWAP")

        if latest['direction_adx'] > 20:
            score += 1
            reasons.append("💪 Strong ADX Trend")
        else:
            reasons.append("😴 Weak ADX Trend")

        support_near = abs(latest['entry_close'] - latest['support']) / latest['entry_close'] < 0.01
        resistance_near = abs(latest['entry_close'] - latest['resistance']) / latest['entry_close'] < 0.01

        if support_near:
            score += 1
            reasons.append("🟢 Near Support")
        if resistance_near:
            reasons.append("🔴 Near Resistance")

        patterns = detect_candlestick_patterns(candles)
        signal_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        decision = "✅ BUY Signal" if latest['macd'] > 0 and support_near else "❌ SELL Signal"

        confidence = ["⚠️ Low", "🔸 Moderate", "🔶 Strong", "💎 Very Strong"]
        result = f"""
📊 === SIGNAL RESULT ===
🕒 Time: {signal_time}
💯 Score: {score} ({confidence[min(score, 3)]})
📌 Decision: {decision}
🗍 Triggered By: {', '.join(reasons)}
🛥️ Patterns: {', '.join(patterns)}
=========================
"""
        print(result)
        send_telegram_alert_sync(result)
        log_signal(signal_time, score, decision, reasons, patterns)
        chart_file = plot_candlestick(entry_df)
        send_telegram_image_sync(chart_file)
        self_learn_from_log()
    except Exception as e:
        print("[❌ generate_signals error]", e)
        traceback.print_exc()


async def feedback_loop():
    while True:
        await asyncio.sleep(FEEDBACK_POLL_INTERVAL)


async def signal_loop():
    while True:
        await generate_signals()
        await asyncio.sleep(600)  # 10 minutes


async def main():
    print("🟢 Pengu Bot Started")
    await asyncio.gather(feedback_loop(), signal_loop())


if __name__ == "__main__":
    import sys
    if sys.platform.startswith("win") and sys.version_info >= (3, 8):
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(main())

