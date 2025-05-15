from picamera2 import Picamera2
import cv2
import time
import numpy as np
from imutils.video import VideoStream
from collections import OrderedDict
import math

pixels_per_cm = 71.37  # your calibrated value
scale = 0.5  # for display

class CentroidTracker:
    def __init__(self, max_distance=50):
        self.next_object_id = 1
        self.objects = OrderedDict()
        self.max_distance = max_distance

    def update(self, input_centroids):
        if len(self.objects) == 0:
            for centroid in input_centroids:
                self.objects[self.next_object_id] = centroid
                self.next_object_id += 1
        else:
            updated = set()
            for object_id, existing_centroid in self.objects.items():
                for i, new_centroid in enumerate(input_centroids):
                    dist = math.dist(existing_centroid, new_centroid)
                    if dist < self.max_distance:
                        self.objects[object_id] = new_centroid
                        updated.add(i)
                        break

            # Register new leaves
            for i, new_centroid in enumerate(input_centroids):
                if i not in updated:
                    self.objects[self.next_object_id] = new_centroid
                    self.next_object_id += 1

        return self.objects

def classify_size(w_cm, h_cm):
    max_dim = max(w_cm, h_cm)
    if max_dim <= 5:
        return "Small"
    elif 5 < max_dim <= 15:
        return "Medium"
    else:
        return "Large"

# Initialize camera
picam2 = Picamera2()
picam2.preview_configuration.main.size = (2304, 1296)
picam2.preview_configuration.main.format = "RGB888"
picam2.configure("preview")
picam2.start()
time.sleep(2)

tracker = CentroidTracker()

print("🌿 Real-time leaf tracking started. Press 'q' to quit.")

while True:
    frame = picam2.capture_array()

    # Convert to HSV and mask green
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    lower_green = np.array([35, 40, 40])
    upper_green = np.array([85, 255, 255])
    mask = cv2.inRange(hsv, lower_green, upper_green)

    # Find contours
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    output = frame.copy()
    input_centroids = []
    bounding_boxes = []

    for cnt in contours:
        area = cv2.contourArea(cnt)
        if area < 500:
            continue

        x, y, w, h = cv2.boundingRect(cnt)
        cx = int(x + w / 2)
        cy = int(y + h / 2)

        input_centroids.append((cx, cy))
        bounding_boxes.append((x, y, w, h))

    # Update tracked leaf positions
    tracked = tracker.update(input_centroids)

    for object_id, centroid in tracked.items():
        # Find the closest bounding box for the tracked centroid
        best_box = None
        best_dist = float("inf")
        for (x, y, w, h) in bounding_boxes:
            c_x = x + w / 2
            c_y = y + h / 2
            dist = math.dist((c_x, c_y), centroid)
            if dist < best_dist:
                best_box = (x, y, w, h)
                best_dist = dist

        if best_box:
            x, y, w, h = best_box
            w_cm = w / pixels_per_cm
            h_cm = h / pixels_per_cm
            label = classify_size(w_cm, h_cm)

            text = f"#{object_id} {label} ({w_cm:.1f}x{h_cm:.1f}cm)"
            cv2.rectangle(output, (x, y), (x + w, y + h), (0, 255, 0), 2)
            cv2.putText(output, text, (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 255, 0), 2)

    # Resize and display
    preview = cv2.resize(output, (0, 0), fx=scale, fy=scale)
    cv2.imshow("Leaf Tracker (press 'q' to quit)", preview)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

picam2.stop()
cv2.destroyAllWindows()
