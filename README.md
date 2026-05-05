# ESIBOT ROS2 Workspace

Monorepo for ESIBOT ROS2 packages and the ESIBOT dashboard UI.

---

## Repository layout

- `esibot_ws/`: ROS2 workspace root
- `esibot_ws/src/esibot_bringup/`: robot driver, odometry, battery publishing
- `esibot_ws/src/esibot_sensors/`: radar node and RViz launch/config
- `esibot_ws/src/esibot_camera/`: ESP32-CAM MJPEG bridge
- `esibot_ws/src/esibot_description/`: placeholder/incomplete package directory
- `esibot_ws/src/esibot_ui/`: placeholder/incomplete package directory
- `esibot_ws/src/esibot_vision/`: placeholder/incomplete package directory
- `dashboard/esibot-ui/`: React + Vite + Tailwind dashboard interface

---

## Prerequisites

### ROS2

- ROS2 Humble
- `colcon`
- `rviz2`

Python dependencies:

- `python3-serial`
- `python3-opencv`
- `python3-numpy`
- `python3-requests`
- `python3-gpiozero`

---

### Dashboard UI

- Node.js `>= 20`
- npm

Check versions:

```bash
node -v
npm -v
Install dashboard dependencies
cd dashboard/esibot-ui
npm install
Install Tailwind (if needed)
npm install -D tailwindcss @tailwindcss/vite
Install icons
npm install lucide-react
Run dashboard (dev)
cd dashboard/esibot-ui
npm run dev

Then open:

http://localhost:5173/

Run on network:

npm run dev -- --host
Build dashboard
cd dashboard/esibot-ui
npm run build

Preview production:

npm run preview
Build ROS2 workspace
cd esibot_ws
source /opt/ros/humble/setup.bash
export ROS_DOMAIN_ID=10
colcon build
source install/setup.bash

Build a single package:

colcon build --packages-select esibot_bringup
Run packages
Driver
ros2 launch esibot_bringup esibot_driver.launch.py
Camera
ros2 launch esibot_camera esibot_camera.launch.py
Radar (with RViz)
ros2 launch esibot_sensors radar.launch.py
Radar (without RViz)
ros2 launch esibot_sensors radar.launch.py use_rviz:=false
Verify runtime
export ROS_DOMAIN_ID=10
source /opt/ros/humble/setup.bash
cd esibot_ws
source install/setup.bash

ros2 node list
ros2 topic list