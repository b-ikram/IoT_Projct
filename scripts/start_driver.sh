#!/bin/bash

source /opt/ros/humble/setup.bash
source ~/esibot_ws/install/setup.bash

rm -f /tmp/esibot_shutdown

LOG_DIR=~/driver_logs
mkdir -p $LOG_DIR

echo "Starting EsiBot driver..."

nohup ros2 run esibot_bringup esibot_driver \
  > $LOG_DIR/driver.log 2>&1 &

sleep 1

echo "EsiBot driver launched."
echo "Log: $LOG_DIR/driver.log"
