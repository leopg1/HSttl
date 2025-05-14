#!/usr/bin/env python3
# encoding: utf-8
# Modul pentru jurnalizarea evenimentelor detectate în labirint

import rclpy
import json
import os
import threading
from rclpy.node import Node
from std_msgs.msg import String
from datetime import datetime

class EventLogger(Node):
    def __init__(self):
        super().__init__('event_logger')
        
        # Parametri
        self.declare_parameter('log_directory', '~/HS/logs')
        self.log_directory = os.path.expanduser(self.get_parameter('log_directory').value)
        
        # Asigură-te că directorul de log există
        os.makedirs(self.log_directory, exist_ok=True)
        
        # Stare logger
        self.event_count = {
            'MAGNET_DETECTED': 0,
            'ALCOHOL_DETECTED': 0,
            'BUMP_DETECTED': 0,
            'EXIT_FOUND': 0,
            'EXPLORATION_COMPLETE': 0
        }
        self.event_log = []
        self.log_lock = threading.Lock()
        
        # Creează fișierele de log
        self.event_log_file = os.path.join(self.log_directory, f"events_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.json")
        self.summary_log_file = os.path.join(self.log_directory, f"summary_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.txt")
        
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
        
        # Timer pentru salvarea periodică a logurilor
        self.log_save_timer = self.create_timer(10.0, self.save_logs)
        
        self.get_logger().info(f'Event Logger initialized, logs will be stored in {self.log_directory}')
    
    def sensor_event_callback(self, msg):
        """Procesează și înregistrează evenimentele de la senzori"""
        event_data = msg.data
        self.get_logger().info(f"Logging sensor event: {event_data}")
        
        try:
            # Parsează evenimentul
            if ":" in event_data:
                parts = event_data.split(":")
                event_type = parts[0]
                coords = parts[1].split(",")
                x, y = float(coords[0]), float(coords[1])
                
                # Adaugă în contorizare
                if event_type in self.event_count:
                    self.event_count[event_type] += 1
                
                # Creează obiectul eveniment
                event = {
                    'type': event_type,
                    'x': x,
                    'y': y,
                    'timestamp': datetime.now().isoformat(),
                    'details': parts[2] if len(parts) > 2 else ""
                }
                
                # Adaugă la log
                with self.log_lock:
                    self.event_log.append(event)
                    
                # Salvează imediat evenimentele importante (magnet, alcool, exit)
                if 'MAGNET' in event_type or 'ALCOHOL' in event_type or 'EXIT' in event_type:
                    self.save_logs()
        except Exception as e:
            self.get_logger().error(f"Error processing sensor event: {str(e)}")
    
    def navigation_event_callback(self, msg):
        """Procesează și înregistrează evenimentele de navigare"""
        event_data = msg.data
        
        try:
            # Verifică dacă evenimentul este de interes pentru logare
            if "EXPLORATION_COMPLETE" in event_data:
                self.event_count['EXPLORATION_COMPLETE'] += 1
                
                # Creează obiectul eveniment
                event = {
                    'type': 'EXPLORATION_COMPLETE',
                    'timestamp': datetime.now().isoformat()
                }
                
                # Adaugă la log
                with self.log_lock:
                    self.event_log.append(event)
                    
                # Salvează imediat logul când explorarea este completă
                self.save_logs()
                self.create_summary()
        except Exception as e:
            self.get_logger().error(f"Error processing navigation event: {str(e)}")
    
    def save_logs(self):
        """Salvează evenimentele în fișierul de log"""
        try:
            with self.log_lock:
                if not self.event_log:
                    return
                    
                # Salvează logul ca JSON
                with open(self.event_log_file, 'w') as f:
                    json.dump(self.event_log, f, indent=2)
                
                self.get_logger().info(f"Events saved to {self.event_log_file}")
        except Exception as e:
            self.get_logger().error(f"Error saving logs: {str(e)}")
    
    def create_summary(self):
        """Creează un fișier rezumat cu statistici despre evenimentele detectate"""
        try:
            # Organizează evenimentele pe categorii
            alcohol_events = [e for e in self.event_log if 'ALCOHOL_DETECTED' in e['type']]
            magnet_events = [e for e in self.event_log if 'MAGNET_DETECTED' in e['type']]
            bump_events = [e for e in self.event_log if 'BUMP_DETECTED' in e['type']]
            exit_events = [e for e in self.event_log if 'EXIT_FOUND' in e['type']]
            
            # Creează rezumatul
            with open(self.summary_log_file, 'w') as f:
                f.write("=== MAZE EXPLORATION SUMMARY ===\n\n")
                f.write(f"Generated at: {datetime.now().isoformat()}\n\n")
                
                f.write("=== EVENT COUNTS ===\n")
                for event_type, count in self.event_count.items():
                    f.write(f"{event_type}: {count}\n")
                
                f.write("\n=== ALCOHOL CONTAINERS ===\n")
                if alcohol_events:
                    for event in alcohol_events:
                        f.write(f"Coordinates: ({event['x']:.2f}, {event['y']:.2f}), Detected at: {event['timestamp']}\n")
                else:
                    f.write("No alcohol containers detected.\n")
                    
                f.write("\n=== SPEED BUMPS ===\n")
                if bump_events:
                    for event in bump_events:
                        f.write(f"Coordinates: ({event['x']:.2f}, {event['y']:.2f}), Detected at: {event['timestamp']}\n")
                else:
                    f.write("No speed bumps detected.\n")
                    
                f.write("\n=== MAGNETS DETECTED ===\n")
                if magnet_events:
                    for event in magnet_events:
                        f.write(f"Coordinates: ({event['x']:.2f}, {event['y']:.2f}), Detected at: {event['timestamp']}\n")
                else:
                    f.write("No magnets detected.\n")
                    
                f.write("\n=== EXIT LOCATION ===\n")
                if exit_events:
                    event = exit_events[0]
                    f.write(f"Coordinates: ({event['x']:.2f}, {event['y']:.2f}), Found at: {event['timestamp']}\n")
                else:
                    f.write("Exit not found.\n")
                    
                f.write("\n=== EXPLORATION STATISTICS ===\n")
                total_events = len(self.event_log)
                f.write(f"Total events recorded: {total_events}\n")
                
                # Calculează timpul de explorare
                if self.event_log:
                    start_time = datetime.fromisoformat(self.event_log[0]['timestamp'])
                    end_time = datetime.fromisoformat(self.event_log[-1]['timestamp'])
                    exploration_time = (end_time - start_time).total_seconds()
                    f.write(f"Total exploration time: {exploration_time:.2f} seconds\n")
            
            self.get_logger().info(f"Summary created at {self.summary_log_file}")
        except Exception as e:
            self.get_logger().error(f"Error creating summary: {str(e)}")
    
    def __del__(self):
        """Cleanup la închiderea nodului"""
        # Salvează logul final și generează rezumatul
        self.save_logs()
        self.create_summary()

def main(args=None):
    rclpy.init(args=args)
    node = EventLogger()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()
