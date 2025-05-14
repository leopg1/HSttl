#!/usr/bin/env python3
# encoding: utf-8
# Interfața cloud pentru transmiterea datelor și streaming video

import rclpy
import json
import time
import threading
import websockets
import asyncio
import cv2
import numpy as np
from rclpy.node import Node
from std_msgs.msg import String, Bool
from sensor_msgs.msg import Image, LaserScan
from nav_msgs.msg import OccupancyGrid, Odometry
from cv_bridge import CvBridge
from datetime import datetime

class CloudInterface(Node):
    def __init__(self):
        super().__init__('cloud_interface')
        
        # Parametri pentru interfața cloud
        self.declare_parameter('websocket_server_url', 'ws://example.com:8765')
        self.declare_parameter('video_stream_enabled', True)
        self.declare_parameter('video_quality', 75)  # Calitate JPEG (0-100)
        self.declare_parameter('video_resolution', '640x480')  # Rezoluție stream video
        self.declare_parameter('websocket_reconnect_interval', 5.0)  # Secunde între încercările de reconectare
        
        # Obține valorile parametrilor
        self.websocket_url = self.get_parameter('websocket_server_url').value
        self.video_enabled = self.get_parameter('video_stream_enabled').value
        self.video_quality = self.get_parameter('video_quality').value
        self.video_resolution = self.get_parameter('video_resolution').value
        self.reconnect_interval = self.get_parameter('websocket_reconnect_interval').value
        
        # Stare conexiune
        self.is_connected = False
        self.websocket = None
        self.connection_lock = threading.Lock()
        
        # Stare robot și navigare
        self.current_position = (0.0, 0.0, 0.0)  # (x, y, theta)
        self.robot_speed = 0.0
        self.events = []
        self.map_data = None
        self.navigation_state = "IDLE"
        
        # Inițializare bridge pentru conversia între ROS Image și OpenCV
        self.cv_bridge = CvBridge()
        
        # Subscribers pentru diverse date
        self.odom_sub = self.create_subscription(
            Odometry,
            '/odom',
            self.odom_callback,
            10
        )
        
        self.map_sub = self.create_subscription(
            OccupancyGrid,
            '/map',
            self.map_callback,
            10
        )
        
        self.camera_sub = self.create_subscription(
            Image,
            '/camera/image_raw',
            self.camera_callback,
            10
        )
        
        self.lidar_sub = self.create_subscription(
            LaserScan,
            '/scan',
            self.lidar_callback,
            10
        )
        
        # Subscribers pentru evenimente
        self.sensor_event_sub = self.create_subscription(
            String,
            '/sensors/events',
            self.sensor_event_callback,
            10
        )
        
        self.nav_event_sub = self.create_subscription(
            String,
            '/navigation/events',
            self.navigation_event_callback,
            10
        )
        
        # Timer pentru trimiterea periodică a datelor către cloud
        self.cloud_update_timer = self.create_timer(0.5, self.send_update_to_cloud)
        
        # Pornim un thread separat pentru a gestiona conexiunea WebSocket
        self.websocket_thread = threading.Thread(target=self.websocket_connection_manager)
        self.websocket_thread.daemon = True
        self.websocket_thread.start()
        
        self.get_logger().info('Cloud Interface initialized')
    
    def odom_callback(self, msg):
        """Actualizează poziția și viteza robotului din odometrie"""
        x = msg.pose.pose.position.x
        y = msg.pose.pose.position.y
        # Calculăm orientarea (theta) din quaternion
        q = msg.pose.pose.orientation
        theta = 2.0 * np.arctan2(q.z, q.w)
        
        self.current_position = (x, y, theta)
        self.robot_speed = msg.twist.twist.linear.x
    
    def map_callback(self, msg):
        """Procesează harta primită și o pregătește pentru transmitere"""
        # Stocăm informațiile despre hartă pentru transmitere
        self.map_data = {
            'width': msg.info.width,
            'height': msg.info.height,
            'resolution': msg.info.resolution,
            'origin_x': msg.info.origin.position.x,
            'origin_y': msg.info.origin.position.y,
            'data': None  # Harta completă ar fi prea mare pentru transmitere frecventă
        }
        
        # Pentru transmiterea către cloud, ar trebui să comprimăm harta sau să o transmitem doar când se schimbă semnificativ
    
    def camera_callback(self, msg):
        """Procesează imaginea de la cameră pentru streaming"""
        if not self.video_enabled or not self.is_connected:
            return
            
        try:
            # Convertim imaginea ROS în format OpenCV
            cv_image = self.cv_bridge.imgmsg_to_cv2(msg, "bgr8")
            
            # Redimensionăm imaginea dacă este necesar
            width, height = map(int, self.video_resolution.split('x'))
            cv_image = cv2.resize(cv_image, (width, height))
            
            # Generăm un overlay cu informații
            self.add_overlay_to_image(cv_image)
            
            # Comprimăm imaginea în format JPEG
            encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), self.video_quality]
            _, jpeg_image = cv2.imencode('.jpg', cv_image, encode_param)
            
            # Convertim în format base64 pentru transmitere
            import base64
            jpeg_base64 = base64.b64encode(jpeg_image).decode('utf-8')
            
            # Trimitem imaginea către cloud
            self.send_video_frame(jpeg_base64)
        except Exception as e:
            self.get_logger().error(f"Error processing camera image: {str(e)}")
    
    def add_overlay_to_image(self, image):
        """Adaugă un overlay cu informații pe imagine"""
        # Adăugăm poziția curentă și starea navigării
        text = f"Pos: ({self.current_position[0]:.2f}, {self.current_position[1]:.2f})"
        cv2.putText(image, text, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        
        text = f"Speed: {self.robot_speed:.2f} m/s"
        cv2.putText(image, text, (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        
        text = f"State: {self.navigation_state}"
        cv2.putText(image, text, (10, 90), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        
        # Adăugăm evenimentele recente
        y_pos = 120
        for i, event in enumerate(self.events[-3:]):  # Ultimele 3 evenimente
            event_text = f"{event['type']} at ({event['x']:.1f}, {event['y']:.1f})"
            color = (0, 0, 255) if 'ALCOHOL' in event['type'] else (255, 0, 0) if 'MAGNET' in event['type'] else (255, 255, 0)
            cv2.putText(image, event_text, (10, y_pos), cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)
            y_pos += 25
    
    def lidar_callback(self, msg):
        """Procesează datele de la LIDAR pentru transmitere"""
        # Pentru interfața cloud, am putea trimite o versiune simplificată a datelor LIDAR
        # Nu trimitem la fiecare frame pentru a economisi lățimea de bandă
        pass
    
    def sensor_event_callback(self, msg):
        """Procesează evenimentele de la senzori și le pregătește pentru transmitere"""
        event_data = msg.data
        self.get_logger().info(f"Sensor event: {event_data}")
        
        # Parsează evenimentul
        if ":" in event_data:
            parts = event_data.split(":")
            event_type = parts[0]
            coords = parts[1].split(",")
            x, y = float(coords[0]), float(coords[1])
            
            # Adaugă în lista de evenimente
            event = {
                'type': event_type,
                'x': x,
                'y': y,
                'timestamp': datetime.now().isoformat(),
                'value': float(parts[2]) if len(parts) > 2 else None
            }
            self.events.append(event)
            
            # Salvează și în fișier log
            self.log_event_to_file(event)
            
            # Trimite evenimentul imediat
            self.send_event_to_cloud(event)
    
    def navigation_event_callback(self, msg):
        """Procesează evenimentele de navigare și actualizează starea"""
        event_data = msg.data
        self.get_logger().info(f"Navigation event: {event_data}")
        
        # Actualizează starea de navigare
        if "NAVIGATING_TO" in event_data:
            self.navigation_state = "NAVIGATING"
        elif "SCANNING_AREA" in event_data:
            self.navigation_state = "SCANNING"
        elif "EXPLORATION_COMPLETE" in event_data:
            self.navigation_state = "COMPLETED"
        else:
            self.navigation_state = event_data
    
    def log_event_to_file(self, event):
        """Salvează un eveniment în fișierul de log"""
        try:
            # Asigură-te că directorul logs există
            import os
            log_dir = os.path.join(os.path.expanduser('~'), 'HS', 'logs')
            os.makedirs(log_dir, exist_ok=True)
            
            # Numele fișierului conține data
            log_file = os.path.join(log_dir, f"events_{datetime.now().strftime('%Y-%m-%d')}.log")
            
            # Adaugă evenimentul în fișier
            with open(log_file, 'a') as f:
                json_event = json.dumps(event)
                f.write(f"{datetime.now().isoformat()} | {json_event}\n")
        except Exception as e:
            self.get_logger().error(f"Error logging event to file: {str(e)}")
    
    def websocket_connection_manager(self):
        """Gestionează conexiunea WebSocket în bucla asyncio"""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        while True:
            try:
                loop.run_until_complete(self.maintain_websocket_connection())
            except Exception as e:
                self.get_logger().error(f"WebSocket loop error: {str(e)}")
            
            # Așteptăm înainte de a încerca reconectarea
            time.sleep(self.reconnect_interval)
    
    async def maintain_websocket_connection(self):
        """Menține conexiunea WebSocket activă"""
        self.get_logger().info(f"Connecting to WebSocket server at {self.websocket_url}")
        
        try:
            async with websockets.connect(self.websocket_url) as websocket:
                with self.connection_lock:
                    self.websocket = websocket
                    self.is_connected = True
                
                self.get_logger().info("Connected to WebSocket server")
                
                # Trimitem mesaj de hello
                await websocket.send(json.dumps({
                    'type': 'hello',
                    'robot_id': 'maze_explorer',
                    'timestamp': datetime.now().isoformat()
                }))
                
                # Bucla principală de recepție
                while True:
                    try:
                        message = await websocket.recv()
                        self.process_cloud_message(message)
                    except websockets.exceptions.ConnectionClosed:
                        self.get_logger().warn("WebSocket connection closed")
                        break
        
        except Exception as e:
            self.get_logger().error(f"WebSocket connection error: {str(e)}")
        
        # Actualizăm starea conexiunii când se închide
        with self.connection_lock:
            self.websocket = None
            self.is_connected = False
    
    def process_cloud_message(self, message):
        """Procesează mesajele primite de la server"""
        try:
            data = json.loads(message)
            message_type = data.get('type', '')
            
            if message_type == 'command':
                # Procesează comenzile de la cloud
                command = data.get('command', '')
                self.get_logger().info(f"Received command from cloud: {command}")
                
                # Aici am putea procesa diverse comenzi
                # De exemplu: 'stop', 'resume', 'return_to_start', etc.
        
        except Exception as e:
            self.get_logger().error(f"Error processing cloud message: {str(e)}")
    
    def send_update_to_cloud(self):
        """Trimite periodic actualizări cu starea robotului către cloud"""
        if not self.is_connected:
            return
            
        # Pregătim datele de stare
        state_data = {
            'type': 'state_update',
            'timestamp': datetime.now().isoformat(),
            'position': {
                'x': self.current_position[0],
                'y': self.current_position[1],
                'theta': self.current_position[2]
            },
            'speed': self.robot_speed,
            'navigation_state': self.navigation_state,
            'events_count': len(self.events)
        }
        
        # Trimitem starea către cloud
        asyncio.run_coroutine_threadsafe(
            self.send_data_to_websocket(json.dumps(state_data)),
            asyncio.get_event_loop()
        )
    
    def send_event_to_cloud(self, event):
        """Trimite un eveniment către cloud"""
        if not self.is_connected:
            return
            
        event_data = {
            'type': 'event',
            'event': event
        }
        
        # Trimitem evenimentul către cloud
        asyncio.run_coroutine_threadsafe(
            self.send_data_to_websocket(json.dumps(event_data)),
            asyncio.get_event_loop()
        )
    
    def send_video_frame(self, frame_data):
        """Trimite un frame video către cloud"""
        if not self.is_connected or not self.video_enabled:
            return
            
        frame_message = {
            'type': 'video_frame',
            'timestamp': datetime.now().isoformat(),
            'frame': frame_data,
            'format': 'jpg',
            'resolution': self.video_resolution
        }
        
        # Trimitem doar headerul pentru a economisi lățimea de bandă în logging
        log_message = frame_message.copy()
        log_message['frame'] = '[FRAME_DATA]'
        self.get_logger().debug(f"Sending video frame: {log_message}")
        
        # Trimitem frame-ul către cloud
        asyncio.run_coroutine_threadsafe(
            self.send_data_to_websocket(json.dumps(frame_message)),
            asyncio.get_event_loop()
        )
    
    async def send_data_to_websocket(self, data):
        """Trimite date către conexiunea WebSocket"""
        with self.connection_lock:
            if self.websocket is not None and self.is_connected:
                try:
                    await self.websocket.send(data)
                except Exception as e:
                    self.get_logger().error(f"Error sending data to WebSocket: {str(e)}")
                    self.is_connected = False

def main(args=None):
    rclpy.init(args=args)
    node = CloudInterface()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()
