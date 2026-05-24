#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from std_msgs.msg import Float32MultiArray

import RPi.GPIO as GPIO
import pigpio
import time

class RadarNode(Node):
    def __init__(self):
        super().__init__('radar_node')

        # -----------------------
        # PARAMÈTRES & ROS 2
        # -----------------------
        self.declare_parameter('topic_name', '/radar/scan')
        self.declare_parameter('servo_gpio_pin', 18)
        self.declare_parameter('sensor_trigger_pins', [16, 20, 26, 24])
        self.declare_parameter('servo_scan_angles_deg', [0.0, 30.0, 60.0])
        self.declare_parameter('servo_settle_time_sec', 0.50)

        topic_name = self.get_parameter('topic_name').value
        self.SERVO_PIN = self.get_parameter('servo_gpio_pin').value
        self.SENSORS_V2 = self.get_parameter('sensor_trigger_pins').value
        self.settle_time = self.get_parameter('servo_settle_time_sec').value

        # Séquence de va-et-vient : [0, 30, 60, 30]
        angles_yaml = self.get_parameter('servo_scan_angles_deg').value
        angles_int = [int(round(a)) for a in angles_yaml]
        self.sequence = angles_int + list(reversed(angles_int[1:-1]))

        self.max_angle = max(self.sequence)  # 60
        self.min_angle = min(self.sequence)  # 0

        self.accumulated_data = {}
        self.seq_index = 0
        self.is_returning = False
        self.was_returning = False

        # Création du Publisher
        self.publisher_ = self.create_publisher(Float32MultiArray, topic_name, 10)

        # -----------------------
        # HARDWARE SETUP
        # -----------------------
        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)

        self.pi = pigpio.pi()
        if not self.pi.connected:
            self.get_logger().error("❌ Impossible de se connecter à pigpio daemon ! Lancez 'sudo pigpiod'")
            # On laisse ROS 2 crasher proprement si le matériel n'est pas là
            raise RuntimeError("pigpiod non démarré")

        for pin in self.SENSORS_V2:
            GPIO.setup(pin, GPIO.OUT)
            GPIO.output(pin, False)

        self.get_logger().info(f"🚀 Radar Node initialisé. Topic: {topic_name}")

        # On utilise un TIMER ROS 2 standard (Appelé toutes les 0.1 secondes)
        self.timer = self.create_timer(0.1, self.main_loop)

    def set_angle(self, angle):
        pulsewidth = 500 + (angle * 2000 / 180)
        self.pi.set_servo_pulsewidth(self.SERVO_PIN, pulsewidth)
        time.sleep(self.settle_time)

    def read_v2(self, pin):
        try:
            GPIO.setup(pin, GPIO.OUT)
            GPIO.output(pin, True)
            time.sleep(0.00001)
            GPIO.output(pin, False)

            GPIO.setup(pin, GPIO.IN)
            timeout = time.time()
            pulse_start = time.time()
            pulse_end = time.time()

            while GPIO.input(pin) == 0:
                pulse_start = time.time()
                if pulse_start - timeout > 0.03:
                    return -1.0

            while GPIO.input(pin) == 1:
                pulse_end = time.time()
                if pulse_end - pulse_start > 0.03:
                    return -1.0

            duration = pulse_end - pulse_start
            distance = round(duration * 34300 / 2, 2)
            return distance if distance <= 400 else -1.0
        except Exception as e:
            return -1.0

    def main_loop(self):
        # Pas de boucle 'while' infinie ici ! C'est le timer ROS 2 qui gère les répétitions.
        angle = int(self.sequence[self.seq_index])

        if angle == self.max_angle:
            self.is_returning = True
        elif angle == self.min_angle:
            self.was_returning = self.is_returning
            self.is_returning = False

        # Bouger le servo
        self.set_angle(angle)

        # Capture
        self.get_logger().info(f"📸 Capture à {angle}°...")
        step_distances = []
        for pin in self.SENSORS_V2:
            d = self.read_v2(pin)
            step_distances.append(d)
            time.sleep(0.02)

        self.accumulated_data[angle] = step_distances

        # Condition d'envoi du paquet global de 12 valeurs
        if angle == self.max_angle or (angle == self.min_angle and self.was_returning):
            if 0 in self.accumulated_data and 30 in self.accumulated_data and 60 in self.accumulated_data:
                total_packet = (
                    self.accumulated_data[0] +
                    self.accumulated_data[30] +
                    self.accumulated_data[60]
                )
                msg = Float32MultiArray()
                msg.data = total_packet
                self.publisher_.publish(msg)
                self.get_logger().info(f"🌐 PAQUET TRANSMIS : {total_packet}")

            if angle == self.min_angle:
                self.was_returning = False

        # Passer à l'index suivant
        self.seq_index = (self.seq_index + 1) % len(self.sequence)

    def destroy_node(self):
        self.get_logger().info("Nettoyage...")
        if hasattr(self, 'pi') and self.pi.connected:
            self.pi.set_servo_pulsewidth(self.SERVO_PIN, 0)
            self.pi.stop()
        GPIO.cleanup()
        super().destroy_node()

def main(args=None):
    rclpy.init(args=args)
    node = RadarNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
