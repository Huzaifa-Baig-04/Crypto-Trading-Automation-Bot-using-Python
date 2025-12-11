import subprocess
import time

while True:
    print("🔄 Starting pengu_bot_step3_alerts.py...")
    process = subprocess.Popen(["python", "pengu_bot_step3_alerts.py"])
    process.wait()
    print("❌ Bot crashed. Restarting in 5 seconds...")
    time.sleep(5)
