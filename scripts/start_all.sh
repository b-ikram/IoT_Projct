#!/bin/bash

source /opt/ros/humble/setup.bash
source ~/esibot_ws/install/setup.bash

rm -f /tmp/esibot_shutdown

echo "Starting full EsiBot stack..."

echo "1) Checking rosbridge..."
if sudo lsof -i :9090 >/dev/null 2>&1; then
  echo "Rosbridge already running."
else
  echo "Rosbridge is not running. Start it from the dashboard Start button or manually."
fi

echo "2) Starting SLAM stack..."
~/start_slam.sh &

sleep 5

echo "3) Starting camera and vision..."
~/start_camera.sh &

echo "EsiBot start_all launched."
