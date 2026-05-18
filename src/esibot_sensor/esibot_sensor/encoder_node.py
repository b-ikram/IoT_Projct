import rclpy
from rclpy.node import Node
from std_msgs.msg import Int64
import RPi.GPIO as GPIO

class EncoderNode(Node):
    def __init__(self):
        super().__init__('encoder_node')
        
        # Configuration des pins (BCM)
        self.left_pin = 5
        self.right_pin = 6
        
        # Initialisation du GPIO
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.left_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        GPIO.setup(self.right_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        
        # Compteurs de trous
        self.left_count = 0
        self.right_count = 0
        
        # Détection des changements d'état (les trous qui passent)
        GPIO.add_event_detect(self.left_pin, GPIO.BOTH, callback=self.left_callback)
        GPIO.add_event_detect(self.right_pin, GPIO.BOTH, callback=self.right_callback)
        
        # Publishers pour envoyer les données au reste du robot
        self.left_pub = self.create_publisher(Int64, 'esibot/encoders/left', 10)
        self.right_pub = self.create_publisher(Int64, 'esibot/encoders/right', 10)
        
        # Timer pour publier à 20Hz
        self.create_timer(0.05, self.publish_counts)
        self.get_logger().info("Node Encodeurs démarré sur GPIO 5 et 6")

    def left_callback(self, channel):
        self.left_count += 1

    def right_callback(self, channel):
        self.right_count += 1

    def publish_counts(self):
        msg_l = Int64()
        msg_l.data = self.left_count
        msg_r = Int64()
        msg_r.data = self.right_count
        
        self.left_pub.publish(msg_l)
        self.right_pub.publish(msg_r)

def main(args=None):
    rclpy.init(args=args)
    node = EncoderNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        GPIO.cleanup()
        rclpy.shutdown()
