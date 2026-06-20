"""
esibot_ekf.launch.py — EKF-based localization stack.

Launches:
    1. esibot_driver           (motor control, /cmd_vel subscriber)
    2. sensors (encoder + IMU + radar + static TFs)
    3. diff_drive_odom_node    (encoder ticks → /wheel/odometry)
    4. ekf_node                (sensor fusion → /odom + TF)

Data flow:
    encoders → diff_drive_odom_node → /wheel/odometry ─┐
                                                        ├→ ekf_node → /odom + TF(odom→base_link)
    MPU6050  → imu_node             → /imu/data ────────┘
"""

import os

from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch_ros.actions import Node
from ament_index_python.packages import get_package_share_directory


def generate_launch_description():
    bringup_share = get_package_share_directory("esibot_bringup")
    sensor_share = get_package_share_directory("esibot_sensor")

    driver_launch = os.path.join(
        bringup_share, "launch", "esibot_driver.launch.py"
    )
    sensors_launch = os.path.join(
        sensor_share, "launch", "sensors.launch.py"
    )
    diff_drive_odom_params = os.path.join(
        sensor_share, "config", "diff_drive_odom_params.yaml"
    )
    ekf_params = os.path.join(bringup_share, "config", "ekf.yaml")

    # ---- 1. Motor driver (odom + TF disabled — EKF owns those) ----
    driver = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(driver_launch),
        launch_arguments={
            "publish_odom_enabled": "false",
            "publish_tf": "false",
        }.items(),
    )

    # ---- 2. Sensor drivers (encoder, IMU, radar + static TFs) ----
    sensors = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(sensors_launch),
    )

    # ---- 3. Differential-drive odometry (ticks → Odometry) ----
    diff_drive_odom_node = Node(
        package="esibot_sensor",
        executable="diff_drive_odom_node",
        name="diff_drive_odom_node",
        output="screen",
        parameters=[diff_drive_odom_params],
    )

    # ---- 4. EKF sensor fusion (remapped /odometry/filtered → /odom) ----
    ekf_node = Node(
        package="robot_localization",
        executable="ekf_node",
        name="ekf_node",
        output="screen",
        parameters=[ekf_params],
        remappings=[("/odometry/filtered", "/odom")],
    )

    # ---- 5. Static TF: base_link → base_footprint (identity) ----
    # slam_toolbox and nav2 expect base_footprint; EKF publishes odom → base_link.
    base_link_to_footprint = Node(
        package="tf2_ros",
        executable="static_transform_publisher",
        name="base_link_to_base_footprint",
        arguments=["0", "0", "0", "0", "0", "0", "base_link", "base_footprint"],
        output="screen",
    )

    return LaunchDescription(
        [
            driver,
            sensors,
            diff_drive_odom_node,
            ekf_node,
            base_link_to_footprint,
        ]
    )
