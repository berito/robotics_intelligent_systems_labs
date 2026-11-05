"""
Part 1, safety stop: the robot drives forward and stops for objects in its path, found by the
detector (stop_on:=boxes) or the segmentation node (stop_on:=masks). Teleop is not needed.

Usage:
    ros2 launch robot_perception safety_stop.launch.py stop_on:=boxes
    ros2 launch robot_perception safety_stop.launch.py stop_on:=masks
"""

import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, PythonExpression
from launch_ros.actions import Node


def generate_launch_description():
    pkg_share = get_package_share_directory("robot_perception")
    stop_on = LaunchConfiguration("stop_on")

    # boxes: detection.launch.py, masks: segmentation.launch.py
    perception = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(PythonExpression([
            "'", os.path.join(pkg_share, "launch"), "/' + ('detection' if '", stop_on,
            "' == 'boxes' else 'segmentation') + '.launch.py'"
        ])),
        launch_arguments={"gui": LaunchConfiguration("gui"), "viewer": LaunchConfiguration("viewer")}.items(),
    )

    stop = Node(
        package="robot_perception",
        executable="safety_stop.py",
        parameters=[{"mode": stop_on, "use_sim_time": True}],
        output="screen",
    )

    return LaunchDescription([
        DeclareLaunchArgument("gui", default_value="true", description="Open the Gazebo window and RViz"),
        DeclareLaunchArgument("viewer", default_value="true", description="Show the camera in an OpenCV window"),
        DeclareLaunchArgument("stop_on", default_value="boxes", choices=["boxes", "masks"],
                              description="What the safety stop checks: boxes or masks"),
        perception,
        stop,
    ])
