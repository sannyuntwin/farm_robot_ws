#!/bin/bash
source /opt/ros/jazzy/setup.bash
source ~/ros2/farm_robot_ws/install/setup.bash

PASS=0
FAIL=0

check() {
    local label=$1
    local cmd=$2
    if eval "$cmd" &>/dev/null; then
        echo "[PASS] $label"
        PASS=$((PASS + 1))
    else
        echo "[FAIL] $label"
        FAIL=$((FAIL + 1))
    fi
}

echo "=== Farm Robot System Check ==="
echo ""

# Topics
echo "--- Topics ---"
check "/clock publishing"        "timeout 5 ros2 topic echo /clock --once 2>&1 | grep -q 'sec'"
check "/scan_fixed publishing"   "timeout 5 ros2 topic echo /scan_fixed --once 2>&1 | grep -q 'frame_id'"
check "/odom publishing"         "timeout 5 ros2 topic echo /odom --once 2>&1 | grep -q 'frame_id'"
check "/joint_states publishing" "timeout 5 ros2 topic echo /joint_states --once 2>&1 | grep -q 'name'"
check "/map published"           "ros2 topic info /map 2>&1 | grep -q 'Publisher count: 1'"
check "/amcl_pose published"     "ros2 topic info /amcl_pose 2>&1 | grep -q 'Publisher count: 1'"

echo ""

# TF chain
echo "--- TF Chain ---"
check "map -> odom"              "timeout 5 ros2 run tf2_ros tf2_echo map odom 2>&1 | grep -q 'Translation'"
check "odom -> base_link"        "timeout 5 ros2 run tf2_ros tf2_echo odom base_link 2>&1 | grep -q 'Translation'"
check "base_link -> lidar_link"  "timeout 5 ros2 run tf2_ros tf2_echo base_link lidar_link 2>&1 | grep -q 'Translation'"

echo ""

# Nav2 nodes
echo "--- Nav2 Nodes ---"
check "map_server active"        "ros2 lifecycle get /map_server 2>&1 | grep -q 'active'"
check "amcl active"              "ros2 lifecycle get /amcl 2>&1 | grep -q 'active'"
check "controller_server active" "ros2 lifecycle get /controller_server 2>&1 | grep -q 'active'"
check "planner_server active"    "ros2 lifecycle get /planner_server 2>&1 | grep -q 'active'"
check "bt_navigator active"      "ros2 lifecycle get /bt_navigator 2>&1 | grep -q 'active'"

echo ""
echo "=== Results: $PASS passed, $FAIL failed ==="
