# Lab 1: ROS 2 and Custom Robot Simulation

ROS 2 basics on turtlesim, then `diffdrive_bot`: a two-wheeled robot with a lidar and a camera,
described in URDF, simulated in Gazebo and driven by Python nodes that use topics, services and actions.

## Contents

- ROS 2 beginner tutorials on turtlesim, in their Python version:
  [Humble](https://docs.ros.org/en/humble/Tutorials.html), [Jazzy](https://docs.ros.org/en/jazzy/Tutorials.html)
- [diffdrive_bot](diffdrive_bot): the robot, its Gazebo world, launch files and nodes, with a walkthrough
  in its [README](diffdrive_bot/README.md)
- [lab_interfaces](lab_interfaces): `ObstacleInfo.msg`, `SetSpeed.srv` and `DriveDistance.action`
- [EXERCISE.md](EXERCISE.md): the exercise, handed in as a GitHub repository

## Requirements

- Ubuntu 22.04, ROS 2 Humble and Gazebo Harmonic (`ros-humble-ros-gzharmonic`)

The system packages are listed in the [diffdrive_bot README](diffdrive_bot/README.md).

## Installation

```bash
source /opt/ros/humble/setup.bash
mkdir -p ~/ros2_ws/src && cd ~/ros2_ws/src
git clone https://github.com/berito/robotics_intelligent_systems_labs.git
cd ~/ros2_ws
colcon build --symlink-install --packages-up-to diffdrive_bot
source install/setup.bash
```

Usage is in the [diffdrive_bot README](diffdrive_bot/README.md#usage).

## License

The packages are released under the MIT license.
