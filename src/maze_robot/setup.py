from setuptools import setup, find_packages

package_name = 'maze_robot'

setup(
    name=package_name,
    version='1.0.0',
    packages=find_packages(),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        ('share/' + package_name + '/launch', [
            'launch/launch_maze_navigation.py',
            'launch/maze_sensors.launch.py',
            'launch/cloud_interface.launch.py'
        ]),
        ('share/' + package_name + '/config', [
            'config/lidar_params.yaml',
            'config/navigation_params.yaml',
            'config/sensor_params.yaml'
        ]),
    ],
    install_requires=['setuptools', 'numpy', 'RPi.GPIO'],
    zip_safe=True,
    maintainer='user',
    maintainer_email='user@todo.todo',
    description='Un pachet ROS2 pentru navigarea autonomă în labirint',
    license='TODO',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            'maze_robot_hardware = maze_robot.maze_robot.hardware.maze_robot_hardware:main',
            'maze_navigator = maze_robot.maze_robot.navigation.maze_navigator:main',
            'maze_sensors = maze_robot.maze_robot.sensors.maze_sensors:main',
            'event_logger = maze_robot.maze_robot.utils.event_logger:main',
            'sensor_test = maze_robot.maze_robot.sensors.sensor_test:main',
        ],
    },
)
