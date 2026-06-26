#!/usr/bin/env python3
"""
imu_node — Raw MPU6050 IMU driver for robot_localization EKF.

Reads accelerometer and gyroscope data from the MPU6050 over I2C,
applies a simple low-pass filter and deadzone, and publishes a
standard sensor_msgs/Imu message with proper covariance matrices.

This node does NOT integrate or compute odometry — that is the
EKF's job.  It only outputs raw (filtered) sensor readings.

Published topics:
    /imu/data  (sensor_msgs/Imu)

Parameters:
    See declare_parameter calls below.
"""

import math

import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Imu
from mpu6050 import mpu6050


class ImuNode(Node):
    def __init__(self):
        super().__init__("imu_node")

        # --------------- parameters ---------------
        self.declare_parameter("topic", "/imu/data")
        self.declare_parameter("frame_id", "imu_link")
        self.declare_parameter("publish_rate_hz", 50.0)
        self.declare_parameter("alpha", 0.2)
        self.declare_parameter("deadzone_deg_s", 0.5)
        self.declare_parameter("i2c_address", 0x68)

        # Covariance diagonal values (rad²/s² for gyro, m²/s⁴ for accel).
        # orientation_covariance is set to -1 (no orientation estimate).
        self.declare_parameter("gyro_covariance", 0.001)
        self.declare_parameter("accel_covariance", 0.1)

        topic = str(self.get_parameter("topic").value)
        self.frame_id = str(self.get_parameter("frame_id").value)
        publish_rate_hz = float(self.get_parameter("publish_rate_hz").value)
        self.alpha = float(self.get_parameter("alpha").value)
        self.deadzone = float(self.get_parameter("deadzone_deg_s").value)
        i2c_address = int(self.get_parameter("i2c_address").value)
        gyro_cov = float(self.get_parameter("gyro_covariance").value)
        accel_cov = float(self.get_parameter("accel_covariance").value)

        # --------------- sensor init ---------------
        self.sensor = None
        try:
            self.sensor = mpu6050(i2c_address)
            self.get_logger().info(
                f"MPU6050 connected at 0x{i2c_address:02X}."
            )
        except Exception as e:
            self.get_logger().error(f"MPU6050 init failed: {e}")

        # --------------- ROS interfaces ---------------
        self.publisher = self.create_publisher(Imu, topic, 10)

        # --------------- filter state ---------------
        self.prev_gx = 0.0
        self.prev_gy = 0.0
        self.prev_gz = 0.0

        # --------------- pre-build static covariance arrays ---------------
        # orientation: -1 means "not provided" (MPU6050 has no magnetometer)
        self.orientation_cov = [-1.0] + [0.0] * 8

        # angular velocity: diagonal covariance
        self.angular_velocity_cov = [0.0] * 9
        self.angular_velocity_cov[0] = gyro_cov  # x
        self.angular_velocity_cov[4] = gyro_cov  # y
        self.angular_velocity_cov[8] = gyro_cov  # z

        # linear acceleration: diagonal covariance
        self.linear_acceleration_cov = [0.0] * 9
        self.linear_acceleration_cov[0] = accel_cov  # x
        self.linear_acceleration_cov[4] = accel_cov  # y
        self.linear_acceleration_cov[8] = accel_cov  # z

        # --------------- timer ---------------
        self.timer = self.create_timer(
            1.0 / publish_rate_hz, self.timer_callback
        )
        self.get_logger().info(
            f"IMU node publishing on {topic} at {publish_rate_hz} Hz"
        )

    def timer_callback(self):
        if self.sensor is None:
            return

        try:
            accel_data = self.sensor.get_accel_data()
            gyro_data = self.sensor.get_gyro_data()
        except Exception as e:
            self.get_logger().warn(f"MPU6050 read error: {e}")
            return

        # --- deadzone on gyro Z ---
        raw_gz = gyro_data["z"]
        if abs(raw_gz) < self.deadzone:
            raw_gz = 0.0

        # --- low-pass filter (exponential moving average) ---
        gx = self.alpha * gyro_data["x"] + (1.0 - self.alpha) * self.prev_gx
        gy = self.alpha * gyro_data["y"] + (1.0 - self.alpha) * self.prev_gy
        gz = self.alpha * raw_gz + (1.0 - self.alpha) * self.prev_gz
        self.prev_gx = gx
        self.prev_gy = gy
        self.prev_gz = gz

        # --- convert deg/s → rad/s ---
        deg2rad = math.pi / 180.0

        # --- build message ---
        msg = Imu()
        msg.header.stamp = self.get_clock().now().to_msg()
        msg.header.frame_id = self.frame_id

        msg.angular_velocity.x = gx * deg2rad
        msg.angular_velocity.y = gy * deg2rad
        msg.angular_velocity.z = gz * deg2rad

        msg.linear_acceleration.x = accel_data["x"]
        msg.linear_acceleration.y = accel_data["y"]
        msg.linear_acceleration.z = accel_data["z"]

        # --- covariance ---
        msg.orientation_covariance = self.orientation_cov
        msg.angular_velocity_covariance = self.angular_velocity_cov
        msg.linear_acceleration_covariance = self.linear_acceleration_cov

        self.publisher.publish(msg)


def main(args=None):
    rclpy.init(args=args)
    node = ImuNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
