#!/bin/bash

echo "Stopping EsiBot..."
sudo ~/stop.sh

echo "Building EsiBot workspace..."
cd ~/esibot_ws || exit 1

source /opt/ros/humble/setup.bash
colcon build --symlink-install
source install/setup.bash

echo "Rebuild finished."
