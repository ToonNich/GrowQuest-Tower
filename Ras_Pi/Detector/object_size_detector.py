from picamera2 import Picamera2
import cv2
import time

pixels_per_cm = 71.37  # Your calibrated value
scale = 0.4  # Resize preview to 40%

drawing = False
start_point = None
end_point = None
image = None
scaled_preview = None

def draw_rectangle(event, x, y, flags, param):
    global start_point, end_point, drawing, scaled_preview

    if event == cv2.EVENT_LBUTTONDOWN:
        drawing = True
        # Convert scaled coordinates to real coordinates
        start_point = (int(x / scale), int(y / scale))
        end_point = start_point

    elif event == cv2.EVENT_MOUSEMOVE and drawing:
        end_point = (int(x / scale), int(y / scale))
        temp = image.copy()
        cv2.rectangle(temp, start_point, end_point, (0, 255, 0), 2)
        scaled_preview = cv2.resize(temp, (0, 0), fx=scale, fy=scale)
        cv2.imshow("Draw Bounding Box (press 'q' to quit)", scaled_preview)

    elif event == cv2.EVENT_LBUTTONUP:
        drawing = False
        end_point = (int(x / scale), int(y / scale))

        # Calculate dimensions
        width_px = abs(end_point[0] - start_point[0])
        height_px = abs(end_point[1] - start_point[1])

        width_cm = width_px / pixels_per_cm
        height_cm = height_px / pixels_per_cm
        max_dim = max(width_cm, height_cm)

        # Classification
        if max_dim <= 5:
            label = "Small"
        elif 5 < max_dim <= 15:
            label = "Medium"
        else:
            label = "Large"

        result_text = f"{label} ({width_cm:.1f} x {height_cm:.1f} cm)"
        print(f"\n📏 Width: {width_cm:.2f} cm, Height: {height_cm:.2f} cm → {label}")

        temp = image.copy()
        cv2.rectangle(temp, start_point, end_point, (0, 255, 0), 2)
        cv2.putText(temp, result_text, (start_point[0], start_point[1] - 10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)

        scaled_preview = cv2.resize(temp, (0, 0), fx=scale, fy=scale)
        cv2.imshow("Draw Bounding Box (press 'q' to quit)", scaled_preview)

# Step 1: Capture image
picam2 = Picamera2()
picam2.still_configuration.main.size = (2304, 1296)
picam2.still_configuration.main.format = "RGB888"
picam2.configure("still")

print("📸 Capturing image...")
picam2.start()
time.sleep(2)
image = picam2.capture_array()
picam2.stop()
print("✅ Image captured.")

# Step 2: Resize for display
scaled_preview = cv2.resize(image.copy(), (0, 0), fx=scale, fy=scale)
cv2.imshow("Draw Bounding Box (press 'q' to quit)", scaled_preview)
cv2.setMouseCallback("Draw Bounding Box (press 'q' to quit)", draw_rectangle)

# Key loop
while True:
    if cv2.waitKey(1) & 0xFF == ord('q'):
        print("👋 Exiting.")
        break

cv2.destroyAllWindows()
