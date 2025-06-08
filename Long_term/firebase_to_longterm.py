import firebase_admin
from firebase_admin import credentials, firestore
import mysql.connector
from datetime import datetime, timedelta, timezone as dt_timezone
import statistics
from pytz import timezone

# --- Firebase Setup ---
cred = credentials.Certificate("D:/Senior_WorkTable/KEYAPI/seniorproject-684c1-firebase-adminsdk-fbsvc-5dfc882149.json")
firebase_admin.initialize_app(cred)
db = firestore.client()

# --- MySQL Setup (on PC) ---
conn = mysql.connector.connect(
    host="localhost",
    user="root",
    password="",
    database="senior_project"
)
cursor = conn.cursor()

# --- Time Range: Last 1 Hour (UTC for Firestore query) ---
bangkok = timezone('Asia/Bangkok')

# ✅ Override with known time range (manual test)
start_time = datetime(2025, 6, 8, 10, 30, 0, tzinfo=dt_timezone.utc)
end_time   = datetime(2025, 6, 8, 12, 30, 0, tzinfo=dt_timezone.utc)

print("📦 Simulated Test: Querying from", start_time, "to", end_time)


# --- Query Firestore ---
docs = db.collection("tube") \
    .where("timestamp", ">=", start_time) \
    .where("timestamp", "<=", end_time) \
    .stream()

# --- Collect and Average Data ---
temps, hums, ecs, phs, lights = [], [], [], [], []

for doc in docs:
    d = doc.to_dict()
    print("🔥 Match:", d.get("timestamp"), "|", d)
    if all(k in d for k in ("temp", "humidity", "ec", "ph", "light")):
        temps.append(d["temp"])
        hums.append(d["humidity"])
        ecs.append(d["ec"])
        phs.append(d["ph"])
        lights.append(d["light"])

def safe_avg(arr):
    return round(statistics.mean(arr), 2) if arr else None

avg_temp = safe_avg(temps)
avg_hum = safe_avg(hums)
avg_ec = safe_avg(ecs)
avg_ph = safe_avg(phs)
avg_light = safe_avg(lights)

print("Hourly Averages:", avg_temp, avg_hum, avg_ec, avg_ph, avg_light)

# --- Insert into MySQL if Data is Valid ---
if None not in (avg_temp, avg_hum, avg_ec, avg_ph, avg_light):
    insert_sql = """
        INSERT INTO long_term (timestamp, Temperature, Humidity, EC, Ph, Light)
        VALUES (%s, %s, %s, %s, %s, %s)
    """
    cursor.execute(insert_sql, (datetime.utcnow(), avg_temp, avg_hum, avg_ec, avg_ph, avg_light))
    conn.commit()
    print("✅ Data inserted into long_term table.")
else:
    print("⚠️ Insufficient data: skipping insert.")

# --- Cleanup ---
cursor.close()
conn.close()
