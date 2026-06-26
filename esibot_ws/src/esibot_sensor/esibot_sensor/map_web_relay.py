#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile, DurabilityPolicy, ReliabilityPolicy, HistoryPolicy
from nav_msgs.msg import OccupancyGrid

class MapWebRelay(Node):
    def __init__(self):
        super().__init__('map_web_relay')

        qos_sub = QoSProfile(
            history=HistoryPolicy.KEEP_LAST,
            depth=1,
            durability=DurabilityPolicy.TRANSIENT_LOCAL,
            reliability=ReliabilityPolicy.RELIABLE
        )

        qos_pub = QoSProfile(
            history=HistoryPolicy.KEEP_LAST,
            depth=1,
            durability=DurabilityPolicy.VOLATILE,
            reliability=ReliabilityPolicy.RELIABLE
        )

        self.last_map = None

        self.sub = self.create_subscription(
            OccupancyGrid,
            '/map',
            self.map_callback,
            qos_sub
        )

        self.pub = self.create_publisher(
            OccupancyGrid,
            '/map_web',
            qos_pub
        )

        self.timer = self.create_timer(1.0, self.publish_map)
        self.get_logger().info("Map Web Relay node started. Bridging /map to /map_web.")

    def map_callback(self, msg):
        self.last_map = msg
        self.get_logger().debug(f'Received map: {msg.info.width}x{msg.info.height}')

    def publish_map(self):
        if self.last_map is not None:
            self.pub.publish(self.last_map)

def main():
    rclpy.init()
    node = MapWebRelay()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.try_shutdown()

if __name__ == '__main__':
    main()
