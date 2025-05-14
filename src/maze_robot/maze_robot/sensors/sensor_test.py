#!/usr/bin/env python3
# encoding: utf-8
# Script pentru testarea senzorilor

import rclpy
import time
import threading
try:
    import RPi.GPIO as GPIO
    SIMULATION_MODE = False
except ImportError:
    SIMULATION_MODE = True
    print("RPi.GPIO nu a putut fi importat. Rulăm în mod simulare.")
    print("Verificați dacă aveți permisiunile necesare pentru accesul la GPIO")
    # Încercăm să instalăm automat pachetul dacă lipsește
    try:
        import subprocess
        print("Încercare de instalare automată a RPi.GPIO...")
        subprocess.check_call(["pip3", "install", "RPi.GPIO"])
        import RPi.GPIO as GPIO
        SIMULATION_MODE = False
        print("RPi.GPIO a fost instalat cu succes!")
    except Exception as e:
        print(f"Nu s-a putut instala automat: {e}")

from rclpy.node import Node
from std_msgs.msg import String, Bool, Float32

class SensorTest(Node):
    def __init__(self):
        super().__init__('sensor_test')
        
        # Parametri pentru senzori
        self.declare_parameter('hall_sensor_pin', 17)
        self.declare_parameter('vibration_sensor_pin', 27)
        self.declare_parameter('alcohol_sensor_pin', 22)
        self.declare_parameter('led_pin_r', 18)
        self.declare_parameter('led_pin_g', 23)
        self.declare_parameter('led_pin_b', 24)
        self.declare_parameter('buzzer_pin', 25)
        
        # Obține valorile parametrilor
        self.hall_pin = self.get_parameter('hall_sensor_pin').value
        self.vibration_pin = self.get_parameter('vibration_sensor_pin').value
        self.alcohol_pin = self.get_parameter('alcohol_sensor_pin').value
        self.led_pin_r = self.get_parameter('led_pin_r').value
        self.led_pin_g = self.get_parameter('led_pin_g').value
        self.led_pin_b = self.get_parameter('led_pin_b').value
        self.buzzer_pin = self.get_parameter('buzzer_pin').value
        
        # Publishers pentru status senzori
        self.status_pub = self.create_publisher(String, '/sensors/status', 10)
        self.hall_pub = self.create_publisher(Bool, '/sensors/hall', 10)
        self.vibration_pub = self.create_publisher(Bool, '/sensors/vibration', 10)
        self.alcohol_pub = self.create_publisher(Float32, '/sensors/alcohol', 10)
        
        # Timer pentru testarea periodică a senzorilor
        self.test_timer = self.create_timer(1.0, self.test_sensors)
        
        # Test LED și buzzer
        self.led_test_timer = self.create_timer(5.0, self.test_led_buzzer)
        
        # Stare pentru testul de LED-uri
        self.led_test_state = 0
        
        # Inițializare GPIO
        self.setup_gpio()
        
        if SIMULATION_MODE:
            self.get_logger().info("Sensor Test inițializat în MOD SIMULARE")
        else:
            self.get_logger().info("Sensor Test inițializat și gata de utilizare")
    
    def setup_gpio(self):
        """Inițializează pinii GPIO pentru senzori și actuatori"""
        if SIMULATION_MODE:
            return
            
        try:
            GPIO.setmode(GPIO.BCM)
            
            # Setup senzori
            GPIO.setup(self.hall_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
            GPIO.setup(self.vibration_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
            
            # Pentru senzorul de alcool analog, ar trebui să folosim un ADC
            # Acest cod simulează doar citirea
            
            # Setup LED-uri și buzzer
            GPIO.setup(self.led_pin_r, GPIO.OUT)
            GPIO.setup(self.led_pin_g, GPIO.OUT)
            GPIO.setup(self.led_pin_b, GPIO.OUT)
            GPIO.setup(self.buzzer_pin, GPIO.OUT)
            
            # Inițial toate LED-urile și buzzer-ul sunt oprite
            GPIO.output(self.led_pin_r, GPIO.LOW)
            GPIO.output(self.led_pin_g, GPIO.LOW)
            GPIO.output(self.led_pin_b, GPIO.LOW)
            GPIO.output(self.buzzer_pin, GPIO.LOW)
            
            self.get_logger().info("GPIO setup complet")
        except Exception as e:
            self.get_logger().warn(f"GPIO setup eșuat: {e}")
            self.get_logger().info("Rulăm în mod simulare")
    
    def test_sensors(self):
        """Testează toți senzorii și publică rezultatele"""
        try:
            # Testează senzorul Hall
            if not SIMULATION_MODE:
                hall_status = GPIO.input(self.hall_pin) == GPIO.LOW
            else:
                # Simulare: alternează între True și False
                hall_status = (time.time() % a) < 1.0  # alternează la fiecare 2 secunde
                
            # Publică starea senzorului Hall
            hall_msg = Bool()
            hall_msg.data = hall_status
            self.hall_pub.publish(hall_msg)
            
            # Testează senzorul de vibrații
            if not SIMULATION_MODE:
                vibration_status = GPIO.input(self.vibration_pin) == GPIO.LOW
            else:
                # Simulare: detecție mai rară
                vibration_status = (time.time() % 10) < 0.5  # activ 0.5s la fiecare 10s
                
            # Publică starea senzorului de vibrații
            vibration_msg = Bool()
            vibration_msg.data = vibration_status
            self.vibration_pub.publish(vibration_msg)
            
            # Simulează senzorul de alcool (ar trebui să folosească un ADC în realitate)
            if not SIMULATION_MODE:
                # În realitate, ar trebui să citim valoarea de la ADC
                alcohol_value = 300  # Valoare simulată
            else:
                # Simulare: valoare oscilantă
                import math
                alcohol_value = 300 + 200 * math.sin(time.time() / 5)
                
            # Publică valoarea senzorului de alcool
            alcohol_msg = Float32()
            alcohol_msg.data = alcohol_value
            self.alcohol_pub.publish(alcohol_msg)
            
            # Publică starea generală
            status_msg = String()
            status_msg.data = (
                f"Hall: {'ACTIV' if hall_status else 'Inactiv'} | "
                f"Vibrații: {'ACTIV' if vibration_status else 'Inactiv'} | "
                f"Alcool: {alcohol_value:.1f}"
            )
            self.status_pub.publish(status_msg)
            self.get_logger().info(status_msg.data)
            
        except Exception as e:
            self.get_logger().error(f"Eroare la testarea senzorilor: {e}")
    
    def test_led_buzzer(self):
        """Testează LED-urile și buzzer-ul într-o secvență"""
        if SIMULATION_MODE:
            self.get_logger().info(f"TEST LED/BUZZER (simulare): Stare {self.led_test_state}")
            self.led_test_state = (self.led_test_state + 1) % 5
            return
            
        try:
            # Reset toate LED-urile
            GPIO.output(self.led_pin_r, GPIO.LOW)
            GPIO.output(self.led_pin_g, GPIO.LOW)
            GPIO.output(self.led_pin_b, GPIO.LOW)
            GPIO.output(self.buzzer_pin, GPIO.LOW)
            
            if self.led_test_state == 0:
                # Roșu + buzzer scurt
                GPIO.output(self.led_pin_r, GPIO.HIGH)
                GPIO.output(self.buzzer_pin, GPIO.HIGH)
                self.get_logger().info("TEST: LED ROȘU + BUZZER")
                # Oprim buzzer-ul după 0.2s
                timer = threading.Timer(0.2, lambda: GPIO.output(self.buzzer_pin, GPIO.LOW))
                timer.start()
            elif self.led_test_state == 1:
                # Verde
                GPIO.output(self.led_pin_g, GPIO.HIGH)
                self.get_logger().info("TEST: LED VERDE")
            elif self.led_test_state == 2:
                # Albastru
                GPIO.output(self.led_pin_b, GPIO.HIGH)
                self.get_logger().info("TEST: LED ALBASTRU")
            elif self.led_test_state == 3:
                # Toate LED-urile (alb)
                GPIO.output(self.led_pin_r, GPIO.HIGH)
                GPIO.output(self.led_pin_g, GPIO.HIGH)
                GPIO.output(self.led_pin_b, GPIO.HIGH)
                self.get_logger().info("TEST: TOATE LED-URILE (ALB)")
            
            # Incrementăm starea
            self.led_test_state = (self.led_test_state + 1) % 5
            
        except Exception as e:
            self.get_logger().error(f"Eroare la testarea LED/BUZZER: {e}")
    
    def __del__(self):
        """Curăță la închidere"""
        if not SIMULATION_MODE:
            try:
                GPIO.cleanup()
            except:
                pass

def main(args=None):
    rclpy.init(args=args)
    node = SensorTest()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()
