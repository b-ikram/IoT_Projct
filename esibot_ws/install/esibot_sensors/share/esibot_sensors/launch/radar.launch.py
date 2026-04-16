from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.conditions import IfCondition
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node
from ament_index_python.packages import get_package_share_directory
import os


def generate_launch_description():
    package_share = get_package_share_directory('esibot_sensors')

    params_file = os.path.join(
        package_share,
        'config',
        'radar_params.yaml'
    )
    rviz_config_file = os.path.join(
        package_share,
        'config',
        'radar.rviz'
    )

    return LaunchDescription([
        DeclareLaunchArgument(
            'use_rviz',
            default_value='true',
            description='Launch RViz2 with the radar visualization config.'
        ),
        Node(
            package='esibot_sensors',
            executable='radar_node',
            name='radar_node',
            output='screen',
            parameters=[params_file]
        ),
        Node(
            package='rviz2',
            executable='rviz2',
            name='rviz2',
            output='screen',
            arguments=['-d', rviz_config_file],
            condition=IfCondition(LaunchConfiguration('use_rviz'))
        )
    ])
