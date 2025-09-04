#!/usr/bin/env python3
"""
PC uploader: reads JSON lines from an Arduino Mega over serial, pushes to Firestore,
sends notifications with debounce (same logic as your update_firebase_uid_serial),
and (optionally) exposes a small /dose HTTP endpoint that proxies commands to serial.

Run examples:
  python pc_update_firebase_from_arduino.py --cred "C:/path/to/serviceAccount.json"
  python pc_update_firebase_from_arduino.py --cred "/Users/you/Downloads/serviceAccount.json" --device-id pc_01
  python pc_update_firebase_from_arduino.py --cred ./service.json --dose-port 5002

Requires: pip install pyserial firebase-admin flask flask-cors
"""

import argparse
import json
import os
import sys
import time
from datetime import datetime
from threading import Lock, Thread

import firebase_admin
from firebase_admin import credentials, firestore

import serial
from serial.tools import list_ports

# --- add this constant near the top ---
DEFAULT_CRED = r"D:/Senior_WorkTable/KEYAPI/seniorproject-684c1-firebase-adminsdk-fbsvc-1247e74837.json"
DEFAULT_DEVICE_ID = "raspi_01"  # change if you like


# Optional HTTP dose proxy (enabled only if --dose-port passed)
try:
    from flask import Flask, request, jsonify
    from flask_cors import CORS
except Exception:
    Flask = None  # we won't start API unless the libs are present

# -----------------------------
# Defaults / thresholds
# -----------------------------
DEBOUNCE_TIME = 300  # seconds between repeated notifications per key
BAUD_RATE = 9600
READ_TIMEOUT = 2
SLEEP_BETWEEN = 1

# Notification keys we debounce
LAST_SENT = {
    "ph": 0,
    "ec": 0,
    "temp": 0,
    "humidity": 0,
    "light": 0,
    "main_level": 0,
    "chem_level": 0,
}

ser = None
ser_lock = Lock()
db = None

# -----------------------------
# Serial helpers
# -----------------------------
ARDUINO_HINTS = ("Arduino", "CH340", "wchusbserial", "usbmodem", "usbserial", "ACM", "CDC", "ttyACM", "ttyUSB")


def autodetect_serial_port() -> str | None:
    ports = list(list_ports.comports())
    if not ports:
        return None
    # Prefer ports whose description looks like Arduino
    for p in ports:
        desc = f"{p.device} {p.description} {p.manufacturer}".lower()
        if any(h.lower() in desc for h in ARDUINO_HINTS):
            return p.device
    # Fallback to the first available
    return ports[0].device


def open_serial(port: str | None, baud: int) -> serial.Serial:
    dev = port or autodetect_serial_port()
    if not dev:
        raise RuntimeError("No serial ports found. Plug in the Arduino Mega and try again.")
    print(f"🔌 Opening serial: {dev} @ {baud}")
    s = serial.Serial(dev, baud, timeout=READ_TIMEOUT)
    time.sleep(2)  # let Arduino reset
    return s


def send_serial_line(line: str):
    if not line.endswith("\n"):
        line += "\n"
    with ser_lock:
        ser.write(line.encode("utf-8"))
        ser.flush()


# -----------------------------
# Firebase helpers
# -----------------------------
def init_firestore(cred_path: str):
    print("⚙️ Initializing Firebase...")
    cred = credentials.Certificate(cred_path)
    firebase_admin.initialize_app(cred)
    print("✅ Firebase initialized\n")
    return firestore.client()


def get_linked_uid(device_id: str) -> str | None:
    """Read /sensorLinks/{device_id} and return uid field"""
    try:
        doc = db.collection("sensorLinks").document(device_id).get(timeout=5)
        if doc.exists:
            uid = (doc.to_dict() or {}).get("uid", "").strip()
            if uid:
                return uid
            print("⚠️ UID field is empty.")
        else:
            print(f"🚫 Document /sensorLinks/{device_id} not found.")
    except Exception as e:
        print("🔥 Error fetching UID:", e)
    return None


def send_sensor_data(uid: str, data: dict):
    try:
        db.collection("tubeData").document(uid).collection("readings").add(data)
        print(f"✅ Sent reading to /tubeData/{uid}/readings")
    except Exception as e:
        print("🔥 Failed to upload sensor data:", e)


def send_warning(uid: str, title: str, content: str, key: str):
    now = time.time()
    last = LAST_SENT.get(key, 0)
    if now - last <= DEBOUNCE_TIME:
        return
    try:
        db.collection("notifications").document(uid).collection("userNotifications").add({
            "title": title,
            "content": content,
            "timestamp": firestore.SERVER_TIMESTAMP,
            "read": False,
            "starred": False,
            "detailLink": "NotificationDetail.html"
        })
        LAST_SENT[key] = now
        print(f"⚠️ Warning sent: {title}")
    except Exception as e:
        print(f"🔥 Failed to send '{key}' warning:", e)


