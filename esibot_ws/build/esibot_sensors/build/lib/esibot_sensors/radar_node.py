#!/usr/bin/env python3

import math
import time
from typing import List, Optional, Sequence, Tuple

import rclpy
from rclpy.node import Node
from sensor_msgs.msg import LaserScan

try:
    from gpiozero import AngularServo, DistanceSensor
except ImportError:
    AngularServo = None
    DistanceSensor = None


class RadarNode(Node):
    def __init__(self):
        super().__init__('radar_node')

        self.declare_parameter('frame_id', 'radar_link')
        self.declare_parameter('topic_name', '/radar/scan')
        self.declare_parameter('publish_rate', 1.0)
        self.declare_parameter('angle_min', -math.pi)
        self.declare_parameter('angle_max', math.pi)
        self.declare_parameter('angle_increment', 0.01745)
        self.declare_parameter('range_min', 0.02)
        self.declare_parameter('range_max', 4.0)
        self.declare_parameter('default_range', 2.5)
        self.declare_parameter('base_angle_deg', 0.0)
        self.declare_parameter('servo_step_angles_deg', [0.0, 60.0, 120.0])
        self.declare_parameter('sensor_offsets_deg', [0.0, 90.0, 180.0, 270.0])
        self.declare_parameter('sensor_fov_deg', 90.0)
        self.declare_parameter('mark_uncovered_as_inf', True)
        self.declare_parameter('use_mock_data', False)
        self.declare_parameter('servo_gpio_pin', 18)
        self.declare_parameter('servo_min_angle_deg', 0.0)
        self.declare_parameter('servo_max_angle_deg', 180.0)
        self.declare_parameter('servo_settle_time_sec', 0.35)
        self.declare_parameter('sensor_trigger_pins', [17, 22, 24, 5])
        self.declare_parameter('sensor_echo_pins', [27, 23, 25, 6])
        self.declare_parameter('sensor_max_distance_m', 4.0)
        self.declare_parameter('sensor_threshold_distance_m', 4.0)
        self.declare_parameter('sensor_queue_len', 3)
        self.declare_parameter('active_sensor_indices', [0, 1, 2, 3])

        self.frame_id = str(self.get_parameter('frame_id').value)
        self.topic_name = str(self.get_parameter('topic_name').value)
        self.publish_rate = float(self.get_parameter('publish_rate').value)
        self.angle_min = float(self.get_parameter('angle_min').value)
        self.angle_max = float(self.get_parameter('angle_max').value)
        self.angle_increment = float(self.get_parameter('angle_increment').value)
        self.range_min = float(self.get_parameter('range_min').value)
        self.range_max = float(self.get_parameter('range_max').value)
        self.default_range = float(self.get_parameter('default_range').value)
        self.base_angle_deg = float(self.get_parameter('base_angle_deg').value)
        self.servo_step_angles_deg = self._read_float_list('servo_step_angles_deg')
        self.sensor_offsets_deg = self._read_float_list('sensor_offsets_deg')
        self.sensor_fov_deg = float(self.get_parameter('sensor_fov_deg').value)
        self.mark_uncovered_as_inf = bool(self.get_parameter('mark_uncovered_as_inf').value)
        self.use_mock_data = bool(self.get_parameter('use_mock_data').value)
        self.servo_gpio_pin = int(self.get_parameter('servo_gpio_pin').value)
        self.servo_min_angle_deg = float(self.get_parameter('servo_min_angle_deg').value)
        self.servo_max_angle_deg = float(self.get_parameter('servo_max_angle_deg').value)
        self.servo_settle_time_sec = float(self.get_parameter('servo_settle_time_sec').value)
        self.sensor_trigger_pins = self._read_int_list('sensor_trigger_pins')
        self.sensor_echo_pins = self._read_int_list('sensor_echo_pins')
        self.sensor_max_distance_m = float(self.get_parameter('sensor_max_distance_m').value)
        self.sensor_threshold_distance_m = float(self.get_parameter('sensor_threshold_distance_m').value)
        self.sensor_queue_len = int(self.get_parameter('sensor_queue_len').value)
        self.active_sensor_indices = self._read_int_list('active_sensor_indices')

        self._validate_geometry()

        self.publisher = self.create_publisher(LaserScan, self.topic_name, 10)

        self.servo: Optional[AngularServo] = None
        self.distance_sensors: List[Optional[DistanceSensor]] = []
        self.hardware_ready = False
        self.hardware_error_logged = False

        if not self.use_mock_data:
            self.hardware_ready = self._setup_hardware()
        else:
            self.get_logger().info('Using mock radar data because use_mock_data=true')

        self.timer = self.create_timer(1.0 / self.publish_rate, self.publish_scan)

        self.get_logger().info('radar_node started')
        self.get_logger().info(f'Publishing {self.topic_name} at {self.publish_rate} Hz')
        self.get_logger().info(
            'Geometry: base=%.1f deg, servo stops=%s, sensor offsets=%s, sensor fov=%.1f deg'
            % (
                self.base_angle_deg,
                self.servo_step_angles_deg,
                self.sensor_offsets_deg,
                self.sensor_fov_deg,
            )
        )

    def _read_float_list(self, name: str) -> List[float]:
        return [float(value) for value in self.get_parameter(name).value]

    def _read_int_list(self, name: str) -> List[int]:
        return [int(value) for value in self.get_parameter(name).value]

    def _validate_geometry(self) -> None:
        if len(self.sensor_offsets_deg) != len(self.sensor_trigger_pins):
            raise ValueError('sensor_offsets_deg and sensor_trigger_pins must have the same length')
        if len(self.sensor_offsets_deg) != len(self.sensor_echo_pins):
            raise ValueError('sensor_offsets_deg and sensor_echo_pins must have the same length')
        if not self.servo_step_angles_deg:
            raise ValueError('servo_step_angles_deg must not be empty')
        if not self.active_sensor_indices:
            raise ValueError('active_sensor_indices must not be empty')

    def _normalize_angle(self, angle_rad: float) -> float:
        return math.atan2(math.sin(angle_rad), math.cos(angle_rad))

    def _wrap_angle_deg_to_servo_range(self, angle_deg: float) -> float:
        wrapped = angle_deg % 360.0
        if wrapped > 180.0:
            wrapped -= 360.0
        return min(max(wrapped, self.servo_min_angle_deg), self.servo_max_angle_deg)

    def _setup_hardware(self) -> bool:
        if AngularServo is None or DistanceSensor is None:
            self.get_logger().warning(
                'gpiozero is not installed. Falling back to mock scan data. '
                'Install python3-gpiozero on the Raspberry Pi to read real sensors.'
            )
            return False

        try:
            self.servo = AngularServo(
                self.servo_gpio_pin,
                min_angle=self.servo_min_angle_deg,
                max_angle=self.servo_max_angle_deg,
            )

            for trigger_pin, echo_pin in zip(self.sensor_trigger_pins, self.sensor_echo_pins):
                sensor = DistanceSensor(
                    echo=echo_pin,
                    trigger=trigger_pin,
                    max_distance=self.sensor_max_distance_m,
                    threshold_distance=self.sensor_threshold_distance_m,
                    queue_len=self.sensor_queue_len,
                )
                self.distance_sensors.append(sensor)

            self.get_logger().info(
                'Hardware ready: servo GPIO=%d, trigger pins=%s, echo pins=%s'
                % (self.servo_gpio_pin, self.sensor_trigger_pins, self.sensor_echo_pins)
            )
            return True
        except Exception as exc:
            self.get_logger().warning(
                f'Failed to initialize GPIO hardware ({exc}). Falling back to mock scan data.'
            )
            self.distance_sensors = []
            self.servo = None
            return False

    def _read_sensor_distance(self, sensor_index: int) -> float:
        sensor = self.distance_sensors[sensor_index]
        if sensor is None:
            return math.inf

        try:
            measured_distance = float(sensor.distance) * self.sensor_max_distance_m
        except Exception as exc:
            self.get_logger().warning(f'Failed to read ultrasonic sensor {sensor_index}: {exc}')
            return math.inf

        if measured_distance < self.range_min or measured_distance > self.range_max:
            return math.inf

        return measured_distance

    def _perform_hardware_sweep(self) -> List[Tuple[float, float, float]]:
        measurements: List[Tuple[float, float, float]] = []

        if not self.hardware_ready or self.servo is None:
            return measurements

        for servo_step_deg in self.servo_step_angles_deg:
            absolute_servo_angle_deg = self.base_angle_deg + servo_step_deg
            servo_command_deg = self._wrap_angle_deg_to_servo_range(absolute_servo_angle_deg)
            self.servo.angle = servo_command_deg
            time.sleep(self.servo_settle_time_sec)

            for sensor_index in self.active_sensor_indices:
                if sensor_index < 0 or sensor_index >= len(self.sensor_offsets_deg):
                    continue

                center_angle_deg = absolute_servo_angle_deg + self.sensor_offsets_deg[sensor_index]
                measured_distance = self._read_sensor_distance(sensor_index)
                measurements.append(
                    (
                        math.radians(center_angle_deg),
                        math.radians(self.sensor_fov_deg),
                        measured_distance,
                    )
                )

        return measurements

    def _build_mock_measurements(self) -> List[Tuple[float, float, float]]:
        measurements: List[Tuple[float, float, float]] = []

        for servo_step_deg in self.servo_step_angles_deg:
            absolute_servo_angle_deg = self.base_angle_deg + servo_step_deg
            for sensor_index in self.active_sensor_indices:
                if sensor_index < 0 or sensor_index >= len(self.sensor_offsets_deg):
                    continue
                center_angle_deg = absolute_servo_angle_deg + self.sensor_offsets_deg[sensor_index]
                measurements.append(
                    (
                        math.radians(center_angle_deg),
                        math.radians(self.sensor_fov_deg),
                        self.default_range,
                    )
                )

        return measurements

    def _measurement_covers_angle(
        self,
        angle_rad: float,
        measurement_center_rad: float,
        measurement_fov_rad: float,
    ) -> bool:
        half_fov = measurement_fov_rad / 2.0
        delta = self._normalize_angle(angle_rad - measurement_center_rad)
        return -half_fov <= delta <= half_fov

    def publish_scan(self) -> None:
        scan = LaserScan()
        scan.header.stamp = self.get_clock().now().to_msg()
        scan.header.frame_id = self.frame_id
        scan.angle_min = self.angle_min
        scan.angle_max = self.angle_max
        scan.angle_increment = self.angle_increment
        scan.time_increment = 0.0
        scan.scan_time = 1.0 / self.publish_rate
        scan.range_min = self.range_min
        scan.range_max = self.range_max

        count = int(math.floor((self.angle_max - self.angle_min) / self.angle_increment)) + 1
        count = max(count, 1)

        uncovered_range = math.inf if self.mark_uncovered_as_inf else self.range_max
        scan.ranges = [uncovered_range] * count
        scan.intensities = [0.0] * count

        measurements = (
            self._perform_hardware_sweep()
            if self.hardware_ready
            else self._build_mock_measurements()
        )

        if not self.hardware_ready and not self.use_mock_data and not self.hardware_error_logged:
            self.get_logger().warning(
                'Publishing mock scan data because real sensor hardware is not available.'
            )
            self.hardware_error_logged = True

        for index in range(count):
            angle = self.angle_min + index * self.angle_increment
            normalized_angle = self._normalize_angle(angle)

            for center_angle_rad, fov_rad, measured_distance in measurements:
                if self._measurement_covers_angle(normalized_angle, center_angle_rad, fov_rad):
                    scan.ranges[index] = measured_distance
                    scan.intensities[index] = 1.0 if math.isfinite(measured_distance) else 0.0
                    break

        self.publisher.publish(scan)

    def destroy_node(self):
        for sensor in self.distance_sensors:
            if sensor is not None:
                sensor.close()

        if self.servo is not None:
            self.servo.detach()
            self.servo.close()

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
