import pandas as pd
from datetime import datetime

df = pd.read_csv("pengu_signal_log.csv")

# Filter only today's signals
today = datetime.now().strftime('%Y-%m-%d')
df['Time'] = pd.to_datetime(df['Time'])
df_today = df[df['Time'].dt.strftime('%Y-%m-%d') == today]

buy_signals = df_today[df_today['Decision'].str.contains("BUY")].shape[0]
sell_signals = df_today[df_today['Decision'].str.contains("SELL")].shape[0]
wait_signals = df_today[df_today['Decision'].str.contains("Wait")].shape[0]

summary = f"""
📅 Daily Summary for {today}
✅ Buy Signals: {buy_signals}
❌ Sell Signals: {sell_signals}
⚠️ Wait Signals: {wait_signals}
📊 Total Signals: {len(df_today)}
"""

print(summary)

# Optional: Send to Telegram
from pengu_telegram_alerts import send_telegram_alert
send_telegram_alert(summary)
