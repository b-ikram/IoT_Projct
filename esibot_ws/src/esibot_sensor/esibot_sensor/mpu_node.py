# import math
# import rclpy
# from rclpy.node import Node
# from sensor_msgs.msg import Imu
# from mpu6050 import mpu6050
#
#
# class MpuNode(Node):
#     def __init__(self):
#         super().__init__("mpu_sensor_node")
#
#         self.declare_parameter("imu_topic", "/esibot/imu")
#         self.declare_parameter("frame_id", "imu_link")
#         self.declare_parameter("publish_rate_hz", 20.0)
#         self.declare_parameter("alpha", 0.2)
#         self.declare_parameter("deadzone_deg_s", 0.5)
#         self.declare_parameter("i2c_address", 0x68)
#
#         imu_topic = str(self.get_parameter("imu_topic").value)
#         frame_id = str(self.get_parameter("frame_id").value)
#         publish_rate_hz = float(self.get_parameter("publish_rate_hz").value)
#         alpha = float(self.get_parameter("alpha").value)
#         deadzone = float(self.get_parameter("deadzone_deg_s").value)
#         i2c_address = int(self.get_parameter("i2c_address").value)
#
#         # Initialize sensor (default address 0x68)
#         try:
#             self.sensor = mpu6050(i2c_address)
#             self.get_logger().info("MPU-6050 connected successfully.")
#         except Exception as e:
#             self.get_logger().error(f"MPU-6050 connection error: {e}")
#
#         self.publisher_ = self.create_publisher(Imu, imu_topic, 10)
#
#         # Stabilization settings
#         self.alpha = alpha  # Smoothing factor (0.1 - 0.5)
#         self.deadzone = deadzone  # Ignore rotations below this deg/s
#
#         # Previous values for filtering
#         self.prev_gx = 0.0
#         self.prev_gy = 0.0
#         self.prev_gz = 0.0
#
#         self.frame_id = frame_id
#         self.timer = self.create_timer(1.0 / publish_rate_hz, self.timer_callback)
#
#     def timer_callback(self):
#         msg = Imu()
#         msg.header.stamp = self.get_clock().now().to_msg()
#         msg.header.frame_id = self.frame_id
#
#         try:
#             # 1) Read raw data
#             accel_data = self.sensor.get_accel_data()
#             gyro_data = self.sensor.get_gyro_data()
#
#             # 2) Apply deadzone on Z axis (yaw)
#             raw_gz = gyro_data["z"]
#             if abs(raw_gz) < self.deadzone:
#                 raw_gz = 0.0
#
#             # 3) Low-pass filter
#             filtered_gx = (self.alpha * gyro_data["x"]) + (
#                 1.0 - self.alpha
#             ) * self.prev_gx
#             filtered_gy = (self.alpha * gyro_data["y"]) + (
#                 1.0 - self.alpha
#             ) * self.prev_gy
#             filtered_gz = (self.alpha * raw_gz) + (1.0 - self.alpha) * self.prev_gz
#
#             # Save for next iteration
#             self.prev_gx, self.prev_gy, self.prev_gz = (
#                 filtered_gx,
#                 filtered_gy,
#                 filtered_gz,
#             )
#
#             # 4) Fill IMU message (deg/s -> rad/s)
#             deg_to_rad = math.pi / 180.0
#             msg.angular_velocity.x = filtered_gx * deg_to_rad
#             msg.angular_velocity.y = filtered_gy * deg_to_rad
#             msg.angular_velocity.z = filtered_gz * deg_to_rad
#
#             # Linear acceleration (m/s^2)
#             msg.linear_acceleration.x = accel_data["x"]
#             msg.linear_acceleration.y = accel_data["y"]
#             msg.linear_acceleration.z = accel_data["z"]
#
#             self.publisher_.publish(msg)
#
#         except Exception as e:
#             self.get_logger().warn(f"MPU-6050 read error: {e}")
#
#
# def main(args=None):
#     rclpy.init(args=args)
#     node = MpuNode()
#     try:
#         rclpy.spin(node)
#     except KeyboardInterrupt:
#         pass
#     finally:
#         node.destroy_node()
#         rclpy.shutdown()
#
#
# if __name__ == "__main__":
#     main()
#
# ============================================================
# MOCK REPLACEMENT
# ============================================================
import math

import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Imu


class MpuNode(Node):
    def __init__(self):
        super().__init__("mpu_sensor_node")

        self.declare_parameter("imu_topic", "/esibot/imu")
        self.declare_parameter("frame_id", "imu_link")
        self.declare_parameter("publish_rate_hz", 20.0)
        self.declare_parameter("mock_yaw_rate_deg_s", 5.0)
        self.declare_parameter("mock_yaw_rate_hz", 0.3)
        self.declare_parameter("mock_linear_accel_mps2", 0.1)
        self.declare_parameter("mock_linear_accel_hz", 0.5)

        self.imu_topic = str(self.get_parameter("imu_topic").value)
        self.frame_id = str(self.get_parameter("frame_id").value)
        self.publish_rate_hz = max(
            1.0, float(self.get_parameter("publish_rate_hz").value)
        )
        self.mock_yaw_rate_deg_s = float(
            self.get_parameter("mock_yaw_rate_deg_s").value
        )
        self.mock_yaw_rate_hz = float(self.get_parameter("mock_yaw_rate_hz").value)
        self.mock_linear_accel_mps2 = float(
            self.get_parameter("mock_linear_accel_mps2").value
        )
        self.mock_linear_accel_hz = float(
            self.get_parameter("mock_linear_accel_hz").value
        )

        self.pub = self.create_publisher(Imu, self.imu_topic, 10)
        self.publish_period = 1.0 / self.publish_rate_hz
        self.timer = self.create_timer(self.publish_period, self.publish)
        self.t = 0.0
        self.get_logger().warn("*** MOCK MODE - real MPU disabled ***")

    def publish(self):
        deg_to_rad = math.pi / 180.0
        msg = Imu()
        msg.header.stamp = self.get_clock().now().to_msg()
        msg.header.frame_id = self.frame_id
        msg.angular_velocity.x = 0.0
        msg.angular_velocity.y = 0.0
        msg.angular_velocity.z = (
            self.mock_yaw_rate_deg_s
            * deg_to_rad
            * math.sin(self.t * self.mock_yaw_rate_hz)
        )
        msg.linear_acceleration.x = (
            self.mock_linear_accel_mps2 * math.sin(self.t * self.mock_linear_accel_hz)
        )
        msg.linear_acceleration.y = (
            self.mock_linear_accel_mps2 * math.cos(self.t * self.mock_linear_accel_hz)
        )
        msg.linear_acceleration.z = 9.81
        msg.linear_acceleration_covariance[0] = -1.0
        msg.angular_velocity_covariance[0] = -1.0
        msg.orientation_covariance[0] = -1.0
        self.pub.publish(msg)
        self.t += self.publish_period


def main(args=None):
    rclpy.init(args=args)
    node = MpuNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    node.destroy_node()
    rclpy.shutdown()


if __name__ == "__main__":
    main()
