import os
from glob import glob
from setuptools import setup

package_name = "esibot_sensor"

setup(
    name=package_name,
    version="1.0.0",
    packages=[package_name],
    data_files=[
        (
            "share/ament_index/resource_index/packages",
            ["resource/" + package_name],
        ),
        ("share/" + package_name, ["package.xml"]),
        (
            os.path.join("share", package_name, "launch"),
            glob("launch/*.launch.py"),
        ),
        (
            os.path.join("share", package_name, "config"),
            glob("config/*"),
        ),
    ],
    install_requires=["setuptools"],
    zip_safe=True,
    maintainer="user",
    maintainer_email="user@todo.todo",
    description="ESIBot sensor drivers and odometry",
    license="TODO: License declaration",
    tests_require=["pytest"],
    entry_points={
        "console_scripts": [
            "radar_node = esibot_sensor.radar_node:main",
            "scan_converter = esibot_sensor.scan_converter:main",
            "imu_node = esibot_sensor.imu_node:main",
            "encoder_node = esibot_sensor.encoder_node:main",
            "diff_drive_odom_node = esibot_sensor.diff_drive_odom_node:main",
        ],
    },
)
