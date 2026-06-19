#!/usr/bin/env python3

import time
import threading
import re

import requests
import cv2
import numpy as np

import rclpy
from rclpy.node import Node

from sensor_msgs.msg import Image, CompressedImage


class EsiRCamNode(Node):
    def __init__(self):
        super().__init__("esircam_node")

        # -----------------------
        # Parameters
        # -----------------------
        self.declare_parameter("stream_url", "http://localhost:81/stream")
        self.declare_parameter("frame_id", "camera_link")
        self.declare_parameter("image_topic", "/camera/image_raw")
        self.declare_parameter("compressed_topic", "/camera/compressed")
        self.declare_parameter("reconnect_delay_sec", 2.0)
        self.declare_parameter("read_chunk_size", 4096)
        self.declare_parameter("log_every_n_frames", 30)

        self.stream_url = self.get_parameter("stream_url").value
        self.frame_id = self.get_parameter("frame_id").value
        self.image_topic = self.get_parameter("image_topic").value
        self.compressed_topic = self.get_parameter("compressed_topic").value
        self.reconnect_delay_sec = float(self.get_parameter("reconnect_delay_sec").value)
        self.read_chunk_size = int(self.get_parameter("read_chunk_size").value)
        self.log_every_n_frames = int(self.get_parameter("log_every_n_frames").value)

        # -----------------------
        # Publishers
        # -----------------------
        self.image_pub = self.create_publisher(Image, self.image_topic, 10)
        self.compressed_pub = self.create_publisher(CompressedImage, self.compressed_topic, 10)

        # -----------------------
        # Internal state
        # -----------------------
        self.frame_count = 0
        self.running = True

        self.get_logger().info("esircam_node started")
        self.get_logger().info(f"stream_url={self.stream_url}")
        self.get_logger().info(f"image_topic={self.image_topic}")
        self.get_logger().info(f"compressed_topic={self.compressed_topic}")

        # Read stream in background thread.
        # This avoids blocking the ROS executor.
        self.worker_thread = threading.Thread(target=self._stream_worker, daemon=True)
        self.worker_thread.start()

    def _stream_worker(self):
        while rclpy.ok() and self.running:
            try:
                self.get_logger().info(f"Connecting to MJPEG stream: {self.stream_url}")

                response = requests.get(
                    self.stream_url,
                    stream=True,
                    timeout=(5, 10),
                    headers={"User-Agent": "esibot-camera-node"},
                )

                self.get_logger().info(f"HTTP status: {response.status_code}")
                self.get_logger().info(f"Content-Type: {response.headers.get('Content-Type')}")

                if response.status_code != 200:
                    raise RuntimeError(f"Bad HTTP status: {response.status_code}")

                self.get_logger().info("Connected to camera stream")

                self._read_mjpeg_stream(response)

            except Exception as exc:
                if self.running:
                    self.get_logger().warn(
                        f"Stream failed: {exc}. Reconnecting in {self.reconnect_delay_sec:.1f}s"
                    )
                    time.sleep(self.reconnect_delay_sec)

    def _read_mjpeg_stream(self, response):
        """
        Read MJPEG stream.

        Your ESP32 stream format is:

            --frame
            Content-Type: image/jpeg
            Content-Length: NNNN

            JPEG_BYTES

        So we parse using Content-Length instead of relying only on JPEG end markers.
        """

        buffer = b""

        for chunk in response.iter_content(chunk_size=self.read_chunk_size):
            if not self.running or not rclpy.ok():
                break

            if not chunk:
                continue

            buffer += chunk

            while True:
                jpeg_bytes, buffer = self._extract_jpeg_by_content_length(buffer)

                if jpeg_bytes is None:
                    # Prevent unlimited memory growth if parsing gets stuck.
                    if len(buffer) > 1_000_000:
                        self.get_logger().warn("MJPEG buffer too large, trimming")
                        buffer = buffer[-300_000:]
                    break

                self._handle_jpeg(jpeg_bytes)

    def _extract_jpeg_by_content_length(self, buffer):
        """
        Extract exactly one JPEG frame from the multipart MJPEG buffer.

        Returns:
            jpeg_bytes, remaining_buffer
        """

        boundary_pos = buffer.find(b"--frame")
        if boundary_pos == -1:
            return None, buffer

        # Remove garbage before boundary.
        if boundary_pos > 0:
            buffer = buffer[boundary_pos:]

        header_end = buffer.find(b"\r\n\r\n")
        separator_len = 4

        if header_end == -1:
            # Some streams may use LF only, but your dump showed CRLF.
            header_end = buffer.find(b"\n\n")
            separator_len = 2

        if header_end == -1:
            return None, buffer

        header = buffer[:header_end].decode(errors="ignore")

        match = re.search(r"Content-Length:\s*(\d+)", header, re.IGNORECASE)
        if not match:
            # Bad header; discard this boundary and search for next one.
            next_boundary = buffer.find(b"--frame", len(b"--frame"))
            if next_boundary == -1:
                return None, buffer
            return None, buffer[next_boundary:]

        jpeg_len = int(match.group(1))
        jpeg_start = header_end + separator_len
        jpeg_end = jpeg_start + jpeg_len

        if len(buffer) < jpeg_end:
            return None, buffer

        jpeg_bytes = buffer[jpeg_start:jpeg_end]
        remaining = buffer[jpeg_end:]

        return jpeg_bytes, remaining

    def _handle_jpeg(self, jpeg_bytes):
        if len(jpeg_bytes) < 4:
            self.get_logger().warn("JPEG too small, skipping")
            return

        if not jpeg_bytes.startswith(b"\xff\xd8"):
            self.get_logger().warn("JPEG does not start with FFD8, skipping")
            return

        # Decode JPEG to OpenCV BGR image.
        np_arr = np.frombuffer(jpeg_bytes, dtype=np.uint8)
        frame = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)

        if frame is None:
            self.get_logger().warn(f"JPEG decode failed, bytes={len(jpeg_bytes)}")
            return

        stamp = self.get_clock().now().to_msg()

        self.publish_compressed_image(jpeg_bytes, stamp)
        self.publish_raw_image(frame, stamp)

        self.frame_count += 1

        if self.frame_count % self.log_every_n_frames == 0:
            self.get_logger().info(
                f"Published {self.frame_count} frames, shape={frame.shape}, jpg_bytes={len(jpeg_bytes)}"
            )

    def publish_compressed_image(self, jpeg_bytes, stamp):
        msg = CompressedImage()
        msg.header.stamp = stamp
        msg.header.frame_id = self.frame_id
        msg.format = "jpeg"
        msg.data = jpeg_bytes

        self.compressed_pub.publish(msg)

    def publish_raw_image(self, frame, stamp):
        height, width = frame.shape[:2]

        msg = Image()
        msg.header.stamp = stamp
        msg.header.frame_id = self.frame_id
        msg.height = height
        msg.width = width
        msg.encoding = "bgr8"
        msg.is_bigendian = False
        msg.step = width * 3
        msg.data = frame.tobytes()

        self.image_pub.publish(msg)

    def stop(self):
        self.running = False


def main(args=None):
    rclpy.init(args=args)

    node = EsiRCamNode()

    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.stop()
        node.destroy_node()

        if rclpy.ok():
            rclpy.shutdown()


if __name__ == "__main__":
    main()
