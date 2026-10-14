
from setuptools import setup
from glob import glob
import os

package_name = 'farm_robot'

setup(
    name=package_name,
    version='0.0.1',
    packages=[package_name],
    data_files=[
        (
            'share/ament_index/resource_index/packages',
            ['resource/' + package_name],
        ),
        ('share/' + package_name, ['package.xml']),
        (
            os.path.join('share', package_name, 'launch'),
            glob('launch/*.launch.py'),
        ),
        (
            os.path.join('share', package_name, 'description'),
            glob('description/*'),
        ),
        (
            os.path.join('share', package_name, 'worlds'),
            glob('worlds/*'),
        ),
        (
            os.path.join('share', package_name, 'config'),
            glob('config/*.yaml'),
        ),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='handsome',
    maintainer_email='sannyuntwin21@gmail.com',
    description='Smart autonomous farming robot simulation',
    license='Apache-2.0',
    entry_points={
        'console_scripts': [
            'obstacle_avoidance = farm_robot.obstacle_avoidance:main',
            'scan_frame_fixer = farm_robot.scan_frame_fixer:main',
            'odom_tf_broadcaster = farm_robot.odom_tf_broadcaster:main',
        ],
    },
)
