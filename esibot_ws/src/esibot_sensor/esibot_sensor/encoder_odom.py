#!/usr/bin/env python3
import math

import rclpy
from rclpy.node import Node
from std_msgs.msg import Int64
from nav_msgs.msg import Odometry
from geometry_msgs.msg import Quaternion, TransformStamped
import tf2_ros


class EncoderOdom(Node):
    def __init__(self):
        super().__init__("encoder_odom")

        # Parameters
        self.declare_parameter("left_topic", "esibot/encoders/left")
        self.declare_parameter("right_topic", "esibot/encoders/right")
        self.declare_parameter("odom_topic", "/wheel/odom")
        self.declare_parameter("ticks_per_rev", 20.0)
        self.declare_parameter("wheel_radius", 0.033)
        self.declare_parameter("wheel_separation", 0.17)
        self.declare_parameter("publish_rate_hz", 20.0)
        self.declare_parameter("frame_id", "odom")
        self.declare_parameter("child_frame_id", "base_footprint")
        self.declare_parameter("publish_tf", False)
        self.declare_parameter("invert_left", False)
        self.declare_parameter("invert_right", False)

        self.left_topic = str(self.get_parameter("left_topic").value)
        self.right_topic = str(self.get_parameter("right_topic").value)
        self.odom_topic = str(self.get_parameter("odom_topic").value)
        self.ticks_per_rev = float(self.get_parameter("ticks_per_rev").value)
        self.wheel_radius = float(self.get_parameter("wheel_radius").value)
        self.wheel_separation = float(self.get_parameter("wheel_separation").value)
        self.publish_rate_hz = max(
            1.0, float(self.get_parameter("publish_rate_hz").value)
        )
        self.frame_id = str(self.get_parameter("frame_id").value)
        self.child_frame_id = str(self.get_parameter("child_frame_id").value)
        self.publish_tf = bool(self.get_parameter("publish_tf").value)
        self.invert_left = bool(self.get_parameter("invert_left").value)
        self.invert_right = bool(self.get_parameter("invert_right").value)

        self.left_count = None
        self.right_count = None
        self.last_left_count = None
        self.last_right_count = None

        self.x = 0.0
        self.y = 0.0
        self.yaw = 0.0
        self.last_time = self.get_clock().now()

        self.left_sub = self.create_subscription(
            Int64, self.left_topic, self.left_callback, 10
        )
        self.right_sub = self.create_subscription(
            Int64, self.right_topic, self.right_callback, 10
        )

        self.odom_pub = self.create_publisher(Odometry, self.odom_topic, 10)
        self.tf_broadcaster = tf2_ros.TransformBroadcaster(self)

        self.create_timer(1.0 / self.publish_rate_hz, self.publish_odom)
        self.get_logger().info(
            "Encoder odom initialized. Subscribing to "
            f"{self.left_topic} and {self.right_topic}, publishing {self.odom_topic}"
        )

    def left_callback(self, msg: Int64):
        self.left_count = int(msg.data)

    def right_callback(self, msg: Int64):
        self.right_count = int(msg.data)

    def publish_odom(self):
        if self.left_count is None or self.right_count is None:
            return

        if (
            self.ticks_per_rev <= 0.0
            or self.wheel_radius <= 0.0
            or self.wheel_separation <= 0.0
        ):
            self.get_logger().error(
                "Invalid encoder odom parameters; check ticks_per_rev and wheel geometry."
            )
            return

        now = self.get_clock().now()
        dt = (now - self.last_time).nanoseconds / 1e9
        if dt <= 0.0:
            return

        if self.last_left_count is None or self.last_right_count is None:
            self.last_left_count = self.left_count
            self.last_right_count = self.right_count
            self.last_time = now
            return

        delta_left_ticks = self.left_count - self.last_left_count
        delta_right_ticks = self.right_count - self.last_right_count

        if self.invert_left:
            delta_left_ticks *= -1
        if self.invert_right:
            delta_right_ticks *= -1

        meters_per_tick = (2.0 * math.pi * self.wheel_radius) / self.ticks_per_rev
        delta_left = delta_left_ticks * meters_per_tick
        delta_right = delta_right_ticks * meters_per_tick

        ds = (delta_left + delta_right) / 2.0
        dtheta = (delta_right - delta_left) / self.wheel_separation

        self.x += ds * math.cos(self.yaw + dtheta / 2.0)
        self.y += ds * math.sin(self.yaw + dtheta / 2.0)
        self.yaw += dtheta

        vx = ds / dt
        wz = dtheta / dt

        qz = math.sin(self.yaw / 2.0)
        qw = math.cos(self.yaw / 2.0)

        odom = Odometry()
        odom.header.stamp = now.to_msg()
        odom.header.frame_id = self.frame_id
        odom.child_frame_id = self.child_frame_id
        odom.pose.pose.position.x = self.x
        odom.pose.pose.position.y = self.y
        odom.pose.pose.orientation = Quaternion(z=qz, w=qw)
        odom.twist.twist.linear.x = vx
        odom.twist.twist.angular.z = wz
        self.odom_pub.publish(odom)

        if self.publish_tf:
            t = TransformStamped()
            t.header.stamp = now.to_msg()
            t.header.frame_id = self.frame_id
            t.child_frame_id = self.child_frame_id
            t.transform.translation.x = self.x
            t.transform.translation.y = self.y
            t.transform.rotation.z = qz
            t.transform.rotation.w = qw
            self.tf_broadcaster.sendTransform(t)

        self.last_left_count = self.left_count
        self.last_right_count = self.right_count
        self.last_time = now


def main(args=None):
    rclpy.init(args=args)
    node = EncoderOdom()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    node.destroy_node()
    rclpy.shutdown()


if __name__ == "__main__":
    main()
