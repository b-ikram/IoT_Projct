# ESIBOT: Autonomous Mobile Robot Platform

A comprehensive ROS2-based autonomous mobile robot system combining real-time hardware control, multi-sensor fusion, computer vision, and a modern web-based monitoring dashboard.



## Project Overview

**ESIBOT** is an autonomous mobile robot system developed at ESI (École Supérieure d'Informatique). The platform integrates:

- **Real-time Hardware Control**: Direct serial communication with robot motors and actuators
- **Multi-Sensor Fusion**: IMU (MPU-6050), Ultrasonic Radar (360°), and encoder odometry
- **Camera Integration**: Raspberry Pi camera stream processing with OpenCV
- **Navigation & Localization**: TF2-based coordinate frame management and odometry calculation
- **Modern Dashboard**: React-based web UI for real-time robot monitoring and control
- **ROS2 Ecosystem**: Built on ROS2 Humble for reliability and modularity

---

## System Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    Web Dashboard (React)                │
│              (Real-time monitoring & control)           │
└──────────────────────┬──────────────────────────────────┘
                       │
        ┌──────────────┼──────────────┐
        │              │              │
   ┌────▼─────┐  ┌────▼────┐  ┌─────▼──────┐
   │ROS Bridge│  │ROS Nodes│  │Launch Files│
   │(WebSock) │  │(Python) │  │            │
   └────┬─────┘  └────┬────┘  └─────┬──────┘
        │             │              │
   ┌────▼─────────────▼──────────────▼────┐
   │          ROS2 Middleware (DDS)       │
   └────┬─────────────┬──────────────┬────┘
        │             │              │
   ┌────▼──┐  ┌──────▼──────┐  ┌───▼────┐
   │Sensors│  │Hardware Ctrl│  │Camera  │
   │       │  │             │  │        │
   ├──────┤  ├─────────────┤  ├────────┤
   │IMU   │  │Motor Driver │  │RPi Cam │
   │Radar │  │Serial Link  │  │OpenCV  │
   │Encode│  │GPIO         │  │Stream  │
   └──────┘  └─────────────┘  └────────┘
```

---

## Project Structure

### ROS2 Workspace: `esibot_ws/`

```
esibot_ws/src/
├── esibot_bringup/
│   ├── esibot_driver.py          # Main hardware interface & odometry
│   ├── launch/
│   │   └── esibot_driver.launch.py
│   └── Publishes: /odom, /tf, /battery
│
├── esibot_camera/
│   ├── esircam_node.py            # Raspberry Pi camera stream bridge
│   ├── launch/
│   │   └── esibot_camera.launch.py
│   ├── config/
│   │   └── camera_params.yaml
│   └── Publishes: /camera/image_raw, /camera/compressed
│
├── esibot_sensor/
│   ├── mpu_node.py                # MPU-6050 IMU (Accel + Gyro)
│   ├── encoder_node.py            # Wheel encoder odometry
│   ├── radar_node.py              # 360° Ultrasonic radar
│   ├── radar_node_360.py          # Multi-sensor radar variant
│   ├── mpu_odom.py                # IMU-based odometry fusion
│   ├── launch/
│   │   └── radar.launch.py        # Integrated sensor launch with RViz
│   ├── config/
│   │   ├── esibot_sensor.yaml
│   │   ├── radar_params.yaml
│   │   ├── config.rviz
│   │   └── radar.rviz
│   └── Publishes: /imu, /radar, /odom
│
├── esibot_description/
│   ├── urdf/
│   │   └── esibot.urdf.xacro      # Robot kinematic model
│   ├── launch/
│   │   └── rsp.launch.py          # Robot state publisher
│   └── Publishes: /tf, /joint_states
│
├── esibot_ui/
│   └── dashboard_node.py          # Backend dashboard service (WIP)
│
└── esibot_vision/
    └── vision_node.py             # Computer vision pipeline (WIP)

---

## Hardware Requirements

| Component | Specification | Purpose |
|-----------|--------------|---------|
| **Main Controller** | Raspberry Pi 4/5 | Robot brain (ROS2 runtime) |
| **Motor Driver** | Custom/L298N | DC motor PWM control |
| **Sensors** | MPU-6050 | 6-axis IMU (accel + gyro) |
| | HC-SR04 Array | Ultrasonic distance sensors (360°) |
| | Wheel Encoders | Odometry feedback |
| **Camera** | Raspberry Pi Camera V2 | Vision/monitoring |
| **Serial Link** | USB/UART | Hardware communication |
| **Power** | Battery pack | Robot power supply |

---

## Software Prerequisites

### System Requirements
- **OS**: Ubuntu 22.04+ (ROS2 Humble compatible)
- **ROS2**: Humble distribution
- **Python**: 3.10+
- **Node.js**: 18+ (for dashboard)

### Install ROS2 Humble

```bash
# https://docs.ros.org/en/humble/Installation.html
sudo apt update
sudo apt upgrade
# [Follow official ROS2 Humble installation guide]
```

### Install Build Tools

```bash
sudo apt install -y \
  build-essential \
  cmake \
  git \
  colcon \
  python3-dev \
  python3-pip
```

### Install Runtime Dependencies

```bash
sudo apt install -y \
  python3-serial \
  python3-pip \
  rviz2 \
  ros-humble-tf2-ros

pip3 install \
  opencv-python \
  numpy \
  requests \
  mpu6050-raspberrypi \
  RPi.GPIO
```

### Install Dashboard Dependencies

```bash
cd dashboard/esibot-ui
npm install
```

---

## Installation & Setup

### 1. Clone the Repository

```bash
git clone <repository-url> ~/esibot_project
cd ~/esibot_project
```

### 2. Set Environment Variables

```bash
# Add to ~/.bashrc or ~/.zshrc
export ROS_DOMAIN_ID=10
export ROS_DISTRO=humble

# Source ROS setup
source /opt/ros/humble/setup.bash
```

### 3. Initialize ROS2 Workspace

```bash
cd esibot_ws
source /opt/ros/humble/setup.bash
```

---

## Building the Project

### Build All Packages

```bash
cd esibot_ws
export ROS_DOMAIN_ID=10
colcon build
source install/setup.bash
```

### Build Specific Package

```bash
# Example: Build only bringup package
colcon build --packages-select esibot_bringup

# Build with verbose output
colcon build --packages-select esibot_sensor --verbose
```

### Clean Build (if needed)

```bash
rm -rf build install log
colcon build
```

---

## Running Components

### Terminal 1: Source Environment

```bash
cd ~/esibot_project/esibot_ws
source /opt/ros/humble/setup.bash
export ROS_DOMAIN_ID=10
source install/setup.bash
```

### Launch Robot Driver (Hardware Interface)

```bash
ros2 launch esibot_bringup esibot_driver.launch.py
```

### Launch Sensors & Visualization

```bash
# With RViz (recommended for development)
ros2 launch esibot_sensor radar.launch.py

# Headless (without RViz)
ros2 launch esibot_sensor radar.launch.py use_rviz:=false
```

### Launch Camera Stream

```bash
ros2 launch esibot_camera esibot_camera.launch.py
```

### Launch Robot Description & TF Tree

```bash
ros2 launch esibot_description rsp.launch.py
```


### Launch Dashboard UI

```bash
cd dashboard/esibot-ui
npm run dev
# Dashboard available at http://localhost:5173
```

---

### Technology Stack

- **Frontend Framework**: React 19+
- **Build Tool**: Vite
- **Styling**: TailwindCSS
- **ROS Integration**: ROSlib (WebSocket bridge)
- **Visualization**: ROS2D, EaselJS
- **Routing**: React Router v7

---

## Team Members

**ESIBOT** is developed by a dedicated team at **ESI (Ecole Nationale Supérieure d'Informatique)**.

### Project Team

| Role | Name |
|------|------|
| **Team Leader** | BADAOUI Ikram |
| **Member** | SAIDI Selma |
| **Member** | HIMEUR Idris |
| **Member** | DIAR Adem |
| **Member** | CHATTAH Salsabila |
| **Member** | MARMOUZE Nor Elhouda |
| **Member** | BERKAT Cheraz |

### Institution

**École Nationale Supérieure d'Informatique (ESI)**

## License

Apache 2.0

---

**Last Updated**: 2026-06-24 | **ROS2 Version**: Humble
