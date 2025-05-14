#!/usr/bin/env python3
# Fișier de lansare pentru interfața cloud a robotului de labirint

from launch import LaunchDescription
from launch_ros.actions import Node
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch.conditions import IfCondition
import os

def generate_launch_description():
    # Parametri de lansare
    use_sim_time = LaunchConfiguration('use_sim_time', default='false')
    enable_video_stream = LaunchConfiguration('enable_video_stream', default='true')
    websocket_url = LaunchConfiguration('websocket_url', default='ws://example.com:8765')
    
    # Declararea argumentelor de lansare
    declare_use_sim_time = DeclareLaunchArgument(
        'use_sim_time',
        default_value='false',
        description='Folosește timpul de simulare sau nu')
        
    declare_enable_video_stream = DeclareLaunchArgument(
        'enable_video_stream',
        default_value='true',
        description='Activează streaming video către cloud')
        
    declare_websocket_url = DeclareLaunchArgument(
        'websocket_url',
        default_value='ws://example.com:8765',
        description='URL-ul serverului WebSocket pentru interfața cloud')
    
    # Nodul pentru interfața cloud
    cloud_interface_node = Node(
        package='maze_robot',
        executable='cloud_interface',
        name='cloud_interface',
        parameters=[
            {'use_sim_time': use_sim_time},
            {'websocket_server_url': websocket_url},
            {'video_stream_enabled': enable_video_stream},
            {'video_quality': 75},
            {'video_resolution': '640x480'}
        ],
        output='screen'
    )
    
    # Opțional: Nodul pentru procesarea suplimentară a imaginilor înainte de transmitere
    image_processor_node = Node(
        package='maze_robot',
        executable='image_processor',
        name='image_processor',
        parameters=[
            {'use_sim_time': use_sim_time}
        ],
        condition=IfCondition(enable_video_stream),
        output='screen'
    )
    
    # Creăm descrierea de lansare
    ld = LaunchDescription()
    
    # Adăugăm declarațiile argumentelor
    ld.add_action(declare_use_sim_time)
    ld.add_action(declare_enable_video_stream)
    ld.add_action(declare_websocket_url)
    
    # Adăugăm nodurile
    ld.add_action(cloud_interface_node)
    ld.add_action(image_processor_node)
    
    return ld
