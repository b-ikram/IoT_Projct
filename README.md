# ESIBOT ROS2 Workspace

Brief description:
This project contains a ROS2 Python package (`esibot_bringup`) for running an ESIBOT driver node. The node forwards velocity commands, republishes odometry, and publishes battery state for Gazebo-based testing.

## Project structure
- `esibot_ws/`: ROS2 workspace root
- `esibot_ws/src/esibot_bringup/`: package source

## Requirements (inside ROS2 VM)
- ROS2 installed (with `colcon`)
- Python dependencies available through ROS2 packages

## Build and run
Open a terminal in the ROS2 VM and run:

```bash
cd ~/esibot_ws
export ROS_DOMAIN_ID=10
source /opt/ros/humble/setup.bash
colcon build --packages-select esibot_bringup
source install/setup.bash
```


Run the node with launch file:

```bash
ros2 launch esibot_bringup esibot_driver.launch.py
```

## Testing the node
List node and topics in another sourced terminal:

```bash
export ROS_DOMAIN_ID=10
ros2 node list
ros2 topic list
```
