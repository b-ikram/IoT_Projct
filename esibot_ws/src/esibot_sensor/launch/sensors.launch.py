import os
from launch import LaunchDescription
from launch_ros.actions import Node
from ament_index_python.packages import get_package_share_directory


def generate_launch_description():
    package_share = get_package_share_directory("esibot_sensor")

    radar_params = os.path.join(package_share, "config", "radar_params.yaml")
    encoder_params = os.path.join(package_share, "config", "encoder_params.yaml")
    mpu_params = os.path.join(package_share, "config", "mpu_params.yaml")

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
        executable="encoder_service",
        name="encoder_node",
        output="screen",
        parameters=[encoder_params],
    )

    static_tf_node = Node(
        package="tf2_ros",
        executable="static_transform_publisher",
        name="footprint_to_radar",
        arguments=["0", "0", "0.1", "0", "0", "0", "base_footprint", "radar_link"],
        output="screen",
    )

    mpu_node = Node(
        package="esibot_sensor",
        executable="mpu_service",
        name="mpu_node",
        output="screen",
        parameters=[mpu_params],
    )

    return LaunchDescription(
        [
            radar_node,
            scan_converter_node,
            encoder_node,
            static_tf_node,
            mpu_node,
        ]
    )
