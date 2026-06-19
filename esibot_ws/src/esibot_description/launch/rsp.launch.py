import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import Command, FindExecutable, LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    use_sim_time = LaunchConfiguration("use_sim_time")
    default_model_path = os.path.join(
        get_package_share_directory("esibot_description"),
        "urdf",
        "esibot.urdf.xacro",
    )
    model = LaunchConfiguration("model")

    robot_description = {
        "robot_description": Command([
            FindExecutable(name="xacro"),
            " ",
            model,
        ])
    }

    return LaunchDescription([
        DeclareLaunchArgument(
            "model",
            default_value=default_model_path,
            description="Absolute path to the ESIBOT URDF/Xacro model.",
        ),
        DeclareLaunchArgument(
            "use_sim_time",
            default_value="false",
            description="Use simulation clock if true.",
        ),
        Node(
            package="robot_state_publisher",
            executable="robot_state_publisher",
            name="robot_state_publisher",
            output="screen",
            parameters=[
                robot_description,
                {"use_sim_time": use_sim_time},
            ],
        ),
        Node(
            package="joint_state_publisher",
            executable="joint_state_publisher",
            name="joint_state_publisher",
            output="screen",
        ),
    ])
