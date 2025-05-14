import cv2

points = []

def click_event(event, x, y, flags, param):
    global points
    if event == cv2.EVENT_LBUTTONDOWN:
        points.append((x, y))
        cv2.circle(frame, (x, y), 5, (0, 0, 255), -1)
        cv2.putText(frame, f"{len(points)}", (x + 10, y - 10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 0), 1)
        cv2.imshow("Click 0 cm then 17 cm", frame)

        if len(points) == 2:
            px1, px2 = points
            distance = ((px2[0] - px1[0]) ** 2 + (px2[1] - px1[1]) ** 2) ** 0.5
            pixels_per_cm = distance / 17.0
            print(f"\nPixels between 0–17 cm: {distance:.2f} px")
            print(f"Calculated Pixels per cm: {pixels_per_cm:.2f} px/cm")
            cv2.destroyAllWindows()

# Start camera
cap = cv2.VideoCapture(0)

if not cap.isOpened():
    print("❌ Could not open camera.")
    exit()

print("📸 Press SPACE to capture image of the ruler...")
while True:
    ret, frame = cap.read()
    if not ret:
        print("Failed to grab frame.")
        break
    cv2.imshow("Live Preview - Press SPACE to capture", frame)
    key = cv2.waitKey(1) & 0xFF
    if key == 32:  # SPACE key
        break

cv2.destroyAllWindows()
cap.release()

# Show the captured frame for calibration
cv2.imshow("Click 0 cm then 17 cm", frame)
cv2.setMouseCallback("Click 0 cm then 17 cm", click_event)
cv2.waitKey(0)
cv2.destroyAllWindows()
