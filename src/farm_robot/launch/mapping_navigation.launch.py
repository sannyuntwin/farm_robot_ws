
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    pkg_share = FindPackageShare('farm_robot')

    slam_params = PathJoinSubstitution([
        pkg_share, 'config', 'farm_slam.yaml'
    ])

    nav2_params = PathJoinSubstitution([
        pkg_share, 'config', 'nav2_params.yaml'
    ])

    slam_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            PathJoinSubstitution([
                FindPackageShare('slam_toolbox'),
                'launch',
                'online_async_launch.py'
            ])
        ),
        launch_arguments={
            'slam_params_file': slam_params,
            'use_sim_time': 'True',
        }.items()
    )

    controller_server = Node(
        package='nav2_controller',
        executable='controller_server',
        output='screen',
        parameters=[nav2_params],
	remappings=[
	    ('cmd_vel', 'cmd_vel_nav'),
	],
    )

    planner_server = Node(
        package='nav2_planner',
        executable='planner_server',
        output='screen',
        parameters=[nav2_params],
    )

    behavior_server = Node(
        package='nav2_behaviors',
        executable='behavior_server',
        output='screen',
        parameters=[nav2_params],
        remappings=[
	    ('cmd_vel', 'cmd_vel_nav'),
	],
    )

    bt_navigator = Node(
        package='nav2_bt_navigator',
        executable='bt_navigator',
        output='screen',
        parameters=[nav2_params],
    )

    waypoint_follower = Node(
        package='nav2_waypoint_follower',
        executable='waypoint_follower',
        output='screen',
        parameters=[nav2_params],
    )

    velocity_smoother = Node(
        package='nav2_velocity_smoother',
        executable='velocity_smoother',
        output='screen',
        parameters=[nav2_params],
        remappings=[
            ('cmd_vel', 'cmd_vel_nav'),
            ('cmd_vel_smoothed', 'cmd_vel'),
        ],
    )

    lifecycle_manager_navigation = Node(
        package='nav2_lifecycle_manager',
        executable='lifecycle_manager',
        name='lifecycle_manager_navigation',
        output='screen',
        parameters=[nav2_params],
    )

    return LaunchDescription([
        controller_server,
        planner_server,
        behavior_server,
        bt_navigator,
        waypoint_follower,
        velocity_smoother,
        lifecycle_manager_navigation,
    ])
