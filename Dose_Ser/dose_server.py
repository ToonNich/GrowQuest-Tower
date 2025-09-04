#!/usr/bin/env python3
"""
dose_server.py
A tiny Flask API that sends a "DOSE" command over USB serial to an Arduino Mega,
OR forwards the command to another service (proxy mode).

Endpoints:
  - GET  /health
  - POST /dose            -> {"ok": true, "sent": "DOSE 3000"}  (JSON body: {"duration_ms": 3000})

Config (env vars):
  - DOSE_SERIAL      : serial device path (default: auto -> /dev/ttyACM0 if present)
  - DOSE_BAUD        : baudrate (default: 115200)
  - DOSE_HOST        : host to bind (default: 0.0.0.0)
  - DOSE_PORT        : port to bind (default: 5000)
  - DOSE_DEFAULT_MS  : default dose duration in ms (default: 3000)
  - DOSE_PROXY_BASE  : if set (e.g., http://127.0.0.1:5002), enable proxy mode and DO NOT open serial
                       (alias: UPLOADER_BASE)
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import time
import threading
import logging
import requests  # --- ADDED (for proxy mode) ---

# ---------- Config ----------
DEFAULT_PORT = os.environ.get("DOSE_SERIAL")  # e.g., "/dev/ttyACM0"
BAUD = int(os.environ.get("DOSE_BAUD", "115200"))
HOST = os.environ.get("DOSE_HOST", "0.0.0.0")
PORT = int(os.environ.get("DOSE_PORT", "5000"))
DEFAULT_MS = int(os.environ.get("DOSE_DEFAULT_MS", "3000"))
MIN_MS = 200          # clamp for safety
MAX_MS = 20_000

# Proxy mode config
PROXY_BASE = os.environ.get("DOSE_PROXY_BASE") or os.environ.get("UPLOADER_BASE")
PROXY_MODE = bool(PROXY_BASE)

# ---------- Logging ----------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s: %(message)s",
)
log = logging.getLogger("dose_server")

# ---------- Serial (only used when NOT in proxy mode) ----------
_ser = None
_ser_lock = threading.Lock()
_ser_port_used = None

if not PROXY_MODE:
    try:
        import serial
        import serial.tools.list_ports as list_ports
    except Exception as e:
        raise SystemExit("pyserial is required in direct-serial mode. Install with: pip install pyserial") from e

    def _pick_default_port() -> str | None:
        """Choose a likely Arduino port if DOSE_SERIAL not set."""
        import os as _os
        if _os.path.exists("/dev/ttyACM0"):
            return "/dev/ttyACM0"
        for p in list(list_ports.comports()):
            name = f"{p.device} {p.description}".lower()
            if "ttyacm" in name or "ttyusb" in name or "arduino" in name:
                return p.device
        return None

    def _open_serial():
        global _ser, _ser_port_used
        port = DEFAULT_PORT or _pick_default_port()
        if not port:
            raise RuntimeError("No serial device found. Set DOSE_SERIAL or plug the Arduino.")
        log.info(f"Opening serial port {port} @ {BAUD}...")
        _ser = serial.Serial(port=port, baudrate=BAUD, timeout=1)
        _ser_port_used = port
        time.sleep(0.5)
        log.info("Serial opened.")

    def _ensure_serial_open():
        global _ser
        if _ser is None or not _ser.is_open:
            _open_serial()

    def _write_line(line: str):
        """Thread-safe write to serial."""
        _ensure_serial_open()
        data = (line if line.endswith("\n") else (line + "\n")).encode("utf-8")
        with _ser_lock:
            _ser.write(data)
            _ser.flush()

# ---------- Flask ----------
app = Flask(__name__)
CORS(app)  # allow browser calls from your PC

@app.get("/health")
def health():
    if PROXY_MODE:
        try:
            r = requests.get(f"{PROXY_BASE}/health", timeout=2)
            return jsonify({"ok": True, "mode": "proxy", "proxy_base": PROXY_BASE, "uploader": r.json()})
        except Exception as e:
            return jsonify({"ok": False, "mode": "proxy", "proxy_base": PROXY_BASE, "error": str(e)}), 502
    # direct-serial mode (original behavior)
    try:
        _ensure_serial_open()
        ok = True
        msg = "ready"
    except Exception as e:
        ok = False
        msg = f"serial error: {e}"
    return jsonify({
        "ok": ok,
        "mode": "serial",
        "message": msg,
        "port": _ser_port_used,
        "is_open": bool(_ser and _ser.is_open) if not PROXY_MODE else None,
        "baud": BAUD,
        "time": time.time(),
    })

@app.post("/dose")
def dose():
    """
    JSON body (optional): { "duration_ms": 3000, "uid": "..." }
    Sends either "DOSE" or "DOSE <ms>".
    """
    body = request.get_json(silent=True) or {}

    if PROXY_MODE:
        # --- proxy to uploader, do not touch serial ---
        try:
            r = requests.post(f"{PROXY_BASE}/dose", json=body, timeout=5)
            return (r.text, r.status_code, {"Content-Type": "application/json"})
        except Exception as e:
            return jsonify({"ok": False, "mode": "proxy", "proxy_base": PROXY_BASE, "error": str(e)}), 502

    # --- direct-serial mode (original path) ---
    ms = body.get("duration_ms", DEFAULT_MS)
    try:
        ms = int(ms)
        if ms <= 0:
            ms = None
    except Exception:
        ms = DEFAULT_MS

    if ms is not None:
        ms = max(MIN_MS, min(MAX_MS, ms))
        cmd = f"DOSE {ms}"
    else:
        cmd = "DOSE"

    try:
        _write_line(cmd)
        log.info(f"Sent: {cmd}")
        return jsonify({"ok": True, "sent": cmd})
    except Exception as e:
        log.exception("Failed to send DOSE")
        return jsonify({"ok": False, "error": str(e)}), 500

# ---------- Main ----------
if __name__ == "__main__":
    if PROXY_MODE:
        log.info(f"Starting in PROXY MODE (no serial). Forwarding to: {PROXY_BASE}")
    else:
        try:
            _open_serial()
        except Exception as e:
            log.warning(f"Startup serial open failed: {e} (will retry on first request)")
    app.run(host=HOST, port=PORT)