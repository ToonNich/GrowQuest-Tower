from picamera2 import Picamera2
import cv2
import time
import numpy as np
from leaf_classifier import classify_size, summarize_tower_growth

pixels_per_cm = 71.37
scale = 0.5
FRAME_LIMIT = 6  # number of simulated rotation frames

# Global counters
global_small = 0
global_medium = 0
global_large = 0
frame_count = 0

# Start camera
picam2 = Picamera2()
picam2.preview_configuration.main.size = (2304, 1296)
picam2.preview_configuration.main.format = "RGB888"
picam2.configure("preview")
picam2.start()
time.sleep(2)

# Autofocus
try:
    picam2.set_controls({"AfMode": 2})
    print("🔧 Autofocus mode ready. Press 'f' to focus.")
except Exception as e:
    print(f"⚠️ Autofocus control failed: {e}")

while frame_count < FRAME_LIMIT:
    # Countdown
    for i in range(3, 0, -1):
        dummy_frame = np.zeros((300, 600, 3), dtype=np.uint8)
        cv2.putText(dummy_frame, f"📸 Capturing in {i}", (50, 180),
                    cv2.FONT_HERSHEY_SIMPLEX, 2, (0, 255, 255), 4)
        cv2.imshow("Countdown", dummy_frame)
        cv2.waitKey(1000)  # 1 second delay

    cv2.destroyWindow("Countdown")

    # Capture frame
    frame = picam2.capture_array()
    output = frame.copy()

    # Create green mask
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    lower_green = np.array([30, 30, 30])
    upper_green = np.array([90, 255, 255])
    mask = cv2.inRange(hsv, lower_green, upper_green)

    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    contours = [c for c in contours if cv2.contourArea(c) > 300]
    contours = sorted(contours, key=cv2.contourArea, reverse=True)[:18]

    print(f"📸 Frame #{frame_count+1} — {len(contours)} leaf contours detected")

    for i, cnt in enumerate(contours):
        x, y, w, h = cv2.boundingRect(cnt)
        w_cm = w / pixels_per_cm
        h_cm = h / pixels_per_cm
        label = classify_size(w_cm, h_cm)

        if label == "Small":
            global_small += 1
        elif label == "Medium":
            global_medium += 1
        else:
            global_large += 1

        cv2.rectangle(output, (x, y), (x + w, y + h), (0, 255, 0), 2)
        text = f"#{i+1} {label} ({w_cm:.1f}x{h_cm:.1f}cm)"
        cv2.putText(output, text, (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 255, 0), 2)
        print(f"🍃 Leaf #{i+1}: {w_cm:.2f} x {h_cm:.2f} cm → {label}")

    frame_count += 1
    preview = cv2.resize(output, (0, 0), fx=scale, fy=scale)
    cv2.imshow("Captured Frame", preview)

    key = cv2.waitKey(3000)  # Wait 3 sec before next frame or key interrupt
    if key == ord('q'):
        break

cv2.destroyWindow("Captured Frame")

# Final summary
total = global_small + global_medium + global_large
if total >= 15:
    growth = summarize_tower_growth(global_small, global_medium, global_large)
else:
    growth = "⚠️ Not enough leaves for tower summary"

print(f"🧮 Final Result: {global_small} Small, {global_medium} Medium, {global_large} Large")
print(f"🌱 Tower Growth Stage → {growth}")
