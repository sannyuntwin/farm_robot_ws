#!/bin/bash
source /opt/ros/jazzy/setup.bash
source ~/ros2/farm_robot_ws/install/setup.bash

MODE=${1:-nav}   # usage: ./test.sh [nav|slam|crop|coverage]  default: nav

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

echo "=== Farm Robot System Check ($MODE mode) ==="
echo ""

echo "--- Topics ---"
check "/clock publishing"        "ros2 topic info /clock 2>&1 | grep -q 'Publisher count: 1'"
check "/scan_fixed publishing"   "ros2 topic info /scan_fixed 2>&1 | grep -q 'Publisher count: 1'"
check "/odom publishing"         "ros2 topic info /odom 2>&1 | grep -q 'Publisher count: 1'"
check "/joint_states publishing" "ros2 topic info /joint_states 2>&1 | grep -q 'Publisher count: 1'"
if [ "$MODE" != "crop" ] && [ "$MODE" != "coverage" ]; then
    check "/map published"       "ros2 topic info /map 2>&1 | grep -q 'Publisher count: 1'"
fi

echo ""

echo "--- TF Chain ---"
if [ "$MODE" != "crop" ] && [ "$MODE" != "coverage" ]; then
    check "map -> odom"          "timeout 10 ros2 run tf2_ros tf2_echo map odom 2>&1 | grep -q 'Translation'"
fi
check "odom -> base_link"        "timeout 10 ros2 run tf2_ros tf2_echo odom base_link 2>&1 | grep -q 'Translation'"
check "base_link -> lidar_link"  "timeout 10 ros2 run tf2_ros tf2_echo base_link lidar_link 2>&1 | grep -q 'Translation'"

echo ""

if [ "$MODE" = "slam" ]; then
    echo "--- SLAM ---"
    check "slam_toolbox running"     "ros2 node list 2>&1 | grep -q '/slam_toolbox'"
    check "/map publishing (SLAM)"   "ros2 topic info /map 2>&1 | grep -q 'Publisher count: 1'"
elif [ "$MODE" = "crop" ]; then
    echo "--- Crop Row Follower ---"
    check "crop_row_follower running"  "ros2 node list 2>&1 | grep -q '/crop_row_follower'"
    check "/cmd_vel publishing"        "ros2 topic info /cmd_vel 2>&1 | grep -q 'Publisher count: 1'"
elif [ "$MODE" = "coverage" ]; then
    echo "--- Field Coverage ---"
    check "field_coverage running"  "ros2 node list 2>&1 | grep -q '/field_coverage'"
    check "/cmd_vel publishing"     "ros2 topic info /cmd_vel 2>&1 | grep -q 'Publisher count: 1'"
else
    echo "--- Nav2 Nodes ---"
    check "/amcl_pose published"        "ros2 topic info /amcl_pose 2>&1 | grep -q 'Publisher count: 1'"
    check "map_server active"           "ros2 lifecycle get /map_server 2>&1 | grep -q 'active'"
    check "amcl active"                 "ros2 lifecycle get /amcl 2>&1 | grep -q 'active'"
    check "controller_server active"    "ros2 lifecycle get /controller_server 2>&1 | grep -q 'active'"
    check "planner_server active"       "ros2 lifecycle get /planner_server 2>&1 | grep -q 'active'"
    check "bt_navigator active"         "ros2 lifecycle get /bt_navigator 2>&1 | grep -q 'active'"
    check "follow_waypoints available"  "ros2 action info /follow_waypoints 2>&1 | grep -q 'waypoint_follower'"
fi

echo ""
echo "=== Results: $PASS passed, $FAIL failed ==="
