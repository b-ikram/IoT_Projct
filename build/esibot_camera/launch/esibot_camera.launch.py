from launch import LaunchDescription
from launch_ros.actions import Node
from ament_index_python.packages import get_package_share_directory
import os


def generate_launch_description():
    package_share = get_package_share_directory("esibot_camera")
    params_file = os.path.join(package_share, "config", "camera_params.yaml")

    return LaunchDescription([
        Node(
            package="esibot_camera",
            executable="esircam_node",
            name="esircam_node",
            output="screen",
            parameters=[params_file],
        )
    ])