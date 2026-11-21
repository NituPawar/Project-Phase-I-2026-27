from ultralytics import YOLO

# Load trained model
model = YOLO(
    "runs/detect/dr_yolo_v2/weights/best.pt"
)

# Predict on test image
results = model.predict(
    source="images/test/IDRiD_55.jpg",
    imgsz=1024,
    conf=0.70,
    device=0,
    save=True,
    save_conf=False,
    show_labels=True,
    show_conf=False,
    line_width=2,
    name="professional_prediction"
)

print()
print("====================================")
print("Clean prediction completed!")
print("====================================")
print()
print("Confidence threshold: 0.70")
print()
print("Result saved to:")
print(
    "runs/detect/professional_prediction"
)