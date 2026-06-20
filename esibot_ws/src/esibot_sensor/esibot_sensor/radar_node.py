#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from std_msgs.msg import Float32MultiArray, MultiArrayDimension, MultiArrayLayout

import pigpio
import time
import queue
import threading


class RadarNode(Node):
    def __init__(self):
        super().__init__('radar_node')

        # -----------------------
        # PARAMETERS & ROS 2
        # -----------------------
        self.declare_parameter('topic_name', '/radar/scan')
        self.declare_parameter('servo_gpio_pin', 24)
        self.declare_parameter('sensor_trigger_pins', [16, 20, 26, 19])
        self.declare_parameter('sensor_offsets_deg', [0.0, 90.0, 180.0, 270.0])
        self.declare_parameter('servo_scan_angles_deg', [0.0, 30.0, 60.0])
        self.declare_parameter('servo_settle_time_sec', 0.50)
        self.declare_parameter('servo_min_angle_deg', 0.0)
        self.declare_parameter('servo_max_angle_deg', 180.0)
        self.declare_parameter('servo_pwm_min_us', 1000.0)
        self.declare_parameter('servo_pwm_max_us', 2000.0)
        self.declare_parameter('publish_timer_sec', 0.1)
        self.declare_parameter('trigger_pulse_low_sec', 0.000002)
        self.declare_parameter('trigger_pulse_high_sec', 0.000010)
        self.declare_parameter('echo_timeout_sec', 0.03)
        self.declare_parameter('inter_sensor_delay_sec', 0.02)
        self.declare_parameter('speed_of_sound_cm_s', 34300.0)
        self.declare_parameter('max_distance_cm', 400.0)

        topic_name = self.get_parameter('topic_name').value
        self.SERVO_PIN = int(self.get_parameter('servo_gpio_pin').value)
        self.SENSORS = [int(p) for p in self.get_parameter('sensor_trigger_pins').value]
        self.offsets = [float(o) for o in self.get_parameter('sensor_offsets_deg').value]
        self.settle_time = float(self.get_parameter('servo_settle_time_sec').value)
        self.servo_min_angle_deg = float(self.get_parameter('servo_min_angle_deg').value)
        self.servo_max_angle_deg = float(self.get_parameter('servo_max_angle_deg').value)
        self.servo_pwm_min_us = float(self.get_parameter('servo_pwm_min_us').value)
        self.servo_pwm_max_us = float(self.get_parameter('servo_pwm_max_us').value)
        self.publish_timer_sec = max(0.01, float(self.get_parameter('publish_timer_sec').value))
        self.trigger_pulse_low_sec = max(0.0, float(self.get_parameter('trigger_pulse_low_sec').value))
        self.trigger_pulse_high_sec = max(0.0, float(self.get_parameter('trigger_pulse_high_sec').value))
        self.echo_timeout_sec = max(0.001, float(self.get_parameter('echo_timeout_sec').value))
        self.inter_sensor_delay_sec = max(0.0, float(self.get_parameter('inter_sensor_delay_sec').value))
        self.speed_of_sound_cm_s = max(1.0, float(self.get_parameter('speed_of_sound_cm_s').value))
        self.max_distance_cm = max(0.0, float(self.get_parameter('max_distance_cm').value))

        angles_yaml = self.get_parameter('servo_scan_angles_deg').value
        self.angles = [float(a) for a in angles_yaml]
        self.angle_keys = [int(round(a)) for a in self.angles]
        self.offset_keys = [int(round(o)) for o in self.offsets]

        angles_str = ','.join(str(a) for a in self.angle_keys)
        offsets_str = ','.join(str(o) for o in self.offset_keys)
        self.msg_layout = MultiArrayLayout(
            dim=[
                MultiArrayDimension(
                    label=f'angles_deg:{angles_str}',
                    size=len(self.angles),
                    stride=len(self.angles) * len(self.SENSORS)
                ),
                MultiArrayDimension(
                    label=f'offsets_deg:{offsets_str}',
                    size=len(self.SENSORS),
                    stride=len(self.SENSORS)
                ),
            ],
            data_offset=0
        )

        # Publisher
        self.publisher_ = self.create_publisher(Float32MultiArray, topic_name, 10)

        # -----------------------
        # HARDWARE SETUP (pigpio only)
        # -----------------------
        self.pi = pigpio.pi()
        if not self.pi.connected:
            self.get_logger().error("Unable to connect to pigpio daemon. Run 'sudo pigpiod'.")
            raise RuntimeError("pigpiod not started")

        self.pi.set_mode(self.SERVO_PIN, pigpio.OUTPUT)

        for pin in self.SENSORS:
            self.pi.set_mode(pin, pigpio.OUTPUT)
            self.pi.write(pin, 0)

        if self.angles:
            self.pi.set_servo_pulsewidth(self.SERVO_PIN, self._angle_to_pulsewidth(self.angles[0]))

        self.get_logger().info(f"Radar node initialized. Topic: {topic_name}")

        # -----------------------
        # SWEEP THREAD
        # -----------------------
        self._queue = queue.Queue(maxsize=1)
        self._running = True
        self._thread = threading.Thread(target=self._sweep_worker, daemon=True)
        self._thread.start()

        # ROS 2 timer publishes only and never blocks
        self.timer = self.create_timer(self.publish_timer_sec, self._publish_if_ready)

    # -----------------------
    # SERVO
    # -----------------------

    def _angle_to_pulsewidth(self, angle):
        """Standard mapping: 1000us @ 0°, 2000us @ 180°"""
        min_angle = self.servo_min_angle_deg
        max_angle = self.servo_max_angle_deg
        if max_angle <= min_angle:
            min_angle, max_angle = 0.0, 180.0

        min_us = min(self.servo_pwm_min_us, self.servo_pwm_max_us)
        max_us = max(self.servo_pwm_min_us, self.servo_pwm_max_us)

        angle_clamped = max(min_angle, min(max_angle, angle))
        ratio = (angle_clamped - min_angle) / (max_angle - min_angle)
        pw = min_us + (ratio * (max_us - min_us))
        return int(max(min_us, min(max_us, pw)))

    def set_angle(self, angle):
        self.pi.set_servo_pulsewidth(self.SERVO_PIN, self._angle_to_pulsewidth(angle))
        time.sleep(self.settle_time)

    # -----------------------
    # SENSOR READ (pigpio only)
    # -----------------------

    def read_v2(self, pin):
        try:
            self.pi.set_mode(pin, pigpio.OUTPUT)
            self.pi.write(pin, 0)
            time.sleep(self.trigger_pulse_low_sec)
            self.pi.write(pin, 1)
            time.sleep(self.trigger_pulse_high_sec)
            self.pi.write(pin, 0)

            self.pi.set_mode(pin, pigpio.INPUT)

            timeout = time.time()
            pulse_start = time.time()
            pulse_end = time.time()

            while self.pi.read(pin) == 0:
                pulse_start = time.time()
                if pulse_start - timeout > self.echo_timeout_sec:
                    return -1.0

            while self.pi.read(pin) == 1:
                pulse_end = time.time()
                if pulse_end - pulse_start > self.echo_timeout_sec:
                    return -1.0

            duration = pulse_end - pulse_start
            distance = round(duration * self.speed_of_sound_cm_s / 2, 2)
            if self.max_distance_cm > 0 and distance > self.max_distance_cm:
                return -1.0
            return distance
        except Exception:
            return -1.0

    # -----------------------
    # SWEEP THREAD
    # -----------------------

    def _sweep_worker(self):
        """Runs in its own thread. time.sleep() is allowed here."""
        self.get_logger().info("Sweep thread started.")

        while self._running:
            accumulated_data = {}

            for angle, angle_key in zip(self.angles, self.angle_keys):
                if not self._running:
                    break

                self.set_angle(angle)

                self.get_logger().info(f"Capture at {angle}°...")
                step_distances = []
                for pin in self.SENSORS:
                    d = self.read_v2(pin)
                    step_distances.append(d)
                    time.sleep(self.inter_sensor_delay_sec)

                accumulated_data[angle_key] = step_distances

            if not self._running:
                break

            total_packet = []
            for angle_key in self.angle_keys:
                total_packet.extend(accumulated_data.get(angle_key, [-1.0] * len(self.SENSORS)))

            if self._queue.full():
                try:
                    self._queue.get_nowait()
                except queue.Empty:
                    pass
            self._queue.put(total_packet)

        self.get_logger().info("Sweep thread stopped.")

    # -----------------------
    # ROS 2 TIMER CALLBACK (never blocks)
    # -----------------------

    def _publish_if_ready(self):
        try:
            total_packet = self._queue.get_nowait()
        except queue.Empty:
            return

        msg = Float32MultiArray(layout=self.msg_layout, data=total_packet)
        self.publisher_.publish(msg)
        self.get_logger().info(f"Published packet: {total_packet}")

    # -----------------------
    # CLEANUP
    # -----------------------

    def destroy_node(self):
        self.get_logger().info("Cleanup...")

        self._running = False
        self._thread.join(timeout=3.0)

        if hasattr(self, 'pi') and self.pi.connected:
            self.pi.set_servo_pulsewidth(self.SERVO_PIN, 0)
            for pin in self.SENSORS:
                self.pi.write(pin, 0)
                self.pi.set_mode(pin, pigpio.INPUT)
            self.pi.stop()

        super().destroy_node()


def main(args=None):
    rclpy.init(args=args)
    node = RadarNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
