#!/usr/bin/env python3

import math
import rclpy
from rclpy.node import Node

from geometry_msgs.msg import Twist
from nav_msgs.msg import Odometry
from sensor_msgs.msg import BatteryState


class EsibotDriver(Node):
    def __init__(self):
        super().__init__('esibot_driver')

        # Parameters
        self.declare_parameter('cmd_in_topic', '/cmd_vel')
        self.declare_parameter('cmd_out_topic', '/gz_cmd_vel')
        self.declare_parameter('odom_in_topic', '/gz_odom')
        self.declare_parameter('odom_out_topic', '/odom')
        self.declare_parameter('battery_topic', '/battery_state')
        self.declare_parameter('battery_voltage', 12.0)
        self.declare_parameter('battery_percentage', 0.85)
        self.declare_parameter('battery_publish_rate', 1.0)

        cmd_in_topic = self.get_parameter('cmd_in_topic').value
        cmd_out_topic = self.get_parameter('cmd_out_topic').value
        odom_in_topic = self.get_parameter('odom_in_topic').value
        odom_out_topic = self.get_parameter('odom_out_topic').value
        battery_topic = self.get_parameter('battery_topic').value
        battery_publish_rate = float(self.get_parameter('battery_publish_rate').value)

        # Subscriptions
        self.cmd_sub = self.create_subscription(
            Twist,
            cmd_in_topic,
            self.cmd_vel_callback,
            10
        )

        self.gz_odom_sub = self.create_subscription(
            Odometry,
            odom_in_topic,
            self.gz_odom_callback,
            10
        )

        # Publishers
        self.gz_cmd_pub = self.create_publisher(Twist, cmd_out_topic, 10)
        self.odom_pub = self.create_publisher(Odometry, odom_out_topic, 10)
        self.battery_pub = self.create_publisher(BatteryState, battery_topic, 10)

        # Timer
        self.battery_timer = self.create_timer(
            1.0 / battery_publish_rate,
            self.publish_battery_state
        )

        self.last_cmd = Twist()

        self.get_logger().info('esibot_driver started')
        self.get_logger().info(f'Subscribing to {cmd_in_topic}')
        self.get_logger().info(f'Forwarding commands to {cmd_out_topic}')
        self.get_logger().info(f'Reading Gazebo odom from {odom_in_topic}')
        self.get_logger().info(f'Publishing ROS odom to {odom_out_topic}')

    def cmd_vel_callback(self, msg: Twist):
        self.last_cmd = msg

        out = Twist()
        out.linear.x = msg.linear.x
        out.linear.y = msg.linear.y
        out.linear.z = msg.linear.z
        out.angular.x = msg.angular.x
        out.angular.y = msg.angular.y
        out.angular.z = msg.angular.z

        self.gz_cmd_pub.publish(out)

    def gz_odom_callback(self, msg: Odometry):
        odom = Odometry()
        odom.header = msg.header
        odom.child_frame_id = msg.child_frame_id
        odom.pose = msg.pose
        odom.twist = msg.twist

        self.odom_pub.publish(odom)

    def publish_battery_state(self):
        msg = BatteryState()
        msg.header.stamp = self.get_clock().now().to_msg()
        msg.voltage = float(self.get_parameter('battery_voltage').value)
        msg.percentage = float(self.get_parameter('battery_percentage').value)
        msg.present = True
        self.battery_pub.publish(msg)


def main(args=None):
    rclpy.init(args=args)
    node = EsibotDriver()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()