#!/bin/bash

source /opt/ros/humble/setup.bash
source /home/user/esibot_ws/install/setup.bash

rm -f /tmp/esibot_shutdown

LOG_DIR=/home/user/slam_logs
mkdir -p "$LOG_DIR"

echo "===================================="
echo "Starting EsiBot EKF + SLAM stack..."
echo "===================================="

echo ""
echo "[1/4] Starting pigpio..."
sudo pigpiod 2>/dev/null || true

echo ""
echo "[2/4] Starting EKF pipeline..."
echo " (driver + sensors + odometry + EKF)"
nohup ros2 launch esibot_bringup esibot_ekf.launch.py > "$LOG_DIR/ekf_pipeline.log" 2>&1 &

sleep 6

echo ""
echo "[3/4] Starting SLAM toolbox..."
nohup ros2 launch slam_toolbox online_async_launch.py slam_params_file:=/home/user/esibot_ws/install/esibot_sensor/share/esibot_sensor/config/slam_params.yaml use_sim_time:=false > "$LOG_DIR/slam_toolbox.log" 2>&1 &

sleep 3

echo ""
echo "[4/4] Starting map_web_relay..."
pkill -f map_web_relay
nohup ros2 run esibot_sensor map_web_relay > "$LOG_DIR/map_web_relay.log" 2>&1 &

sleep 2

echo ""
echo "===================================="
echo "ESIBOT EKF + SLAM STACK STARTED"
echo ""
echo "Logs:"
echo " $LOG_DIR/ekf_pipeline.log"
echo " $LOG_DIR/slam_toolbox.log"
echo " $LOG_DIR/map_web_relay.log"
echo ""
echo "Check:"
echo " ros2 node list | grep -E 'slam|map_web|ekf|radar|scan|imu|encoder|odom|driver'"
echo " ros2 topic list | grep -E 'scan|map|odom|imu|encoder'"
echo "===================================="
