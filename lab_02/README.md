# Lab 2: Perception, Sensor Fusion and SLAM

Object detection and segmentation on `diffdrive_bot`'s camera with pretrained YOLOv8 models, and a node
that stops the robot when an object is in its way. The robot drives in a room with a person, a stop
sign, a fire hydrant, a suitcase, a chair and a bench.

## Requirements

- Ubuntu 22.04, ROS 2 Humble and Gazebo Harmonic (`ros-humble-ros-gzharmonic`)
- `diffdrive_bot` from Lab 1
- About 1.5 GB of disk space for the Python environment

## Installation

```bash
sudo apt install python3.10-venv ros-humble-vision-msgs ros-humble-cv-bridge ros-humble-teleop-twist-keyboard
cd ~/ros2_ws/src/robotics_intelligent_systems_labs
git pull
./lab_02/setup.sh
source /opt/ros/humble/setup.bash
cd ~/ros2_ws
colcon build --symlink-install --packages-up-to robot_perception
```

`setup.sh` creates a virtual environment in `lab_02/.venv` with ultralytics, the CPU build of PyTorch
and NumPy 1 for `cv_bridge`, and downloads `yolov8n.pt` and `yolov8n-seg.pt` into
`robot_perception/models/`. Run it before building.

Before running anything, in each terminal:

```bash
source /opt/ros/humble/setup.bash
source ~/ros2_ws/install/setup.bash
source ~/ros2_ws/src/robotics_intelligent_systems_labs/lab_02/.venv/bin/activate
```

## Usage

### Object detection

```bash
ros2 launch robot_perception detection.launch.py
```

This starts Gazebo, RViz, a camera window and the detector. The first start downloads the world's
models from Gazebo Fuel and takes a while. Drive the robot from another terminal:

```bash
ros2 run teleop_twist_keyboard teleop_twist_keyboard
```

Detections are published on `/detections` (`vision_msgs/Detection2DArray`: class name, confidence and
box in pixels) and drawn on `/detections/overlay`, which RViz shows.

### Segmentation

```bash
ros2 launch robot_perception segmentation.launch.py
```

Enable the Segments display in RViz. The boxes are published on `/segments` and the masks on
`/segments/labels`, a `mono8` image where pixel value n marks the n-th detection in `/segments` and 0
is background.

### Safety stop

With the detector's boxes:

```bash
ros2 launch robot_perception safety_stop.launch.py stop_on:=boxes
```

or with the segmentation masks:

```bash
ros2 launch robot_perception safety_stop.launch.py stop_on:=masks
```

The robot drives forward and stops when an object is in the area at the bottom of the image. The Path
display in RViz shows that area, green when it is clear and red when it is blocked. Try both and
compare where the robot stops.

### Running the nodes separately

```bash
ros2 launch robot_perception simulation.launch.py
```

then, each in its own terminal:

```bash
ros2 run robot_perception camera_viewer.py
ros2 run robot_perception detector_node.py
ros2 run robot_perception segmentation_node.py
ros2 run robot_perception safety_stop.py --ros-args -p mode:=boxes
```

### Testing a model on an image

Press `s` in the camera window to save the current frame as `frame_0.png`. From the same folder:

```bash
ros2 run robot_perception yolo_on_image.py frame_0.png
ros2 run robot_perception yolo_on_image.py frame_0.png --model yolov8n-seg.pt
```

The script prints the detections and writes `detections.png` with them drawn.

## Package layout

```
lab_02/
  setup.sh                 creates .venv and downloads the models
  requirements.txt
  robot_perception/
    models/                YOLO weights (created by setup.sh)
    launch/
      simulation.launch.py   world, robot, bridge and RViz
      detection.launch.py    simulation, camera viewer and detector
      segmentation.launch.py simulation, camera viewer and segmentation
      safety_stop.launch.py  detection or segmentation, with the safety stop
    scripts/
      camera_viewer.py       camera image in an OpenCV window
      yolo_on_image.py       YOLO on an image file, for testing the model
      detector_node.py       boxes on /detections
      segmentation_node.py   boxes, masks and label image on /segments
      safety_stop.py         drives forward, stops for objects in the path
    worlds/perception.sdf
    rviz/perception.rviz
```

## Launch arguments

| Launch file | Argument | Default | Meaning |
|-------------|----------|---------|---------|
| all three | `gui` | `true` | Open the Gazebo window and RViz |
| | `viewer` | `true` | Show the camera in an OpenCV window |
| detection | `model` | `yolov8n.pt` | Weights of the detector |
| segmentation | `model` | `yolov8n-seg.pt` | Weights of the segmentation node |
| safety_stop | `stop_on` | `boxes` | What the safety stop checks: `boxes` (detector) or `masks` (segmentation) |

## Parameters

| Node | Parameter | Default | Meaning |
|------|-----------|---------|---------|
| detector, segmentation | `model_path` | `yolov8n.pt`, `yolov8n-seg.pt` | YOLO weights file, or the name of one in `robot_perception/models/` |
| | `score_threshold` | `0.45` | Minimum confidence kept |
| | `nms_threshold` | `0.5` | Overlap above which the weaker of two boxes is removed |
| | `classes` | all | COCO class ids to keep, e.g. `[0]` for people |
| | `device` | auto | `cpu`, or a GPU id such as `0` |
| safety_stop | `mode` | `boxes` | `boxes` or `masks` |
| | `speed` | `0.2` | Forward speed in m/s |
| | `path_width` | `0.5` | Width of the path area, as a fraction of the image width |
| | `path_height` | `0.3` | Height of the path area from the bottom, as a fraction of the image height |
| | `min_pixels` | `200` | Object pixels in the area that block the path (masks) |
| | `timeout` | `1.0` | Seconds without perception after which the robot stops |

## Troubleshooting

| Problem | Fix |
|---------|-----|
| `AttributeError: _ARRAY_API not found` | `cv_bridge` loaded NumPy 2: activate `lab_02/.venv` |
| `ModuleNotFoundError: No module named 'ultralytics'` | Activate `lab_02/.venv` |
| Objects missing in Gazebo | The Fuel download did not finish; wait, then restart the launch |
| The node downloads the weights when it starts | Run `setup.sh`, then build again |

## License

The packages are released under the MIT license.
