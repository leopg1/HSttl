#!/usr/bin/env python3
# Fișier de lansare pentru modulul de senzori al robotului de labirint

from launch import LaunchDescription
from launch_ros.actions import Node
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
import os

def generate_launch_description():
    # Parametri de lansare
    use_sim_time = LaunchConfiguration('use_sim_time', default='false')
    
    # Declararea argumentelor de lansare
    declare_use_sim_time = DeclareLaunchArgument(
        'use_sim_time',
        default_value='false',
        description='Folosește timpul de simulare sau nu')
    
    # Încărcarea parametrilor de configurare
    config_dir = os.path.join(
        os.path.dirname(os.path.realpath(__file__)),
        '..',
        'config'
    )
    sensor_config = os.path.join(config_dir, 'sensor_params.yaml')
    
    # Nodul pentru senzori
    sensors_node = Node(
        package='maze_robot',
        executable='maze_sensors',
        name='maze_sensors',
        parameters=[
            {'use_sim_time': use_sim_time},
            sensor_config
        ],
        output='screen'
    )
    
    # Nodul pentru logger-ul de evenimente
    event_logger_node = Node(
        package='maze_robot',
        executable='event_logger',
        name='event_logger',
        parameters=[
            {'use_sim_time': use_sim_time},
            {'log_directory': os.path.expanduser('~/HSttl/logs')}
        ],
        output='screen'
    )
    
    # Creăm descrierea de lansare
    ld = LaunchDescription()
    
    # Adăugăm declarațiile argumentelor
    ld.add_action(declare_use_sim_time)
    
    # Adăugăm nodurile
    ld.add_action(sensors_node)
    ld.add_action(event_logger_node)
    
    return ld
