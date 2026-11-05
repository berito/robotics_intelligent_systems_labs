cmake_minimum_required(VERSION 3.10)
project(robot_perception)

find_package(ament_cmake REQUIRED)

install(PROGRAMS
  scripts/camera_viewer.py
  scripts/yolo_on_image.py
  scripts/detector_node.py
  scripts/segmentation_node.py
  scripts/safety_stop.py
  DESTINATION lib/${PROJECT_NAME}
)

install(DIRECTORY
  launch
  rviz
  worlds
  DESTINATION share/${PROJECT_NAME}
)

# downloaded by setup.sh
install(DIRECTORY models DESTINATION share/${PROJECT_NAME} OPTIONAL)

ament_package()
