#!/bin/bash
source /opt/ros/jazzy/setup.bash
cd ~/ros2/farm_robot_ws
colcon build --merge-install --packages-select farm_robot
source install/setup.bash
ros2 launch farm_robot bringup.launch.py
