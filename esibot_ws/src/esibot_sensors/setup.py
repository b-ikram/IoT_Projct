from setuptools import setup
import os
from glob import glob

package_name = 'esibot_sensors'

setup(
    name=package_name,
    version='0.0.1',
    packages=[package_name],
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        (os.path.join('share', package_name, 'launch'), glob('launch/*.launch.py')),
        (os.path.join('share', package_name, 'config'), glob('config/*.yaml') + glob('config/*.rviz')),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='CHATTAH SALSABILA, BADAOUI IKRAM',
    maintainer_email='ms_chattah@esi.dz, mi_badaoui@esi.dz',
    description='Radar sensor node package for ESIBOT',
    license='Apache-2.0',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            'radar_node = esibot_sensors.radar_node:main',
        ],
    },
)
