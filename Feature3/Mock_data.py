import json
import time
import random
import firebase_admin
from firebase_admin import credentials, firestore
from datetime import datetime

# --- 1. INITIALIZE FIREBASE ---
# IMPORTANT: Update this path to where you saved your Firebase credentials file on your PC.
CREDENTIALS_PATH = "D:/Senior_WorkTable/KEYAPI/seniorproject-684c1-firebase-adminsdk-fbsvc-1247e74837.json"

try:
    # Check if the app is already initialized to prevent errors on re-running
    if not firebase_admin._apps:
        cred = credentials.Certificate(CREDENTIALS_PATH)
        firebase_admin.initialize_app(cred)
    db = firestore.client()
    print("✅ Firebase initialized successfully!")
except Exception as e:
    print(f"❌ Firebase initialization failed. Please check the CREDENTIALS_PATH.")
    print(f"Error: {e}")
    exit()


# --- 2. DEBOUNCE SETUP (To prevent spamming notifications) ---
last_sent = {
    "ph": 0, "ec": 0, "temp": 0, "humidity": 0, "light": 0,
    "main_tank": 0, "chemical": 0
}
DEBOUNCE_TIME = 300  # 5 minutes


print("🚀 Starting mock data uploader. Press CTRL+C to stop.")

# --- 3. MAIN SIMULATION LOOP ---
while True:
    try:
        # --- MOCK SENSOR DATA ---
        # Data fields now match your DashboardPage.html exactly.
        mock_data = {
            "temp": round(random.uniform(24.0, 26.0), 1),
            "humidity": round(random.uniform(55.0, 65.0), 1), # CORRECTED from 'hum'
            "ph": round(random.uniform(6.0, 6.5), 2),
            "ec": round(random.uniform(1.8, 2.2), 2),
            "light": random.randint(8000, 12000),
            "main_tank": random.choice([10, 50, 100]), # For future use
            "chemical": random.choice([10, 50, 100]),      # CORRECTED from 'chem_tank'
            "timestamp": datetime.utcnow()
        }

        # --- Upload to "tube" collection for dashboard ---
        db.collection("tube").add(mock_data)
        print(f"✅ Data uploaded: {mock_data}")

        # --- Conditional Notification Upload to "Main" with debounce ---
        current_time = time.time()

        # Check Main Tank Level
        if mock_data['main_tank'] <= 10 and (current_time - last_sent['main_tank'] > DEBOUNCE_TIME):
            db.collection("Main").add({
                "title": "💧 Main Tank Level Low",
                "content": f"Main water tank is at {mock_data['main_tank']}%. Please refill soon.",
                "timestamp": firestore.SERVER_TIMESTAMP, "read": False, "starred": False, "detailLink": "NotificationDetail.html"
            })
            last_sent['main_tank'] = current_time
            print("❗ Sent 'Main Tank Low' notification.")

        # Check Chemical Tank Level
        if mock_data['chemical'] <= 10 and (current_time - last_sent['chemical'] > DEBOUNCE_TIME):
            db.collection("Main").add({
                "title": "🧪 Chemical Tank Level Low",
                "content": f"Nutrient/chemical tank is at {mock_data['chemical']}%. Auto-dosing may fail.",
                "timestamp": firestore.SERVER_TIMESTAMP, "read": False, "starred": False, "detailLink": "NotificationDetail.html"
            })
            last_sent['chemical'] = current_time
            print("❗ Sent 'Chemical Tank Low' notification.")
            
        # Add other checks (pH, EC, temp, etc.) here if needed...


        # Wait for 5 seconds before sending the next batch of data
        time.sleep(5)

    except KeyboardInterrupt:
        print("\n🛑 Uploader stopped by user.")
        break
    except Exception as e:
        print(f"❌ An error occurred: {e}")
        time.sleep(10) # Wait a bit before retrying