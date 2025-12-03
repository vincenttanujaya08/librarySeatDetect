from ultralytics import YOLO
import cv2

# Load image
image = cv2.imread('data/test_images/image4.jpg')

# Load YOLO
model = YOLO('yolov8s.pt')

# Detect ALL objects
results = model.predict(image, conf=0.1, verbose=True)  

# Show results
annotated = results[0].plot()
cv2.imwrite('test_yolo_raw.jpg', annotated)

print("\nAll detections:")
for box in results[0].boxes:
    cls = int(box.cls[0])
    conf = float(box.conf[0])
    name = model.names[cls]
    print(f"- {name}: {conf:.2f}")