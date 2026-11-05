# diffdrive_bot

A two-wheeled differential-drive robot with a lidar and a camera, for ROS 2 Humble and Gazebo Harmonic.
The robot is described in [urdf/diffdrive_bot.urdf.xacro](urdf/diffdrive_bot.urdf.xacro). Python
nodes drive it using the message, service and action from [lab_interfaces](../lab_interfaces).

## Requirements

- Ubuntu 22.04 with ROS 2 Humble (`ros-humble-desktop`)
- Gazebo Harmonic, from the Gazebo apt repository:

```bash
sudo curl https://packages.osrfoundation.org/gazebo.gpg --output /usr/share/keyrings/pkgs-osrf-archive-keyring.gpg
echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/pkgs-osrf-archive-keyring.gpg] http://packages.osrfoundation.org/gazebo/ubuntu-stable $(lsb_release -cs) main" | sudo tee /etc/apt/sources.list.d/gazebo-stable.list > /dev/null
sudo apt update
sudo apt install ros-humble-ros-gzharmonic ros-humble-xacro ros-humble-joint-state-publisher-gui ros-humble-teleop-twist-keyboard
```

Install these with apt, not `rosdep install`: rosdep pulls in `ros-humble-ros-gz`, which conflicts
with Harmonic.

## Installation

```bash
source /opt/ros/humble/setup.bash
mkdir -p ~/ros2_ws/src && cd ~/ros2_ws/src
git clone https://github.com/berito/robotics_intelligent_systems_labs.git
cd ~/ros2_ws
colcon build --symlink-install --packages-up-to diffdrive_bot
```

In each terminal:

```bash
source /opt/ros/humble/setup.bash
source ~/ros2_ws/install/setup.bash
```

## Usage

### View the model

```bash
ros2 launch diffdrive_bot display.launch.py
```

Opens RViz with the model and its TF frames, and a Joint State Publisher window with a slider for each
wheel.

### Simulate in Gazebo

```bash
ros2 launch diffdrive_bot gazebo.launch.py
```

Starts Gazebo with [worlds/obstacles.sdf](worlds/obstacles.sdf) (a red box ahead, a green cylinder to
the left, a wall behind), the bridge from [config/bridge.yaml](config/bridge.yaml), and RViz with the
lidar scan and the camera image. Drive the robot from another terminal:

```bash
ros2 run teleop_twist_keyboard teleop_twist_keyboard
```

`i` forward, `,` back, `j`/`l` turn, `k` stop, `q`/`z` faster/slower. Keep the teleop terminal focused.

To inspect the running system:

```bash
ros2 topic list
ros2 topic echo /odom --once
ros2 topic hz /scan
ros2 run tf2_tools view_frames
ros2 run tf2_ros tf2_echo odom base_link
```

### Run the nodes

```bash
ros2 launch diffdrive_bot control.launch.py
```

Starts the simulation with three nodes:

- `obstacle_detector.py` publishes the nearest obstacle ahead on `/obstacle`
- `drive_controller.py` drives forward on `/cmd_vel` while `/drive_enable` is on, and stops in front
  of an obstacle
- `drive_distance_server.py` serves the `/drive_distance` action

From another terminal:

```bash
ros2 topic echo /obstacle --once
ros2 service call /drive_enable std_srvs/srv/SetBool "{data: true}"
ros2 service call /set_speed lab_interfaces/srv/SetSpeed "{speed: 0.5}"
ros2 run diffdrive_bot drive_distance_client.py 1.0
```

The robot starts 1.75 m from the red box. With `/drive_enable` it drives forward and stops at 0.5 m.
The action client prints the distance travelled as feedback, then the result; a goal that would reach
the box is aborted. The same goal can be sent without the client:

```bash
ros2 action send_goal --feedback /drive_distance lab_interfaces/action/DriveDistance "{distance: 1.0}"
```

Speed and stopping distance are launch arguments:

```bash
ros2 launch diffdrive_bot control.launch.py speed:=0.2 stop_distance:=0.8
```

## Package layout

```
diffdrive_bot/
  urdf/diffdrive_bot.urdf.xacro   the robot: parts, joints, sensors, Gazebo plugins
  launch/
    display.launch.py             RViz with the model only
    gazebo.launch.py              Gazebo, bridge and RViz
    control.launch.py             simulation with the nodes
  scripts/                        the nodes and the action client
  config/bridge.yaml              topics bridged between Gazebo and ROS 2
  worlds/obstacles.sdf
  rviz/diffdrive_bot.rviz
```

