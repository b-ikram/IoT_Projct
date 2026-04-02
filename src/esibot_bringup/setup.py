from setuptools import setup
import os
from glob import glob

package_name = 'esibot_bringup'

setup(
    name=package_name,
    version='0.0.1',
    packages=[package_name],
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        (os.path.join('share', package_name, 'launch'), glob('launch/*.launch.py')),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='CHATTAH SALSABILA',
    maintainer_email='ms_chattah@esi.dz',
    description='ESIBOT driver node for Gazebo testing',
    license='Apache-2.0',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            'esibot_driver = esibot_bringup.esibot_driver:main',
        ],
    },
)