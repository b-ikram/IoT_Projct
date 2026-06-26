#!/bin/bash

echo "Stopping EsiBot nodes, except rosbridge..."

touch /tmp/esibot_shutdown

pkill -f esibot_driver
pkill -f radar_node
pkill -f scan_converter
pkill -f slam_toolbox
pkill -f map_web_relay
pkill -f camera_node
pkill -f camera_ros
pkill -f vision_node.py
pkill -f ekf
pkill -f robot_localization
pkill -f controller_server
pkill -f planner_server
pkill -f behavior_server
pkill -f bt_navigator
pkill -f waypoint_follower
pkill -f velocity_smoother
pkill -f map_server
pkill -f lifecycle_manager

echo "EsiBot stopped. Rosbridge is still running."
