from picamera2 import Picamera2
import cv2
import time
import numpy as np
from leaf_classifier import classify_size, summarize_tower_growth

pixels_per_cm = 71.37  # your calibrated value
scale = 0.5  # display scaling
EXPECTED_LEAVES = 18
TOLERANCE = 3

# Global counters for accumulation
global_small = 0
global_medium = 0
global_large = 0
total_detected_leaves = 0

# Start Pi camera
picam2 = Picamera2()
picam2.preview_configuration.main.size = (2304, 1296)
picam2.preview_configuration.main.format = "RGB888"
picam2.configure("preview")
picam2.start()
time.sleep(2)

# Try to enable autofocus mode
try:
    picam2.set_controls({"AfMode": 2})  # Manual one-shot AF
    print("🔧 Autofocus mode ready. Press 'f' to focus.")
except Exception as e:
    print(f"⚠️ Autofocus control failed: {e}")

while True:
    frame = picam2.capture_array()
    output = frame.copy()

    # HSV conversion & mask
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    lower_green = np.array([30, 30, 30])  # expanded range
    upper_green = np.array([90, 255, 255])
    mask = cv2.inRange(hsv, lower_green, upper_green)

    # Find and filter contours
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    contours = [c for c in contours if cv2.contourArea(c) > 300]  # reduced threshold
    num_detected = len(contours)
    print(f"📸 Contours in this frame: {num_detected}")

    # Sort top contours
    contours = sorted(contours, key=cv2.contourArea, reverse=True)[:18]

    # Analyze contours
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

        total_detected_leaves += 1

        # Draw
        cv2.rectangle(output, (x, y), (x + w, y + h), (0, 255, 0), 2)
        text = f"#{i+1} {label} ({w_cm:.1f}x{h_cm:.1f}cm)"
        cv2.putText(output, text, (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 255, 0), 2)
        print(f"🍃 Leaf #{i+1}: {w_cm:.2f} x {h_cm:.2f} cm → {label}")

    # Display status or final result
    if EXPECTED_LEAVES - TOLERANCE <= total_detected_leaves <= EXPECTED_LEAVES + TOLERANCE:
        growth = summarize_tower_growth(global_small, global_medium, global_large)
        print(f"✅ Tower Scan Complete → {growth}")
        cv2.putText(output, f"{growth}", (10, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)

        # Reset counters
        global_small = 0
        global_medium = 0
        global_large = 0
        total_detected_leaves = 0
    else:
        cv2.putText(output, f"🕵️ Detecting: {total_detected_leaves}/18",
                    (10, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 255), 2)

    # Show mask for debug (optional)
    # cv2.imshow("Mask", mask)

    # Resize and display
    preview = cv2.resize(output, (0, 0), fx=scale, fy=scale)
    cv2.imshow("Multi Leaf Detection (press 'q' to quit, 'f' to focus)", preview)

    # Key controls
    key = cv2.waitKey(1) & 0xFF
    if key == ord('q'):
        break
    elif key == ord('f'):
        try:
            picam2.set_controls({"AfTrigger": 0})
            print("🔍 Autofocus triggered manually.")
        except Exception as e:
            print(f"⚠️ Failed to trigger autofocus: {e}")

picam2.stop()
cv2.destroyAllWindows()
