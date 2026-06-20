from setuptools import setup
from glob import glob
import os

package_name = "esibot_camera"

setup(
    name=package_name,
    version="0.1.0",
    packages=[package_name],
    data_files=[
        (
            "share/ament_index/resource_index/packages",
            [os.path.join("resource", package_name)],
        ),
        (
            os.path.join("share", package_name),
            ["package.xml"],
        ),
        (
            os.path.join("share", package_name, "launch"),
            glob("launch/*.launch.py"),
        ),
        (
            os.path.join("share", package_name, "config"),
            glob("config/*.yaml"),
        ),
    ],
    install_requires=["setuptools"],
    zip_safe=True,
    maintainer="EsiBot Team",
    maintainer_email="team@esibot.local",
    description="ROS2 camera bridge for EsiBot ESP32-CAM MJPEG stream.",
    license="Apache-2.0",
    tests_require=["pytest"],
    entry_points={
        "console_scripts": [
            "esircam_node = esibot_camera.esircam_node:main",
        ],
    },
)