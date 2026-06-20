from launch import LaunchDescription
from launch_ros.actions import Node
from ament_index_python.packages import get_package_share_directory
import os

def generate_launch_description():
    model_path = os.path.join(
        get_package_share_directory('esibot_vision'),
        'yolov8n.onnx'
    )
    return LaunchDescription([
        Node(
            package='esibot_vision',
            executable='vision_node',
            name='vision_pipeline',
            output='screen',
        )
    ])
