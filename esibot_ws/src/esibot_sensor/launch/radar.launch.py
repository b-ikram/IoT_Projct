import os
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch_ros.actions import Node
from ament_index_python.packages import get_package_share_directory


def generate_launch_description():
    package_share = get_package_share_directory("esibot_sensor")

    params_file = os.path.join(package_share, "config", "radar_params.yaml")
    encoder_params_file = os.path.join(package_share, "config", "encoder_params.yaml")
    mpu_params_file = os.path.join(package_share, "config", "mpu_params.yaml")
    mpu_odom_params_file = os.path.join(package_share, "config", "mpu_odom_params.yaml")
    slam_params_file = os.path.join(package_share, "config", "slam_params.yaml")

    # 1. Radar Materiel
    radar_node = Node(
        package="esibot_sensor",
        executable="radar_node",
        name="radar_node",
        output="screen",
        parameters=[params_file],
    )

    # 2. Convertisseur Radar -> LaserScan
    scan_converter_node = Node(
        package="esibot_sensor",
        executable="scan_converter",
        name="scan_converter",
        output="screen",
        parameters=[params_file],
    )

    # 3. Encoder counts
    encoder_node = Node(
        package="esibot_sensor",
        executable="encoder_service",
        name="encoder_node",
        output="screen",
        parameters=[encoder_params_file],
    )

    # 4. Liaison geometrique statique
    static_tf_node = Node(
        package="tf2_ros",
        executable="static_transform_publisher",
        name="footprint_to_radar",
        arguments=["0", "0", "0.1", "0", "0", "0", "base_footprint", "radar_link"],
        output="screen",
    )

    # 5. Lecture capteur MPU6050
    mpu_hardware_node = Node(
        package="esibot_sensor",
        executable="mpu_service",
        name="mpu_node",
        output="screen",
        parameters=[mpu_params_file],
    )

    # 6. Calcul odometrie MPU6050
    mpu_odom_node = Node(
        package="esibot_sensor",
        executable="mpu_odom",
        name="mpu_odom_node",
        output="screen",
        parameters=[mpu_odom_params_file],
    )

    # 7. SLAM avec config
    slam_toolbox_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(
                get_package_share_directory("slam_toolbox"),
                "launch",
                "online_async_launch.py",
            )
        ),
        launch_arguments={
            "scan_topic": "/scan",
            "params_file": slam_params_file,
        }.items(),
    )

    return LaunchDescription(
        [
            radar_node,
            scan_converter_node,
            encoder_node,
            static_tf_node,
            mpu_hardware_node,
            mpu_odom_node,
            slam_toolbox_launch,
        ]
    )
