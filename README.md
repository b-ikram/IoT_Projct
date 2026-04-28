# ESIBOT ROS2 Workspace

Monorepo for ESIBOT ROS2 packages (bringup, sensors, camera) under one workspace.

## Repository layout
- `esibot_ws/`: ROS2 workspace root
- `esibot_ws/src/esibot_bringup/`: robot driver, odometry, battery publishing
- `esibot_ws/src/esibot_sensors/`: radar node and RViz launch/config
- `esibot_ws/src/esibot_camera/`: ESP32-CAM MJPEG bridge
- `esibot_ws/src/esibot_description/`: placeholder/incomplete package directory
- `esibot_ws/src/esibot_ui/`: placeholder/incomplete package directory
- `esibot_ws/src/esibot_vision/`: placeholder/incomplete package directory

## Prerequisites
- ROS2 (tested layout for Humble)
- `colcon`
- Python dependencies from ROS packages used by each node:
- `python3-serial`
- `python3-opencv`
- `python3-numpy`
- `python3-requests`
- `python3-gpiozero`
- `rviz2`

## Build
From repository root:

```bash
cd esibot_ws
source /opt/ros/humble/setup.bash
export ROS_DOMAIN_ID=10
colcon build
source install/setup.bash
```

Build a single package:

```bash
colcon build --packages-select esibot_bringup
```

## Run packages
Driver:

```bash
ros2 launch esibot_bringup esibot_driver.launch.py
```

Camera bridge:

```bash
ros2 launch esibot_camera esibot_camera.launch.py
```

Radar (with RViz by default):

```bash
ros2 launch esibot_sensors radar.launch.py
```

Radar without RViz:

```bash
ros2 launch esibot_sensors radar.launch.py use_rviz:=false
```

## Verify runtime
In another sourced terminal:

```bash
export ROS_DOMAIN_ID=10
source /opt/ros/humble/setup.bash
cd esibot_ws
source install/setup.bash
ros2 node list
ros2 topic list
```

## Notes
- Generated ROS artifacts (`build/`, `install/`, `log/`, caches) are ignored by git at the repo root.
- `esibot_description`, `esibot_ui`, and `esibot_vision` currently contain placeholders and are not fully packaged yet.
