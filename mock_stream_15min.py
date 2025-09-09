# mock_stream_15min.py
import random
import time
from datetime import datetime
import firebase_admin
from firebase_admin import credentials, firestore

# === Firebase Init ===
# Use your existing service account key path
cred = credentials.Certificate(r"D:\Senior_WorkTable\KEYAPI\seniorproject-684c1-firebase-adminsdk-fbsvc-1247e74837.json")
if not firebase_admin._apps:
    firebase_admin.initialize_app(cred)
db = firestore.client()

# === Config ===
USER_UID = "zG3FGDcmT7hEImtzCKiY73HhGOs2"
COLLECTION_PATH = f"tubeData/{USER_UID}/readings"

# 15 minutes at 1 sample/second = 900 writes
DURATION_SECONDS = 15 * 60
INTERVAL_SECONDS = 1.0

def generate_reading():
    return {
        "temp": round(random.uniform(18, 35), 2),
        "hum": round(random.uniform(40, 90), 2),
        "ph": round(random.uniform(5.5, 7.5), 2),
        "ec": round(random.uniform(1.0, 3.5), 2),
        "light": random.randint(100, 2000),
        "main_tank": random.choice([0, 10, 50, 100]),
        "chem_tank": random.choice([0, 10, 50, 100]),
        "timestamp": datetime.utcnow(),
    }

def main():
    print(f"Starting 15‑min stream: 1 write/sec ({DURATION_SECONDS} total)...")
    start_monotonic = time.monotonic()

    for i in range(DURATION_SECONDS):
        reading = generate_reading()
        db.collection(COLLECTION_PATH).document().set(reading)

        # Progress ping every 30 seconds (and at start)
        if (i + 1) % 30 == 0 or i == 0:
            print(f"➜ wrote {i+1}/{DURATION_SECONDS} at {reading['timestamp'].isoformat()}Z")

        # Schedule next tick with drift correction
        next_tick = start_monotonic + (i + 1) * INTERVAL_SECONDS
        time.sleep(max(0, next_tick - time.monotonic()))

    print("✅ Done: 15 minutes of data written.")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n⏹️ Stopped early by user.")