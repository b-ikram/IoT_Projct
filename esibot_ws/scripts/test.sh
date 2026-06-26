#!/usr/bin/env bash
set -eo pipefail

# Isolated Nav2 smoke test for ESIBOT.
# Run this script from any directory. Runtime files and logs go under /tmp.

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DEFAULT_WS="$(cd "$SCRIPT_DIR/.." && pwd)"

ESIBOT_WS="${ESIBOT_WS:-$DEFAULT_WS}"
TEST_ROOT="${TEST_ROOT:-/tmp/esibot_nav_isolated}"
TEST_NS="${TEST_NS:-esibot_nav_test}"
MAP="${MAP:-$ESIBOT_WS/src/esibot_bringup/maps/mockup_50cm.yaml}"
PARAMS="${PARAMS:-$ESIBOT_WS/src/esibot_bringup/config/nav2_params.yaml}"
USE_SIM_TIME="${USE_SIM_TIME:-false}"
USE_REAL_ODOM="${USE_REAL_ODOM:-1}"

INITIAL_X="${INITIAL_X:-0.0}"
INITIAL_Y="${INITIAL_Y:-0.0}"
INITIAL_YAW="${INITIAL_YAW:-0.0}"

GOAL_X="${GOAL_X:-0.75}"
GOAL_Y="${GOAL_Y:-0.0}"
GOAL_YAW="${GOAL_YAW:-0.0}"

ACTION_TIMEOUT_SEC="${ACTION_TIMEOUT_SEC:-45}"
CMD_VEL_TIMEOUT_SEC="${CMD_VEL_TIMEOUT_SEC:-20}"

usage() {
  cat <<EOF
Usage:
  ESIBOT_WS=/path/to/esibot_ws $0 [goal_x goal_y [goal_yaw]]

What this tests:
  - Loads the preloaded map from esibot_bringup/maps/mockup_50cm.yaml
  - Starts Nav2 without launching ESIBOT hardware drivers
  - Runs test topics under /\$TEST_NS so existing robot topics stay untouched
  - Uses real /odom by default, while keeping scan/initialpose/cmd_vel namespaced
  - Sends a NavigateToPose goal
  - Verifies Nav2 produces /\$TEST_NS/cmd_vel

Environment overrides:
  ESIBOT_WS             Built workspace path. Default: parent of this script
  TEST_NS               ROS namespace for test topics. Default: esibot_nav_test
  USE_REAL_ODOM         1 uses real /odom and real odom TF. 0 publishes fake isolated odom. Default: 1
  MAP                   Map yaml. Default: \$ESIBOT_WS/src/esibot_bringup/maps/mockup_50cm.yaml
  PARAMS                Nav2 params. Default: \$ESIBOT_WS/src/esibot_bringup/config/nav2_params.yaml
  TEST_ROOT             Isolated runtime/log directory. Default: /tmp/esibot_nav_isolated
  INITIAL_X/Y/YAW       Initial robot pose in map frame. Default: 0, 0, 0
  GOAL_X/Y/YAW          Goal pose in map frame. Default: 0.75, 0, 0
  ACTION_TIMEOUT_SEC    Max seconds to wait for action feedback. Default: 45
  CMD_VEL_TIMEOUT_SEC   Max seconds to wait for /cmd_vel. Default: 20

Examples:
  /tmp/esibot_nav_isolated/test_navigation_isolated.sh
  ESIBOT_WS=/home/user/esibot_ws /tmp/esibot_nav_isolated/test_navigation_isolated.sh 0.5 0.2
EOF
}

if [[ "${1:-}" == "-h" || "${1:-}" == "--help" ]]; then
  usage
  exit 0
fi

