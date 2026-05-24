import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Imu
from nav_msgs.msg import Odometry
from geometry_msgs.msg import TransformStamped
import tf2_ros
import math

class MpuOdomNode(Node):
    def __init__(self):
        super().__init__('mpu_odom_node')

        self.subscription = self.create_subscription(Imu, 'esibot/imu', self.imu_callback, 10)
        self.odom_pub = self.create_publisher(Odometry, '/odom', 10)
        self.tf_broadcaster = tf2_ros.TransformBroadcaster(self)

        self.yaw = 0.0
        self.x = 0.0
        self.y = 0.0
        self.vx = 0.1      # vitesse estimée fixe (0.1 m/s) — à remplacer par encodeurs plus tard
        self.last_time = self.get_clock().now()

    def imu_callback(self, msg):
        current_time = self.get_clock().now()
        dt = (current_time - self.last_time).nanoseconds / 1e9

        gz = msg.angular_velocity.z
        if abs(gz) > 0.01:
            self.yaw += gz * dt

        # Estimation position X/Y avec vitesse constante
        self.x += self.vx * math.cos(self.yaw) * dt
        self.y += self.vx * math.sin(self.yaw) * dt

        qz = math.sin(self.yaw / 2.0)
        qw = math.cos(self.yaw / 2.0)

        # Publication Odometry
        odom = Odometry()
        odom.header.stamp = current_time.to_msg()
        odom.header.frame_id = "odom"
        odom.child_frame_id = "base_footprint"
        odom.pose.pose.position.x = self.x
        odom.pose.pose.position.y = self.y
        odom.pose.pose.orientation.z = qz
        odom.pose.pose.orientation.w = qw
        self.odom_pub.publish(odom)

        # Publication TF odom -> base_footprint
        t = TransformStamped()
        t.header.stamp = current_time.to_msg()
        t.header.frame_id = "odom"
        t.child_frame_id = "base_footprint"
        t.transform.translation.x = self.x
        t.transform.translation.y = self.y
        t.transform.translation.z = 0.0
        t.transform.rotation.z = qz
        t.transform.rotation.w = qw
        self.tf_broadcaster.sendTransform(t)

        self.last_time = current_time
        self.get_logger().info(f"Odom: x={self.x:.2f} y={self.y:.2f} yaw={math.degrees(self.yaw):.1f}°")

def main(args=None):
    rclpy.init(args=args)
    node = MpuOdomNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    node.destroy_node()
    rclpy.shutdown()
