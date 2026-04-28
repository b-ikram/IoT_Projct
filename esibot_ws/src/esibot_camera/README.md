# esibot_camera

ROS2 Python package that connects to an ESP32-CAM MJPEG stream and republishes frames as:

- `sensor_msgs/msg/Image` (`/camera/image_raw`)
- `sensor_msgs/msg/CompressedImage` (`/camera/compressed`)

## What this package does

- Opens an HTTP MJPEG stream (for example `http://esp32cam.local:81/stream`)
- Parses multipart MJPEG frames using `Content-Length`
- Decodes JPEG bytes with OpenCV
- Publishes both compressed and raw image topics
- Automatically reconnects if the stream drops

## Package structure

- `esibot_camera/esircam_node.py`: main node
- `launch/esibot_camera.launch.py`: launch file
- `config/camera_params.yaml`: default launch parameters
- `package.xml`, `setup.py`, `setup.cfg`: package metadata/build config

## Dependencies

Runtime dependencies (from `package.xml`):

- `rclpy`
- `sensor_msgs`
- `std_msgs`
- `python3-opencv`
- `python3-numpy`
- `python3-requests`
- `ament_index_python`
- `launch`
- `launch_ros`

## Build

From workspace root:

```bash
cd esibot_ws
source /opt/ros/humble/setup.bash
colcon build --packages-select esibot_camera
source install/setup.bash
```

## Run

With launch file (recommended):

```bash
ros2 launch esibot_camera esibot_camera.launch.py
```

Run node directly:

```bash
ros2 run esibot_camera esircam_node
```

## Parameters

The launch file loads `config/camera_params.yaml`.

| Parameter             | Type   | Node default                 | Value in `camera_params.yaml`     | Description                          |
| --------------------- | ------ | ---------------------------- | --------------------------------- | ------------------------------------ |
| `stream_url`          | string | `http://localhost:81/stream` | `http://esp32cam.local:81/stream` | MJPEG stream URL                     |
| `frame_id`            | string | `camera_link`                | `camera_link`                     | Frame ID set in message headers      |
| `image_topic`         | string | `/camera/image_raw`          | `/camera/image_raw`               | Raw BGR image topic                  |
| `compressed_topic`    | string | `/camera/compressed`         | `/camera/compressed`              | JPEG compressed image topic          |
| `reconnect_delay_sec` | float  | `2.0`                        | `2.0`                             | Delay before reconnect after failure |
| `read_chunk_size`     | int    | `4096`                       | `1024`                            | HTTP stream read chunk size          |
| `log_every_n_frames`  | int    | `30`                         | `30`                              | Periodic publish log interval        |

Override parameters at launch:

```bash
ros2 launch esibot_camera esibot_camera.launch.py \
  --ros-args -p stream_url:=http://192.168.1.50:81/stream
```

## Published topics

- `/camera/image_raw` (`sensor_msgs/msg/Image`)
- `/camera/compressed` (`sensor_msgs/msg/CompressedImage`)

## Quick verification

In another terminal (after sourcing workspace):

```bash
ros2 topic list | grep camera
ros2 topic hz /camera/compressed
ros2 topic echo /camera/compressed --once
```

If `rqt_image_view` is installed:

```bash
rqt_image_view
```

Select `/camera/image_raw` or `/camera/compressed`.

## Troubleshooting

1. `Cannot connect to stream`

- Check `stream_url` in `config/camera_params.yaml`.
- Verify endpoint availability: `curl -I http://esp32cam.local:81/stream`.
- If mDNS (`*.local`) is unreliable, use the camera IP address.

2. `Frequent reconnects`

- Check Wi-Fi/network stability between ROS host and ESP32-CAM.
- Confirm the endpoint is MJPEG multipart, not single-image snapshots.

3. `Topics exist but images are invalid or empty`

- Verify stream frames include valid JPEG payloads.
- Confirm multipart headers include `Content-Length`.
- Check node logs for warnings like malformed JPEG or decode failure.

4. `High CPU usage`

- Consume `/camera/compressed` when raw images are not required.
- Lower camera resolution or FPS on the ESP32-CAM side.

## Notes

- This package currently publishes both compressed and raw images from each frame.
