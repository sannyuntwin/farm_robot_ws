import os

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, ExecuteProcess, IncludeLaunchDescription, TimerAction
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import Command, LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    # Find the installed farm_robot package
    pkg_share = FindPackageShare('farm_robot')

    world_arg = DeclareLaunchArgument(
        'world',
        default_value='farm',
        description='World to load: farm | obstacle | crop'
    )

    # Robot description file
    robot_description_file = PathJoinSubstitution([
        pkg_share,
        'description',
        'farm_robot.urdf.xacro'
    ])

    # World file selected by argument
    world_file = PathJoinSubstitution([
        pkg_share,
        'worlds',
        [LaunchConfiguration('world'), '.world.sdf']
    ])

    # Expand the Xacro into a URDF robot description
    robot_description = ParameterValue(
        Command(['xacro ', robot_description_file]),
        value_type=str
    )

    # Kill any stale Gazebo process before launching
    kill_gz = ExecuteProcess(
        cmd=['bash', '-c', 'pkill -9 -f gz_sim 2>/dev/null; pkill -9 -f gz-sim 2>/dev/null; sleep 1'],
        output='screen'
    )

    # Start Gazebo Sim (delayed to let kill complete)
    gazebo = TimerAction(period=1.5, actions=[IncludeLaunchDescription(
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
    )])

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
            '-x', '1.0',
            '-y', '-3.5',
            '-z', '0.2',
            '-Y', '1.5708'
        ],
        output='screen'
    )
    
    
    cmd_vel_bridge = Node(
        package='ros_gz_bridge',
        executable='parameter_bridge',
        arguments=[
            '/clock@rosgraph_msgs/msg/Clock[gz.msgs.Clock',
            '/cmd_vel@geometry_msgs/msg/Twist@gz.msgs.Twist',
            '/scan@sensor_msgs/msg/LaserScan[gz.msgs.LaserScan',
            '/odom@nav_msgs/msg/Odometry[gz.msgs.Odometry',
        ],
        output='screen'
    )


    joint_state_publisher = Node(
        package='joint_state_publisher',
        executable='joint_state_publisher',
        name='joint_state_publisher',
        parameters=[{
            'use_sim_time': True,
            'robot_description': robot_description,
        }],
        output='screen'
    )

    odom_tf_broadcaster = Node(
        package='farm_robot',
        executable='odom_tf_broadcaster',
        parameters=[{
	    'use_sim_time': True,
	}],
	 output='screen'
    )

    scan_frame_fixer = Node(
        package='farm_robot',
        executable='scan_frame_fixer',
        output='screen'
    )

    return LaunchDescription([
        world_arg,
        kill_gz,
        gazebo,
        robot_state_publisher,
        spawn_robot,
        cmd_vel_bridge,
        joint_state_publisher,
        odom_tf_broadcaster,
        scan_frame_fixer,
    ])
