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

    # Delay Nav2 by 15s so Gazebo and robot spawn first
    navigation = TimerAction(
        period=15.0,
        actions=[IncludeLaunchDescription(
            PythonLaunchDescriptionSource([
                PathJoinSubstitution([pkg_share, 'launch', 'navigation.launch.py'])
            ])
        )]
    )

    # Delay RViz by 20s so Nav2 is up first
    rviz = TimerAction(
        period=20.0,
        actions=[Node(
            package='rviz2',
            executable='rviz2',
            arguments=['-d', PathJoinSubstitution([pkg_share, 'config', 'nav2_rviz.rviz'])],
            output='screen'
        )]
    )

    return LaunchDescription([
        simulation,
        navigation,
        rviz,
    ])
