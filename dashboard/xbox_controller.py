#!/usr/bin/env python3
"""
xbox_controller.py - Control EsiBot robot with Xbox 360 controller

Reads Xbox 360 controller (USB) and publishes geometry_msgs/Twist
to /cmd_vel via rosbridge WebSocket on the Raspberry Pi.

Controls:
  - Left stick Y : forward / backward speed
  - Right stick X: rotate left / right
  - RT (right trigger, held >50%): turbo mode (1.5x)
  - Start button : emergency stop

Requires: pip install inputs websocket-client
"""

import json
import signal
import sys
import threading
import time

import websocket
from inputs import get_gamepad

# ── Configuration ──────────────────────────────────────────
ROSBRIDGE_URI = "ws://10.243.104.154:9090"
PUBLISH_INTERVAL = 1.0 / 20.0        # 20 Hz publish rate
MAX_LINEAR  = 0.6                    # m/s at full stick
MAX_ANGULAR = 0.6                    # rad/s at full stick
TURBO_FACTOR = 1.5                   # multiplier when RT held
DEADZONE = 0.10                      # ignore stick noise < 10%
SMOOTHING = 0.25                     # exponential smoothing factor (lower = smoother)

# evdev codes for Xbox 360 controller (xpad driver)
AXIS_LEFT_Y  = "ABS_Y"    # Left stick vertical
AXIS_RIGHT_X = "ABS_RX"   # Right stick horizontal
AXIS_RT      = "ABS_RZ"   # Right trigger
BTN_START    = "BTN_START"

# ── Shared state ───────────────────────────────────────────
lock = threading.Lock()
left_y = 0.0     # -1..1
right_x = 0.0    # -1..1
rt = 0.0         #  0..1
running = True

# ── Axis helpers ───────────────────────────────────────────

def normalize(v, max_val=32767.0):
    if abs(v) < 1:
        return 0.0
    return max(-1.0, min(1.0, v / max_val))

def deadzone(v, threshold=DEADZONE):
    if abs(v) < threshold:
        return 0.0
    sign = 1.0 if v > 0 else -1.0
    return sign * (abs(v) - threshold) / (1.0 - threshold)

# ── Joystick reader (background thread) ────────────────────

def joystick_reader():
    global left_y, right_x, rt, running

    while running:
        try:
            events = get_gamepad()
        except Exception as e:
            if running:
                print(f"\n[!] Controller error: {e}")
                print("    Make sure the Xbox 360 controller is connected via USB.")
            time.sleep(1)
            continue

        for ev in events:
            if not running:
                return
            if ev.ev_type not in ("Absolute", "Key"):
                continue

            with lock:
                if ev.code == AXIS_LEFT_Y:
                    left_y = -normalize(ev.state)     # up = +forward
                elif ev.code == AXIS_RIGHT_X:
                    right_x = -normalize(ev.state)    # negate: stick right = +rotation
                elif ev.code == AXIS_RT:
                    if ev.state > 255:
                        rt = max(0.0, normalize(ev.state))
                    elif ev.state > 0:
                        rt = min(1.0, ev.state / 255.0)
                    else:
                        rt = 0.0
                elif ev.code == BTN_START and ev.state == 1:
                    print("\n[!] Emergency stop (Start button)")
                    running = False
                    return

# ── Publisher (main thread) ────────────────────────────────

def publish_loop(ws):
    global running

    # Advertise topic on rosbridge
    ws.send(json.dumps({
        "op": "advertise",
        "topic": "/cmd_vel",
        "type": "geometry_msgs/Twist",
    }))
    print("[+] Advertised /cmd_vel on rosbridge")
    print("[*] Ready — move the sticks to drive\n")

    smooth_lin = 0.0
    smooth_ang = 0.0

    while running:
        with lock:
            ly = left_y
            rx = right_x
            rt_val = rt

        ly = deadzone(ly)
        rx = deadzone(rx)

        multiplier = TURBO_FACTOR if rt_val > 0.5 else 1.0

        target_lin = ly * MAX_LINEAR * multiplier
        target_ang = rx * MAX_ANGULAR * multiplier
        target_lin = max(-0.9, min(0.9, target_lin))
        target_ang = max(-0.9, min(0.9, target_ang))

        # Snap to zero when stick centered (instant stop), smooth ramp-up otherwise
        if abs(target_lin) < 0.001:
            smooth_lin = 0.0
        else:
            smooth_lin += (target_lin - smooth_lin) * SMOOTHING
        if abs(target_ang) < 0.001:
            smooth_ang = 0.0
        else:
            smooth_ang += (target_ang - smooth_ang) * SMOOTHING

        msg = {
            "op": "publish",
            "topic": "/cmd_vel",
            "msg": {
                "linear":  {"x": smooth_lin,  "y": 0.0, "z": 0.0},
                "angular": {"x": 0.0,         "y": 0.0, "z": smooth_ang},
            },
        }

        try:
            ws.send(json.dumps(msg))
        except (websocket.WebSocketConnectionClosedException,
                ConnectionRefusedError, OSError) as e:
            print(f"\n[!] Connection lost: {e}")
            break

        turbo_tag = "  [TURBO]" if rt_val > 0.5 else ""
        sys.stdout.write(f"\r  lin={smooth_lin:+.3f}  ang={smooth_ang:+.3f}{turbo_tag}")
        sys.stdout.flush()

        time.sleep(PUBLISH_INTERVAL)

    # Cleanup: send stop
    try:
        ws.send(json.dumps({
            "op": "publish",
            "topic": "/cmd_vel",
            "msg": {
                "linear":  {"x": 0.0, "y": 0.0, "z": 0.0},
                "angular": {"x": 0.0, "y": 0.0, "z": 0.0},
            },
        }))
    except Exception:
        pass

# ── Signal handling ────────────────────────────────────────

def signal_handler(sig, frame):
    global running
    print("\n[+] Shutting down…")
    running = False

# ── Main ───────────────────────────────────────────────────

def main():
    global running

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    print(f"[*] Connecting to rosbridge at {ROSBRIDGE_URI} …")
    try:
        ws = websocket.create_connection(ROSBRIDGE_URI, timeout=5)
    except Exception as e:
        print(f"[!] Failed to connect: {e}")
        print(f"    Make sure rosbridge_server is running on the Pi:")
        print(f"    ros2 launch rosbridge_server rosbridge_websocket_launch.xml")
        sys.exit(1)
    print("[+] Connected to rosbridge")

    reader = threading.Thread(target=joystick_reader, daemon=True)
    reader.start()

    try:
        publish_loop(ws)
    except KeyboardInterrupt:
        pass
    finally:
        running = False
        ws.close()
        print("\n[+] Done")

if __name__ == "__main__":
    main()
