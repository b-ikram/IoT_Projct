#!/usr/bin/env bash
set -euo pipefail

# Demo sequence for cmd_vel
# Requires: ros2 environment sourced and driver running

echo "[demo] Forward"
ros2 topic pub --once /cmd_vel geometry_msgs/Twist "{linear: {x: 0.2}, angular: {z: 0.0}}"
sleep 2

echo "[demo] Backward"
ros2 topic pub --once /cmd_vel geometry_msgs/Twist "{linear: {x: -0.2}, angular: {z: 0.0}}"
sleep 2

echo "[demo] Rotate right"
ros2 topic pub --once /cmd_vel geometry_msgs/Twist "{linear: {x: 0.0}, angular: {z: -0.3}}"
sleep 2


echo "[demo] Rotate left"
ros2 topic pub --once /cmd_vel geometry_msgs/Twist "{linear: {x: 0.0}, angular: {z: 0.3}}"
sleep 2


echo "[demo] Stop"
ros2 topic pub --once /cmd_vel geometry_msgs/Twist "{linear: {x: 0.0}, angular: {z: 0.0}}"
