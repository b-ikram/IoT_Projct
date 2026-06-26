#!/usr/bin/env python3
"""
diff_drive_odom_node — Differential-drive wheel odometry.

Subscribes to raw encoder tick counts (Int64) for left and right wheels,
computes forward velocity and yaw rate using standard differential-drive
kinematics, and publishes nav_msgs/Odometry with proper covariance.

This node does NOT publish TF — the EKF owns the odom→base_link transform.

Published topics:
    /wheel/odometry  (nav_msgs/Odometry)

Subscribed topics:
    /encoders/left   (std_msgs/Int64)
    /encoders/right  (std_msgs/Int64)
"""

import math

import rclpy
from rclpy.node import Node
from std_msgs.msg import Int64
from nav_msgs.msg import Odometry
from geometry_msgs.msg import Quaternion


class DiffDriveOdomNode(Node):
    def __init__(self):
        super().__init__("diff_drive_odom_node")

        # --------------- parameters ---------------
        self.declare_parameter("left_encoder_topic", "/encoders/left")
        self.declare_parameter("right_encoder_topic", "/encoders/right")
        self.declare_parameter("odom_topic", "/wheel/odometry")
        self.declare_parameter("ticks_per_rev", 20.0)
        self.declare_parameter("wheel_radius", 0.033)
        self.declare_parameter("wheel_separation", 0.17)
        self.declare_parameter("publish_rate_hz", 20.0)
        self.declare_parameter("frame_id", "odom")
        self.declare_parameter("child_frame_id", "base_link")
        self.declare_parameter("invert_left", False)
        self.declare_parameter("invert_right", False)

        # Covariance diagonal values for the Odometry message.
        # Pose covariance (m², rad²) — grows with drift, these are base values.
        self.declare_parameter("pose_cov_x", 0.01)
        self.declare_parameter("pose_cov_y", 0.01)
        self.declare_parameter("pose_cov_yaw", 0.03)
        # Twist covariance ((m/s)², (rad/s)²)
        self.declare_parameter("twist_cov_vx", 0.01)
        self.declare_parameter("twist_cov_vyaw", 0.05)

        left_topic = str(self.get_parameter("left_encoder_topic").value)
        right_topic = str(self.get_parameter("right_encoder_topic").value)
        odom_topic = str(self.get_parameter("odom_topic").value)
        self.ticks_per_rev = float(self.get_parameter("ticks_per_rev").value)
        self.wheel_radius = float(self.get_parameter("wheel_radius").value)
        self.wheel_separation = float(
            self.get_parameter("wheel_separation").value
        )
        publish_rate = float(self.get_parameter("publish_rate_hz").value)
        self.frame_id = str(self.get_parameter("frame_id").value)
        self.child_frame_id = str(self.get_parameter("child_frame_id").value)
        self.invert_left = bool(self.get_parameter("invert_left").value)
        self.invert_right = bool(self.get_parameter("invert_right").value)

        pose_cov_x = float(self.get_parameter("pose_cov_x").value)
        pose_cov_y = float(self.get_parameter("pose_cov_y").value)
        pose_cov_yaw = float(self.get_parameter("pose_cov_yaw").value)
        twist_cov_vx = float(self.get_parameter("twist_cov_vx").value)
        twist_cov_vyaw = float(self.get_parameter("twist_cov_vyaw").value)

        # --------------- pre-build static covariance arrays (6×6 = 36) ------
        # Row-major.  Only diag elements for x, y, yaw are set.
        self.pose_covariance = [0.0] * 36
        self.pose_covariance[0] = pose_cov_x      # x
        self.pose_covariance[7] = pose_cov_y      # y
        self.pose_covariance[35] = pose_cov_yaw   # yaw

        self.twist_covariance = [0.0] * 36
        self.twist_covariance[0] = twist_cov_vx    # vx
        self.twist_covariance[35] = twist_cov_vyaw  # vyaw

        # --------------- state ---------------
        self.left_count = None
        self.right_count = None
        self.last_left_count = None
        self.last_right_count = None

        self.x = 0.0
        self.y = 0.0
        self.yaw = 0.0
        self.last_time = self.get_clock().now()

        # --------------- ROS interfaces ---------------
        self.left_sub = self.create_subscription(
            Int64, left_topic, self._left_cb, 10
        )
        self.right_sub = self.create_subscription(
            Int64, right_topic, self._right_cb, 10
        )
        self.odom_pub = self.create_publisher(Odometry, odom_topic, 10)

        self.create_timer(1.0 / publish_rate, self._publish_odom)
        self.get_logger().info(
            f"Diff-drive odom: {left_topic} + {right_topic} → {odom_topic}"
        )

    # ---- encoder callbacks ----
    def _left_cb(self, msg: Int64):
        self.left_count = int(msg.data)

    def _right_cb(self, msg: Int64):
        self.right_count = int(msg.data)

    # ---- odometry computation ----
    def _publish_odom(self):
        if self.left_count is None or self.right_count is None:
            return

        if (
            self.ticks_per_rev <= 0.0
            or self.wheel_radius <= 0.0
            or self.wheel_separation <= 0.0
        ):
            self.get_logger().error(
                "Invalid parameters: ticks_per_rev, wheel_radius, "
                "and wheel_separation must all be positive."
            )
            return

        now = self.get_clock().now()
        dt = (now - self.last_time).nanoseconds / 1e9
        if dt <= 0.0:
            return

        # First iteration: latch counts and return.
        if self.last_left_count is None or self.last_right_count is None:
            self.last_left_count = self.left_count
            self.last_right_count = self.right_count
            self.last_time = now
            return

        # Compute tick deltas.
        delta_left = self.left_count - self.last_left_count
        delta_right = self.right_count - self.last_right_count

        if self.invert_left:
            delta_left *= -1
        if self.invert_right:
            delta_right *= -1

        # Ticks → metres.
        meters_per_tick = (
            2.0 * math.pi * self.wheel_radius
        ) / self.ticks_per_rev
        dl = delta_left * meters_per_tick
        dr = delta_right * meters_per_tick

        # Differential-drive kinematics.
        ds = (dl + dr) / 2.0
        dtheta = (dr - dl) / self.wheel_separation

        self.x += ds * math.cos(self.yaw + dtheta / 2.0)
        self.y += ds * math.sin(self.yaw + dtheta / 2.0)
        self.yaw += dtheta

        vx = ds / dt
        wz = dtheta / dt

        # Quaternion from yaw.
        qz = math.sin(self.yaw / 2.0)
        qw = math.cos(self.yaw / 2.0)

        # Build Odometry message.
        odom = Odometry()
        odom.header.stamp = now.to_msg()
        odom.header.frame_id = self.frame_id
        odom.child_frame_id = self.child_frame_id

        odom.pose.pose.position.x = self.x
        odom.pose.pose.position.y = self.y
        odom.pose.pose.orientation = Quaternion(
            x=0.0, y=0.0, z=qz, w=qw
        )
        odom.pose.covariance = self.pose_covariance

        odom.twist.twist.linear.x = vx
        odom.twist.twist.angular.z = wz
        odom.twist.covariance = self.twist_covariance

        self.odom_pub.publish(odom)

        # Latch for next cycle.
        self.last_left_count = self.left_count
        self.last_right_count = self.right_count
        self.last_time = now


def main(args=None):
    rclpy.init(args=args)
    node = DiffDriveOdomNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
