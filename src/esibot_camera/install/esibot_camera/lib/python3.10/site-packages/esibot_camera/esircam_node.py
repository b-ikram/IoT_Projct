#!/usr/bin/env python3

import time
import urllib.request
import urllib.error

import rclpy
from rclpy.node import Node

from sensor_msgs.msg import Image, CompressedImage


class EsiRCamNode(Node):
    def __init__(self):
        super().__init__("esircam_node")

        # Parameters
        self.declare_parameter("stream_url", "http://192.168.4.1:81/stream")
        self.declare_parameter("frame_id", "camera_link")
        self.declare_parameter("image_topic", "/camera/image_raw")
        self.declare_parameter("compressed_topic", "/camera/compressed")
        self.declare_parameter("reconnect_delay_sec", 2.0)
        self.declare_parameter("read_chunk_size", 1024)
        self.declare_parameter("log_every_n_frames", 30)

        self.stream_url = self.get_parameter("stream_url").value
        self.frame_id = self.get_parameter("frame_id").value
        self.image_topic = self.get_parameter("image_topic").value
        self.compressed_topic = self.get_parameter("compressed_topic").value
        self.reconnect_delay_sec = self.get_parameter("reconnect_delay_sec").value
        self.read_chunk_size = self.get_parameter("read_chunk_size").value
        self.log_every_n_frames = self.get_parameter("log_every_n_frames").value

        # Publishers
        self.image_pub = self.create_publisher(Image, self.image_topic, 10)
        self.compressed_pub = self.create_publisher(CompressedImage, self.compressed_topic, 10)

        # Internal state
        self.stream = None
        self.connected = False
        self.buffer = b""
        self.frame_count = 0

        # Timer loop
        self.timer = self.create_timer(0.1, self._spin_once)

        self.get_logger().info("esircam_node started")
        self.get_logger().info(f"stream_url={self.stream_url}")
        self.get_logger().info(f"image_topic={self.image_topic}")
        self.get_logger().info(f"compressed_topic={self.compressed_topic}")

    def _spin_once(self):
        """
        Main loop step:
        1. connect if needed
        2. read bytes from stream
        3. extract JPEG frame
        4. publish compressed/raw topics
        """
        if not self.connected:
            self._connect_stream()
            return

        try:
            jpeg_bytes = self._read_next_jpeg()
            if jpeg_bytes is None:
                return

            self.frame_count += 1

            self.publish_compressed_image(jpeg_bytes)

            # Raw image publication will be added next step
            # once we wire OpenCV decoding
            # self.publish_raw_image(decoded_frame)

            if self.frame_count % self.log_every_n_frames == 0:
                self.get_logger().info(f"Received {self.frame_count} frames")

        except Exception as exc:
            self.get_logger().warn(f"Stream read failed: {exc}")
            self._disconnect_stream()

    def _connect_stream(self):
        try:
            self.get_logger().info(f"Connecting to MJPEG stream: {self.stream_url}")
            request = urllib.request.Request(
                self.stream_url,
                headers={"User-Agent": "esibot-camera-node"}
            )
            self.stream = urllib.request.urlopen(request, timeout=5)
            self.connected = True
            self.buffer = b""
            self.get_logger().info("Connected to camera stream")
        except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, Exception) as exc:
            self.connected = False
            self.stream = None
            self.get_logger().warn(
                f"Connection failed: {exc}. Retrying in {self.reconnect_delay_sec:.1f}s"
            )
            time.sleep(self.reconnect_delay_sec)

    def _disconnect_stream(self):
        if self.stream is not None:
            try:
                self.stream.close()
            except Exception:
                pass
        self.stream = None
        self.connected = False
        self.buffer = b""

    def _read_next_jpeg(self):
        """
        Reads MJPEG byte stream until one full JPEG frame is found.

        JPEG start marker: FFD8
        JPEG end marker:   FFD9
        """
        chunk = self.stream.read(self.read_chunk_size)
        if not chunk:
            raise RuntimeError("Empty chunk from stream")

        self.buffer += chunk

        start = self.buffer.find(b"\xff\xd8")
        end = self.buffer.find(b"\xff\xd9")

        if start != -1 and end != -1 and end > start:
            jpeg_bytes = self.buffer[start:end + 2]
            self.buffer = self.buffer[end + 2:]
            return jpeg_bytes

        return None

    def publish_compressed_image(self, jpeg_bytes):
        msg = CompressedImage()
        msg.header.stamp = self.get_clock().now().to_msg()
        msg.header.frame_id = self.frame_id
        msg.format = "jpeg"
        msg.data = jpeg_bytes
        self.compressed_pub.publish(msg)

    def publish_raw_image(self, frame):
        """
        Placeholder for next step.
        Here we will convert an OpenCV BGR frame into sensor_msgs/Image.
        """
        raise NotImplementedError("Raw image publishing not implemented yet")


def main(args=None):
    rclpy.init(args=args)
    node = EsiRCamNode()

    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node._disconnect_stream()
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
