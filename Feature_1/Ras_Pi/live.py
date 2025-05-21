from flask import Flask, Response
from picamera2 import Picamera2
import cv2
import time
import threading

app = Flask(__name__)

# 🎥 Initialize Camera
picam2 = Picamera2()
picam2.preview_configuration.main.size = (1280, 720)  # smaller for smoother streaming
picam2.preview_configuration.main.format = "RGB888"
picam2.configure("preview")
picam2.start()
time.sleep(2)

# 🎛️ Set White Balance + Autofocus
try:
    picam2.set_controls({
        "AfMode": 2,
        "AwbMode": 0,
        "ColourGains": (1.8, 1.3)
    })
except Exception as e:
    print(f"⚠️ Camera config error: {e}")

# 🌍 Global frame holder
output_frame = None
lock = threading.Lock()

# 🧵 Background frame update thread
def update_frames():
    global output_frame
    while True:
        frame = picam2.capture_array()
        with lock:
            output_frame = frame

# Start the background thread
thread = threading.Thread(target=update_frames, daemon=True)
thread.start()

# 📡 Frame generator for MJPEG stream
def generate_frames():
    global output_frame
    while True:
        with lock:
            if output_frame is None:
                continue
            frame = output_frame.copy()
        ret, buffer = cv2.imencode('.jpg', frame, [int(cv2.IMWRITE_JPEG_QUALITY), 80])
        if not ret:
            continue
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + buffer.tobytes() + b'\r\n')

# 🌐 Routes
@app.route('/')
def index():
    return '''
    <html>
    <head>
        <title>GrowQuest Live Stream</title>
        <style>
            body { text-align: center; font-family: sans-serif; background: #fff; }
            img { margin-top: 20px; border: 3px solid green; }
        </style>
    </head>
    <body>
        <h2>🌿 GrowQuest Tower Live View</h2>
        <img src="/video_feed" width="720">
    </body>
    </html>
    '''

@app.route('/video_feed')
def video_feed():
    return Response(generate_frames(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
