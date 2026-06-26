#!/bin/bash

source /opt/ros/humble/setup.bash
source ~/esibot_ws/install/setup.bash

rm -f /tmp/esibot_shutdown

LOG_DIR=~/camera_logs
mkdir -p $LOG_DIR

echo "Starting Camera and Vision..."

pkill -f camera_node
pkill -f camera_ros
pkill -f vision_node.py

sleep 2

echo "Starting camera node..."
cd ~/esibot_ws
nohup ros2 launch esibot_camera raspicam.launch.py \
  > $LOG_DIR/camera.log 2>&1 &

sleep 5

echo "Starting vision node..."
cd ~/esibot_ws/src/esibot_vision/esibot_vision
nohup python3 vision_node.py \
  > $LOG_DIR/vision.log 2>&1 &

sleep 2

echo "Camera and Vision launched."
echo "Camera log: $LOG_DIR/camera.log"
echo "Vision log: $LOG_DIR/vision.log"
