#!/usr/bin/env python3
"""
Segment the objects in the camera image with a pretrained YOLO segmentation model.

The masks are published as a mono8 label image of the camera's size: pixel value n marks
object n, detection n - 1 of segments; 0 is background.

Topics:
    camera/image (sensor_msgs/Image)                 in
    segments (vision_msgs/Detection2DArray)          out, the boxes, as from detector_node.py
    segments/labels (sensor_msgs/Image, mono8)       out, the label image
    segments/overlay (sensor_msgs/Image)             out, the image with the masks drawn

Parameters: as detector_node.py, with model_path yolov8n-seg.pt.

Usage:
    ros2 run robot_perception segmentation_node.py
"""

import os

import cv2
import numpy as np
import rclpy
from ament_index_python.packages import get_package_share_directory
from cv_bridge import CvBridge
from rclpy.exceptions import ParameterUninitializedException
from rclpy.node import Node
from rclpy.parameter import Parameter
from rclpy.qos import QoSProfile
from rclpy.signals import SignalHandlerOptions
from sensor_msgs.msg import Image
from ultralytics import YOLO
from vision_msgs.msg import Detection2D, Detection2DArray, ObjectHypothesisWithPose


def find_model(name):
    """Return name if it is a file, else the file of that name in the package's models folder."""
    if os.path.isfile(name):
        return name
    return os.path.join(get_package_share_directory("robot_perception"), "models", name)

# mono8 labels: 0 is background
MAX_OBJECTS = 255


def to_detection_array(result, header):
    """Convert the boxes of one ultralytics result to a Detection2DArray."""
    array = Detection2DArray(header=header)
    for box in result.boxes:
        cx, cy, w, h = box.xywh[0].tolist()
        detection = Detection2D(header=header)
        detection.bbox.center.position.x = cx
        detection.bbox.center.position.y = cy
        detection.bbox.size_x = w
        detection.bbox.size_y = h
        hypothesis = ObjectHypothesisWithPose()
        hypothesis.hypothesis.class_id = result.names[int(box.cls)]
        hypothesis.hypothesis.score = float(box.conf)
        detection.results.append(hypothesis)
        array.detections.append(detection)
    return array


def label_image(result, height, width):
    """Draw each object's mask into a label image, object n with value n."""
    labels = np.zeros((height, width), dtype=np.uint8)
    if result.masks is None:
        return labels
    # masks.xy is already in original image pixels
    for n, outline in enumerate(result.masks.xy[:MAX_OBJECTS], start=1):
        if len(outline) >= 3:
            cv2.fillPoly(labels, [outline.astype(np.int32)], n)
    return labels


class SegmentationNode(Node):
    def __init__(self):
        super().__init__("segmentation")
        self.declare_parameter("model_path", "yolov8n-seg.pt")
        self.declare_parameter("score_threshold", 0.45)
        self.declare_parameter("nms_threshold", 0.5)
        self.declare_parameter("classes", Parameter.Type.INTEGER_ARRAY)
        self.declare_parameter("device", "")
        try:
            self.classes = list(self.get_parameter("classes").value)
        except ParameterUninitializedException:
            self.classes = None

        model_path = find_model(self.get_parameter("model_path").value)
        self.model = YOLO(model_path)
        self.bridge = CvBridge()

        self.create_subscription(Image, "camera/image", self.on_image, QoSProfile(depth=1))
        self.segments_pub = self.create_publisher(Detection2DArray, "segments", 10)
        self.labels_pub = self.create_publisher(Image, "segments/labels", 10)
        self.overlay_pub = self.create_publisher(Image, "segments/overlay", 1)
        self.get_logger().info(f"Segmenting with {model_path}")

    def on_image(self, msg):
        frame = self.bridge.imgmsg_to_cv2(msg, desired_encoding="bgr8")
        result = self.model(
            frame,
            conf=self.get_parameter("score_threshold").value,
            iou=self.get_parameter("nms_threshold").value,
            classes=self.classes,
            device=self.get_parameter("device").value or None,
            verbose=False,
        )[0]

        self.segments_pub.publish(to_detection_array(result, msg.header))
        labels = self.bridge.cv2_to_imgmsg(label_image(result, msg.height, msg.width), encoding="mono8")
        labels.header = msg.header
        self.labels_pub.publish(labels)
        if self.overlay_pub.get_subscription_count() > 0:
            overlay = self.bridge.cv2_to_imgmsg(result.plot(), encoding="bgr8")
            overlay.header = msg.header
            self.overlay_pub.publish(overlay)


def main():
    # handle Ctrl+C here, before rclpy shuts the context down
    rclpy.init(signal_handler_options=SignalHandlerOptions.NO)
    node = SegmentationNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
