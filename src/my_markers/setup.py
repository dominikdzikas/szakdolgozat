from setuptools import setup

package_name = 'my_markers'

setup(
    name=package_name,
    version='0.0.0',
    packages=[package_name],
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='dominikdzikas',
    maintainer_email='dzikasdominik@gmail.com',
    description='TODO: Package description',
    license='TODO: License declaration',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
        'camera_info_publisher = my_markers.camera_info_publisher:main',
        'png_reader = my_markers.png_reader:main',
        'camera_publisher = my_markers.camera_publisher:main',
        'rectify_node = my_markers.rectify_node:main',
        'marker_node = my_markers.marker_node:main',
    ],
    },
)
