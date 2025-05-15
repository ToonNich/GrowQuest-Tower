from picamera2 import Picamera2
import cv2
import time
import numpy as np

pixels_per_cm = 71.37  # your calibrated value
scale = 0.5  # display scaling

def classify_size(w_cm, h_cm):
    max_dim = max(w_cm, h_cm)
    if max_dim <= 5:
        return "Small"
    elif 5 < max_dim <= 15:
        return "Medium"
    else:
        return "Large"

# Start Pi camera
picam2 = Picamera2()
picam2.preview_configuration.main.size = (2304, 1296)
picam2.preview_configuration.main.format = "RGB888"
picam2.configure("preview")
picam2.start()
time.sleep(2)

print("🌿 Press 'q' to quit. Running leaf detection...")

while True:
    frame = picam2.capture_array()

    # Convert to HSV and create green mask
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    lower_green = np.array([35, 40, 40])
    upper_green = np.array([85, 255, 255])
    mask = cv2.inRange(hsv, lower_green, upper_green)

    # Find contours in the green mask
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    output = frame.copy()

    if contours:
        # Find largest green object (assume it's the leaf)
        leaf_contour = max(contours, key=cv2.contourArea)
        x, y, w, h = cv2.boundingRect(leaf_contour)

        # Convert to cm
        w_cm = w / pixels_per_cm
        h_cm = h / pixels_per_cm
        label = classify_size(w_cm, h_cm)

        # Draw bounding box and label
        cv2.rectangle(output, (x, y), (x + w, y + h), (0, 255, 0), 2)
        text = f"{label} ({w_cm:.1f} x {h_cm:.1f} cm)"
        cv2.putText(output, text, (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)

        print(f"📏 Width: {w_cm:.2f} cm, Height: {h_cm:.2f} cm → {label}")

    # Resize for display
    preview = cv2.resize(output, (0, 0), fx=scale, fy=scale)
    cv2.imshow("Auto Leaf Detection (press 'q' to quit)", preview)

    # Exit key
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

picam2.stop()
cv2.destroyAllWindows()
