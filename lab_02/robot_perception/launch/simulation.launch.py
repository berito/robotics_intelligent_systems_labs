"""
Run diffdrive_bot in the perception world: start the world, spawn the robot from its URDF,
bridge its topics to ROS 2, and show the model, lidar scan, camera image and the
perception overlays in RViz.

The robot and its bridge configuration come from diffdrive_bot; the world and the RViz
configuration are this package's. As in diffdrive_bot's gazebo.launch.py, the Gazebo window
opens after the robot is spawned, so that it receives the whole scene.

Usage:
    ros2 launch robot_perception simulation.launch.py
    ros2 launch robot_perception simulation.launch.py gui:=false
"""

import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import (DeclareLaunchArgument, ExecuteProcess, RegisterEventHandler,
                            Shutdown, TimerAction)
from launch.conditions import IfCondition
from launch.event_handlers import OnProcessExit
from launch.substitutions import Command, LaunchConfiguration
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue

# Time for the server to load the world and its Fuel models before spawning
SPAWN_DELAY_S = 5.0


def generate_launch_description():
    bot_share = get_package_share_directory("diffdrive_bot")
    pkg_share = get_package_share_directory("robot_perception")
    gui = LaunchConfiguration("gui")

    robot_description = ParameterValue(
        Command(["xacro ", os.path.join(bot_share, "urdf", "diffdrive_bot.urdf.xacro")]),
        value_type=str,
    )

    gazebo_server = ExecuteProcess(
        cmd=["gz", "sim", "-s", "-r", os.path.join(pkg_share, "worlds", "perception.sdf")],
        name="gazebo_server",
        output="screen",
        on_exit=Shutdown(),
    )

    gazebo_gui = ExecuteProcess(
        cmd=["gz", "sim", "-g"],
        name="gazebo_gui",
        output="screen",
        on_exit=Shutdown(),
        condition=IfCondition(gui),
    )

    robot_state_publisher = Node(
        package="robot_state_publisher",
        executable="robot_state_publisher",
        parameters=[{"robot_description": robot_description, "use_sim_time": True}],
        output="screen",
    )

    spawn = Node(
        package="ros_gz_sim",
        executable="create",
        arguments=["-world", "perception", "-topic", "robot_description", "-name", "diffdrive_bot", "-z", "0.05"],
        output="screen",
    )

    bridge = Node(
        package="ros_gz_bridge",
        executable="parameter_bridge",
        parameters=[{"config_file": os.path.join(bot_share, "config", "bridge.yaml")}],
        output="screen",
    )

    rviz = Node(
        package="rviz2",
        executable="rviz2",
        arguments=["-d", os.path.join(pkg_share, "rviz", "perception.rviz"), "-f", "odom"],
        parameters=[{"use_sim_time": True}],
        output="screen",
        condition=IfCondition(gui),
    )

    return LaunchDescription([
        DeclareLaunchArgument("gui", default_value="true",
                              description="Open the Gazebo window and RViz"),
        gazebo_server,
        robot_state_publisher,
        TimerAction(period=SPAWN_DELAY_S, actions=[spawn]),
        RegisterEventHandler(OnProcessExit(target_action=spawn, on_exit=[gazebo_gui])),
        bridge,
        rviz,
    ])
