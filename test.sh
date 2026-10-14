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
check "/clock publishing"        "ros2 topic hz /clock --num-messages 3 2>&1 | grep -q 'average rate'"
check "/scan_fixed publishing"   "ros2 topic hz /scan_fixed --num-messages 3 2>&1 | grep -q 'average rate'"
check "/odom publishing"         "ros2 topic hz /odom --num-messages 3 2>&1 | grep -q 'average rate'"
check "/joint_states publishing" "ros2 topic hz /joint_states --num-messages 3 2>&1 | grep -q 'average rate'"
check "/map published"           "ros2 topic info /map 2>&1 | grep -q 'Publisher count: 1'"
check "/amcl_pose published"     "ros2 topic info /amcl_pose 2>&1 | grep -q 'Publisher count: 1'"

echo ""

# TF chain
echo "--- TF Chain ---"
check "map -> odom"              "ros2 run tf2_ros tf2_echo map odom 2>&1 | grep -q 'Translation'"
check "odom -> base_link"        "ros2 run tf2_ros tf2_echo odom base_link 2>&1 | grep -q 'Translation'"
check "base_link -> lidar_link"  "ros2 run tf2_ros tf2_echo base_link lidar_link 2>&1 | grep -q 'Translation'"

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
