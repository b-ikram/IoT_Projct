import os
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from ament_index_python.packages import get_package_share_directory

def generate_launch_description():
    bringup_share = get_package_share_directory('esibot_bringup')
    nav2_dir = get_package_share_directory('nav2_bringup')
    default_map = os.path.join(bringup_share, 'maps', 'mockup_50cm.yaml')

    map_arg = DeclareLaunchArgument(
        'map',
        default_value=default_map,
        description='Full path to the map YAML file used for Nav2 localization',
    )
    use_sim_time_arg = DeclareLaunchArgument(
        'use_sim_time',
        default_value='false',
        description='Use simulation time when running in Gazebo or recorded bags',
    )
    autostart_arg = DeclareLaunchArgument(
        'autostart',
        default_value='true',
        description='Automatically activate the Nav2 lifecycle nodes',
    )
    use_composition_arg = DeclareLaunchArgument(
        'use_composition',
        default_value='False',
        description='Start Nav2 nodes as separate processes for clearer hardware logs',
    )

    return LaunchDescription([
        map_arg,
        use_sim_time_arg,
        autostart_arg,
        use_composition_arg,
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(
                os.path.join(nav2_dir, 'launch', 'bringup_launch.py')
            ),
            launch_arguments={
                'slam': 'False',
                'map': LaunchConfiguration('map'),
                'use_sim_time': LaunchConfiguration('use_sim_time'),
                'autostart': LaunchConfiguration('autostart'),
                'use_composition': LaunchConfiguration('use_composition'),
                'params_file': os.path.join(bringup_share, 'config', 'nav2_params.yaml'),
            }.items()
        )
    ])
