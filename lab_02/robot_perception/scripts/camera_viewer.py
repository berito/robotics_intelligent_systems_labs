#!/usr/bin/env python3
"""
Show the camera image in an OpenCV window, converted with cv_bridge.

Usage:
    ros2 run robot_perception camera_viewer.py
    ros2 run robot_perception camera_viewer.py --ros-args -r camera/image:=/other/image
Keys in the window: s saves the frame as frame_<n>.png in the current folder.
"""

import cv2
import rclpy
from cv_bridge import CvBridge
from rclpy.node import Node
from rclpy.signals import SignalHandlerOptions
from sensor_msgs.msg import Image

WINDOW = "camera"


class CameraViewer(Node):
    def __init__(self):
        super().__init__("camera_viewer")
        self.bridge = CvBridge()
        self.saved = 0
        self.create_subscription(Image, "camera/image", self.on_image, 10)
        self.get_logger().info("Showing camera/image; press s in the window to save a frame")

    def on_image(self, msg):
        frame = self.bridge.imgmsg_to_cv2(msg, desired_encoding="bgr8")
        cv2.imshow(WINDOW, frame)
        # waitKey also redraws the window
        if cv2.waitKey(1) & 0xFF == ord("s"):
            name = f"frame_{self.saved}.png"
            cv2.imwrite(name, frame)
            self.saved += 1
            self.get_logger().info(f"Saved {name} ({msg.width}x{msg.height})")


def main():
    # handle Ctrl+C here, before rclpy shuts the context down
    rclpy.init(signal_handler_options=SignalHandlerOptions.NO)
    node = CameraViewer()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        cv2.destroyAllWindows()
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
