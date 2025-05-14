#!/usr/bin/env python3
# encoding: utf-8
# Controlul hardware al robotului - motoare, LED-uri, buzzer

import enum
import time
import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist
from sensor_msgs.msg import LaserScan
from std_msgs.msg import Bool, Int32, Float32, String
from rclpy.qos import QoSProfile, QoSReliabilityPolicy

# Codurile din kit-ul original pentru controlul motoarelor
class PacketFunction(enum.IntEnum):
    PACKET_FUNC_SYS = 0
    PACKET_FUNC_LED = 1      # LED control
    PACKET_FUNC_BUZZER = 2   # Buzzer control
    PACKET_FUNC_MOTOR = 3    # Motor control
    PACKET_FUNC_PWM_SERVO = 4 # PWM servo control
    PACKET_FUNC_BUS_SERVO = 5 # Bus servo control
    PACKET_FUNC_KEY = 6      # Button control
    PACKET_FUNC_IMU = 7      # IMU sensor
    PACKET_FUNC_RGB = 11     # RGB control

class MazeRobotHardware(Node):
    def __init__(self):
        super().__init__('maze_robot_hardware')
        
        # Parametrii hardware
        self.declare_parameter('max_speed', 0.3)
        self.declare_parameter('min_speed', 0.1)
        self.declare_parameter('angular_speed', 0.5)
        self.declare_parameter('lidar_angle_min', -2.35619)  # ~ -135 grade
        self.declare_parameter('lidar_angle_max', 2.35619)   # ~ 135 grade
        
        self.max_speed = self.get_parameter('max_speed').value
        self.min_speed = self.get_parameter('min_speed').value
        self.angular_speed = self.get_parameter('angular_speed').value
        self.lidar_angle_min = self.get_parameter('lidar_angle_min').value
        self.lidar_angle_max = self.get_parameter('lidar_angle_max').value
        
        # Stare robot
        self.is_moving = False
        self.current_speed = 0.0
        self.current_direction = 0.0  # unghi în radiani
        self.obstacles_detected = False
        
        # Publishers & Subscribers
        self.cmd_vel_pub = self.create_publisher(Twist, '/cmd_vel', 10)
        self.led_control_pub = self.create_publisher(Int32, '/led_control', 10)
        self.buzzer_control_pub = self.create_publisher(Bool, '/buzzer_control', 10)
        
        # Calitatea serviciului (QoS) pentru LIDAR
        qos = QoSProfile(depth=10, reliability=QoSReliabilityPolicy.BEST_EFFORT)
        self.lidar_sub = self.create_subscription(
            LaserScan, 
            '/scan', 
            self.lidar_callback, 
            qos_profile=qos
        )
        
        # Timer pentru logica de control
        self.control_timer = self.create_timer(0.1, self.control_loop)
        
        self.get_logger().info('Maze Robot Hardware initialized')
    
    def lidar_callback(self, msg):
        """Procesează datele de la LIDAR pentru detecția obstacolelor"""
        # Verifică doar raza frontală pentru obstacole
        front_range = []
        for i, r in enumerate(msg.ranges):
            angle = msg.angle_min + i * msg.angle_increment
            # Verificăm doar unghiuri frontale într-un unghi de ~30 grade
            if -0.26 < angle < 0.26 and r < float('inf'):
                front_range.append(r)
        
        # Dacă există obstacole în față la mai puțin de 0.3m, notificăm
        if front_range and min(front_range) < 0.3:
            self.obstacles_detected = True
        else:
            self.obstacles_detected = False
    
    def set_motor_speed(self, linear_x, angular_z):
        """Setează vitezele motoarelor cu limitare de siguranță"""
        # Limitarea vitezelor pentru siguranță
        linear_x = max(-self.max_speed, min(self.max_speed, linear_x))
        angular_z = max(-self.angular_speed, min(self.angular_speed, angular_z))
        
        # Trimite comanda de viteză
        twist_msg = Twist()
        twist_msg.linear.x = linear_x
        twist_msg.angular.z = angular_z
        self.cmd_vel_pub.publish(twist_msg)
        
        # Actualizează starea
        self.is_moving = linear_x != 0.0 or angular_z != 0.0
        self.current_speed = linear_x
    
    def stop_motors(self):
        """Oprește toate motoarele"""
        self.set_motor_speed(0.0, 0.0)
    
    def set_led_color(self, color_code):
        """Setează culoarea LED-urilor
        color_code: 0 = Oprit, 1 = Roșu, 2 = Verde, 3 = Albastru, 4 = Galben
        """
        msg = Int32()
        msg.data = color_code
        self.led_control_pub.publish(msg)
    
    def activate_buzzer(self, state):
        """Activează sau dezactivează buzzer-ul"""
        msg = Bool()
        msg.data = state
        self.buzzer_control_pub.publish(msg)
    
    def signal_event(self, event_type):
        """Semnalizează un eveniment folosind LED-uri și buzzer
        event_type: 'alcohol', 'magnet', 'bump'
        """
        if event_type == 'alcohol':
            # Alcool detectat - LED roșu și buzzer intermitent
            self.set_led_color(1)  # Roșu
            self.activate_buzzer(True)
            time.sleep(0.5)
            self.activate_buzzer(False)
        elif event_type == 'magnet':
            # Magnet detectat (ieșire) - LED verde constant
            self.set_led_color(2)  # Verde
            self.activate_buzzer(True)
            time.sleep(0.2)
            self.activate_buzzer(False)
            time.sleep(0.1)
            self.activate_buzzer(True)
            time.sleep(0.2)
            self.activate_buzzer(False)
        elif event_type == 'bump':
            # Denivelare detectată - LED albastru scurt
            self.set_led_color(3)  # Albastru
            self.activate_buzzer(True)
            time.sleep(0.1)
            self.activate_buzzer(False)
    
    def control_loop(self):
        """Logica principală de control hardware executată periodic"""
        # Oprește robotul dacă detectează un obstacol foarte aproape
        if self.obstacles_detected and self.is_moving:
            self.get_logger().warn('Obstacle detected, stopping')
            self.stop_motors()

def main(args=None):
    rclpy.init(args=args)
    node = MazeRobotHardware()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()
