import os
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch_ros.actions import Node
from ament_index_python.packages import get_package_share_directory


def generate_launch_description():
    bringup_share = get_package_share_directory("esibot_bringup")
    sensor_share = get_package_share_directory("esibot_sensor")

    driver_launch = os.path.join(bringup_share, "launch", "esibot_driver.launch.py")
    sensors_launch = os.path.join(sensor_share, "launch", "sensors.launch.py")
    encoder_odom_params = os.path.join(
        sensor_share, "config", "encoder_odom_params.yaml"
    )
    mpu_odom_params = os.path.join(sensor_share, "config", "mpu_odom_params.yaml")
    ekf_params = os.path.join(bringup_share, "config", "ekf.yaml")

    driver_node = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(driver_launch),
        launch_arguments={
            "publish_odom_enabled": "false",
            "publish_tf": "false",
        }.items(),
    )

    sensors_node = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(sensors_launch),
    )

    encoder_odom_node = Node(
        package="esibot_sensor",
        executable="encoder_odom",
        name="encoder_odom",
        output="screen",
        parameters=[encoder_odom_params],
    )

    mpu_odom_node = Node(
        package="esibot_sensor",
        executable="mpu_odom",
        name="mpu_odom_node",
        output="screen",
        parameters=[mpu_odom_params],
    )

    ekf_node = Node(
        package="robot_localization",
        executable="ekf_node",
        name="ekf_filter_node",
        output="screen",
        parameters=[ekf_params],
    )

    return LaunchDescription(
        [
            driver_node,
            sensors_node,
            encoder_odom_node,
            mpu_odom_node,
            ekf_node,
        ]
    )
