from flask import Flask, Response, request, jsonify
from flask_cors import CORS
from picamera2 import Picamera2
import cv2
import time
import threading
import subprocess
import os
import RPi.GPIO as GPIO

app = Flask(__name__)
CORS(app)

# -----------------------
# Paths / Config
# -----------------------
# TODO: set this to the real path of your scan script
TOWER_SCAN_SCRIPT = "/home/pi/GrowQuest/tower_scan_by_magnets_rpigpio.py"

STREAM_WIDTH = 2304
STREAM_HEIGHT = 1296
STREAM_FORMAT = "RGB888"

# Motor pins (same as your code)
IN1, IN2, IN3, IN4 = 17, 18, 27, 22
motor_pins = [IN1, IN2, IN3, IN4]
sequence = [
    [1, 0, 0, 1],
    [1, 0, 0, 0],
    [1, 1, 0, 0],
    [0, 1, 0, 0],
    [0, 1, 1, 0],
    [0, 0, 1, 0],
    [0, 0, 1, 1],
    [0, 0, 0, 1]
]

# -----------------------
# Global state
# -----------------------
picam2 = None
output_frame = None
frame_lock = threading.Lock()
stop_event = None
update_thread = None

scanning = False  # True while tower scan is running

# -----------------------
# GPIO / Motor init (call after any GPIO.cleanup())
# -----------------------
def init_motor_gpio():
    GPIO.setwarnings(False)
    GPIO.setmode(GPIO.BCM)
    for pin in motor_pins:
        GPIO.setup(pin, GPIO.OUT)
        GPIO.output(pin, 0)

def move_steps(steps, delay=0.002):
    print(f"Moving {steps} steps")
    direction = 1 if steps > 0 else -1
    steps = abs(steps)
    pos = 0
    for _ in range(steps):
        for pin in range(4):
            GPIO.output(motor_pins[pin], sequence[pos][pin])
        pos = (pos + direction) % len(sequence)
        time.sleep(delay)

# -----------------------
# Camera start/stop + update thread
# -----------------------
def start_camera():
    global picam2, stop_event, update_thread
    if picam2 is not None:
        return
    print("🎥 Starting camera…")
    picam2 = Picamera2()
    picam2.still_configuration.main.size = (STREAM_WIDTH, STREAM_HEIGHT)
    picam2.still_configuration.main.format = STREAM_FORMAT
    picam2.configure("still")
    picam2.start()
    time.sleep(2)  # warm-up

    try:
        picam2.set_controls({"AfMode": 2, "AwbMode": 1})
    except Exception as e:
        print(f"Camera controls warning: {e}")

    stop_event = threading.Event()
    update_thread = threading.Thread(target=_update_frames_loop, daemon=True)
    update_thread.start()

def stop_camera():
    global picam2, stop_event, update_thread, output_frame
    if picam2 is None:
        return
    print("🛑 Stopping camera…")
    # stop the update loop
    if stop_event:
        stop_event.set()
    if update_thread:
        update_thread.join(timeout=2.0)
    # release camera
    try:
        picam2.stop()
        picam2.close()
    except Exception as e:
        print(f"Camera stop/close warning: {e}")
    picam2 = None
    update_thread = None
    stop_event = None
    with frame_lock:
        output_frame = None

def _update_frames_loop():
    global output_frame
    while stop_event and (not stop_event.is_set()):
        try:
            frame = picam2.capture_array("main")
            with frame_lock:
                output_frame = frame
        except Exception as e:
            print(f"Frame loop error: {e}")
            time.sleep(0.1)

def generate_frames():
    global output_frame
    while True:
        with frame_lock:
            frame = None if output_frame is None else output_frame.copy()
        if frame is None:
            time.sleep(0.05)
            continue
        ok, buffer = cv2.imencode('.jpg', frame, [int(cv2.IMWRITE_JPEG_QUALITY), 80])
        if not ok:
            continue
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + buffer.tobytes() + b'\r\n')

# -----------------------
# Routes
# -----------------------
@app.route('/')
def index():
    return '''
    <html>
    <head><title>GrowQuest Live</title></head>
    <body>
      <h2>Live View</h2>
      <img src="/video_feed" width="720">
      <div style="margin-top:10px">
        <button onclick="fetch('/scan_tower',{method:'POST'}).then(r=>r.json()).then(j=>alert(JSON.stringify(j))).catch(e=>alert(e))">
          Run Tower Scan
        </button>
      </div>
    </body>
    </html>
    '''

@app.route('/video_feed')
def video_feed():
    return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/pause_stream', methods=['POST'])
def pause_stream():
    stop_camera()
    return jsonify({'status': 'stream paused'})

@app.route('/resume_stream', methods=['POST'])
def resume_stream():
    start_camera()
    return jsonify({'status': 'stream resumed'})

@app.route('/move', methods=['POST'])
def move():
    if scanning:
        return jsonify({'error': 'Scan in progress, motor control disabled'}), 409
    try:
        data = request.get_json()
        direction = data.get('direction')
        print(f"Received direction: {direction}")
        if direction not in ['left', 'right']:
            return jsonify({'error': 'Invalid or missing direction'}), 400
        steps = -100 if direction == 'left' else 100
        move_steps(steps)
        return jsonify({'status': f'Moved {direction}'})
    except Exception as e:
        print(f"Error in /move: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/auto', methods=['POST'])
def auto_mode():
    if scanning:
        return jsonify({'error': 'Scan in progress, motor control disabled'}), 409
    try:
        move_steps(4096)
        time.sleep(2)
        move_steps(-4096)
        return jsonify({'status': 'Auto rotation complete'})
    except Exception as e:
        print(f"Error in /auto: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/scan_tower', methods=['POST'])
def scan_tower():
    """
    Orchestrates: pause stream -> run scan script -> resume stream.
    Also re-initializes GPIO outputs because scan script calls GPIO.cleanup().
    Returns script stdout/stderr for debugging.
    """
    global scanning
    if scanning:
        return jsonify({'error': 'Scan already in progress'}), 409

    scanning = True
    try:
        print("🔒 Pausing live stream for tower scan…")
        stop_camera()

        print(f"🚀 Running scan script: {TOWER_SCAN_SCRIPT}")
        proc = subprocess.run(
            ["python3", TOWER_SCAN_SCRIPT],
            capture_output=True, text=True
        )
        rc = proc.returncode
        print(f"Scan finished with code {rc}")

        # GPIO was cleaned up by the scan script, so re-init motor pins
        init_motor_gpio()

        # Bring camera back
        start_camera()

        return jsonify({
            'status': 'scan finished',
            'returncode': rc,
            'stdout': proc.stdout[-4000:],  # tail to keep payload small
            'stderr': proc.stderr[-4000:]
        }), (200 if rc == 0 else 500)

    except Exception as e:
        # Attempt recovery anyway
        try:
            init_motor_gpio()
            start_camera()
        except Exception as e2:
            print(f"Recovery error: {e2}")
        return jsonify({'error': str(e)}), 500
    finally:
        scanning = False

@app.route('/cleanup')
def cleanup():
    stop_camera()
    GPIO.cleanup()
    return jsonify({'status': 'GPIO cleaned up, camera stopped'})

# -----------------------
# Boot
# -----------------------
if __name__ == '__main__':
    init_motor_gpio()
    start_camera()
    app.run(host='0.0.0.0', port=5000)
