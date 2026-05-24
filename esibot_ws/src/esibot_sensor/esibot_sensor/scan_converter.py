#!/usr/bin/env python3
import math
import rclpy
from rclpy.node import Node
from std_msgs.msg import Float32MultiArray
from sensor_msgs.msg import LaserScan

class ScanConverter(Node):
    def __init__(self):
        super().__init__('scan_converter')
        self.sub = self.create_subscription(
            Float32MultiArray,
            '/radar/scan',
            self.callback,
            10
        )
        self.pub = self.create_publisher(LaserScan, '/scan', 10)
        self.get_logger().info("Convertisseur active : Float32MultiArray -> LaserScan")

    def callback(self, msg):
        if len(msg.data) < 12:
            return

        laser_scan = LaserScan()
        laser_scan.header.stamp = self.get_clock().now().to_msg()
        laser_scan.header.frame_id = 'radar_link'
        laser_scan.angle_min = -math.pi
        laser_scan.angle_max = math.pi
        laser_scan.angle_increment = math.radians(1)
        laser_scan.time_increment = 0.0
        laser_scan.range_min = 0.02
        laser_scan.range_max = 4.0

        ranges = [float('inf')] * 360

        servo_angles = [0, 30, 60]
        sensor_offsets = [0, 90, 180, 270]

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
                idx = int(total_angle_deg)

                if 0 <= idx < 360:
                    ranges[idx] = dist_m
                    measured_points[idx] = dist_m

        measured_angles = sorted(measured_points.keys())

        if len(measured_angles) >= 2:
            for i in range(len(measured_angles)):
                angle_a = measured_angles[i]
                angle_b = measured_angles[(i + 1) % len(measured_angles)]
                dist_a = measured_points[angle_a]
                dist_b = measured_points[angle_b]

                if angle_b > angle_a:
                    steps = angle_b - angle_a
                else:
                    steps = (360 - angle_a) + angle_b

                if steps > 0 and steps < 120:
                    for step in range(1, steps):
                        t = step / steps
                        interp_dist = dist_a + t * (dist_b - dist_a)
                        interp_angle = (angle_a + step) % 360
                        ranges[interp_angle] = interp_dist

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
