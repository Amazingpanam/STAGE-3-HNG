import os
import time
import json
import re
import requests
from collections import deque

# Load environment variables
SLACK_WEBHOOK_URL = os.getenv("SLACK_WEBHOOK_URL")
ACTIVE_POOL = os.getenv("ACTIVE_POOL", "blue")
ERROR_RATE_THRESHOLD = float(os.getenv("ERROR_RATE_THRESHOLD", 2))
WINDOW_SIZE = int(os.getenv("WINDOW_SIZE", 200))
ALERT_COOLDOWN_SEC = int(os.getenv("ALERT_COOLDOWN_SEC", 300))
LOG_FILE = "/var/log/nginx/access.log"

# Track state
recent_statuses = deque(maxlen=WINDOW_SIZE)
last_pool = ACTIVE_POOL
last_alert_time = 0

def send_slack_alert(title, message, color="#ff0000"):
    """Send formatted message to Slack."""
    payload = {
        "attachments": [{
            "color": color,
            "title": title,
            "text": message,
            "ts": int(time.time())
        }]
    }
    try:
        requests.post(SLACK_WEBHOOK_URL, json=payload)
    except Exception as e:
        print(f"Slack error: {e}")

def detect_failover(current_pool):
    global last_pool, last_alert_time
    if current_pool != last_pool:
        now = time.time()
        if now - last_alert_time > ALERT_COOLDOWN_SEC:
            send_slack_alert(
                title="⚠️ Failover Detected",
                message=f"Traffic switched from *{last_pool}* → *{current_pool}*"
            )
            last_alert_time = now
        last_pool = current_pool

def detect_error_rate():
    """Check 5xx error percentage."""
    if not recent_statuses:
        return
    total = len(recent_statuses)
    errors = sum(1 for code in recent_statuses if str(code).startswith("5"))
    error_rate = (errors / total) * 100

    if error_rate > ERROR_RATE_THRESHOLD:
        now = time.time()
        global last_alert_time
        if now - last_alert_time > ALERT_COOLDOWN_SEC:
            send_slack_alert(
                title="🚨 High Error Rate",
                message=f"5xx errors exceeded threshold: {error_rate:.2f}% (>{ERROR_RATE_THRESHOLD}%) over last {total} requests."
            )
            last_alert_time = now

def tail_log(file_path):
    """Continuously read Nginx access logs."""
    with open(file_path, "r") as f:
        f.seek(0, 2)  # Go to end of file
        while True:
            line = f.readline()
            if not line:
                time.sleep(0.5)
                continue

            # Example log fields extraction
            match = re.search(r'pool=(\w+).*release=([\w\.]+).*upstream_status=(\d+)', line)
            if match:
                pool, release, status = match.groups()
                recent_statuses.append(status)
                detect_failover(pool)
                detect_error_rate()

if __name__ == "__main__":
    print("👀 Starting Nginx log watcher...")
    while not os.path.exists(LOG_FILE):
        print("Waiting for Nginx log file...")
        time.sleep(2)
    tail_log(LOG_FILE)
