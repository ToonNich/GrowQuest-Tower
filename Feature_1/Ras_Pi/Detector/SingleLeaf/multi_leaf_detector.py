from picamera2 import Picamera2
import cv2
import time
import numpy as np
from leaf_classifier import classify_size, summarize_growth_stage

pixels_per_cm = 71.37  # your calibrated value
scale = 0.5  # display scaling

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
    # Count leaves by category
    small_count = 0
    medium_count = 0
    large_count = 0

    frame = picam2.capture_array()

    # Convert to HSV and create green mask
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    lower_green = np.array([35, 40, 40])
    upper_green = np.array([85, 255, 255])
    mask = cv2.inRange(hsv, lower_green, upper_green)

    # Find all green contours
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    output = frame.copy()

    for i, cnt in enumerate(contours):
        area = cv2.contourArea(cnt)
        if area < 500:  # skip noise/small blobs
            continue

        x, y, w, h = cv2.boundingRect(cnt)
        w_cm = w / pixels_per_cm
        h_cm = h / pixels_per_cm
        label = classify_size(w_cm, h_cm)

        # Tally leaf sizes
        if label == "Small":
            small_count += 1
        elif label == "Medium":
            medium_count += 1
        else:
            large_count += 1

        # Draw bounding box and label
        cv2.rectangle(output, (x, y), (x + w, y + h), (0, 255, 0), 2)
        text = f"#{i+1} {label} ({w_cm:.1f}x{h_cm:.1f}cm)"
        cv2.putText(output, text, (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 255, 0), 2)
        print(f"🍃 Leaf #{i+1}: {w_cm:.2f} x {h_cm:.2f} cm → {label}")

    # Summarize growth stage using weighted scoring
    growth = summarize_growth_stage(small_count, medium_count, large_count)
    cv2.putText(output, f"Growth Stage: {growth}", (10, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 0), 2)
    print(f"🌱 Summary: {small_count} Small, {medium_count} Medium, {large_count} Large → {growth}")

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
