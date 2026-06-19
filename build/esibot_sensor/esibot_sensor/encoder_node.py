import rclpy
from rclpy.node import Node
from std_msgs.msg import Int64
import RPi.GPIO as GPIO


class EncoderNode(Node):
    def __init__(self):
        super().__init__("encoder_node")

        # Parameters
        self.declare_parameter("left_pin", 5)
        self.declare_parameter("right_pin", 6)
        self.declare_parameter("left_topic", "esibot/encoders/left")
        self.declare_parameter("right_topic", "esibot/encoders/right")
        self.declare_parameter("publish_rate_hz", 20.0)
        self.declare_parameter("pull_up", True)
        self.declare_parameter("queue_size", 10)
        self.declare_parameter("edge_type", "both")
        self.declare_parameter("bouncetime_ms", 0.0)

        self.left_pin = int(self.get_parameter("left_pin").value)
        self.right_pin = int(self.get_parameter("right_pin").value)
        self.left_topic = str(self.get_parameter("left_topic").value)
        self.right_topic = str(self.get_parameter("right_topic").value)
        self.publish_rate_hz = max(
            1.0, float(self.get_parameter("publish_rate_hz").value)
        )
        self.pull_up = bool(self.get_parameter("pull_up").value)
        self.queue_size = max(1, int(self.get_parameter("queue_size").value))
        self.edge_type = str(self.get_parameter("edge_type").value).strip().lower()
        self.bouncetime_ms = max(0.0, float(self.get_parameter("bouncetime_ms").value))

        # GPIO init
        GPIO.setmode(GPIO.BCM)
        pull_mode = GPIO.PUD_UP if self.pull_up else GPIO.PUD_DOWN
        GPIO.setup(self.left_pin, GPIO.IN, pull_up_down=pull_mode)
        GPIO.setup(self.right_pin, GPIO.IN, pull_up_down=pull_mode)

        # Counters
        self.left_count = 0
        self.right_count = 0

        # Edge detection
        if self.edge_type == "rising":
            edge_mode = GPIO.RISING
        elif self.edge_type == "falling":
            edge_mode = GPIO.FALLING
        else:
            edge_mode = GPIO.BOTH

        bouncetime = int(round(self.bouncetime_ms)) if self.bouncetime_ms > 0.0 else None
        if bouncetime is None:
            GPIO.add_event_detect(self.left_pin, edge_mode, callback=self.left_callback)
            GPIO.add_event_detect(self.right_pin, edge_mode, callback=self.right_callback)
        else:
            GPIO.add_event_detect(
                self.left_pin, edge_mode, callback=self.left_callback, bouncetime=bouncetime
            )
            GPIO.add_event_detect(
                self.right_pin, edge_mode, callback=self.right_callback, bouncetime=bouncetime
            )

        # Publishers
        self.left_pub = self.create_publisher(Int64, self.left_topic, self.queue_size)
        self.right_pub = self.create_publisher(Int64, self.right_topic, self.queue_size)

        # Timer for publishing counts
        self.create_timer(1.0 / self.publish_rate_hz, self.publish_counts)
        self.get_logger().info(
            f"Encoder node started on GPIO {self.left_pin} and {self.right_pin} at {self.publish_rate_hz} Hz"
        )

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
