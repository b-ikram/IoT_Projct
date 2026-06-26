from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue


def generate_launch_description():
    publish_odom_arg = DeclareLaunchArgument(
        "publish_odom_enabled",
        default_value="False",
        description="Publish /odom message from esibot_driver",
    )
    publish_tf_arg = DeclareLaunchArgument(
        "publish_tf",
        default_value="false",
        description="Publish odom -> base_footprint TF from esibot_driver",
    )

    return LaunchDescription(
        [
            publish_odom_arg,
            publish_tf_arg,
            Node(
                package="esibot_bringup",
                executable="esibot_driver",
                name="esibot_driver",
                output="screen",
                parameters=[
                    {
                        "wheel_radius": 0.033,
                        "wheel_separation": 0.17,
                        "max_wheel_speed": 0.6,
                        "cmd_timeout": 0.5,
                        "publish_rate": 20.0,
                        # Wiring validated on RPi4 + L298N:
                        # left wheel  -> IN1=27 IN2=17 EN=12
                        # right wheel -> IN1=23 IN2=22 EN=13
                        "left_in1": 17,
                        "left_in2": 27,
                        "left_pwm": 12,
                        "right_in1": 23,
                        "right_in2": 22,
                        "right_pwm": 13,
                        "pwm_frequency": 1000,
                        "min_pwm_duty": 35.0,
                        "dry_run": False,
                        "invert_left": False,
                        "invert_right": False,
                        "publish_open_loop_odom": False,
                        "publish_odom_enabled": ParameterValue(
                            LaunchConfiguration("publish_odom_enabled"), value_type=bool
                        ),
                        "publish_tf": False,
                        "battery_source": "fixed",
                        "battery_voltage": 12.0,
                        "battery_percentage": 0.80,
                    }
                ],
            ),
        ]
    )
