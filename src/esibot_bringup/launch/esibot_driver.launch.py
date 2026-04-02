from launch import LaunchDescription
from launch_ros.actions import Node


def generate_launch_description():
    return LaunchDescription([
        Node(
            package='esibot_bringup',
            executable='esibot_driver',
            name='esibot_driver',
            output='screen',
            parameters=[{
                'cmd_in_topic': '/cmd_vel',
                'cmd_out_topic': '/gz_cmd_vel',
                'odom_in_topic': '/gz_odom',
                'odom_out_topic': '/odom',
                'battery_topic': '/battery_state',
                'battery_voltage': 12.0,
                'battery_percentage': 0.85,
                'battery_publish_rate': 1.0,
            }]
        )
    ])