## Robot parts

| Part | Shape | Size |
|------|-------|------|
| Chassis | box | 0.40 x 0.30 x 0.10 m, 5 kg |
| Driven wheels | 2 cylinders | radius 0.08 m, 0.34 m apart |
| Caster | sphere at the rear | radius 0.04 m, frictionless |
| Lidar | cylinder on top | 360 samples, 0.12 to 10 m, 10 Hz |
| Camera | box on the front | 640 x 480, 60 degree field of view, 15 Hz |

## Interfaces

The nodes use one message, one service and one action, all defined in the lab_interfaces package.

[msg/ObstacleInfo.msg](../lab_interfaces/msg/ObstacleInfo.msg) is the nearest obstacle in front of the robot:

```
std_msgs/Header header
float32 distance  # m, inf when nothing is in range
float32 angle     # rad, 0 straight ahead, positive to the left
bool too_close    # distance is below the stop distance
```

[srv/SetSpeed.srv](../lab_interfaces/srv/SetSpeed.srv) sets the forward speed:

```
float32 speed     # request, m/s
---
bool success
string message
```

[action/DriveDistance.action](../lab_interfaces/action/DriveDistance.action) drives straight forward for a distance:

```
float32 distance    # goal, m
---
float32 travelled   # result, m
bool reached
---
float32 travelled   # feedback, m
```

## Parameters

| Node | Parameter | Default | Meaning |
|------|-----------|---------|---------|
| `obstacle_detector.py` | `front_angle` | 0.35 | half-width of the sector in front of the robot that is checked, rad |
| `obstacle_detector.py` | `stop_distance` | 0.5 | obstacles closer than this, in m, are `too_close` |
| `drive_controller.py` | `speed` | 0.3 | forward speed, m/s |
| `drive_controller.py` | `max_speed` | 1.0 | highest speed `/set_speed` accepts, m/s |
| `drive_distance_server.py` | `speed` | 0.3 | forward speed, m/s |
| `drive_distance_server.py` | `heading_gain` | 1.0 | turning speed per radian of heading error, 1/s; keeps the robot on its starting heading |

## Topics

| Topic | Type | Direction |
|-------|------|-----------|
| `/cmd_vel` | `geometry_msgs/msg/Twist` | ROS 2 to Gazebo |
| `/odom` | `nav_msgs/msg/Odometry` | Gazebo to ROS 2 |
| `/tf` | `tf2_msgs/msg/TFMessage` | Gazebo to ROS 2 (`odom` to `base_footprint`) |
| `/joint_states` | `sensor_msgs/msg/JointState` | Gazebo to ROS 2 |
| `/scan` | `sensor_msgs/msg/LaserScan` | Gazebo to ROS 2 |
| `/camera/image` | `sensor_msgs/msg/Image` | Gazebo to ROS 2 |
| `/camera/camera_info` | `sensor_msgs/msg/CameraInfo` | Gazebo to ROS 2 |
| `/clock` | `rosgraph_msgs/msg/Clock` | Gazebo to ROS 2 |
| `/obstacle` | `lab_interfaces/msg/ObstacleInfo` | published by `obstacle_detector.py` |

| Service | Type |
|---------|------|
| `/drive_enable` | `std_srvs/srv/SetBool` |
| `/set_speed` | `lab_interfaces/srv/SetSpeed` |

| Action | Type |
|--------|------|
| `/drive_distance` | `lab_interfaces/action/DriveDistance` |

## Frames

```
odom -> base_footprint -> base_link -> left_wheel, right_wheel, caster, lidar_link, camera_link
```

## Troubleshooting

| Problem | Fix |
|---------|-----|
| `Package 'diffdrive_bot' not found` | Source the terminal |
| Build ends with `1 package had stderr output` | CMake warnings from the Humble message generator; the build succeeded |
| Robot does not move with teleop | Focus the teleop terminal; check `ros2 topic echo /cmd_vel` |
| RViz shows "No transform" or an empty scan | Wait for Gazebo to load; check the simulation is playing |
| `Goal rejected` from the action client | Distance must be above zero; wait until odometry arrives |
| `/obstacle` not found | Check `control.launch.py` is running; try `ros2 daemon stop` |
| Gazebo will not start, or two robots appear | `pkill -f "gz sim"` |
| URDF change does not show up | Restart the launch; without `--symlink-install`, rebuild |

## License

The package is released under the MIT license.
