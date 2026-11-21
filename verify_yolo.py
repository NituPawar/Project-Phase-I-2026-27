from pathlib import Path
import cv2

# ==========================================
# Project folder
# ==========================================

project_folder = Path(__file__).parent

# Image and label
image_path = (
    project_folder
    / "images"
    / "train"
    / "IDRiD_01.jpg"
)

label_path = (
    project_folder
    / "labels"
    / "train"
    / "IDRiD_01.txt"
)

# ==========================================
# Class names
# ==========================================

class_names = {
    0: "Microaneurysm",
    1: "Haemorrhage",
    2: "Hard Exudate",
    3: "Soft Exudate"
}

# ==========================================
# Read image
# ==========================================

image = cv2.imread(str(image_path))

height, width = image.shape[:2]

# ==========================================
# Read YOLO labels
# ==========================================

with open(label_path, "r") as file:
    lines = file.readlines()

print("Total annotations:", len(lines))

# ==========================================
# Draw boxes
# ==========================================

for line in lines:

    parts = line.strip().split()

    if len(parts) != 5:
        continue

    class_id = int(parts[0])

    center_x = float(parts[1])
    center_y = float(parts[2])
    box_width = float(parts[3])
    box_height = float(parts[4])

    # Convert normalized YOLO coordinates
    center_x *= width
    center_y *= height
    box_width *= width
    box_height *= height

    # Calculate corners
    x1 = int(center_x - box_width / 2)
    y1 = int(center_y - box_height / 2)

    x2 = int(center_x + box_width / 2)
    y2 = int(center_y + box_height / 2)

    # Draw bounding box
    cv2.rectangle(
        image,
        (x1, y1),
        (x2, y2),
        (0, 255, 0),
        2
    )

    # Add class name
    label = class_names[class_id]

    cv2.putText(
        image,
        label,
        (x1, max(y1 - 5, 20)),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.5,
        (0, 255, 0),
        1
    )

# ==========================================
# Save result
# ==========================================

output_path = (
    project_folder
    / "IDRiD_01_YOLO_verification.jpg"
)

cv2.imwrite(
    str(output_path),
    image
)

print("Verification image saved:")
print(output_path)