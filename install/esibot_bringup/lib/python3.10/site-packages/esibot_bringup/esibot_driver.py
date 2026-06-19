#!/usr/bin/env python3

import math
from typing import Optional

import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist, Quaternion, TransformStamped
from nav_msgs.msg import Odometry
from sensor_msgs.msg import BatteryState
import tf2_ros

try:
    import RPi.GPIO as GPIO
except ImportError:  # pragma: no cover - expected on non-RPi dev environments
    GPIO = None


class EsibotDriver(Node):
    def __init__(self):
        super().__init__("esibot_driver")

        # Hardware and motion parameters
        self.declare_parameter("wheel_radius", 0.033)  # meters
        self.declare_parameter("wheel_separation", 0.17)  # meters
        self.declare_parameter("max_wheel_speed", 0.6)  # m/s at 100% PWM
        self.declare_parameter("cmd_timeout", 0.5)  # seconds
        self.declare_parameter("publish_rate", 20.0)  # Hz

        # L298N pin mapping (BCM)
        self.declare_parameter("left_in1", 17)
        self.declare_parameter("left_in2", 27)
        self.declare_parameter("left_pwm", 12)
        self.declare_parameter("right_in1", 22)
        self.declare_parameter("right_in2", 23)
        self.declare_parameter("right_pwm", 13)
        self.declare_parameter("pwm_frequency", 1000)
        self.declare_parameter(
            "min_pwm_duty", 35.0
        )  # percent, helps overcome motor deadzone

        # Runtime behavior
        self.declare_parameter("dry_run", False)
        self.declare_parameter("publish_open_loop_odom", True)
        self.declare_parameter("publish_odom_enabled", True)
        self.declare_parameter("publish_tf", True)
        self.declare_parameter("invert_left", False)
        self.declare_parameter("invert_right", False)

        # Battery strategy while no sensor is wired yet
        self.declare_parameter("battery_source", "fixed")  # fixed|none
        self.declare_parameter("battery_voltage", 12.0)
        self.declare_parameter("battery_percentage", 0.8)

        self.r = float(self.get_parameter("wheel_radius").value)
        self.L = float(self.get_parameter("wheel_separation").value)
        self.max_wheel_speed = max(
            0.01, float(self.get_parameter("max_wheel_speed").value)
        )
        self.cmd_timeout = max(0.05, float(self.get_parameter("cmd_timeout").value))
        self.publish_rate = max(1.0, float(self.get_parameter("publish_rate").value))
        self.publish_open_loop_odom = bool(
            self.get_parameter("publish_open_loop_odom").value
        )
        self._publish_odom_enabled = bool(self.get_parameter("publish_odom_enabled").value)
        self.publish_tf = bool(self.get_parameter("publish_tf").value)
        self.battery_source = (
            str(self.get_parameter("battery_source").value).strip().lower()
        )
        self.battery_voltage = float(self.get_parameter("battery_voltage").value)
        self.battery_percentage = float(self.get_parameter("battery_percentage").value)
        self.dry_run = bool(self.get_parameter("dry_run").value)
        self.invert_left = bool(self.get_parameter("invert_left").value)
        self.invert_right = bool(self.get_parameter("invert_right").value)

        self.left_in1 = int(self.get_parameter("left_in1").value)
        self.left_in2 = int(self.get_parameter("left_in2").value)
        self.left_pwm_pin = int(self.get_parameter("left_pwm").value)
        self.right_in1 = int(self.get_parameter("right_in1").value)
        self.right_in2 = int(self.get_parameter("right_in2").value)
        self.right_pwm_pin = int(self.get_parameter("right_pwm").value)
        self.pwm_frequency = int(self.get_parameter("pwm_frequency").value)
        self.min_pwm_duty = max(
            0.0, min(100.0, float(self.get_parameter("min_pwm_duty").value))
        )

        # Internal state
        self.last_cmd_time = self.get_clock().now()
        self.last_update_time = self.get_clock().now()
        self.target_left_speed = 0.0
        self.target_right_speed = 0.0
        self.current_left_speed = 0.0
        self.current_right_speed = 0.0

        self.x = 0.0
        self.y = 0.0
        self.th = 0.0

        self.gpio_ready = False
        self.left_pwm: Optional[object] = None
        self.right_pwm: Optional[object] = None
        self._init_gpio()

        self.tf_broadcaster = tf2_ros.TransformBroadcaster(self)

        # ROS interfaces
        self.odom_pub = self.create_publisher(Odometry, "/odom", 10)
        self.battery_pub = self.create_publisher(BatteryState, "/battery_state", 10)

        self.cmd_sub = self.create_subscription(
            Twist, "/cmd_vel", self.cmd_vel_callback, 10
        )

        self.timer = self.create_timer(1.0 / self.publish_rate, self.update_robot_state)

        mode = (
            "DRY RUN"
            if self.dry_run
            else ("GPIO READY" if self.gpio_ready else "GPIO DISABLED")
        )
        self.get_logger().info(f"Esibot Driver Started ({mode})")

    def _init_gpio(self):
        if self.dry_run:
            self.get_logger().warn("dry_run=true: motors will not be driven")
            return
        if GPIO is None:
            self.get_logger().error(
                "RPi.GPIO not available: install python3-rpi.gpio or use dry_run=true"
            )
            return

        GPIO.setmode(GPIO.BCM)
        for pin in [
            self.left_in1,
            self.left_in2,
            self.left_pwm_pin,
            self.right_in1,
            self.right_in2,
            self.right_pwm_pin,
        ]:
            GPIO.setup(pin, GPIO.OUT)

        self.left_pwm = GPIO.PWM(self.left_pwm_pin, self.pwm_frequency)
        self.right_pwm = GPIO.PWM(self.right_pwm_pin, self.pwm_frequency)
        self.left_pwm.start(0.0)
        self.right_pwm.start(0.0)
        self._drive_wheel(self.left_in1, self.left_in2, self.left_pwm, 0.0)
        self._drive_wheel(self.right_in1, self.right_in2, self.right_pwm, 0.0)
        self.gpio_ready = True

    def cmd_vel_callback(self, msg: Twist):
        """Convert Twist (v, w) to wheel speeds for the L298N motor driver."""
        v = msg.linear.x
        w = msg.angular.z

        left_speed = v - (w * self.L / 2.0)
        right_speed = v + (w * self.L / 2.0)

        self.target_left_speed = left_speed
        self.target_right_speed = right_speed
        self.last_cmd_time = self.get_clock().now()

        self._apply_motor_command(left_speed, right_speed)

    def update_robot_state(self):
        now = self.get_clock().now()
        dt = (now - self.last_update_time).nanoseconds / 1e9
        self.last_update_time = now

        stale = (now - self.last_cmd_time).nanoseconds / 1e9 > self.cmd_timeout
        if stale and (
            self.current_left_speed != 0.0 or self.current_right_speed != 0.0
        ):
            self._apply_motor_command(0.0, 0.0)

        if self.publish_open_loop_odom and dt > 0.0:
            self._integrate_open_loop_odometry(dt)

        if self._publish_odom_enabled:
            self.publish_odom(self.x, self.y, self.th)
        self.publish_battery()

    def _integrate_open_loop_odometry(self, dt: float):
        v = (self.current_right_speed + self.current_left_speed) / 2.0
        w = (self.current_right_speed - self.current_left_speed) / self.L

        self.th += w * dt
        self.x += v * math.cos(self.th) * dt
        self.y += v * math.sin(self.th) * dt

    def _apply_motor_command(self, left_speed: float, right_speed: float):
        self.current_left_speed = left_speed
        self.current_right_speed = right_speed

        left_norm = max(-1.0, min(1.0, left_speed / self.max_wheel_speed))
        right_norm = max(-1.0, min(1.0, right_speed / self.max_wheel_speed))

        if self.invert_left:
            left_norm = -left_norm
        if self.invert_right:
            right_norm = -right_norm

        if self.gpio_ready and not self.dry_run:
            self._drive_wheel(self.left_in1, self.left_in2, self.left_pwm, left_norm)
            self._drive_wheel(
                self.right_in1, self.right_in2, self.right_pwm, right_norm
            )

    def _drive_wheel(self, pin_fwd: int, pin_bwd: int, pwm, norm_speed: float):
        duty = abs(norm_speed) * 100.0
        if duty > 0.0:
            duty = self.min_pwm_duty + (100.0 - self.min_pwm_duty) * (duty / 100.0)

        if norm_speed > 0.0:
            GPIO.output(pin_fwd, GPIO.HIGH)
            GPIO.output(pin_bwd, GPIO.LOW)
        elif norm_speed < 0.0:
            GPIO.output(pin_fwd, GPIO.LOW)
            GPIO.output(pin_bwd, GPIO.HIGH)
        else:
            GPIO.output(pin_fwd, GPIO.LOW)
            GPIO.output(pin_bwd, GPIO.LOW)

        pwm.ChangeDutyCycle(duty)

    def publish_odom(self, x, y, th):
        now = self.get_clock().now().to_msg()
        q = self.euler_to_quaternion(0, 0, th)

        if self.publish_tf:
            t = TransformStamped()
            t.header.stamp = now
            t.header.frame_id = "odom"
            t.child_frame_id = "base_footprint"
            t.transform.translation.x = x
            t.transform.translation.y = y
            t.transform.rotation = q
            self.tf_broadcaster.sendTransform(t)

        # 2. Publish Odometry Message
        odom = Odometry()
        odom.header.stamp = now
        odom.header.frame_id = "odom"
        odom.child_frame_id = "base_footprint"
        odom.pose.pose.position.x = x
        odom.pose.pose.position.y = y
        odom.pose.pose.orientation = q
        odom.twist.twist.linear.x = (
            self.current_right_speed + self.current_left_speed
        ) / 2.0
        odom.twist.twist.angular.z = (
            self.current_right_speed - self.current_left_speed
        ) / self.L
        self.odom_pub.publish(odom)

    def publish_battery(self):
        msg = BatteryState()
        msg.header.stamp = self.get_clock().now().to_msg()

        if self.battery_source == "fixed":
            msg.voltage = self.battery_voltage
            msg.percentage = max(0.0, min(1.0, self.battery_percentage))
        else:
            # Unknown battery state until a real sensor/ADC is connected.
            msg.voltage = float("nan")
            msg.percentage = float("nan")

        self.battery_pub.publish(msg)

    def euler_to_quaternion(self, roll, pitch, yaw):
        qx = math.sin(roll / 2) * math.cos(pitch / 2) * math.cos(yaw / 2) - math.cos(
            roll / 2
        ) * math.sin(pitch / 2) * math.sin(yaw / 2)
        qy = math.cos(roll / 2) * math.sin(pitch / 2) * math.cos(yaw / 2) + math.sin(
            roll / 2
        ) * math.cos(pitch / 2) * math.sin(yaw / 2)
        qz = math.cos(roll / 2) * math.cos(pitch / 2) * math.sin(yaw / 2) - math.sin(
            roll / 2
        ) * math.sin(pitch / 2) * math.cos(yaw / 2)
        qw = math.cos(roll / 2) * math.cos(pitch / 2) * math.cos(yaw / 2) + math.sin(
            roll / 2
        ) * math.sin(pitch / 2) * math.sin(yaw / 2)
        return Quaternion(x=qx, y=qy, z=qz, w=qw)


def main(args=None):
    rclpy.init(args=args)
    node = EsibotDriver()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node._apply_motor_command(0.0, 0.0)
        if node.gpio_ready and GPIO is not None:
            if node.left_pwm is not None:
                node.left_pwm.stop()
            if node.right_pwm is not None:
                node.right_pwm.stop()
            GPIO.cleanup()
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
