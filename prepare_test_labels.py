from pathlib import Path
from PIL import Image
import numpy as np
import cv2
import re

# ==========================================
# Project folders
# ==========================================

project_folder = Path(__file__).parent

idrid_folder = project_folder / "IDRiD"

images_folder = (
    idrid_folder
    / "1. Original Images"
    / "b. Testing Set"
)

groundtruth_folder = (
    idrid_folder
    / "2. All Segmentation Groundtruths"
    / "b. Testing Set"
)

output_labels = (
    project_folder
    / "labels"
    / "test"
)

output_labels.mkdir(
    parents=True,
    exist_ok=True
)


# ==========================================
# Four YOLO classes
# ==========================================

classes = {
    0: ("Microaneurysm", "1. Microaneurysms", "MA"),
    1: ("Haemorrhage", "2. Haemorrhages", "HE"),
    2: ("Hard Exudate", "3. Hard Exudates", "EX"),
    3: ("Soft Exudate", "4. Soft Exudates", "SE")
}


# ==========================================
# Convert mask to YOLO boxes
# ==========================================

def mask_to_yolo(
    mask_path,
    class_id,
    image_width,
    image_height
):

    mask = Image.open(mask_path)

    mask_array = np.array(mask)

    # Handle grayscale and RGBA masks
    if mask_array.ndim == 3:

        binary_mask = (
            np.any(
                mask_array[:, :, :3] > 0,
                axis=2
            )
        ).astype(np.uint8)

    else:

        binary_mask = (
            mask_array > 0
        ).astype(np.uint8)


    # Find connected regions
    num_labels, labels, stats, centroids = (
        cv2.connectedComponentsWithStats(
            binary_mask,
            connectivity=8
        )
    )


    yolo_lines = []


    # Skip label 0 because it is background
    for i in range(1, num_labels):

        x = stats[
            i,
            cv2.CC_STAT_LEFT
        ]

        y = stats[
            i,
            cv2.CC_STAT_TOP
        ]

        width = stats[
            i,
            cv2.CC_STAT_WIDTH
        ]

        height = stats[
            i,
            cv2.CC_STAT_HEIGHT
        ]


        # Bounding-box center
        center_x = x + width / 2
        center_y = y + height / 2


        # Normalize coordinates
        center_x = center_x / image_width
        center_y = center_y / image_height

        width = width / image_width
        height = height / image_height


        # YOLO format
        line = (
            f"{class_id} "
            f"{center_x:.6f} "
            f"{center_y:.6f} "
            f"{width:.6f} "
            f"{height:.6f}"
        )


        yolo_lines.append(line)


    return yolo_lines


# ==========================================
# Find mask
# ==========================================

def find_mask(
    image_stem,
    folder_name,
    suffix
):

    folder = (
        groundtruth_folder
        / folder_name
    )


    if not folder.exists():

        return None


    possible_names = [

        f"{image_stem}_{suffix}.tif",

        f"{image_stem}{suffix}.tif"
    ]


    for name in possible_names:

        path = folder / name


        if path.exists():

            return path


    return None


# ==========================================
# Find testing images
# ==========================================

image_files = sorted(
    images_folder.glob("*.jpg"),
    key=lambda p: int(
        re.search(
            r"(\d+)",
            p.stem
        ).group(1)
    )
)


print()
print("==============================================")
print("IDRiD TEST SET → YOLO LABEL PREPARATION")
print("==============================================")
print()

print(
    "Test images found:",
    len(image_files)
)

print()


# ==========================================
# Process every test image
# ==========================================

for image_path in image_files:

    image_stem = image_path.stem


    print("----------------------------------------------")

    print(
        "Processing:",
        image_path.name
    )


    image = Image.open(image_path)

    image_width, image_height = image.size


    all_yolo_lines = []


    # Process four classes
    for (
        class_id,
        (
            class_name,
            folder_name,
            suffix
        )
    ) in classes.items():


        mask_path = find_mask(
            image_stem,
            folder_name,
            suffix
        )


        if mask_path is None:

            print(
                f"  {class_name}: "
                f"mask not found → skipped"
            )

            continue


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


    # ======================================
    # Save YOLO label
    # ======================================

    label_path = (
        output_labels
        / f"{image_stem}.txt"
    )


    with open(
        label_path,
        "w"
    ) as file:

        for line in all_yolo_lines:

            file.write(
                line + "\n"
            )


    print(
        "  Total annotations:",
        len(all_yolo_lines)
    )


# ==========================================
# Final summary
# ==========================================

print()

print("==============================================")

print(
    "TEST LABEL PREPARATION COMPLETED!"
)

print("==============================================")

print(
    "Test images:",
    len(image_files)
)

print()

print(
    "Labels saved to:"
)

print(output_labels)

print()

print("==============================================")