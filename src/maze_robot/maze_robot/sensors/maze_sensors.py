#!/usr/bin/env python3
# encoding: utf-8
# Detectarea evenimentelor în labirint folosind diverși senzori

import rclpy
import time
import math
import RPi.GPIO as GPIO  # Se va utiliza pe Raspberry Pi
import threading
from rclpy.node import Node
from std_msgs.msg import String, Float32, Bool
from geometry_msgs.msg import Point, PoseStamped
from nav_msgs.msg import Odometry
from sensor_msgs.msg import LaserScan

class MazeSensors(Node):
    def __init__(self):
        super().__init__('maze_sensors')
        
        # Parametri pentru senzori (trebuie ajustați în funcție de conexiunile reale)
        self.declare_parameter('hall_sensor_pin', 17)        # GPIO pin pentru senzorul Hall
        self.declare_parameter('vibration_sensor_pin', 27)   # GPIO pin pentru senzorul de vibrații
        self.declare_parameter('alcohol_sensor_pin', 22)     # GPIO pin pentru senzorul de alcool (analog)
        self.declare_parameter('alcohol_threshold', 400)     # Pragul pentru detectarea alcoolului (valoare analogică)
        self.declare_parameter('led_pin_r', 18)              # GPIO pin pentru LED roșu
        self.declare_parameter('led_pin_g', 23)              # GPIO pin pentru LED verde
        self.declare_parameter('led_pin_b', 24)              # GPIO pin pentru LED albastru
        self.declare_parameter('buzzer_pin', 25)             # GPIO pin pentru buzzer
        
        # Obține valorile parametrilor
        self.hall_pin = self.get_parameter('hall_sensor_pin').value
        self.vibration_pin = self.get_parameter('vibration_sensor_pin').value
        self.alcohol_pin = self.get_parameter('alcohol_sensor_pin').value
        self.alcohol_threshold = self.get_parameter('alcohol_threshold').value
        self.led_pin_r = self.get_parameter('led_pin_r').value
        self.led_pin_g = self.get_parameter('led_pin_g').value
        self.led_pin_b = self.get_parameter('led_pin_b').value
        self.buzzer_pin = self.get_parameter('buzzer_pin').value
        
        # Stare senzori
        self.magnet_detected = False
        self.magnet_count = 0
        self.vibration_detected = False
        self.alcohol_detected = False
        self.current_position = (0.0, 0.0)
        self.position_lock = threading.Lock()
        
        # Publishers pentru evenimente și date de la senzori
        self.event_pub = self.create_publisher(String, '/sensors/events', 10)
        self.hall_pub = self.create_publisher(Bool, '/sensors/hall', 10)
        self.vibration_pub = self.create_publisher(Bool, '/sensors/vibration', 10)
        self.alcohol_pub = self.create_publisher(Float32, '/sensors/alcohol', 10)
        
        # Subscriber pentru poziția robotului
        self.odom_sub = self.create_subscription(
            Odometry,
            '/odom',
            self.odom_callback,
            10
        )
        
        # Timer pentru verificarea periodică a senzorilor
        self.sensor_timer = self.create_timer(0.1, self.check_sensors)
        
        # Inițializare GPIO (se va executa pe Raspberry Pi)
        try:
            GPIO.setmode(GPIO.BCM)
            GPIO.setup(self.hall_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
            GPIO.setup(self.vibration_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
            
            # ADC pentru senzorul de alcool ar trebui configurat aici (ADS1115/MCP3008)
            # Pe Raspberry Pi, vom folosi un ADC pentru a citi senzorul analogic MQ-3
            
            # Setup LED și buzzer
            GPIO.setup(self.led_pin_r, GPIO.OUT)
            GPIO.setup(self.led_pin_g, GPIO.OUT)
            GPIO.setup(self.led_pin_b, GPIO.OUT)
            GPIO.setup(self.buzzer_pin, GPIO.OUT)
            
            # Setăm callbackuri pentru Hall și vibrații (edge detection)
            GPIO.add_event_detect(self.hall_pin, GPIO.FALLING, callback=self.hall_callback, bouncetime=300)
            GPIO.add_event_detect(self.vibration_pin, GPIO.FALLING, callback=self.vibration_callback, bouncetime=100)
            
            self.get_logger().info("GPIO setup complete for sensors")
        except:
            # Vom primi excepție dacă nu rulăm pe un Raspberry Pi
            self.get_logger().warn("GPIO setup failed - not running on Raspberry Pi or missing permissions")
            # SIMULARE: Facem o simulare simplă pentru dezvoltare/testare
            self.get_logger().info("Running in simulation mode for development")
        
        self.get_logger().info('Maze Sensors initialized')
    
    def odom_callback(self, msg):
        """Actualizează poziția curentă din datele de odometrie"""
        with self.position_lock:
            self.current_position = (
                msg.pose.pose.position.x,
                msg.pose.pose.position.y
            )
    
    def hall_callback(self, channel):
        """Callback pentru senzorul Hall când detectează un magnet"""
        # Această funcție va fi apelată când senzorul Hall detectează un magnet
        self.magnet_detected = True
        self.magnet_count += 1
        
        # Publicăm starea senzorului
        hall_msg = Bool()
        hall_msg.data = True
        self.hall_pub.publish(hall_msg)
        
        # Emitem un eveniment cu coordonatele actuale
        with self.position_lock:
            position = self.current_position
        
        event_msg = String()
        event_msg.data = f"MAGNET_DETECTED:{position[0]:.2f},{position[1]:.2f}"
        self.event_pub.publish(event_msg)
        
        # Semnalizăm cu LED/buzzer
        self.signal_event('magnet')
        
        self.get_logger().info(f"Magnet detected at position ({position[0]:.2f}, {position[1]:.2f})! Magnet count: {self.magnet_count}")
        
        # Verificăm dacă am găsit ieșirea (două magneți)
        if self.magnet_count >= 2:
            event_msg = String()
            event_msg.data = f"EXIT_FOUND:{position[0]:.2f},{position[1]:.2f}"
            self.event_pub.publish(event_msg)
            self.get_logger().info(f"Exit found at position ({position[0]:.2f}, {position[1]:.2f})!")
    
    def vibration_callback(self, channel):
        """Callback pentru senzorul de vibrații când detectează o denivelare"""
        # Această funcție va fi apelată când senzorul de vibrații detectează o denivelare
        self.vibration_detected = True
        
        # Publicăm starea senzorului
        vibration_msg = Bool()
        vibration_msg.data = True
        self.vibration_pub.publish(vibration_msg)
        
        # Emitem un eveniment cu coordonatele actuale
        with self.position_lock:
            position = self.current_position
            
        event_msg = String()
        event_msg.data = f"BUMP_DETECTED:{position[0]:.2f},{position[1]:.2f}"
        self.event_pub.publish(event_msg)
        
        # Semnalizăm cu LED/buzzer
        self.signal_event('bump')
        
        self.get_logger().info(f"Speed bump detected at position ({position[0]:.2f}, {position[1]:.2f})!")
        
        # Resetăm starea după un timp
        timer = threading.Timer(2.0, self.reset_vibration_state)
        timer.start()
    
    def reset_vibration_state(self):
        """Resetează starea senzorului de vibrații după un timp"""
        self.vibration_detected = False
    
    def read_alcohol_sensor(self):
        """Citește valoarea de la senzorul de alcool (analogic)"""
        # Aici ar trebui să implementăm logica pentru citirea valorii analogice de la senzorul MQ-3
        # În modul simulare, vom genera o valoare aleatorie pentru demonstrație
        import random
        return random.randint(200, 600)  # Simulăm o valoare între 200 și 600
    
    def check_sensors(self):
        """Verifică periodic starea senzorilor"""
        # Verificăm senzorul de alcool (analogic)
        alcohol_value = self.read_alcohol_sensor()
        
        # Publicăm valoarea senzorului
        alcohol_msg = Float32()
        alcohol_msg.data = float(alcohol_value)
        self.alcohol_pub.publish(alcohol_msg)
        
        # Verificăm dacă valoarea depășește pragul pentru alcool
        if alcohol_value > self.alcohol_threshold and not self.alcohol_detected:
            self.alcohol_detected = True
            
            # Emitem un eveniment cu coordonatele actuale
            with self.position_lock:
                position = self.current_position
                
            event_msg = String()
            event_msg.data = f"ALCOHOL_DETECTED:{position[0]:.2f},{position[1]:.2f}:{alcohol_value}"
            self.event_pub.publish(event_msg)
            
            # Semnalizăm cu LED/buzzer
            self.signal_event('alcohol')
            
            self.get_logger().info(f"Alcohol detected at position ({position[0]:.2f}, {position[1]:.2f})! Value: {alcohol_value}")
            
            # Resetăm starea după un timp
            timer = threading.Timer(5.0, self.reset_alcohol_state)
            timer.start()
    
    def reset_alcohol_state(self):
        """Resetează starea senzorului de alcool după un timp"""
        self.alcohol_detected = False
    
    def signal_event(self, event_type):
        """Semnalizează un eveniment folosind LED-uri și buzzer
        event_type: 'alcohol', 'magnet', 'bump'
        """
        try:
            if event_type == 'alcohol':
                # Alcool detectat - LED roșu și buzzer intermitent
                GPIO.output(self.led_pin_r, GPIO.HIGH)
                GPIO.output(self.led_pin_g, GPIO.LOW)
                GPIO.output(self.led_pin_b, GPIO.LOW)
                
                GPIO.output(self.buzzer_pin, GPIO.HIGH)
                time.sleep(0.5)
                GPIO.output(self.buzzer_pin, GPIO.LOW)
                
                # Resetăm LEDurile după 3 secunde
                timer = threading.Timer(3.0, self.reset_leds)
                timer.start()
                
            elif event_type == 'magnet':
                # Magnet detectat (ieșire) - LED verde constant
                GPIO.output(self.led_pin_r, GPIO.LOW)
                GPIO.output(self.led_pin_g, GPIO.HIGH)
                GPIO.output(self.led_pin_b, GPIO.LOW)
                
                # Buzzer cu două beep-uri scurte
                GPIO.output(self.buzzer_pin, GPIO.HIGH)
                time.sleep(0.2)
                GPIO.output(self.buzzer_pin, GPIO.LOW)
                time.sleep(0.1)
                GPIO.output(self.buzzer_pin, GPIO.HIGH)
                time.sleep(0.2)
                GPIO.output(self.buzzer_pin, GPIO.LOW)
                
                # Resetăm LEDurile după 2 secunde
                timer = threading.Timer(2.0, self.reset_leds)
                timer.start()
                
            elif event_type == 'bump':
                # Denivelare detectată - LED albastru scurt
                GPIO.output(self.led_pin_r, GPIO.LOW)
                GPIO.output(self.led_pin_g, GPIO.LOW)
                GPIO.output(self.led_pin_b, GPIO.HIGH)
                
                # Buzzer cu un beep scurt
                GPIO.output(self.buzzer_pin, GPIO.HIGH)
                time.sleep(0.1)
                GPIO.output(self.buzzer_pin, GPIO.LOW)
                
                # Resetăm LEDurile după 1 secundă
                timer = threading.Timer(1.0, self.reset_leds)
                timer.start()
        except:
            self.get_logger().warn("LED/Buzzer control failed - not running on Raspberry Pi or missing permissions")
    
    def reset_leds(self):
        """Resetează starea LED-urilor"""
        try:
            GPIO.output(self.led_pin_r, GPIO.LOW)
            GPIO.output(self.led_pin_g, GPIO.LOW)
            GPIO.output(self.led_pin_b, GPIO.LOW)
        except:
            pass

    def __del__(self):
        """Cleanup la închiderea nodului"""
        try:
            GPIO.cleanup()
        except:
            pass

def main(args=None):
    rclpy.init(args=args)
    node = MazeSensors()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()
