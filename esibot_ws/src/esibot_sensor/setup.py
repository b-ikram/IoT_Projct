import os
from glob import glob
from setuptools import setup

package_name = "esibot_sensor"

setup(
    name=package_name,
    version="0.0.0",
    packages=[package_name],
    data_files=[
        ("share/ament_index/resource_index/packages", ["resource/" + package_name]),
        ("share/" + package_name, ["package.xml"]),
        # ICI : Dit à ROS d'installer tes fichiers Launch et Config
        (os.path.join("share", package_name, "launch"), glob("launch/*.launch.py")),
        (os.path.join("share", package_name, "config"), glob("config/*")),
    ],
    install_requires=["setuptools"],
    zip_safe=True,
    maintainer="user",
    maintainer_email="user@todo.todo",
    description="TODO: Package description",
    license="TODO: License declaration",
    tests_require=["pytest"],
    entry_points={
        "console_scripts": [
            # ICI : Créé la commande 'radar_node' pour 'ros2 run'
            "radar_node = esibot_sensor.radar_node:main",
            "scan_converter = esibot_sensor.scan_converter:main",
            "mpu_service = esibot_sensor.mpu_node:main",
            "mpu_odom = esibot_sensor.mpu_odom:main",
            "encoder_service = esibot_sensor.encoder_node:main",
            "encoder_odom = esibot_sensor.encoder_odom:main",
        ],
    },
)
