#!/usr/bin/env python3

import math
from typing import List, Sequence, Tuple

import rclpy
from rclpy.node import Node
from sensor_msgs.msg import LaserScan


class RadarNode(Node):
    def __init__(self):
        super().__init__('radar_node')

        self.declare_parameter('frame_id', 'radar_link')
        self.declare_parameter('topic_name', '/radar/scan')
        self.declare_parameter('publish_rate', 10.0)
        self.declare_parameter('angle_min', -1.57)
        self.declare_parameter('angle_max', 1.57)
        self.declare_parameter('angle_increment', 0.01745)
        self.declare_parameter('range_min', 0.1)
        self.declare_parameter('range_max', 6.0)
        self.declare_parameter('default_range', 2.5)
        self.declare_parameter('base_angle_deg', 0.0)
        self.declare_parameter('servo_step_angles_deg', [0.0, 60.0, 120.0])
        self.declare_parameter('sensor_offsets_deg', [0.0, 90.0, 180.0, 270.0])
        self.declare_parameter('sensor_fov_deg', 90.0)
        self.declare_parameter('mark_uncovered_as_inf', True)

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
        self.covered_sectors = self._build_covered_sectors()

        self.publisher = self.create_publisher(LaserScan, self.topic_name, 10)
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
        values = self.get_parameter(name).value
        return [float(value) for value in values]

    def _normalize_angle(self, angle_rad: float) -> float:
        return math.atan2(math.sin(angle_rad), math.cos(angle_rad))

    def _build_covered_sectors(self) -> List[Tuple[float, float]]:
        half_fov = math.radians(self.sensor_fov_deg / 2.0)
        sectors: List[Tuple[float, float]] = []

        for servo_step_deg in self.servo_step_angles_deg:
            servo_angle = math.radians(self.base_angle_deg + servo_step_deg)
            for sensor_offset_deg in self.sensor_offsets_deg:
                center_angle = self._normalize_angle(servo_angle + math.radians(sensor_offset_deg))
                start = center_angle - half_fov
                end = center_angle + half_fov

                if start < -math.pi:
                    sectors.append((start + 2.0 * math.pi, math.pi))
                    sectors.append((-math.pi, end))
                elif end > math.pi:
                    sectors.append((start, math.pi))
                    sectors.append((-math.pi, end - 2.0 * math.pi))
                else:
                    sectors.append((start, end))

        return sectors

    def _angle_is_covered(self, angle_rad: float, sectors: Sequence[Tuple[float, float]]) -> bool:
        return any(start <= angle_rad <= end for start, end in sectors)

    def publish_scan(self):
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

        for index in range(count):
            angle = self.angle_min + index * self.angle_increment
            normalized_angle = self._normalize_angle(angle)
            if self._angle_is_covered(normalized_angle, self.covered_sectors):
                scan.ranges[index] = self.default_range
                scan.intensities[index] = 1.0

        self.publisher.publish(scan)


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
