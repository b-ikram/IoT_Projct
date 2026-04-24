#!/usr/bin/env python3

import math
import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist, Quaternion, TransformStamped
from nav_msgs.msg import Odometry
from sensor_msgs.msg import BatteryState
import tf2_ros

# Import your custom utility classes
from .odometry_utils import OdometryComputer
from .serial_interface import SerialInterface

class EsibotDriver(Node):
    def __init__(self):
        super().__init__('esibot_driver')

        # 1. Parameters (Hardware specific)
        self.declare_parameter('serial_port', '/dev/ttyUSB0')
        self.declare_parameter('wheel_radius', 0.033)        # meters
        self.declare_parameter('wheel_separation', 0.17)    # meters
        self.declare_parameter('ticks_per_rev', 2000)       # resolution
        
        # 2. Initialize Hardware & Utils
        port = self.get_parameter('serial_port').value
        self.serial = SerialInterface(port=port)
        
        self.odom_computer = OdometryComputer(
            wheel_radius=self.get_parameter('wheel_radius').value,
            wheel_separation=self.get_parameter('wheel_separation').value,
            ticks_per_rev=self.get_parameter('ticks_per_rev').value
        )

        # 3. TF Broadcaster (Required for SLAM)
        self.tf_broadcaster = tf2_ros.TransformBroadcaster(self)

        # 4. Publishers & Subscribers
        self.odom_pub = self.create_publisher(Odometry, '/odom', 10)
        self.battery_pub = self.create_publisher(BatteryState, '/battery_state', 10)
        
        self.cmd_sub = self.create_subscription(
            Twist, '/cmd_vel', self.cmd_vel_callback, 10
        )

        # 5. Main Control Loop (Reads serial and publishes Odom)
        self.timer = self.create_timer(0.05, self.update_robot_state) # 20Hz

        self.get_logger().info('Esibot Real Driver Started')

    def cmd_vel_callback(self, msg: Twist):
        """Convert Twist (v, w) to wheel speeds for the ESP32"""
        v = msg.linear.x
        w = msg.angular.z
        
        L = self.odom_computer.L
        
        # Differential drive kinematics
        left_speed = v - (w * L / 2.0)
        right_speed = v + (w * L / 2.0)
        
        # Send to ESP32 via Serial
        self.serial.send_command(left_speed, right_speed)

    def update_robot_state(self):
        """Read serial data and update Odometry"""
        line = self.serial.read_line()
        if not line:
            return

        try:
            # Expecting format from ESP32: "ticks_l,ticks_r,voltage"
            parts = line.split(',')
            left_ticks = int(parts[0])
            right_ticks = int(parts[1])
            voltage = float(parts[2])

            # Update Odometry logic
            x, y, th = self.odom_computer.update(left_ticks, right_ticks)
            
            self.publish_odom(x, y, th)
            self.publish_battery(voltage)
            
        except (ValueError, IndexError):
            self.get_logger().warn(f"Malformed serial data: {line}")

    def publish_odom(self, x, y, th):
        now = self.get_clock().now().to_msg()
        q = self.euler_to_quaternion(0, 0, th)

        # 1. Publish Transform (tf)
        t = TransformStamped()
        t.header.stamp = now
        t.header.frame_id = 'odom'
        t.child_frame_id = 'base_footprint'
        t.transform.translation.x = x
        t.transform.translation.y = y
        t.transform.rotation = q
        self.tf_broadcaster.sendTransform(t)

        # 2. Publish Odometry Message
        odom = Odometry()
        odom.header.stamp = now
        odom.header.frame_id = 'odom'
        odom.child_frame_id = 'base_footprint'
        odom.pose.pose.position.x = x
        odom.pose.pose.position.y = y
        odom.pose.pose.orientation = q
        self.odom_pub.publish(odom)

    def publish_battery(self, voltage):
        msg = BatteryState()
        msg.header.stamp = self.get_clock().now().to_msg()
        msg.voltage = voltage
        # Simple estimate: (Current - Min) / (Max - Min)
        msg.percentage = max(0.0, min(1.0, (voltage - 10.0) / 2.6)) 
        self.battery_pub.publish(msg)

    def euler_to_quaternion(self, roll, pitch, yaw):
        qx = math.sin(roll/2) * math.cos(pitch/2) * math.cos(yaw/2) - math.cos(roll/2) * math.sin(pitch/2) * math.sin(yaw/2)
        qy = math.cos(roll/2) * math.sin(pitch/2) * math.cos(yaw/2) + math.sin(roll/2) * math.cos(pitch/2) * math.sin(yaw/2)
        qz = math.cos(roll/2) * math.cos(pitch/2) * math.sin(yaw/2) - math.sin(roll/2) * math.sin(pitch/2) * math.cos(yaw/2)
        qw = math.cos(roll/2) * math.cos(pitch/2) * math.cos(yaw/2) + math.sin(roll/2) * math.sin(pitch/2) * math.sin(yaw/2)
        return Quaternion(x=qx, y=qy, z=qz, w=qw)

def main(args=None):
    rclpy.init(args=args)
    node = EsibotDriver()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.serial.close()
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()