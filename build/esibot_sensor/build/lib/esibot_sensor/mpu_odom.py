import math

import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Imu
from nav_msgs.msg import Odometry
from geometry_msgs.msg import TransformStamped
import tf2_ros


class MpuOdomNode(Node):
    def __init__(self):
        super().__init__("mpu_odom_node")

        self.declare_parameter("imu_topic", "/esibot/imu")
        self.declare_parameter("odom_topic", "/imu/odom")
        self.declare_parameter("frame_id", "odom")
        self.declare_parameter("child_frame_id", "base_footprint")
        self.declare_parameter("publish_tf", False)
        self.declare_parameter("linear_speed_mps", 0.1)
        self.declare_parameter("min_gyro_z", 0.01)

        self.imu_topic = str(self.get_parameter("imu_topic").value)
        self.odom_topic = str(self.get_parameter("odom_topic").value)
        self.frame_id = str(self.get_parameter("frame_id").value)
        self.child_frame_id = str(self.get_parameter("child_frame_id").value)
        self.publish_tf = bool(self.get_parameter("publish_tf").value)
        self.linear_speed_mps = float(self.get_parameter("linear_speed_mps").value)
        self.min_gyro_z = float(self.get_parameter("min_gyro_z").value)

        self.subscription = self.create_subscription(
            Imu, self.imu_topic, self.imu_callback, 10
        )
        self.odom_pub = self.create_publisher(Odometry, self.odom_topic, 10)
        self.tf_broadcaster = tf2_ros.TransformBroadcaster(self)

        self.yaw = 0.0
        self.x = 0.0
        self.y = 0.0
        self.last_time = self.get_clock().now()

        self.get_logger().info(
            "MPU odom initialized. Subscribing to "
            f"{self.imu_topic}, publishing {self.odom_topic}"
        )

    def imu_callback(self, msg):
        current_time = self.get_clock().now()
        dt = (current_time - self.last_time).nanoseconds / 1e9
        if dt <= 0.0:
            return

        gz = msg.angular_velocity.z
        if abs(gz) > self.min_gyro_z:
            self.yaw += gz * dt

        # Estimate X/Y position with a constant forward speed.
        vx = self.linear_speed_mps
        self.x += vx * math.cos(self.yaw) * dt
        self.y += vx * math.sin(self.yaw) * dt

        qz = math.sin(self.yaw / 2.0)
        qw = math.cos(self.yaw / 2.0)

        odom = Odometry()
        odom.header.stamp = current_time.to_msg()
        odom.header.frame_id = self.frame_id
        odom.child_frame_id = self.child_frame_id
        odom.pose.pose.position.x = self.x
        odom.pose.pose.position.y = self.y
        odom.pose.pose.orientation.z = qz
        odom.pose.pose.orientation.w = qw
        odom.twist.twist.linear.x = vx
        odom.twist.twist.angular.z = gz
        self.odom_pub.publish(odom)

        if self.publish_tf:
            t = TransformStamped()
            t.header.stamp = current_time.to_msg()
            t.header.frame_id = self.frame_id
            t.child_frame_id = self.child_frame_id
            t.transform.translation.x = self.x
            t.transform.translation.y = self.y
            t.transform.translation.z = 0.0
            t.transform.rotation.z = qz
            t.transform.rotation.w = qw
            self.tf_broadcaster.sendTransform(t)

        self.last_time = current_time
        self.get_logger().debug(
            f"Odom: x={self.x:.2f} y={self.y:.2f} yaw={math.degrees(self.yaw):.1f} deg"
        )


def main(args=None):
    rclpy.init(args=args)
    node = MpuOdomNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    node.destroy_node()
    rclpy.shutdown()
