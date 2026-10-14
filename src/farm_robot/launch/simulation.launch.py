import os

from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import Command, PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    # Find the installed farm_robot package
    pkg_share = FindPackageShare('farm_robot')

    # Robot description file
    robot_description_file = PathJoinSubstitution([
        pkg_share,
        'description',
        'farm_robot.urdf.xacro'
    ])

    # Farm world file
    world_file = PathJoinSubstitution([
        pkg_share,
        'worlds',
        'farm.world.sdf'
    ])

    # Expand the Xacro into a URDF robot description
    robot_description = Command([
        'xacro ',
        robot_description_file
    ])

    # Start Gazebo Sim
    gazebo = IncludeLaunchDescription(
        PythonLaunchDescriptionSource([
            PathJoinSubstitution([
                FindPackageShare('ros_gz_sim'),
                'launch',
                'gz_sim.launch.py'
            ])
        ]),
        launch_arguments={
            'gz_args': ['-r ', world_file]
        }.items()
    )

    # Publish robot links and joints
    robot_state_publisher = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        output='screen',
        parameters=[{
            'robot_description': robot_description,
            'use_sim_time': True
        }]
    )

    # Spawn the robot into Gazebo
    spawn_robot = Node(
        package='ros_gz_sim',
        executable='create',
        arguments=[
            '-name', 'farm_robot',
            '-topic', 'robot_description',
            '-x', '0',
            '-y', '0',
            '-z', '0.2'
        ],
        output='screen'
    )
    
    
    cmd_vel_bridge = Node(
        package='ros_gz_bridge',
        executable='parameter_bridge',
        arguments=[
            # ROS 2 -> Gazebo: control the robot
            '/cmd_vel@geometry_msgs/msg/Twist]gz.msgs.Twist',

            # Gazebo -> ROS 2: receive LiDAR data
            '/scan@sensor_msgs/msg/LaserScan[gz.msgs.LaserScan',

            # Gazebo -> ROS 2: receive odometry data
            '/odom@nav_msgs/msg/Odometry[gz.msgs.Odometry',
        ],
        output='screen'
    )


    return LaunchDescription([
        gazebo,
        robot_state_publisher,
        spawn_robot,
        cmd_vel_bridge
    ])
