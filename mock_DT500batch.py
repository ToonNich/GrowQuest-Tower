import random
from datetime import datetime, timedelta
import firebase_admin
from firebase_admin import credentials, firestore

# === Firebase Init ===
cred = credentials.Certificate("D:/Senior_WorkTable/KEYAPI/seniorproject-684c1-firebase-adminsdk-fbsvc-1247e74837.json")
firebase_admin.initialize_app(cred)
db = firestore.client()

# === Config ===
user_uid = "zG3FGDcmT7hEImtzCKiY73HhGOs2"
collection_path = f"tubeData/{user_uid}/readings"

# === Generate & Upload Mock Data ===
start_time = datetime.utcnow() - timedelta(hours=1)  # Start from 1 hour ago

batch = db.batch()
batch_counter = 0

for i in range(1200):
    doc = {
        "temp": round(random.uniform(18, 35), 2),
        "hum": round(random.uniform(40, 90), 2),
        "ph": round(random.uniform(5.5, 7.5), 2),
        "ec": round(random.uniform(1.0, 3.5), 2),
        "light": random.randint(100, 2000),
        "main_tank": random.choice([0, 10, 50, 100]),
        "chem_tank": random.choice([0, 10, 50, 100]),
        "timestamp": start_time + timedelta(seconds=i * 3)
    }

    doc_ref = db.collection(collection_path).document()
    batch.set(doc_ref, doc)
    batch_counter += 1

    # Firestore limits batch writes to 500 per commit
    if batch_counter == 500:
        batch.commit()
        print(f"✅ Uploaded batch up to record {i+1}")
        batch = db.batch()
        batch_counter = 0

# Commit remaining batch
if batch_counter > 0:
    batch.commit()
    print("✅ Final batch uploaded.")

print("✅ Mock data upload completed.")
