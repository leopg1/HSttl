#!/usr/bin/env python3
# Fișierul de lansare principal pentru navigarea în labirint

from launch import LaunchDescription
from launch_ros.actions import Node
from launch.actions import IncludeLaunchDescription, GroupAction, DeclareLaunchArgument
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch.conditions import IfCondition, UnlessCondition
import os

def generate_launch_description():
    # Parametri de lansare
    use_sim_time = LaunchConfiguration('use_sim_time', default='false')
    use_slam = LaunchConfiguration('use_slam', default='true')
    use_cloud = LaunchConfiguration('use_cloud', default='false')  # Dezactivat implicit
    map_file = LaunchConfiguration('map_file', default='')
    
    # Declararea argumentelor de lansare
    declare_use_sim_time = DeclareLaunchArgument(
        'use_sim_time',
        default_value='false',
        description='Folosește timpul de simulare sau nu')
    
    declare_use_slam = DeclareLaunchArgument(
        'use_slam',
        default_value='true',
        description='Activează SLAM pentru cartografierea labirintului')
    
    declare_use_cloud = DeclareLaunchArgument(
        'use_cloud',
        default_value='true',
        description='Activează interfața cloud pentru monitorizare')
    
    declare_map_file = DeclareLaunchArgument(
        'map_file',
        default_value='',
        description='Calea către fișierul de hartă pre-salvat (.yaml)')
    
    # Nodul pentru controlul hardware
    hardware_node = Node(
        package='maze_robot',
        executable='maze_robot_hardware',
        name='maze_robot_hardware',
        parameters=[
            {'use_sim_time': use_sim_time},
            {'max_speed': 0.3},
            {'min_speed': 0.1},
            {'angular_speed': 0.5}
        ],
        output='screen'
    )
    
    # Nodul pentru navigare
    navigator_node = Node(
        package='maze_robot',
        executable='maze_navigator',
        name='maze_navigator',
        parameters=[
            {'use_sim_time': use_sim_time},
            {'exploration_rate': 0.3},
            {'turn_rate': 0.5},
            {'min_front_distance': 0.4},
            {'wall_follow_distance': 0.3}
        ],
        output='screen'
    )
    
    # Nodul pentru senzori
    sensors_node = Node(
        package='maze_robot',
        executable='maze_sensors',
        name='maze_sensors',
        parameters=[
            {'use_sim_time': use_sim_time},
            {'hall_sensor_pin': 17},
            {'vibration_sensor_pin': 27},
            {'alcohol_sensor_pin': 22},
            {'alcohol_threshold': 400},
            {'led_pin_r': 18},
            {'led_pin_g': 23},
            {'led_pin_b': 24},
            {'buzzer_pin': 25}
        ],
        output='screen'
    )
    
    # Nodul pentru înregistrarea evenimentelor
    event_logger_node = Node(
        package='maze_robot',
        executable='event_logger',
        name='event_logger',
        parameters=[
            {'use_sim_time': use_sim_time},
            {'log_directory': '~/HS/logs'}
        ],
        output='screen'
    )
    
    # Nodul pentru interfața cloud (condiționat de parametrul use_cloud)
    cloud_interface_node = Node(
        package='maze_robot',
        executable='cloud_interface',
        name='cloud_interface',
        parameters=[
            {'use_sim_time': use_sim_time},
            {'websocket_server_url': 'ws://example.com:8765'},
            {'video_stream_enabled': True},
            {'video_quality': 75},
            {'video_resolution': '640x480'}
        ],
        condition=IfCondition(use_cloud),
        output='screen'
    )
    
    # Pachetul SLAM (condiționat de parametrul use_slam)
    slam_node = Node(
        package='slam_toolbox',
        executable='async_slam_toolbox_node',
        name='slam_toolbox',
        parameters=[
            {'use_sim_time': use_sim_time},
            {'max_laser_range': 5.0},
            {'resolution': 0.05},
            {'map_update_interval': 5.0}
        ],
        condition=IfCondition(use_slam),
        output='screen'
    )
    
    # Pachetul pentru server hartă (când folosim o hartă pre-salvată)
    map_server_node = Node(
        package='nav2_map_server',
        executable='map_server',
        name='map_server',
        parameters=[
            {'use_sim_time': use_sim_time},
            {'yaml_filename': map_file}
        ],
        condition=UnlessCondition(use_slam),
        output='screen'
    )
    
    # Creăm descrierea de lansare
    ld = LaunchDescription()
    
    # Adăugăm declarațiile argumentelor
    ld.add_action(declare_use_sim_time)
    ld.add_action(declare_use_slam)
    ld.add_action(declare_use_cloud)
    ld.add_action(declare_map_file)
    
    # Adăugăm nodurile
    ld.add_action(hardware_node)
    ld.add_action(navigator_node)
    ld.add_action(sensors_node)
    ld.add_action(event_logger_node)
    ld.add_action(cloud_interface_node)
    ld.add_action(slam_node)
    ld.add_action(map_server_node)
    
    return ld
