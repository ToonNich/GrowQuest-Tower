from picamera2 import Picamera2
import cv2
import numpy as np
import time

selected_hsv = []
frame = None  # global frame for mouse callback

def mouse_callback(event, x, y, flags, param):
    global frame
    if event == cv2.EVENT_LBUTTONDOWN:
        pixel = frame[y, x]
        hsv_pixel = cv2.cvtColor(np.uint8([[pixel]]), cv2.COLOR_BGR2HSV)[0][0]
        selected_hsv.append(hsv_pixel)
        print(f"📍 HSV at ({x}, {y}): {hsv_pixel}")

# Initialize and start Pi Camera
picam2 = Picamera2()
picam2.preview_configuration.main.size = (1280, 720)
picam2.preview_configuration.main.format = "RGB888"
picam2.configure("preview")
picam2.start()
time.sleep(2)

# Try autofocus (if supported)
try:
    picam2.set_controls({"AfMode": 2})         # One-shot AF mode
    time.sleep(0.1)
    picam2.set_controls({"AfTrigger": 0})      # Trigger autofocus
    print("🔍 Autofocus triggered.")
except Exception as e:
    print(f"⚠️ Autofocus error: {e}")

# Setup OpenCV window
cv2.namedWindow("Click on leaf to get HSV")
cv2.setMouseCallback("Click on leaf to get HSV", mouse_callback)

print("🟢 Autofocus complete. Click on the leaf to get HSV (press 'q' to quit)")

while True:
    frame = picam2.capture_array()
    display = frame.copy()

    if selected_hsv:
        hsv_text = f"Last HSV: {selected_hsv[-1]}"
        cv2.putText(display, hsv_text, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0,255,0), 2)

    preview = cv2.resize(display, (640, 360))
    cv2.imshow("Click on leaf to get HSV", preview)

    key = cv2.waitKey(1) & 0xFF
    if key == ord('q'):
        break

picam2.stop()
cv2.destroyAllWindows()

# Print all collected HSV values
print("\n🎯 Sampled HSV values:")
for idx, hsv in enumerate(selected_hsv):
    print(f"{idx+1}: HSV = {hsv}")
