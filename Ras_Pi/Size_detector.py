import cv2

# Global variable to store clicked points
points = []

def click_event(event, x, y, flags, param):
    if event == cv2.EVENT_LBUTTONDOWN:
        points.append((x, y))
        cv2.circle(img, (x, y), 5, (0, 0, 255), -1)
        cv2.putText(img, f"{len(points)}", (x + 10, y - 10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 0), 1)
        cv2.imshow("Click 0cm then 17cm", img)

        if len(points) == 2:
            # Calculate distance in pixels
            px1, px2 = points
            distance = ((px2[0] - px1[0]) ** 2 + (px2[1] - px1[1]) ** 2) ** 0.5
            pixels_per_cm = distance / 17.0
            print(f"\nPixels between 0–17 cm: {distance:.2f} px")
            print(f"Calculated Pixels per cm: {pixels_per_cm:.2f} px/cm")

# Load your ruler image
img = cv2.imread("ruler.jpg")  # Change filename if needed
if img is None:
    print("❌ Could not load image. Check the filename.")
    exit()

cv2.imshow("Click 0cm then 17cm", img)
cv2.setMouseCallback("Click 0cm then 17cm", click_event)
cv2.waitKey(0)
cv2.destroyAllWindows()
