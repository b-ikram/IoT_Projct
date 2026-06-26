"""
sensors.launch.py — Launch all ESIBot sensor driver nodes.

Nodes launched:
    - radar_node        (LD19 lidar driver)
    - scan_converter    (radar → LaserScan conversion)
    - encoder_node      (GPIO wheel encoder ticks)
    - imu_node          (MPU6050 raw IMU data)

Static transforms:
    - base_link → radar_link
    - base_link → imu_link
"""

import os

from launch import LaunchDescription
from launch_ros.actions import Node
from ament_index_python.packages import get_package_share_directory


def generate_launch_description():
    pkg_share = get_package_share_directory("esibot_sensor")

    radar_params = os.path.join(pkg_share, "config", "radar_params.yaml")
    encoder_params = os.path.join(pkg_share, "config", "encoder_params.yaml")
    imu_params = os.path.join(pkg_share, "config", "imu_params.yaml")

    # ---- sensor driver nodes ----
    base_footprint_tf=Node(
        package="tf2_ros",
        executable="static_transform_publisher",
        name="base_footprint_to_base_link",
        arguments=[
            "0", "0", "0",
            "0", "0", "0",
            "base_footprint",
            "base_link",
        ],
    )

    radar_node = Node(
        package="esibot_sensor",
        executable="radar_node",
        name="radar_node",
        output="screen",
        parameters=[radar_params],
    )

    scan_converter_node = Node(
        package="esibot_sensor",
        executable="scan_converter",
        name="scan_converter",
        output="screen",
        parameters=[radar_params],
    )

    encoder_node = Node(
        package="esibot_sensor",
        executable="encoder_node",
        name="encoder_node",
        output="screen",
        parameters=[encoder_params],
    )

    imu_node = Node(
        package="esibot_sensor",
        executable="imu_node",
        name="imu_node",
        output="screen",
        parameters=[imu_params],
    )

    # ---- static transforms (no URDF) ----

    # Radar mounted 10 cm above base_link, no rotation.
    static_tf_radar = Node(
        package="tf2_ros",
        executable="static_transform_publisher",
        name="base_link_to_radar_link",
        arguments=[
            "0", "0", "0.1", "0", "0", "0",
            "base_link", "radar_link",
        ],
        output="screen",
    )

    # IMU co-located with base_link (adjust if physically offset).
    static_tf_imu = Node(
        package="tf2_ros",
        executable="static_transform_publisher",
        name="base_link_to_imu_link",
        arguments=[
            "0", "0", "0", "0", "0", "0",
            "base_link", "imu_link",
        ],
        output="screen",
    )

    map_web_relay_node = Node(
        package="esibot_sensor",
        executable="map_web_relay",
        name="map_web_relay",
        output="screen",
    )

    return LaunchDescription(
        [
            radar_node,
            scan_converter_node,
            encoder_node,
            imu_node,
            map_web_relay_node,
            static_tf_radar,
            static_tf_imu,
            base_footprint_tf,
        ]
    )
