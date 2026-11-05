#!/usr/bin/env python3
"""
Drive the robot forward and stop it while an object is in its path.

The path is a fixed area of the camera image: a band at the bottom centre, the ground the
robot is about to drive over. Whether an object is in it is decided in one of two ways,
set by the mode parameter:

    boxes  an object is in the path when its box from detector_node.py overlaps the area
    masks  an object is in the path when enough of its pixels in the label image from
           segmentation_node.py fall inside the area

The robot also stops when no perception message has arrived within the timeout.

Topics:
    detections (vision_msgs/Detection2DArray)   in, mode boxes
    segments/labels (sensor_msgs/Image)         in, mode masks
    camera/camera_info (sensor_msgs/CameraInfo) in, the image size for mode boxes
    cmd_vel (geometry_msgs/Twist)               out
    path/overlay (sensor_msgs/Image)            out, the path area drawn on the camera image

Parameters:
    mode           boxes or masks (boxes)
    speed          forward speed while the path is clear, m/s (0.2)
    path_width     width of the path area, as a fraction of the image width (0.5)
    path_height    height of the path area from the bottom, as a fraction of the image height (0.3)
    min_pixels     object pixels inside the area that count as an object in the path, mode masks (200)
    timeout        seconds without perception after which the robot stops (1.0)

Usage:
    ros2 run robot_perception safety_stop.py --ros-args -p mode:=boxes
    ros2 run robot_perception safety_stop.py --ros-args -p mode:=masks
"""

import cv2
import numpy as np
import rclpy
from cv_bridge import CvBridge
from geometry_msgs.msg import Twist
from rclpy.node import Node
from rclpy.qos import QoSProfile
from rclpy.signals import SignalHandlerOptions
from sensor_msgs.msg import CameraInfo, Image
from vision_msgs.msg import Detection2DArray

CONTROL_RATE_HZ = 10.0


class SafetyStop(Node):
    def __init__(self):
        super().__init__("safety_stop")
        self.declare_parameter("mode", "boxes")
        self.declare_parameter("speed", 0.2)
        self.declare_parameter("path_width", 0.5)
        self.declare_parameter("path_height", 0.3)
        self.declare_parameter("min_pixels", 200)
        self.declare_parameter("timeout", 1.0)

        self.mode = self.get_parameter("mode").value
        if self.mode not in ("boxes", "masks"):
            raise ValueError(f"mode must be boxes or masks, not {self.mode}")

        self.bridge = CvBridge()
        self.image_size = None   # (width, height), from camera_info or the label image
        self.blocked = False
        self.blocking = ""
        self.last_perception = None

        if self.mode == "boxes":
            self.create_subscription(Detection2DArray, "detections", self.on_detections, 10)
            self.create_subscription(CameraInfo, "camera/camera_info", self.on_camera_info, 10)
        else:
            self.create_subscription(Image, "segments/labels", self.on_labels, 10)
        self.create_subscription(Image, "camera/image", self.on_image, QoSProfile(depth=1))

        self.cmd_pub = self.create_publisher(Twist, "cmd_vel", 10)
        self.overlay_pub = self.create_publisher(Image, "path/overlay", 1)
        self.create_timer(1.0 / CONTROL_RATE_HZ, self.control)
        self.get_logger().info(f"Safety stop with {self.mode}")

    def path_area(self):
        """The path area as (x1, y1, x2, y2) in pixels."""
        width, height = self.image_size
        half = self.get_parameter("path_width").value * width / 2
        top = height * (1.0 - self.get_parameter("path_height").value)
        return width / 2 - half, top, width / 2 + half, height

    def on_camera_info(self, msg):
        self.image_size = (msg.width, msg.height)

    def on_detections(self, msg):
        if self.image_size is None:
            return
        x1, y1, x2, y2 = self.path_area()
        self.blocked = False
        for detection in msg.detections:
            box = detection.bbox
            bx1 = box.center.position.x - box.size_x / 2
            by1 = box.center.position.y - box.size_y / 2
            bx2 = bx1 + box.size_x
            by2 = by1 + box.size_y
            if bx1 < x2 and bx2 > x1 and by1 < y2 and by2 > y1:
                self.blocked = True
                self.blocking = detection.results[0].hypothesis.class_id if detection.results else "object"
                break
        self.last_perception = self.get_clock().now()

    def on_labels(self, msg):
        labels = self.bridge.imgmsg_to_cv2(msg, desired_encoding="mono8")
        self.image_size = (msg.width, msg.height)
        x1, y1, x2, y2 = (int(v) for v in self.path_area())
        inside = labels[y1:y2, x1:x2]
        counts = np.bincount(inside.ravel(), minlength=2)[1:]
        self.blocked = counts.size > 0 and counts.max() >= self.get_parameter("min_pixels").value
        if self.blocked:
            self.blocking = f"object {int(counts.argmax()) + 1}"
        self.last_perception = self.get_clock().now()

    def on_image(self, msg):
        if self.image_size is None or self.overlay_pub.get_subscription_count() == 0:
            return
        frame = self.bridge.imgmsg_to_cv2(msg, desired_encoding="bgr8")
        x1, y1, x2, y2 = (int(v) for v in self.path_area())
        colour = (0, 0, 255) if self.blocked else (0, 255, 0)
        cv2.rectangle(frame, (x1, y1), (x2 - 1, y2 - 1), colour, 2)
        overlay = self.bridge.cv2_to_imgmsg(frame, encoding="bgr8")
        overlay.header = msg.header
        self.overlay_pub.publish(overlay)

    def control(self):
        cmd = Twist()
        stale = (
            self.last_perception is None
            or (self.get_clock().now() - self.last_perception).nanoseconds * 1e-9
            > self.get_parameter("timeout").value
        )
        if not stale and not self.blocked:
            cmd.linear.x = self.get_parameter("speed").value
        elif not stale:
            self.get_logger().info(f"Stopped: {self.blocking} in the path", throttle_duration_sec=2.0)
        self.cmd_pub.publish(cmd)

    def stop(self):
        self.cmd_pub.publish(Twist())


def main():
    # handle Ctrl+C here, before rclpy shuts the context down
    rclpy.init(signal_handler_options=SignalHandlerOptions.NO)
    node = SafetyStop()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.stop()
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
