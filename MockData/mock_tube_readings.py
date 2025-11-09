# -*- coding: utf-8 -*-
"""
GrowQuest Tower – Firestore mock data generator (infinite loop)
Writes docs to: /tubeData/{UID}/readings
Stop with: Ctrl+C
"""

import os
import time
import random
from argparse import ArgumentParser
from datetime import datetime
import firebase_admin
from firebase_admin import credentials, firestore

# --- defaults (you can change these) ---
DEFAULT_UID = "zG3FGDcmT7hEImtzCKiY73HhGOs2"
DEFAULT_KEY = r"D:\Senior_WorkTable\KEYAPI\seniorproject-684c1-firebase-adminsdk-fbsvc-1247e74837.json"

def parse_args():
    p = ArgumentParser()
    p.add_argument("--uid", default=os.environ.get("GQT_UID", DEFAULT_UID),
                   help="Target UID (Firestore doc under /tubeData/{uid})")
    p.add_argument("--interval", type=float, default=4.0,
                   help="Seconds between writes")
    p.add_argument("--spikes", type=float, default=0.15,
                   help="Probability to push one out-of-range value for warnings")
    p.add_argument("--service_account", default=os.environ.get("GOOGLE_APPLICATION_CREDENTIALS", DEFAULT_KEY),
                   help="Path to Firebase Admin SDK JSON")
    p.add_argument("--print", dest="do_print", action="store_true",
                   help="Print each payload")
    return p.parse_args()

def generate_reading(spike_prob=0.15):
    """Create realistic values; sometimes push one out-of-range."""
    temp = round(random.uniform(23.0, 31.0), 2)      # °C
    hum  = round(random.uniform(55.0, 80.0), 2)      # %
    ph   = round(random.uniform(5.8, 6.8), 2)
    ec   = round(random.uniform(1.2, 2.4), 2)        # mS/cm
    light = random.randint(1200, 6000)               # lux
    chem_tank = random.randint(35, 95)               # %
    main_tank = random.randint(35, 95)               # %

    payload = {
        "temp": temp,
        "hum": hum,
        "ph": ph,
        "ec": ec,
        "light": light,
        "chem_tank": chem_tank,
        "main_tank": main_tank,
        "timestamp": firestore.SERVER_TIMESTAMP,     # for orderBy("timestamp","desc")
    }

    if random.random() < spike_prob:
        which = random.choice(["temp", "hum", "ph", "ec", "light", "chem_tank"])
        if which == "temp":
            payload["temp"] = round(random.choice([random.uniform(9, 12), random.uniform(40.5, 44)]), 2)
        elif which == "hum":
            payload["hum"] = round(random.choice([random.uniform(15, 19.5), random.uniform(90.5, 96)]), 2)
        elif which == "ph":
            payload["ph"] = round(random.choice([random.uniform(4.6, 5.4), random.uniform(8.2, 9.0)]), 2)
        elif which == "ec":
            payload["ec"] = round(random.choice([random.uniform(0.05, 0.18), random.uniform(3.2, 4.2)]), 2)
        elif which == "light":
            payload["light"] = random.choice([0, random.randint(50000, 70000)])
        elif which == "chem_tank":
            payload["chem_tank"] = random.randint(0, 8)
    return payload

def main():
    args = parse_args()

    # Init Firebase
    if not firebase_admin._apps:
        cred = credentials.Certificate(args.service_account)
        firebase_admin.initialize_app(cred)
    db = firestore.client()
    readings = db.collection("tubeData").document(args.uid).collection("readings")

    print(f"🌿 Mocking to /tubeData/{args.uid}/readings every {args.interval}s (Ctrl+C to stop)")
    print(f"🔑 Using key: {args.service_account}")

    try:
        while True:
            payload = generate_reading(spike_prob=args.spikes)
            readings.add(payload)
            if args.do_print:
                shown = dict(payload)
                shown["timestamp"] = datetime.now().isoformat(timespec="seconds")
                print("✅ wrote:", shown)
            time.sleep(args.interval)
    except KeyboardInterrupt:
        print("\n🛑 Stopped by user (Ctrl+C).")
    except Exception as e:
        # Keep the process alive unless it’s a keyboard interrupt
        print("❌ Unexpected error:", e)
        print("Tip: check your service account path and Firestore rules.")
        raise

if __name__ == "__main__":
    main()
