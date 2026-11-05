#!/usr/bin/env python3
"""
Detect objects in the camera image with a pretrained YOLO model.

Each Detection2D holds the class name as class_id, the confidence as score, and the box
centre and size in pixels. The overlay is published only while something subscribes to it.

Topics:
    camera/image (sensor_msgs/Image)                 in
    detections (vision_msgs/Detection2DArray)        out
    detections/overlay (sensor_msgs/Image)           out, the image with the boxes drawn

Parameters:
    model_path       YOLO weights file, or the name of one in the package's models folder
                     (yolov8n.pt)
    score_threshold  minimum confidence kept (0.45)
    nms_threshold    overlap above which the weaker of two boxes is removed (0.5)
    classes          COCO class ids to keep, for example [0] for people; unset keeps all
    device           where the model runs: "" picks the GPU when there is one, "cpu", "0", ...

Usage:
    ros2 run robot_perception detector_node.py
    ros2 run robot_perception detector_node.py --ros-args -p score_threshold:=0.6 -p "classes:=[0, 11]"
"""

import os

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


class DetectorNode(Node):
    def __init__(self):
        super().__init__("detector")
        self.declare_parameter("model_path", "yolov8n.pt")
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

        # depth 1: drop stale frames while the model is busy
        self.create_subscription(Image, "camera/image", self.on_image, QoSProfile(depth=1))
        self.detections_pub = self.create_publisher(Detection2DArray, "detections", 10)
        self.overlay_pub = self.create_publisher(Image, "detections/overlay", 1)
        self.get_logger().info(f"Detecting with {model_path}")

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

        self.detections_pub.publish(to_detection_array(result, msg.header))
        if self.overlay_pub.get_subscription_count() > 0:
            overlay = self.bridge.cv2_to_imgmsg(result.plot(), encoding="bgr8")
            overlay.header = msg.header
            self.overlay_pub.publish(overlay)


def main():
    # handle Ctrl+C here, before rclpy shuts the context down
    rclpy.init(signal_handler_options=SignalHandlerOptions.NO)
    node = DetectorNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
