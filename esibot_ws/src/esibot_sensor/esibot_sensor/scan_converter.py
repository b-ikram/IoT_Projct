#!/usr/bin/env python3
import math
import rclpy
from rclpy.node import Node
from std_msgs.msg import Float32MultiArray
from sensor_msgs.msg import LaserScan


class ScanConverter(Node):
    def __init__(self):
        super().__init__('scan_converter')

        self.declare_parameter('input_topic', '/radar/scan')
        self.declare_parameter('output_topic', '/scan')
        self.declare_parameter('frame_id', 'radar_link')
        self.declare_parameter('angle_min_deg', 0.0)
        self.declare_parameter('angle_max_deg', 359.0)
        self.declare_parameter('angle_increment_deg', 1.0)
        self.declare_parameter('range_min_m', 0.02)
        self.declare_parameter('range_max_m', 4.0)
        self.declare_parameter('interpolate_max_gap_deg', 120.0)
        self.declare_parameter('fallback_servo_angles_deg', [0.0, 30.0, 60.0])
        self.declare_parameter('fallback_sensor_offsets_deg', [0.0, 90.0, 180.0, 270.0])

        self.input_topic = str(self.get_parameter('input_topic').value)
        self.output_topic = str(self.get_parameter('output_topic').value)
        self.frame_id = str(self.get_parameter('frame_id').value)
        self.angle_min_deg = float(self.get_parameter('angle_min_deg').value)
        self.angle_max_deg = float(self.get_parameter('angle_max_deg').value)
        self.angle_increment_deg = float(self.get_parameter('angle_increment_deg').value)
        self.range_min_m = float(self.get_parameter('range_min_m').value)
        self.range_max_m = float(self.get_parameter('range_max_m').value)
        self.interpolate_max_gap_deg = float(self.get_parameter('interpolate_max_gap_deg').value)
        self.fallback_servo_angles = [float(v) for v in self.get_parameter('fallback_servo_angles_deg').value]
        self.fallback_sensor_offsets = [float(v) for v in self.get_parameter('fallback_sensor_offsets_deg').value]

        self.sub = self.create_subscription(
            Float32MultiArray,
            self.input_topic,
            self.callback,
            10
        )
        self.pub = self.create_publisher(LaserScan, self.output_topic, 10)
        self.get_logger().info("Converter active: Float32MultiArray -> LaserScan")

    @staticmethod
    def _parse_label_values(label: str):
        """Parse 'angles_deg:0,30,60' -> [0.0, 30.0, 60.0]"""
        try:
            _, values_str = label.split(':', 1)
            return [float(v) for v in values_str.split(',')]
        except Exception:
            return []

    def _get_layout(self, msg):
        """
        Read angles and offsets from the message layout.
        Fallback to defaults if layout is missing (backward compatibility).
        """
        dims = msg.layout.dim
        if len(dims) >= 2:
            angles = self._parse_label_values(dims[0].label)
            offsets = self._parse_label_values(dims[1].label)
            if len(angles) == dims[0].size and len(offsets) == dims[1].size:
                return angles, offsets

        self.get_logger().warn(
            f"Layout missing on {self.input_topic}. Using defaults for angles/offsets.",
            throttle_duration_sec=30.0
        )
        return self.fallback_servo_angles, self.fallback_sensor_offsets

    def callback(self, msg):
        servo_angles, sensor_offsets = self._get_layout(msg)
        n_angles = len(servo_angles)
        n_sensors = len(sensor_offsets)

        if len(msg.data) < n_angles * n_sensors:
            return
        if self.angle_increment_deg <= 0:
            return
        if self.angle_max_deg <= self.angle_min_deg:
            return

        laser_scan = LaserScan()
        laser_scan.header.stamp = self.get_clock().now().to_msg()
        laser_scan.header.frame_id = self.frame_id

        laser_scan.angle_min = math.radians(self.angle_min_deg)
        laser_scan.angle_max = math.radians(self.angle_max_deg)
        laser_scan.angle_increment = math.radians(self.angle_increment_deg)
        laser_scan.time_increment = 0.0
        laser_scan.range_min = self.range_min_m
        laser_scan.range_max = self.range_max_m

        bin_count = int(round((self.angle_max_deg - self.angle_min_deg) / self.angle_increment_deg)) + 1
        bin_count = max(1, bin_count)
        ranges = [float('inf')] * bin_count
        measured_points = {}
        data_idx = 0

        for s_angle in servo_angles:
            for offset in sensor_offsets:
                dist_cm = msg.data[data_idx]
                data_idx += 1

                if dist_cm < 0:
                    continue

                dist_m = dist_cm / 100.0
                total_angle_deg = (s_angle + offset) % 360
                idx = int(round((total_angle_deg - self.angle_min_deg) / self.angle_increment_deg))

                if 0 <= idx < bin_count:
                    ranges[idx] = dist_m
                    measured_points[total_angle_deg] = dist_m

        measured_angles = sorted(measured_points.keys())

        if len(measured_angles) >= 2:
            for i in range(len(measured_angles)):
                angle_a = measured_angles[i]
                angle_b = measured_angles[(i + 1) % len(measured_angles)]
                dist_a = measured_points[angle_a]
                dist_b = measured_points[angle_b]

                if angle_b > angle_a:
                    gap = angle_b - angle_a
                else:
                    gap = (360 - angle_a) + angle_b

                steps = int(round(gap))
                if 0 < steps < self.interpolate_max_gap_deg:
                    for step in range(1, steps):
                        t = step / steps
                        interp_dist = dist_a + t * (dist_b - dist_a)
                        interp_angle = (angle_a + step) % 360
                        interp_idx = int(round((interp_angle - self.angle_min_deg) / self.angle_increment_deg))
                        if 0 <= interp_idx < bin_count:
                            ranges[interp_idx] = interp_dist

        laser_scan.ranges = ranges
        self.pub.publish(laser_scan)


def main(args=None):
    rclpy.init(args=args)
    node = ScanConverter()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
