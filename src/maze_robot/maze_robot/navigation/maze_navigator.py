#!/usr/bin/env python3
# encoding: utf-8
# Navigare autonomă în labirint folosind SLAM și algoritmi de explorare

import rclpy
import numpy as np
import math
import time
from rclpy.node import Node
from geometry_msgs.msg import Twist, PoseStamped, Point
from nav_msgs.msg import OccupancyGrid, Odometry
from std_msgs.msg import Bool, String
from sensor_msgs.msg import LaserScan
from tf2_ros import TransformListener, Buffer
from rclpy.qos import QoSProfile, QoSReliabilityPolicy

class MazeNavigator(Node):
    def __init__(self):
        super().__init__('maze_navigator')
        
        # Parametri navigare
        self.declare_parameter('exploration_rate', 0.3)  # m/s
        self.declare_parameter('turn_rate', 0.5)  # rad/s
        self.declare_parameter('min_front_distance', 0.4)  # m
        self.declare_parameter('wall_follow_distance', 0.3)  # m
        self.declare_parameter('frontier_size_threshold', 5)  # celule
        
        self.exploration_rate = self.get_parameter('exploration_rate').value
        self.turn_rate = self.get_parameter('turn_rate').value
        self.min_front_distance = self.get_parameter('min_front_distance').value
        self.wall_follow_distance = self.get_parameter('wall_follow_distance').value
        self.frontier_size_threshold = self.get_parameter('frontier_size_threshold').value
        
        # Stare navigare
        self.current_pose = None  # poziția curentă (x, y, theta)
        self.map_data = None  # datele hărții
        self.frontiers = []  # frontierele detectate
        self.exploration_complete = False
        self.path_to_follow = []  # calea planificată
        self.is_navigating = False
        self.exit_found = False
        self.start_position = (0.0, 0.0)  # poziția de start
        
        # Crearea unui ascultător pentru transformări
        self.tf_buffer = Buffer()
        self.tf_listener = TransformListener(self.tf_buffer, self)
        
        # Publishers & Subscribers
        qos = QoSProfile(depth=10, reliability=QoSReliabilityPolicy.BEST_EFFORT)
        
        # Controlul mișcării
        self.cmd_vel_pub = self.create_publisher(Twist, '/cmd_vel', 10)
        
        # Abonare la scanner-ul laser pentru evitarea obstacolelor
        self.scan_sub = self.create_subscription(
            LaserScan, 
            '/scan', 
            self.scan_callback, 
            qos_profile=qos
        )
        
        # Abonare la odometrie pentru determinarea poziției
        self.odom_sub = self.create_subscription(
            Odometry,
            '/odom',
            self.odom_callback,
            10
        )
        
        # Abonare la harta pentru explorare
        self.map_sub = self.create_subscription(
            OccupancyGrid,
            '/map',
            self.map_callback,
            10
        )
        
        # Publisher pentru evenimente de navigare
        self.nav_event_pub = self.create_publisher(String, '/navigation/events', 10)
        
        # Subscriber pentru evenimente de la senzori
        self.sensor_event_sub = self.create_subscription(
            String,
            '/sensors/events',
            self.sensor_event_callback,
            10
        )
        
        # Timer pentru logica de navigare
        self.navigation_timer = self.create_timer(0.1, self.navigation_loop)
        
        # Timer pentru actualizarea frontierelor
        self.frontier_timer = self.create_timer(2.0, self.update_frontiers)
        
        self.get_logger().info('Maze Navigator initialized at position (0, 0)')
        
    def odom_callback(self, msg):
        """Actualizează poziția curentă din datele de odometrie"""
        self.current_pose = (
            msg.pose.pose.position.x,
            msg.pose.pose.position.y,
            self.get_yaw_from_quaternion(msg.pose.pose.orientation)
        )
    
    def get_yaw_from_quaternion(self, q):
        """Calculează unghiul yaw din quaternion"""
        # Simplificat - ar trebui să folosim funcții din tf2 pentru conversii complete
        siny_cosp = 2.0 * (q.w * q.z + q.x * q.y)
        cosy_cosp = 1.0 - 2.0 * (q.y * q.y + q.z * q.z)
        return math.atan2(siny_cosp, cosy_cosp)
    
    def scan_callback(self, msg):
        """Procesează datele de la scanner-ul laser"""
        # Verificăm dacă există obstacole în față
        front_ranges = []
        for i, r in enumerate(msg.ranges):
            angle = msg.angle_min + i * msg.angle_increment
            # Considerăm doar unghiurile frontale într-un con de ~30 grade
            if -0.26 < angle < 0.26 and r < float('inf'):
                front_ranges.append(r)
        
        # Dacă suntem în mod de navigare și detectăm obstacole prea apropiate, încetinește sau oprește
        if self.is_navigating and front_ranges and min(front_ranges) < self.min_front_distance:
            self.get_logger().info(f'Obstacle detected at {min(front_ranges)}m, slowing down')
            self.slow_down()
    
    def map_callback(self, msg):
        """Procesează datele hărții pentru explorare și planificare traseu"""
        self.map_data = msg
        self.map_width = msg.info.width
        self.map_height = msg.info.height
        self.map_resolution = msg.info.resolution
        self.map_origin = (msg.info.origin.position.x, msg.info.origin.position.y)
        
        # Emite un eveniment de navigare indicând actualizarea hărții
        event_msg = String()
        event_msg.data = f"MAP_UPDATED:{self.map_width}x{self.map_height}"
        self.nav_event_pub.publish(event_msg)
    
    def sensor_event_callback(self, msg):
        """Gestionează evenimentele de la senzori"""
        if "MAGNET_DETECTED" in msg.data:
            self.get_logger().info("Exit detected! Navigating to exit.")
            self.exit_found = True
            # Ar trebui să navigăm către ieșire când este detectată
            
        # Alte tipuri de evenimente care ar putea afecta navigarea
        elif "OBSTACLE_DETECTED" in msg.data:
            self.get_logger().warn("New obstacle detected, updating path...")
            # Actualizăm planificarea dacă este necesar
    
    def update_frontiers(self):
        """Detectează frontierele pentru explorare"""
        if self.map_data is None or self.current_pose is None:
            return
        
        # Codul ar trebui să implementeze detectarea frontierelor în harta ocupată
        # Aceasta este o implementare simplificată - în practică, ar trebui să folosim
        # algoritmii de detectare a frontierelor precum WFD (Wavefront Frontier Detection)
        
        # Simulăm găsirea frontierelor
        self.frontiers = self.detect_frontiers_simplified()
        
        if not self.frontiers and self.map_data is not None and not self.exploration_complete:
            self.get_logger().info("No more frontiers detected, exploration complete!")
            self.exploration_complete = True
            
            # Notificăm că explorarea este completă
            event_msg = String()
            event_msg.data = "EXPLORATION_COMPLETE"
            self.nav_event_pub.publish(event_msg)
    
    def detect_frontiers_simplified(self):
        """Implementare simplificată a detecției frontierelor"""
        # Această implementare este un placeholder
        # Ar trebui să detecteze granițele între spațiile libere și necunoscute din hartă
        frontiers = []
        
        # Logica reală ar fi mai complexă, implicând analiza hărții
        # și identificarea zonelor de tranziție între spațiul explorat și neexplorat
        
        return frontiers
    
    def choose_next_frontier(self):
        """Alege următoarea frontieră pentru explorare"""
        if not self.frontiers:
            return None
            
        # Strategia cea mai simplă: alege cea mai apropiată frontieră
        closest_frontier = None
        min_distance = float('inf')
        
        for frontier in self.frontiers:
            dist = self.calculate_distance(self.current_pose, frontier)
            if dist < min_distance:
                min_distance = dist
                closest_frontier = frontier
                
        return closest_frontier
    
    def calculate_distance(self, point1, point2):
        """Calculează distanța euclidiană între două puncte"""
        return math.sqrt((point1[0] - point2[0])**2 + (point1[1] - point2[1])**2)
    
    def set_motion(self, linear_x, angular_z):
        """Trimite comenzi de mișcare către robot"""
        twist_msg = Twist()
        twist_msg.linear.x = linear_x
        twist_msg.angular.z = angular_z
        self.cmd_vel_pub.publish(twist_msg)
    
    def slow_down(self):
        """Încetinește robotul când detectează obstacole"""
        twist_msg = Twist()
        twist_msg.linear.x = 0.05  # Viteză foarte mică
        self.cmd_vel_pub.publish(twist_msg)
    
    def stop(self):
        """Oprește robotul"""
        twist_msg = Twist()
        twist_msg.linear.x = 0.0
        twist_msg.angular.z = 0.0
        self.cmd_vel_pub.publish(twist_msg)
    
    def navigation_loop(self):
        """Logica principală de navigare și explorare"""
        if self.current_pose is None:
            self.get_logger().warn("No pose data available yet")
            return
            
        # Dacă am găsit ieșirea și explorarea e completă, ne întoarcem la start
        if self.exit_found and self.exploration_complete:
            self.get_logger().info("Exploration complete and exit found. Returning to start...")
            # Planifică un traseu către poziția de start
            self.navigate_to_point(self.start_position)
            return
            
        # Dacă suntem deja în mișcare pe o cale planificată, continuăm
        if self.is_navigating and self.path_to_follow:
            # Urmează calea curentă
            # (Cod simplificat - ar trebui să implementeze logica de urmărire)
            return
            
        # Dacă nu avem o cale sau am terminat-o, cautăm o nouă frontieră
        if not self.is_navigating or not self.path_to_follow:
            next_frontier = self.choose_next_frontier()
            
            if next_frontier:
                self.get_logger().info(f"Navigating to next frontier at {next_frontier}")
                self.navigate_to_point(next_frontier)
            else:
                # Nu mai avem frontiere, facem rotație pentru a scana mai bine
                self.get_logger().info("No frontiers found, scanning area...")
                self.scan_area()
    
    def navigate_to_point(self, target_point):
        """Planifică un traseu către un punct țintă"""
        # Aici ar trebui să folosim ROS Navigation Stack pentru planificarea traseului
        # Implementare simplificată pentru demo
        
        self.is_navigating = True
        
        # Calculăm direcția către țintă
        dx = target_point[0] - self.current_pose[0]
        dy = target_point[1] - self.current_pose[1]
        target_angle = math.atan2(dy, dx)
        
        # Diferența între unghiul curent și cel dorit
        angle_diff = target_angle - self.current_pose[2]
        
        # Normalizăm între -pi și pi
        angle_diff = math.atan2(math.sin(angle_diff), math.cos(angle_diff))
        
        # Dacă unghiul este semnificativ, mai întâi ne rotim
        if abs(angle_diff) > 0.1:
            # Rotim spre direcția dorită
            angular_speed = self.turn_rate * (1.0 if angle_diff > 0 else -1.0)
            self.set_motion(0.0, angular_speed)
        else:
            # Mergem înainte când suntem orientați corect
            self.set_motion(self.exploration_rate, 0.0)
        
        # Emitem un eveniment de navigare
        event_msg = String()
        event_msg.data = f"NAVIGATING_TO:{target_point[0]:.2f},{target_point[1]:.2f}"
        self.nav_event_pub.publish(event_msg)
    
    def scan_area(self):
        """Rotește robotul pentru a scana zona"""
        self.set_motion(0.0, self.turn_rate)
        time.sleep(1.0)  # Rotire timp de 1 secundă
        self.stop()
        
        # Emitem un eveniment de navigare
        event_msg = String()
        event_msg.data = "SCANNING_AREA"
        self.nav_event_pub.publish(event_msg)

def main(args=None):
    rclpy.init(args=args)
    node = MazeNavigator()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()
