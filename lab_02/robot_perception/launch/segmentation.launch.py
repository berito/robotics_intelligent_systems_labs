"""
Part 1, segmentation: diffdrive_bot in the perception world with the camera viewer and the
YOLO segmentation node.

Usage:
    ros2 launch robot_perception segmentation.launch.py
    ros2 run teleop_twist_keyboard teleop_twist_keyboard
"""

import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.conditions import IfCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    pkg_share = get_package_share_directory("robot_perception")

    simulation = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(os.path.join(pkg_share, "launch", "simulation.launch.py")),
        launch_arguments={"gui": LaunchConfiguration("gui")}.items(),
    )

    camera_viewer = Node(
        package="robot_perception",
        executable="camera_viewer.py",
        parameters=[{"use_sim_time": True}],
        output="screen",
        condition=IfCondition(LaunchConfiguration("viewer")),
    )

    segmentation = Node(
        package="robot_perception",
        executable="segmentation_node.py",
        parameters=[{"model_path": LaunchConfiguration("model"), "use_sim_time": True}],
        output="screen",
    )

    return LaunchDescription([
        DeclareLaunchArgument("gui", default_value="true", description="Open the Gazebo window and RViz"),
        DeclareLaunchArgument("viewer", default_value="true", description="Show the camera in an OpenCV window"),
        DeclareLaunchArgument("model", default_value="yolov8n-seg.pt", description="Weights of the segmentation model"),
        simulation,
        camera_viewer,
        segmentation,
    ])
