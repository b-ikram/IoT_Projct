#!/usr/bin/env bash
set -eo pipefail

WORKSPACE="${WORKSPACE:-$HOME/esibot_ws}"
MAP="${MAP:-$WORKSPACE/src/esibot_bringup/maps/mockup_50cm.yaml}"
INITIAL_X="${INITIAL_X:-0.0}"
INITIAL_Y="${INITIAL_Y:-0.0}"
INITIAL_YAW_Z="${INITIAL_YAW_Z:-0.0}"
INITIAL_YAW_W="${INITIAL_YAW_W:-1.0}"
GOAL_X="${GOAL_X:-1.0}"
GOAL_Y="${GOAL_Y:-0.0}"
GOAL_YAW_Z="${GOAL_YAW_Z:-0.0}"
GOAL_YAW_W="${GOAL_YAW_W:-1.0}"
START_NAV2="${START_NAV2:-1}"
WAIT_LOCALIZATION="${WAIT_LOCALIZATION:-1}"

usage() {
  cat <<EOF
Usage:
  ./scripts/test_navigation.sh [goal_x goal_y [goal_yaw_z goal_yaw_w]]

Environment overrides:
  WORKSPACE      Workspace path. Default: $HOME/esibot_ws
  MAP            Map YAML path. Default: \$WORKSPACE/src/esibot_bringup/maps/mockup_50cm.yaml
  START_NAV2     1 launches Nav2, 0 assumes Nav2 is already running. Default: 1
  WAIT_LOCALIZATION 1 waits for AMCL/map->odom TF before sending goal. Default: 1
  INITIAL_X/Y    Initial AMCL pose in map frame. Default: 0.0, 0.0
  INITIAL_YAW_Z/W Initial orientation quaternion z/w. Default: 0.0, 1.0
  GOAL_X/Y       Goal pose in map frame. Default: 1.0, 0.0
  GOAL_YAW_Z/W   Goal orientation quaternion z/w. Default: 0.0, 1.0

Examples:
  ./scripts/test_navigation.sh
  ./scripts/test_navigation.sh 0.75 0.25
  INITIAL_X=0.1 INITIAL_Y=0.1 ./scripts/test_navigation.sh 1.2 0.4
  START_NAV2=0 ./scripts/test_navigation.sh 1.0 0.0
EOF
}

if [[ "${1:-}" == "-h" || "${1:-}" == "--help" ]]; then
  usage
  exit 0
fi

if [[ $# -ge 1 ]]; then GOAL_X="$1"; fi
if [[ $# -ge 2 ]]; then GOAL_Y="$2"; fi
if [[ $# -ge 3 ]]; then GOAL_YAW_Z="$3"; fi
if [[ $# -ge 4 ]]; then GOAL_YAW_W="$4"; fi

if [[ ! -f "$WORKSPACE/install/setup.bash" ]]; then
  echo "ERROR: cannot find $WORKSPACE/install/setup.bash"
  echo "Set WORKSPACE=/path/to/esibot_ws or build the workspace first."
  exit 1
fi

if [[ ! -f "$MAP" ]]; then
  echo "ERROR: cannot find map file: $MAP"
  exit 1
fi

source /opt/ros/humble/setup.bash
source "$WORKSPACE/install/setup.bash"
set -u

cleanup() {
  if [[ -n "${NAV2_PID:-}" ]]; then
    echo "Stopping Nav2 launch..."
    kill "$NAV2_PID" 2>/dev/null || true
    wait "$NAV2_PID" 2>/dev/null || true
  fi
}
trap cleanup EXIT

if [[ "$START_NAV2" == "1" ]]; then
  echo "Launching Nav2 with map: $MAP"
  ros2 launch esibot_bringup nav2.launch.py map:="$MAP" use_sim_time:=false use_composition:=False &
  NAV2_PID=$!
  echo "Waiting for Nav2 action server..."
else
  echo "Using already-running Nav2."
fi

for attempt in $(seq 1 60); do
  if ros2 action list | grep -qx "/navigate_to_pose"; then
    break
  fi

  if [[ "$attempt" -eq 60 ]]; then
    echo "ERROR: /navigate_to_pose action server did not appear after 60 seconds."
    echo "Current nodes:"
    ros2 node list || true
    echo "Current actions:"
    ros2 action list || true
    echo "Check the controller_server log above; Nav2 did not finish starting."
    exit 1
  fi

  sleep 1
done

echo "Publishing initial pose: x=$INITIAL_X y=$INITIAL_Y"
ros2 topic pub --once /initialpose geometry_msgs/msg/PoseWithCovarianceStamped "{
  header: {frame_id: 'map'},
  pose: {
    pose: {
      position: {x: $INITIAL_X, y: $INITIAL_Y, z: 0.0},
      orientation: {x: 0.0, y: 0.0, z: $INITIAL_YAW_Z, w: $INITIAL_YAW_W}
    },
    covariance: [
      0.25, 0.0, 0.0, 0.0, 0.0, 0.0,
      0.0, 0.25, 0.0, 0.0, 0.0, 0.0,
      0.0, 0.0, 0.0, 0.0, 0.0, 0.0,
      0.0, 0.0, 0.0, 0.0, 0.0, 0.0,
      0.0, 0.0, 0.0, 0.0, 0.0, 0.0,
      0.0, 0.0, 0.0, 0.0, 0.0, 0.0685
    ]
  }
}"

if [[ "$WAIT_LOCALIZATION" == "1" ]]; then
  echo "Waiting for localization transform map -> base_footprint..."
  for attempt in $(seq 1 30); do
    if ros2 run tf2_ros tf2_echo map base_footprint --once >/dev/null 2>&1; then
      break
    fi

    if [[ "$attempt" -eq 30 ]]; then
      echo "ERROR: localization transform map -> base_footprint is not available."
      echo "AMCL probably has not accepted the initial pose, or TF odom -> base_footprint is missing."
      echo "Check: ros2 topic echo --once /amcl_pose"
      echo "Check: ros2 run tf2_ros tf2_echo odom base_footprint"
      exit 1
    fi

    sleep 1
  done
else
  sleep 2
fi

echo "Lifecycle states:"
for node in map_server amcl planner_server controller_server bt_navigator behavior_server waypoint_follower; do
  ros2 lifecycle get "/$node" 2>/dev/null || true
done

echo "Sending navigation goal: x=$GOAL_X y=$GOAL_Y"
ros2 action send_goal /navigate_to_pose nav2_msgs/action/NavigateToPose "{
  pose: {
    header: {frame_id: 'map'},
    pose: {
      position: {x: $GOAL_X, y: $GOAL_Y, z: 0.0},
      orientation: {x: 0.0, y: 0.0, z: $GOAL_YAW_Z, w: $GOAL_YAW_W}
    }
  }
}" --feedback
