from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription, TimerAction
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    pkg_share = FindPackageShare('farm_robot')

    simulation = IncludeLaunchDescription(
        PythonLaunchDescriptionSource([
            PathJoinSubstitution([pkg_share, 'launch', 'simulation.launch.py'])
        ])
    )

    slam = TimerAction(
        period=5.0,
        actions=[Node(
            package='slam_toolbox',
            executable='async_slam_toolbox_node',
            name='slam_toolbox',
            output='screen',
            parameters=[
                PathJoinSubstitution([pkg_share, 'config', 'farm_slam.yaml']),
                {'use_sim_time': True}
            ],
        )]
    )

    lifecycle_manager_slam = TimerAction(
        period=7.0,
        actions=[Node(
            package='nav2_lifecycle_manager',
            executable='lifecycle_manager',
            name='lifecycle_manager_slam',
            output='screen',
            parameters=[{
                'use_sim_time': True,
                'autostart': True,
                'bond_timeout': 0.0,
                'node_names': ['slam_toolbox']
            }]
        )]
    )

    rviz = TimerAction(
        period=8.0,
        actions=[Node(
            package='rviz2',
            executable='rviz2',
            arguments=['-d', PathJoinSubstitution([pkg_share, 'config', 'nav2_rviz.rviz'])],
            output='screen'
        )]
    )

    return LaunchDescription([
        simulation,
        slam,
        lifecycle_manager_slam,
        rviz,
    ])