if [[ $# -ge 1 ]]; then GOAL_X="$1"; fi
if [[ $# -ge 2 ]]; then GOAL_Y="$2"; fi
if [[ $# -ge 3 ]]; then GOAL_YAW="$3"; fi

if [[ ! -f /opt/ros/humble/setup.bash ]]; then
  echo "ERROR: ROS 2 Humble setup not found at /opt/ros/humble/setup.bash"
  exit 1
fi

if [[ ! -f "$ESIBOT_WS/install/setup.bash" ]]; then
  echo "ERROR: cannot find workspace overlay: $ESIBOT_WS/install/setup.bash"
  echo "Set ESIBOT_WS=/path/to/esibot_ws and build the workspace first."
  exit 1
fi

if [[ ! -f "$MAP" ]]; then
  echo "ERROR: cannot find map file: $MAP"
  exit 1
fi

if [[ ! -f "$PARAMS" ]]; then
  echo "ERROR: cannot find Nav2 params file: $PARAMS"
  exit 1
fi

mkdir -p "$TEST_ROOT"
RUN_DIR="$(mktemp -d "$TEST_ROOT/run.XXXXXX")"
LOG_DIR="$RUN_DIR/log"
mkdir -p "$LOG_DIR"

cleanup() {
  set +e
  if [[ -n "${GOAL_PID:-}" ]]; then kill "$GOAL_PID" 2>/dev/null; fi
  if [[ -n "${CMD_PID:-}" ]]; then kill "$CMD_PID" 2>/dev/null; fi
  if [[ -n "${FAKE_PID:-}" ]]; then kill "$FAKE_PID" 2>/dev/null; fi
  if [[ -n "${NAV2_PID:-}" ]]; then kill "$NAV2_PID" 2>/dev/null; fi
  wait 2>/dev/null
}
trap cleanup EXIT

source /opt/ros/humble/setup.bash
source "$ESIBOT_WS/install/setup.bash"
set -u

TEST_NS="${TEST_NS#/}"
TEST_NS="${TEST_NS%/}"
TEST_NS_ABS="/$TEST_NS"
MAP_FRAME="${MAP_FRAME:-${TEST_NS}_map}"
ODOM_FRAME="${ODOM_FRAME:-${TEST_NS}_odom}"
BASE_FRAME="${BASE_FRAME:-${TEST_NS}_base_footprint}"
LASER_FRAME="${LASER_FRAME:-${TEST_NS}_laser}"

if [[ "$USE_REAL_ODOM" == "1" ]]; then
  ODOM_TOPIC="/odom"
  ODOM_FRAME="${REAL_ODOM_FRAME:-odom}"
  BASE_FRAME="${REAL_BASE_FRAME:-base_footprint}"
else
  ODOM_TOPIC="odom"
fi

TEST_PARAMS="$RUN_DIR/nav2_params.namespaced.yaml"
sed \
  -e 's#scan_topic: /scan#scan_topic: scan#g' \
  -e 's#topic: /scan#topic: scan#g' \
  -e 's#yaml_filename: .*#yaml_filename: '"$MAP"'\n    frame_id: '"$MAP_FRAME"'#g' \
  -e 's#base_frame_id: .*#base_frame_id: '"$BASE_FRAME"'#g' \
  -e 's#odom_frame_id: .*#odom_frame_id: '"$ODOM_FRAME"'#g' \
  -e 's#global_frame_id: .*#global_frame_id: '"$MAP_FRAME"'#g' \
  -e 's#global_frame: odom#global_frame: '"$ODOM_FRAME"'#g' \
  -e 's#global_frame: map#global_frame: '"$MAP_FRAME"'#g' \
  -e 's#robot_base_frame: .*#robot_base_frame: '"$BASE_FRAME"'#g' \
  "$PARAMS" > "$TEST_PARAMS"

awk -v odom_topic="$ODOM_TOPIC" '
  { print }
  $0 == "controller_server:" { in_controller = 1; next }
  in_controller && $0 == "  ros__parameters:" {
    print "    odom_topic: " odom_topic
    in_controller = 0
  }
' "$TEST_PARAMS" > "$TEST_PARAMS.tmp"
mv "$TEST_PARAMS.tmp" "$TEST_PARAMS"

cat > "$RUN_DIR/fake_robot.py" <<'PY'
#!/usr/bin/env python3
import math

import rclpy
from rclpy.node import Node
from geometry_msgs.msg import TransformStamped
from nav_msgs.msg import Odometry
from sensor_msgs.msg import LaserScan
from tf2_ros import TransformBroadcaster, StaticTransformBroadcaster


class FakeRobot(Node):
    def __init__(self):
        super().__init__("esibot_fake_robot")
        self.declare_parameter("initial_x", 0.0)
        self.declare_parameter("initial_y", 0.0)
        self.declare_parameter("initial_yaw", 0.0)
        self.declare_parameter("odom_frame", "odom")
        self.declare_parameter("base_frame", "base_footprint")
        self.declare_parameter("laser_frame", "laser")
        self.declare_parameter("publish_odom", True)

        self.x = float(self.get_parameter("initial_x").value)
        self.y = float(self.get_parameter("initial_y").value)
        self.yaw = float(self.get_parameter("initial_yaw").value)
        self.odom_frame = str(self.get_parameter("odom_frame").value)
        self.base_frame = str(self.get_parameter("base_frame").value)
        self.laser_frame = str(self.get_parameter("laser_frame").value)
        self.publish_odom = bool(self.get_parameter("publish_odom").value)

        self.odom_pub = self.create_publisher(Odometry, "odom", 10)
        self.scan_pub = self.create_publisher(LaserScan, "scan", 10)
        self.tf_pub = TransformBroadcaster(self)
        self.static_tf_pub = StaticTransformBroadcaster(self)
        self.publish_static_transforms()
        self.create_timer(0.05, self.tick)

    def quat(self, yaw):
        return (0.0, 0.0, math.sin(yaw / 2.0), math.cos(yaw / 2.0))

    def publish_static_transforms(self):
        now = self.get_clock().now().to_msg()

        base_to_scan = TransformStamped()
        base_to_scan.header.stamp = now
        base_to_scan.header.frame_id = self.base_frame
        base_to_scan.child_frame_id = self.laser_frame
        base_to_scan.transform.translation.x = 0.05
        base_to_scan.transform.translation.z = 0.05
        base_to_scan.transform.rotation.w = 1.0

        self.static_tf_pub.sendTransform(base_to_scan)

    def tick(self):
        now = self.get_clock().now().to_msg()
        qx, qy, qz, qw = self.quat(self.yaw)

        if self.publish_odom:
            tf = TransformStamped()
            tf.header.stamp = now
            tf.header.frame_id = self.odom_frame
            tf.child_frame_id = self.base_frame
            tf.transform.translation.x = self.x
            tf.transform.translation.y = self.y
            tf.transform.rotation.x = qx
            tf.transform.rotation.y = qy
            tf.transform.rotation.z = qz
            tf.transform.rotation.w = qw
            self.tf_pub.sendTransform(tf)

            odom = Odometry()
            odom.header.stamp = now
            odom.header.frame_id = self.odom_frame
            odom.child_frame_id = self.base_frame
            odom.pose.pose.position.x = self.x
            odom.pose.pose.position.y = self.y
            odom.pose.pose.orientation.x = qx
            odom.pose.pose.orientation.y = qy
            odom.pose.pose.orientation.z = qz
            odom.pose.pose.orientation.w = qw
            self.odom_pub.publish(odom)

        scan = LaserScan()
        scan.header.stamp = now
        scan.header.frame_id = self.laser_frame
        scan.angle_min = -math.pi
        scan.angle_max = math.pi
        scan.angle_increment = math.pi / 180.0
        scan.time_increment = 0.0
        scan.scan_time = 0.05
        scan.range_min = 0.08
        scan.range_max = 8.0
        scan.ranges = [8.0] * 361
        self.scan_pub.publish(scan)


def main():
    rclpy.init()
    node = FakeRobot()
    try:
        rclpy.spin(node)
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
PY
chmod +x "$RUN_DIR/fake_robot.py"

yaw_to_quat_z() {
  python3 -c "import math; print(math.sin(float('$1') / 2.0))"
}

yaw_to_quat_w() {
  python3 -c "import math; print(math.cos(float('$1') / 2.0))"
}

INITIAL_QZ="$(yaw_to_quat_z "$INITIAL_YAW")"
INITIAL_QW="$(yaw_to_quat_w "$INITIAL_YAW")"
GOAL_QZ="$(yaw_to_quat_z "$GOAL_YAW")"
GOAL_QW="$(yaw_to_quat_w "$GOAL_YAW")"

echo "Isolated Nav2 test directory: $RUN_DIR"
echo "Test namespace: $TEST_NS_ABS"
echo "Odom mode: $([[ "$USE_REAL_ODOM" == "1" ]] && echo "real /odom" || echo "fake isolated odom")"
echo "Test frames: $MAP_FRAME, $ODOM_FRAME, $BASE_FRAME, $LASER_FRAME"
echo "Workspace overlay: $ESIBOT_WS/install/setup.bash"
echo "Map: $MAP"
echo "Params copy: $TEST_PARAMS"

ROS_LOG_DIR="$LOG_DIR/fake_robot" "$RUN_DIR/fake_robot.py" \
  --ros-args \
  -r __ns:="$TEST_NS_ABS" \
  -p initial_x:="$INITIAL_X" \
  -p initial_y:="$INITIAL_Y" \
  -p initial_yaw:="$INITIAL_YAW" \
  -p odom_frame:="$ODOM_FRAME" \
  -p base_frame:="$BASE_FRAME" \
  -p laser_frame:="$LASER_FRAME" \
  -p publish_odom:="$([[ "$USE_REAL_ODOM" == "1" ]] && echo false || echo true)" \
  > "$LOG_DIR/fake_robot.log" 2>&1 &
FAKE_PID=$!

ROS_LOG_DIR="$LOG_DIR/nav2" ros2 launch nav2_bringup bringup_launch.py \
  namespace:="$TEST_NS" \
  use_namespace:=True \
  slam:=False \
  map:="$MAP" \
  params_file:="$TEST_PARAMS" \
  use_sim_time:="$USE_SIM_TIME" \
  autostart:=true \
  use_composition:=False \
  > "$LOG_DIR/nav2.log" 2>&1 &
NAV2_PID=$!

echo "Waiting for $TEST_NS_ABS/navigate_to_pose action server..."
for attempt in $(seq 1 90); do
  if ros2 action list 2>/dev/null | grep -qx "$TEST_NS_ABS/navigate_to_pose"; then
    break
  fi
  if [[ "$attempt" -eq 90 ]]; then
    echo "ERROR: $TEST_NS_ABS/navigate_to_pose did not appear."
    echo "Nav2 log: $LOG_DIR/nav2.log"
    ros2 node list || true
    exit 1
  fi
  sleep 1
done

echo "Publishing initial pose: x=$INITIAL_X y=$INITIAL_Y yaw=$INITIAL_YAW"
ros2 topic pub --once "$TEST_NS_ABS/initialpose" geometry_msgs/msg/PoseWithCovarianceStamped "{
  header: {frame_id: '$MAP_FRAME'},
  pose: {
    pose: {
      position: {x: $INITIAL_X, y: $INITIAL_Y, z: 0.0},
      orientation: {x: 0.0, y: 0.0, z: $INITIAL_QZ, w: $INITIAL_QW}
    },
    covariance: [
      0.05, 0.0, 0.0, 0.0, 0.0, 0.0,
      0.0, 0.05, 0.0, 0.0, 0.0, 0.0,
      0.0, 0.0, 0.0, 0.0, 0.0, 0.0,
      0.0, 0.0, 0.0, 0.0, 0.0, 0.0,
      0.0, 0.0, 0.0, 0.0, 0.0, 0.0,
      0.0, 0.0, 0.0, 0.0, 0.0, 0.02
    ]
  }
}"

sleep 3

echo "Watching $TEST_NS_ABS/cmd_vel for up to ${CMD_VEL_TIMEOUT_SEC}s..."
timeout "$CMD_VEL_TIMEOUT_SEC" ros2 topic echo --once "$TEST_NS_ABS/cmd_vel" \
  > "$LOG_DIR/cmd_vel.txt" 2>&1 &
CMD_PID=$!

echo "Sending goal: x=$GOAL_X y=$GOAL_Y yaw=$GOAL_YAW"
timeout "$ACTION_TIMEOUT_SEC" ros2 action send_goal "$TEST_NS_ABS/navigate_to_pose" nav2_msgs/action/NavigateToPose "{
  pose: {
    header: {frame_id: '$MAP_FRAME'},
    pose: {
      position: {x: $GOAL_X, y: $GOAL_Y, z: 0.0},
      orientation: {x: 0.0, y: 0.0, z: $GOAL_QZ, w: $GOAL_QW}
    }
  }
}" --feedback > "$LOG_DIR/goal.log" 2>&1 &
GOAL_PID=$!

CMD_STATUS=1
wait "$CMD_PID" || CMD_STATUS=$?
CMD_PID=""

if [[ "$CMD_STATUS" -eq 0 ]]; then
  echo "PASS: Nav2 produced $TEST_NS_ABS/cmd_vel."
  cat "$LOG_DIR/cmd_vel.txt"
  echo "Logs: $LOG_DIR"
  exit 0
fi

echo "FAIL: no $TEST_NS_ABS/cmd_vel observed within ${CMD_VEL_TIMEOUT_SEC}s."
echo "Goal log tail:"
tail -n 40 "$LOG_DIR/goal.log" || true
echo "Nav2 log tail:"
tail -n 80 "$LOG_DIR/nav2.log" || true
echo "Logs: $LOG_DIR"
exit 1
