import os
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from ament_index_python.packages import get_package_share_directory

def generate_launch_description():
    bringup_share = get_package_share_directory('esibot_bringup')
    nav2_dir = get_package_share_directory('nav2_bringup')

    return LaunchDescription([
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(
                os.path.join(nav2_dir, 'launch', 'bringup_launch.py')
            ),
            launch_arguments={
                'slam': 'True',
                'use_sim_time': 'false',
                'params_file': os.path.join(bringup_share, 'config', 'nav2_params.yaml'),
            }.items()
        )
    ])
