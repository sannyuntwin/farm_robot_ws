# Farm Robot

A fully autonomous farm robot simulation built with **ROS 2 Jazzy**, **Gazebo Harmonic**, **Nav2**, and **SLAM Toolbox**. The robot operates in a simulated 10 m × 10 m farm world with crop rows, using LiDAR for perception, AMCL for localisation, and Nav2 for path planning.

## Features

| # | Feature | Node | Description |
|---|---------|------|-------------|
| 1 | Simulation | Gazebo + bridges | Physics, LiDAR, odometry, TF |
| 2 | SLAM Mapping | `slam_toolbox` | Online async map building |
| 3 | Autonomous Navigation | Nav2 stack | AMCL + DWB planner + bt_navigator |
| 4 | Waypoint Following | `farm_waypoints` | Patrol 6-point crop-aisle route |
| 5 | Crop Row Following | `crop_row_follower` | LiDAR-guided row navigation |
| 6 | Field Coverage | `field_coverage` | Systematic coverage of the field |
| 7 | Data Logging | `data_logger` | CSV log of odometry + scan |
| 8 | Return to Home | `return_to_home` | Navigate back to spawn point |
| 9 | Web Dashboard | `web_dashboard` | Live browser UI at port 8080 |

## Technology Stack

- **OS:** Ubuntu 24.04 (developed on Windows 11 with WSL / direct Ubuntu)
- **ROS 2:** Jazzy Jalisco
- **Simulator:** Gazebo Harmonic (gz-sim 8)
- **Navigation:** Nav2 (AMCL, DWB, NavFn, bt_navigator)
- **Mapping:** SLAM Toolbox (online async)
- **Visualisation:** RViz2
- **Language:** Python 3.12

## Project Structure

```text
farm_robot_ws/
├── test.sh                          # system-check test runner
└── src/
    └── farm_robot/
        ├── config/
        │   ├── farm_slam.yaml                    # SLAM Toolbox config
        │   ├── mapper_params_online_async.yaml   # online mapping params
        │   ├── nav2_params.yaml                  # full Nav2 config (AMCL, DWB, costmaps…)
        │   └── nav2_rviz.rviz                    # RViz layout
        ├── description/
        │   └── farm_robot.urdf.xacro             # robot model (links, joints, sensors)
        ├── farm_robot/
        │   ├── obstacle_avoidance.py             # reactive obstacle avoidance
        │   ├── odom_tf_broadcaster.py            # odom → base_link TF publisher
        │   ├── scan_frame_fixer.py               # re-stamps LiDAR to /scan_fixed
        │   ├── farm_waypoints.py                 # waypoint patrol (Feature 4)
        │   ├── crop_row_follower.py              # crop-row guidance (Feature 5)
        │   ├── field_coverage.py                 # field coverage planner (Feature 6)
        │   ├── data_logger.py                    # CSV data logger (Feature 7)
        │   ├── return_to_home.py                 # return-to-home (Feature 8)
        │   └── web_dashboard.py                  # HTTP dashboard (Feature 9)
        ├── launch/
        │   ├── simulation.launch.py              # Gazebo only
        │   ├── slam.launch.py                    # SLAM mapping
        │   ├── navigation.launch.py              # Nav2 stack
        │   └── bringup.launch.py                 # full stack (sim + nav + rviz)
        ├── maps/
        │   ├── farm_map.pgm                      # saved occupancy grid
        │   └── farm_map.yaml                     # map metadata
        ├── worlds/
        │   └── farm.world.sdf                    # 10 m × 10 m farm world
        ├── package.xml
        ├── setup.py
        └── setup.cfg
```

## Prerequisites

```bash
sudo apt install \
  ros-jazzy-navigation2 \
  ros-jazzy-nav2-bringup \
  ros-jazzy-slam-toolbox \
  ros-jazzy-ros-gz-bridge \
  ros-jazzy-robot-state-publisher \
  ros-jazzy-xacro
```

## Build

```bash
cd ~/ros2/farm_robot_ws
source /opt/ros/jazzy/setup.bash
colcon build --packages-select farm_robot
pip3 install -e src/farm_robot --no-deps --break-system-packages
```

> Run `pip3 install -e ...` again after every `colcon build`.

## Environment Setup

Add to `~/.bashrc` (or run before each session):

```bash
source /opt/ros/jazzy/setup.bash
source ~/ros2/farm_robot_ws/install/setup.bash
export AMENT_PREFIX_PATH="$HOME/ros2/farm_robot_ws/install/farm_robot:$AMENT_PREFIX_PATH"
export PYTHONPATH="$HOME/ros2/farm_robot_ws/install/farm_robot/lib/python3.12/site-packages:$PYTHONPATH"
```

## Running the Simulation

### Full stack (recommended)

Launches simulation, Nav2, and RViz2 in a single command. Nav2 starts 15 s after Gazebo to allow TF to stabilise.

```bash
ros2 launch farm_robot bringup.launch.py
```

Wait ~60 s for all lifecycle nodes to reach **active** state.

### SLAM mapping (separate)

Terminal 1 — simulation:
```bash
ros2 launch farm_robot simulation.launch.py
```

Terminal 2 — SLAM:
```bash
ros2 launch farm_robot slam.launch.py
```

## Feature Usage

### Waypoint Patrol

```bash
ros2 run farm_robot farm_waypoints
```

Follows a 6-point route: aisle C south → north, then aisle B north → south.

### Crop Row Follower

```bash
ros2 run farm_robot crop_row_follower
```

### Field Coverage

```bash
ros2 run farm_robot field_coverage
```

### Data Logger

```bash
ros2 run farm_robot data_logger
```

Logs are saved to `~/farm_robot_logs/robot_log_<timestamp>.csv`.

### Return to Home

```bash
ros2 run farm_robot return_to_home
```

Trigger via topic:
```bash
ros2 topic pub /return_home std_msgs/Bool "data: true" --once
```

### Web Dashboard

```bash
ros2 run farm_robot web_dashboard
```

Open `http://localhost:8080` in a browser. Shows live position, velocity, LiDAR distances, and a **Return to Home** button.

## System Tests

`test.sh` verifies topics, TF chain, and mode-specific nodes:

```bash
chmod +x test.sh
./test.sh nav          # Nav2 full stack
./test.sh slam         # SLAM mapping
./test.sh waypoints    # waypoint follower
./test.sh crop         # crop row follower
./test.sh coverage     # field coverage
./test.sh log          # data logger
./test.sh home         # return to home
./test.sh dashboard    # web dashboard
```

Expected output: all checks `[PASS]`.

## TF Tree

```
map
 └── odom          (published by AMCL)
      └── base_link (published by odom_tf_broadcaster)
           └── lidar_link (published by robot_state_publisher)
```

## License

Apache-2.0
