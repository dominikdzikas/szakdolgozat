from setuptools import setup
from glob import glob
import os

package_name = 'road_launch'

setup(
    name=package_name,
    version='0.0.0',
    packages=[package_name],
    data_files=[
    ('share/ament_index/resource_index/packages',
        ['resource/' + package_name]),
    ('share/' + package_name, ['package.xml']),
    (os.path.join('share', package_name, 'launch'), glob('launch/*.launch.py')),
    (os.path.join('share', package_name, 'rviz'), glob('rviz/*.rviz')),
],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='dominikdzikas',
    maintainer_email='dzikasdominik@gmail.com',
    description='Launch files for the road surface detection pipeline',
    license='Apache-2.0',
    tests_require=['pytest'],
    entry_points={},
)