from pathlib import Path
from PIL import Image
import numpy as np
import cv2
import shutil
import random

# ============================================================
# 1. PROJECT LOCATIONS
# ============================================================

project_folder = Path(__file__).parent
idrid_folder = project_folder / "IDRiD"

# Original retinal images
images_folder = (
    idrid_folder
    / "1. Original Images"
    / "a. Training Set"
)

# Segmentation ground truths
groundtruth_folder = (
    idrid_folder
    / "2. All Segmentation Groundtruths"
    / "a. Training Set"
)

# YOLO folders
train_images_folder = project_folder / "images" / "train"
val_images_folder = project_folder / "images" / "val"

train_labels_folder = project_folder / "labels" / "train"
val_labels_folder = project_folder / "labels" / "val"

# Create folders if they don't exist
train_images_folder.mkdir(parents=True, exist_ok=True)
val_images_folder.mkdir(parents=True, exist_ok=True)

train_labels_folder.mkdir(parents=True, exist_ok=True)
val_labels_folder.mkdir(parents=True, exist_ok=True)


# ============================================================
# 2. OUR FOUR YOLO CLASSES
# ============================================================

classes = {
    0: ("Microaneurysm", "1. Microaneurysms", "MA"),
    1: ("Haemorrhage", "2. Haemorrhages", "HE"),
    2: ("Hard Exudate", "3. Hard Exudates", "EX"),
    3: ("Soft Exudate", "4. Soft Exudates", "SE")
}


# ============================================================
# 3. FIND THE CORRESPONDING MASK
# ============================================================

def find_mask(image_stem, folder_name, suffix):

    folder = groundtruth_folder / folder_name

    if not folder.exists():
        return None

    # Look for the image number + correct lesion suffix.
    # This handles filenames such as:
    # IDRiD_01_MA.tif
    # IDRiD_01HE.tif
    # IDRiD_01_HE.tif
    # IDRiD_01EX.tif
    # IDRiD_01_EX.tif
    # etc.

    possible_files = list(folder.glob(f"{image_stem}*{suffix}.tif"))

    if len(possible_files) == 0:
        return None

    # Use the first matching file
    return possible_files[0]


# ============================================================
# 4. CONVERT ONE MASK INTO YOLO BOXES
# ============================================================

def mask_to_yolo(mask_path, class_id, image_width, image_height):

    mask = Image.open(mask_path)
    mask_array = np.array(mask)

    # Mask contains 0 for background and 1 for lesion
    binary_mask = (mask_array > 0).astype(np.uint8)

    # Find separate connected lesions
    num_labels, labels, stats, centroids = cv2.connectedComponentsWithStats(
        binary_mask,
        connectivity=8
    )

    yolo_lines = []

    # Label 0 is the background, so start from 1
    for i in range(1, num_labels):

        x = stats[i, cv2.CC_STAT_LEFT]
        y = stats[i, cv2.CC_STAT_TOP]

        width = stats[i, cv2.CC_STAT_WIDTH]
        height = stats[i, cv2.CC_STAT_HEIGHT]

        # Center of bounding box
        center_x = x + width / 2
        center_y = y + height / 2

        # Normalize to 0-1 for YOLO
        center_x = center_x / image_width
        center_y = center_y / image_height

        width = width / image_width
        height = height / image_height

        # YOLO format:
        # class center_x center_y width height
        line = (
            f"{class_id} "
            f"{center_x:.6f} "
            f"{center_y:.6f} "
            f"{width:.6f} "
            f"{height:.6f}"
        )

        yolo_lines.append(line)

    return yolo_lines


# ============================================================
# 5. GET ALL ORIGINAL TRAINING IMAGES
# ============================================================

image_files = sorted(images_folder.glob("*.jpg"))

print()
print("==============================================")
print("IDRiD → YOLO DATASET PREPARATION")
print("==============================================")
print()

print("Training images found:", len(image_files))
print()


# ============================================================
# 6. CREATE TRAIN / VALIDATION SPLIT
# ============================================================

random.seed(42)

shuffled_images = image_files.copy()

random.shuffle(shuffled_images)

# 80% training, 20% validation
split_index = int(len(shuffled_images) * 0.8)

train_files = shuffled_images[:split_index]
val_files = shuffled_images[split_index:]

print("Training images:", len(train_files))
print("Validation images:", len(val_files))
print()


# ============================================================
# 7. PROCESS IMAGES
# ============================================================

def process_image(image_path, output_image_folder, output_label_folder):

    image_stem = image_path.stem
    image_name = image_path.name

    print("----------------------------------------------")
    print("Processing:", image_name)

    # Open original image
    image = Image.open(image_path)

    image_width, image_height = image.size

    all_yolo_lines = []

    # Process the four lesion types
    for class_id, (class_name, folder_name, suffix) in classes.items():

        mask_path = find_mask(
            image_stem,
            folder_name,
            suffix
        )

        # No mask = no annotation for this lesion type
        if mask_path is None:

            print(
                f"  {class_name}: mask not found → skipped"
            )

            continue

        # Convert mask to YOLO boxes
        lines = mask_to_yolo(
            mask_path,
            class_id,
            image_width,
            image_height
        )

        print(
            f"  {class_name}: "
            f"{len(lines)} regions"
        )

        all_yolo_lines.extend(lines)

    # Copy original image
    output_image_path = output_image_folder / image_name

    shutil.copy2(
        image_path,
        output_image_path
    )

    # Create label file
    label_path = (
        output_label_folder
        / f"{image_stem}.txt"
    )

    with open(label_path, "w") as file:

        for line in all_yolo_lines:
            file.write(line + "\n")

    print(
        f"  Total annotations: "
        f"{len(all_yolo_lines)}"
    )


# ============================================================
# 8. PROCESS TRAINING IMAGES
# ============================================================

print("========== TRAINING SET ==========")

for image_path in train_files:

    process_image(
        image_path,
        train_images_folder,
        train_labels_folder
    )


# ============================================================
# 9. PROCESS VALIDATION IMAGES
# ============================================================

print()
print("========== VALIDATION SET ==========")

for image_path in val_files:

    process_image(
        image_path,
        val_images_folder,
        val_labels_folder
    )


# ============================================================
# 10. FINAL SUMMARY
# ============================================================

print()
print("==============================================")
print("DATASET PREPARATION COMPLETED!")
print("==============================================")

print("Total original images:", len(image_files))
print("Training images:", len(train_files))
print("Validation images:", len(val_files))

print()
print("Training images saved to:")
print(train_images_folder)

print()
print("Training labels saved to:")
print(train_labels_folder)

print()
print("Validation images saved to:")
print(val_images_folder)

print()
print("Validation labels saved to:")
print(val_labels_folder)

print()
print("Original IDRiD dataset was not modified.")
print("==============================================")