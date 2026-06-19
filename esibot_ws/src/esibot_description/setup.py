import os
from glob import glob

from setuptools import setup


package_name = "esibot_description"

setup(
    name=package_name,
    version="0.1.0",
    packages=[],
    data_files=[
        ("share/ament_index/resource_index/packages", ["resource/" + package_name]),
        ("share/" + package_name, ["package.xml"]),
        (os.path.join("share", package_name, "launch"), glob("launch/*.launch.py")),
        (os.path.join("share", package_name, "urdf"), glob("urdf/*.xacro")),
    ],
    install_requires=["setuptools"],
    zip_safe=True,
    maintainer="EsiBot Team",
    maintainer_email="team@esibot.local",
    description="ESIBOT robot description with URDF/Xacro and launch files.",
    license="Apache-2.0",
    tests_require=["pytest"],
)
