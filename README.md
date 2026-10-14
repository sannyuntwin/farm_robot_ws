# Farm Robot 🤖

A simulated farm robot built with **ROS 2 Jazzy**, **Gazebo**, **SLAM Toolbox**, and **Nav2**. The project aims to support autonomous navigation by mapping the environment, detecting obstacles with LiDAR, and planning robot movements.

## Features

- Robot simulation in Gazebo
- LiDAR-based obstacle detection
- 2D environment mapping using SLAM Toolbox
- Robot visualization with RViz2
- Autonomous navigation using Nav2
- Odometry and TF coordinate transforms

## Technology Stack

- Ubuntu / WSL2
- ROS 2 Jazzy
- Gazebo
- SLAM Toolbox
- Nav2
- RViz2
- Python
- URDF / robot description files

## Project Structure
## Project Structure

```text
farm_robot_ws/
├── README.md
├── frames_2026-10-14_21.46.34.gv
├── frames_2026-10-14_21.46.34.pdf
└── src/
    └── farm_robot/
        ├── config/
        │   ├── farm_slam.yaml
        │   ├── mapper_params_online_async.yaml
        │   ├── nav2_params.yaml
        │   └── nav2_rviz.rviz
        ├── description/
        │   └── farm_robot.urdf.xacro
        ├── farm_robot/
        │   ├── __init__.py
        │   ├── obstacle_avoidance.py
        │   ├── odom_tf_broadcaster.py
        │   └── scan_frame_fixer.py
        ├── launch/
        │   ├── mapping_navigation.launch.py
        │   ├── navigation.launch.py
        │   └── simulation.launch.py
        ├── maps/
        │   ├── farm_map.pgm
        │   ├── farm_map.yaml
        │   └── .gitkeep
        ├── package.xml
        ├── resource/
        │   └── farm_robot
        ├── setup.cfg
        ├── setup.py
        └── worlds/
            └── farm.world.sdf
```

### Directory and File Descriptions

| Path | Description |
|---|---|
| `config/farm_slam.yaml` | SLAM Toolbox configuration for mapping |
| `config/mapper_params_online_async.yaml` | Online asynchronous mapping parameters |
| `config/nav2_params.yaml` | Navigation, planning, and controller configuration |
| `config/nav2_rviz.rviz` | RViz configuration for navigation visualization |
| `description/farm_robot.urdf.xacro` | Robot model, links, joints, and sensor descriptions |
| `farm_robot/obstacle_avoidance.py` | Obstacle avoidance node |
| `farm_robot/odom_tf_broadcaster.py` | Publishes odometry-related TF transforms |
| `farm_robot/scan_frame_fixer.py` | Processes LiDAR scan frame information |
| `launch/simulation.launch.py` | Launches the Gazebo simulation |
| `launch/mapping_navigation.launch.py` | Launches the mapping and navigation setup |
| `launch/navigation.launch.py` | Launches the navigation setup |
| `maps/farm_map.pgm` | Saved occupancy-grid map image |
| `maps/farm_map.yaml` | Saved map metadata |
| `worlds/farm.world.sdf` | Gazebo farm environment |
| `package.xml` | Package metadata and dependencies |
| `setup.py` | Python package installation configuration |
| `setup.cfg` | Python package script installation settings |
| `resource/farm_robot` | ROS 2 package resource marker |
| `frames_*.gv` | Generated TF frame graph in Graphviz format |
| `frames_*.pdf` | PDF visualization of the TF frame graph |

### Technologies

- ROS 2 Jazzy
- Gazebo
- SLAM Toolbox
- Nav2
- RViz2
- Python
- URDF/Xacro
- TF2
- LiDAR and odometry



## Prerequisites

Install ROS 2 Jazzy and the required Gazebo, SLAM Toolbox, and Nav2 packages before running the project.

## Build the Project

```bash
source /opt/ros/jazzy/setup.bash
cd ~/ros2/farm_robot_ws
colcon build --merge-install --packages-select farm_robot
source install/local_setup.bash
```

## Run the Simulation

### 1. Start Gazebo

Open Terminal 1:

```bash
source /opt/ros/jazzy/setup.bash
cd ~/ros2/farm_robot_ws
source install/local_setup.bash
export AMENT_PREFIX_PATH="$HOME/ros2/farm_robot_ws/install:$AMENT_PREFIX_PATH"
ros2 launch farm_robot simulation.launch.py
```

### 2. Start SLAM Toolbox

Open Terminal 2:

```bash
source /opt/ros/jazzy/setup.bash
cd ~/ros2/farm_robot_ws
source install/local_setup.bash
export AMENT_PREFIX_PATH="$HOME/ros2/farm_robot_ws/install:$AMENT_PREFIX_PATH"
ros2 launch slam_toolbox online_async_launch.py \
  slam_params_file:=$HOME/ros2/farm_robot_ws/src/farm_robot/config/farm_slam.yaml \
  use_sim_time:=True
```

### 3. Start Nav2

Open Terminal 3:

```bash
source /opt/ros/jazzy/setup.bash
cd ~/ros2/farm_robot_ws
source install/local_setup.bash
export AMENT_PREFIX_PATH="$HOME/ros2/farm_robot_ws/install:$AMENT_PREFIX_PATH"
ros2 launch farm_robot mapping_navigation.launch.py
```

### 4. Start RViz2

Open Terminal 4:

```bash
source /opt/ros/jazzy/setup.bash
rviz2
```

Set the RViz2 **Fixed Frame** to `map`, then add the map and LiDAR scan displays.

## Verify Topics

```bash
ros2 topic list
ros2 topic info /map
ros2 topic info /odom
ros2 topic hz /scan_fixed
```

## Current Progress

- [x] Gazebo simulation running
- [x] LiDAR scan publishing
- [x] SLAM map publishing
- [x] Nav2 lifecycle nodes active
- [x] Map and LiDAR scan visible in RViz2
- [ ] Expand the map by exploring the environment
- [ ] Verify autonomous navigation to a safe goal

## Safety and Testing

Test navigation in simulation first. Choose goals only in clearly mapped free space and monitor the robot in Gazebo.

## License

Add your preferred open-source license here if you plan to share the project publicly.