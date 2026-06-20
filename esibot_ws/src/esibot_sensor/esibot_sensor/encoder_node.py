#!/usr/bin/env python3
"""
encoder_node — Raw wheel encoder tick counter.

Uses GPIO interrupts to count edges from left and right quadrature
encoders and publishes cumulative tick counts as std_msgs/Int64.

Published topics:
    /encoders/left   (std_msgs/Int64)
    /encoders/right  (std_msgs/Int64)
"""

import rclpy
from rclpy.node import Node
from std_msgs.msg import Int64
import RPi.GPIO as GPIO


class EncoderNode(Node):
    def __init__(self):
        super().__init__("encoder_node")

        # --------------- parameters ---------------
        self.declare_parameter("left_pin", 5)
        self.declare_parameter("right_pin", 6)
        self.declare_parameter("left_topic", "/encoders/left")
        self.declare_parameter("right_topic", "/encoders/right")
        self.declare_parameter("publish_rate_hz", 20.0)
        self.declare_parameter("pull_up", True)
        self.declare_parameter("queue_size", 10)
        self.declare_parameter("edge_type", "both")
        self.declare_parameter("bouncetime_ms", 0.0)

        self.left_pin = int(self.get_parameter("left_pin").value)
        self.right_pin = int(self.get_parameter("right_pin").value)
        left_topic = str(self.get_parameter("left_topic").value)
        right_topic = str(self.get_parameter("right_topic").value)
        publish_rate_hz = max(
            1.0, float(self.get_parameter("publish_rate_hz").value)
        )
        pull_up = bool(self.get_parameter("pull_up").value)
        queue_size = max(1, int(self.get_parameter("queue_size").value))
        edge_type = str(self.get_parameter("edge_type").value).strip().lower()
        bouncetime_ms = max(
            0.0, float(self.get_parameter("bouncetime_ms").value)
        )

        # --------------- GPIO init ---------------
        GPIO.setmode(GPIO.BCM)
        pull_mode = GPIO.PUD_UP if pull_up else GPIO.PUD_DOWN
        GPIO.setup(self.left_pin, GPIO.IN, pull_up_down=pull_mode)
        GPIO.setup(self.right_pin, GPIO.IN, pull_up_down=pull_mode)

        # Counters
        self.left_count = 0
        self.right_count = 0

        # Edge detection mode
        if edge_type == "rising":
            edge_mode = GPIO.RISING
        elif edge_type == "falling":
            edge_mode = GPIO.FALLING
        else:
            edge_mode = GPIO.BOTH

        bouncetime = (
            int(round(bouncetime_ms)) if bouncetime_ms > 0.0 else None
        )
        if bouncetime is None:
            GPIO.add_event_detect(
                self.left_pin, edge_mode, callback=self._left_cb
            )
            GPIO.add_event_detect(
                self.right_pin, edge_mode, callback=self._right_cb
            )
        else:
            GPIO.add_event_detect(
                self.left_pin,
                edge_mode,
                callback=self._left_cb,
                bouncetime=bouncetime,
            )
            GPIO.add_event_detect(
                self.right_pin,
                edge_mode,
                callback=self._right_cb,
                bouncetime=bouncetime,
            )

        # --------------- ROS interfaces ---------------
        self.left_pub = self.create_publisher(Int64, left_topic, queue_size)
        self.right_pub = self.create_publisher(Int64, right_topic, queue_size)

        self.create_timer(1.0 / publish_rate_hz, self._publish_counts)
        self.get_logger().info(
            f"Encoder node: GPIO {self.left_pin}/{self.right_pin} "
            f"→ {left_topic}, {right_topic} at {publish_rate_hz} Hz"
        )

    def _left_cb(self, channel):
        self.left_count += 1

    def _right_cb(self, channel):
        self.right_count += 1

    def _publish_counts(self):
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
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