# -----------------------------
# Optional: tiny DOSE API
# -----------------------------
def start_dose_api(bind_port: int):
    if Flask is None:
        print("⚠️ Flask/Flask-Cors not installed; skipping /dose API.")
        return

    app = Flask(__name__)
    CORS(app)

    @app.get("/health")
    def health():
        return jsonify({"ok": True})

    @app.post("/dose")
    def dose():
        body = request.get_json(silent=True) or {}
        ms = body.get("duration_ms")
        if isinstance(ms, int) and ms > 0:
            send_serial_line(f"DOSE {ms}")
            return jsonify({"ok": True, "sent": f"DOSE {ms}"})
        else:
            send_serial_line("DOSE")
            return jsonify({"ok": True, "sent": "DOSE"})

    print(f"🛰  DOSE API listening on http://0.0.0.0:{bind_port}")
    app.run(host="0.0.0.0", port=bind_port, threaded=True)


# -----------------------------
# Main loop
# -----------------------------
def main():
    global ser, db

    parser = argparse.ArgumentParser(description="PC uploader for Arduino → Firestore (GrowQuest).")
    parser.add_argument("--cred", default=DEFAULT_CRED, help="Path to Firebase service account JSON")
    parser.add_argument("--device-id", default=DEFAULT_DEVICE_ID,
                        help="sensorLinks document id to read the UID from")
    parser.add_argument("--port", help="Serial port (COM3, /dev/ttyACM0, etc.). If omitted, auto-detect.")
    parser.add_argument("--baud", type=int, default=BAUD_RATE)
    parser.add_argument("--dose-port", type=int, default=None, help="If set, expose /dose API on this port")
    args = parser.parse_args()

    db = init_firestore(args.cred)
    ser = open_serial(args.port, args.baud)

    # Start dose API if requested
    if args.dose_port:
        Thread(target=start_dose_api, args=(args.dose_port,), daemon=True).start()

    print(f"📟 Using device-id: {args.device_id} (for /sensorLinks/{{device_id}} → uid)")
    print("⏳ Waiting for serial JSON lines like: {\"ph\":7.0, \"ec\":1.1, ...}\n")

    while True:
        uid = get_linked_uid(args.device_id)
        if not uid:
            print("⚠️ No UID yet; will retry in 10s.\n")
            time.sleep(10)
            continue

        try:
            raw = ser.readline().decode(errors="ignore").strip()
            if not raw:
                time.sleep(SLEEP_BETWEEN)
                continue

            print("📥 Raw:", repr(raw))

            if raw.startswith("{") and raw.endswith("}"):
                try:
                    data = json.loads(raw)
                except json.JSONDecodeError as je:
                    print("❌ JSON parse error:", je)
                    time.sleep(SLEEP_BETWEEN)
                    continue

                # Attach server timestamp
                data["timestamp"] = datetime.utcnow()

                # Push reading
                send_sensor_data(uid, data)

                # Threshold checks (same as your Pi script)
                try:
                    if "ph" in data and (data["ph"] < 5.5 or data["ph"] > 8.5):
                        send_warning(uid, "⚠️ pH level out of range",
                                     f"Current pH is {float(data['ph']):.2f}. Please adjust solution.", "ph")
                    if "ec" in data and (data["ec"] < 0.5 or data["ec"] > 3.5):
                        send_warning(uid, "⚠️ EC level abnormal",
                                     f"EC reading is {float(data['ec']):.2f}. Nutrient imbalance suspected.", "ec")
                    if "temp" in data and (data["temp"] < 10 or data["temp"] > 40):
                        send_warning(uid, "⚠️ Temperature warning",
                                     f"Temperature is {float(data['temp']):.1f}°C. Check environment controls.", "temp")
                    # your field name was 'hum' in the Pi script
                    if "hum" in data and (data["hum"] < 20 or data["hum"] > 90):
                        send_warning(uid, "⚠️ Humidity warning",
                                     f"Humidity is {float(data['hum']):.1f}%. Consider ventilation or misting.", "humidity")
                    if "light" in data and (data["light"] < 50 or data["light"] > 100000):
                        send_warning(uid, "⚠️ Light level warning",
                                     f"Light intensity is {float(data['light']):.0f} lux. Check lighting.", "light")

                    # Water-level hints (same as your original)
                    if "mainLevel" in data:
                        ml = int(data["mainLevel"])
                        if ml <= 10:
                            send_warning(uid, "⚠️ Main tank low", f"Main tank level is {ml}%. Refill soon.", "main_level")
                        elif ml >= 100:
                            send_warning(uid, "ℹ️ Main tank full", f"Main tank level is {ml}%.", "main_level")

                    if "chemLevel" in data:
                        cl = int(data["chemLevel"])
                        if cl <= 10:
                            send_warning(uid, "⚠️ Chemical tank low", f"Chemical tank level is {cl}%. Refill soon.", "chem_level")
                        elif cl >= 100:
                            send_warning(uid, "ℹ️ Chemical tank full", f"Chemical tank level is {cl}%.", "chem_level")

                except Exception as e:
                    # don't let a bad field kill the loop
                    print("⚠️ Warning checks skipped due to error:", e)

            else:
                print("❌ Not JSON (skipped).")

        except KeyboardInterrupt:
            print("\n👋 Exiting.")
            break
        except Exception as e:
            print("🔥 Unexpected error:", e)
            time.sleep(2)

    try:
        ser.close()
    except Exception:
        pass


if __name__ == "__main__":
    main()
