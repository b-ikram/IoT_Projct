from setuptools import find_packages, setup
import os
from glob import glob

package_name = 'esibot_bringup'

setup(
    name=package_name,
    version='0.0.1',
    # find_packages ensures odometry_utils and serial_interface are included
    packages=find_packages(exclude=['test']), 
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        # Correctly joins the path for launch files
        (os.path.join('share', package_name, 'launch'), glob('launch/*.launch.py')),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    # Match the maintainer info from your package.xml
    maintainer='CHATTAH SALSABILA, BADAOUI IKRAM',
    maintainer_email='ms_chattah@esi.dz, mi_badaoui@esi.dz',
    description='ESIBOT real hardware driver and odometry bridge',
    license='Apache-2.0',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            'esibot_driver = esibot_bringup.esibot_driver:main',
        ],
    },
)