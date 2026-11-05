#!/usr/bin/env python3
"""
Run a pretrained YOLO model on one image, outside ROS.

Prints each detection (class, confidence, box in pixels) and saves the image with the boxes,
and the masks for a segmentation model, drawn on it. The model is a weights file, or the name
of one in the package's models folder.

Usage:
    ros2 run robot_perception yolo_on_image.py frame_0.png
    ros2 run robot_perception yolo_on_image.py frame_0.png --model yolov8n-seg.pt --out segmented.png
"""

import argparse
import os

import cv2
from ament_index_python.packages import get_package_share_directory
from ultralytics import YOLO


def find_model(name):
    """Return name if it is a file, else the file of that name in the package's models folder."""
    if os.path.isfile(name):
        return name
    return os.path.join(get_package_share_directory("robot_perception"), "models", name)


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("image", help="image file to run the model on")
    parser.add_argument("--model", default="yolov8n.pt", help="YOLO weights file")
    parser.add_argument("--conf", type=float, default=0.25, help="minimum confidence kept")
    parser.add_argument("--out", default="detections.png", help="where to save the annotated image")
    args = parser.parse_args()

    model = YOLO(find_model(args.model))
    result = model(args.image, conf=args.conf, verbose=False)[0]

    for box in result.boxes:
        x1, y1, x2, y2 = box.xyxy[0].tolist()
        name = result.names[int(box.cls)]
        print(f"{name:15s} {float(box.conf):.2f}  box ({x1:.0f}, {y1:.0f}) to ({x2:.0f}, {y2:.0f})")
    print(f"{len(result.boxes)} objects, {result.speed['inference']:.1f} ms inference")

    cv2.imwrite(args.out, result.plot())
    print(f"Saved {args.out}")


if __name__ == "__main__":
    main()
