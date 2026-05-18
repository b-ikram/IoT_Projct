#!/usr/bin/env python3
"""
ROS 2 ultrasonic radar node for the esibot_sensor package.

Hardware idea:
- 4 ultrasonic sensors mounted on top of a servo.
- Sensor angular spacing: 90 degrees.
- Each sensor covers about 30 degrees.
- Servo stops at 0, 30, and 60 degrees.
- At each servo stop, all 4 sensors are read.
- Together this gives 12 measurements around 360 degrees.

Supported sensors:
- Two classic TRIG/ECHO sensors, for example HC-SR04.
- Two one-wire SIG sensors, for example PING-style sensors.

Important Raspberry Pi safety note:
- Raspberry Pi GPIO is 3.3 V only.
- Any 5 V ECHO or SIG return signal must go through a voltage divider or level shifter.
"""

import math
import statistics
import time
from dataclasses import dataclass
from typing import List, Optional, Sequence, Tuple

import rclpy
from rclpy.node import Node
from sensor_msgs.msg import LaserScan

try:
    from gpiozero import AngularServo, DistanceSensor, DigitalInputDevice, DigitalOutputDevice
except ImportError:  # Allows the node to run in mock mode on non-RPi machines.
    AngularServo = None
    DistanceSensor = None
    DigitalInputDevice = None
    DigitalOutputDevice = None

try:
    import RPi.GPIO as GPIO
except ImportError:
    GPIO = None


@dataclass
class UltrasonicMeasurement:
    center_angle_rad: float
    fov_rad: float
    distance_m: float


class OneWireUltrasonicSensor:
    """
    Driver for one-wire SIG ultrasonic sensors.

    This uses two Raspberry Pi GPIOs electrically connected to the same sensor SIG line:
    - trigger_gpio drives the SIG line through a small resistor, for example 470 ohm.
    - echo_gpio reads the SIG line through a voltage divider or level shifter.

    The trigger and echo GPIOs must NOT be shorted directly without protection.
    """

    SPEED_OF_SOUND_M_PER_SEC = 343.0

    def __init__(
        self,
        trigger_gpio: int,
        echo_gpio: int,
        max_distance_m: float = 4.0,
        timeout_sec: Optional[float] = None,
        samples: int = 3,
        sample_delay_sec: float = 0.06,
    ) -> None:
        if DigitalInputDevice is None or DigitalOutputDevice is None:
            raise RuntimeError("gpiozero is not available")

        self.trigger_gpio = trigger_gpio
        self.echo_gpio = echo_gpio
        self.max_distance_m = max_distance_m
        self.timeout_sec = timeout_sec or (2.0 * max_distance_m / self.SPEED_OF_SOUND_M_PER_SEC + 0.02)
        self.samples = max(1, int(samples))
        self.sample_delay_sec = sample_delay_sec

        self.trigger = DigitalOutputDevice(trigger_gpio, initial_value=False)
        self.echo = DigitalInputDevice(echo_gpio, pull_up=False)

    def close(self) -> None:
        self.trigger.close()
        self.echo.close()

    def distance(self) -> float:
        readings: List[float] = []
        for _ in range(self.samples):
            value = self._single_distance_reading()
            if math.isfinite(value):
                readings.append(value)
            time.sleep(self.sample_delay_sec)

        if not readings:
            return math.inf

        return float(statistics.median(readings))

    def _single_distance_reading(self) -> float:
        # Make sure the line is low before triggering.
        self.trigger.off()
        time.sleep(0.000005)

        # Trigger pulse. Many ultrasonic modules use 10 us.
        self.trigger.on()
        time.sleep(0.00001)
        self.trigger.off()

        start_wait = time.monotonic()
        while not self.echo.value:
            if time.monotonic() - start_wait > self.timeout_sec:
                return math.inf

        pulse_start = time.monotonic()
        while self.echo.value:
            if time.monotonic() - pulse_start > self.timeout_sec:
                return math.inf

        pulse_end = time.monotonic()
        pulse_width_sec = pulse_end - pulse_start

        # Sound travels to the object and back, so divide by 2.
        distance_m = pulse_width_sec * self.SPEED_OF_SOUND_M_PER_SEC / 2.0

        if distance_m <= 0.0 or distance_m > self.max_distance_m:
            return math.inf

        return distance_m


class OneWireUltrasonicSensorSinglePin:
    """
    Driver for one-wire SIG ultrasonic sensors using a single GPIO pin.

    This toggles the same pin between output (trigger) and input (echo).
    """

    SPEED_OF_SOUND_M_PER_SEC = 343.0

    def __init__(
        self,
        gpio_pin: int,
        max_distance_m: float = 4.0,
        timeout_sec: Optional[float] = None,
        samples: int = 3,
        sample_delay_sec: float = 0.06,
    ) -> None:
        if GPIO is None:
            raise RuntimeError("RPi.GPIO is not available")

        self.gpio_pin = gpio_pin
        self.max_distance_m = max_distance_m
        self.timeout_sec = timeout_sec or (2.0 * max_distance_m / self.SPEED_OF_SOUND_M_PER_SEC + 0.02)
        self.samples = max(1, int(samples))
        self.sample_delay_sec = sample_delay_sec

        GPIO.setwarnings(False)
        if GPIO.getmode() is None:
            GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.gpio_pin, GPIO.OUT, initial=GPIO.LOW)

    def close(self) -> None:
        try:
            GPIO.cleanup(self.gpio_pin)
        except Exception:
            pass

    def distance(self) -> float:
        readings: List[float] = []
        for _ in range(self.samples):
            value = self._single_distance_reading()
            if math.isfinite(value):
                readings.append(value)
            time.sleep(self.sample_delay_sec)

        if not readings:
            return math.inf

        return float(statistics.median(readings))

    def _single_distance_reading(self) -> float:
        GPIO.setup(self.gpio_pin, GPIO.OUT, initial=GPIO.LOW)
        time.sleep(0.000005)

        GPIO.output(self.gpio_pin, True)
        time.sleep(0.00001)
        GPIO.output(self.gpio_pin, False)

        GPIO.setup(self.gpio_pin, GPIO.IN)

        start_wait = time.monotonic()
        while not GPIO.input(self.gpio_pin):
            if time.monotonic() - start_wait > self.timeout_sec:
                return math.inf

        pulse_start = time.monotonic()
        while GPIO.input(self.gpio_pin):
            if time.monotonic() - pulse_start > self.timeout_sec:
                return math.inf

        pulse_end = time.monotonic()
        pulse_width_sec = pulse_end - pulse_start

        distance_m = pulse_width_sec * self.SPEED_OF_SOUND_M_PER_SEC / 2.0

        if distance_m <= 0.0 or distance_m > self.max_distance_m:
            return math.inf

        return distance_m


class EsibotSensorNode(Node):
    def __init__(self) -> None:
        super().__init__("esibot_sensor_node")

        # ROS output parameters.
        self.declare_parameter("frame_id", "radar_link")
        self.declare_parameter("topic_name", "/esibot/scan")
        self.declare_parameter("publish_rate_hz", 1.0)

        # LaserScan parameters.
        self.declare_parameter("angle_min_deg", 0.0)
        self.declare_parameter("angle_max_deg", 360.0)
        self.declare_parameter("angle_increment_deg", 1.0)
        self.declare_parameter("range_min_m", 0.02)
        self.declare_parameter("range_max_m", 4.0)
        self.declare_parameter("mark_uncovered_as_inf", True)

        # Geometry.
        self.declare_parameter("base_angle_deg", 0.0)
        self.declare_parameter("servo_scan_angles_deg", [0.0, 30.0, 60.0])
        self.declare_parameter("sensor_offsets_deg", [0.0, 90.0, 180.0, 270.0])
        self.declare_parameter("sensor_fov_deg", 30.0)

        # Hardware mode.
        self.declare_parameter("use_mock_data", False)

        # Servo configuration.
        self.declare_parameter("servo_gpio_pin", 18)
        self.declare_parameter("servo_min_angle_deg", 0.0)
        self.declare_parameter("servo_max_angle_deg", 180.0)
        self.declare_parameter("servo_settle_time_sec", 0.35)

        # Sensor configuration.
        # type values must be either "trig_echo" or "sig".
        self.declare_parameter("sensor_types", ["trig_echo", "trig_echo", "sig", "sig"])

        # For TRIG/ECHO sensors, both trigger and echo are used normally.
        # For SIG sensors, trigger_gpio should be connected to SIG through about 470 ohm,
        # and echo_gpio should read the same SIG line through a voltage divider.
        self.declare_parameter("sensor_trigger_pins", [24, 26, 16, 20])
        self.declare_parameter("sensor_echo_pins", [21, 25, 16, 20])

        self.declare_parameter("sensor_max_distance_m", 4.0)
        self.declare_parameter("sensor_threshold_distance_m", 4.0)
        self.declare_parameter("sensor_queue_len", 3)
        self.declare_parameter("sig_sensor_samples", 3)
        self.declare_parameter("active_sensor_indices", [0, 1, 2, 3])

        self.frame_id = str(self.get_parameter("frame_id").value)
        self.topic_name = str(self.get_parameter("topic_name").value)
        self.publish_rate_hz = float(self.get_parameter("publish_rate_hz").value)

        self.angle_min = math.radians(float(self.get_parameter("angle_min_deg").value))
        self.angle_max = math.radians(float(self.get_parameter("angle_max_deg").value))
        self.angle_increment = math.radians(float(self.get_parameter("angle_increment_deg").value))
        self.range_min_m = float(self.get_parameter("range_min_m").value)
        self.range_max_m = float(self.get_parameter("range_max_m").value)
        self.mark_uncovered_as_inf = bool(self.get_parameter("mark_uncovered_as_inf").value)

        self.base_angle_deg = float(self.get_parameter("base_angle_deg").value)
        self.servo_scan_angles_deg = self._read_float_list("servo_scan_angles_deg")
        self.sensor_offsets_deg = self._read_float_list("sensor_offsets_deg")
        self.sensor_fov_deg = float(self.get_parameter("sensor_fov_deg").value)

        self.use_mock_data = bool(self.get_parameter("use_mock_data").value)

        self.servo_gpio_pin = int(self.get_parameter("servo_gpio_pin").value)
        self.servo_min_angle_deg = float(self.get_parameter("servo_min_angle_deg").value)
        self.servo_max_angle_deg = float(self.get_parameter("servo_max_angle_deg").value)
        self.servo_settle_time_sec = float(self.get_parameter("servo_settle_time_sec").value)

        self.sensor_types = [str(value) for value in self.get_parameter("sensor_types").value]
        self.sensor_trigger_pins = self._read_int_list("sensor_trigger_pins")
        self.sensor_echo_pins = self._read_int_list("sensor_echo_pins")
        self.sensor_max_distance_m = float(self.get_parameter("sensor_max_distance_m").value)
        self.sensor_threshold_distance_m = float(self.get_parameter("sensor_threshold_distance_m").value)
        self.sensor_queue_len = int(self.get_parameter("sensor_queue_len").value)
        self.sig_sensor_samples = int(self.get_parameter("sig_sensor_samples").value)
        self.active_sensor_indices = self._read_int_list("active_sensor_indices")

        self._validate_parameters()

        self.publisher = self.create_publisher(LaserScan, self.topic_name, 10)

        self.servo: Optional[AngularServo] = None
        self.sensors: List[object] = []
        self.hardware_ready = False
        self.hardware_warning_already_printed = False
        self._sweep_forward = True

        if self.use_mock_data:
            self.get_logger().info("Using mock data because use_mock_data=true")
        else:
            self.hardware_ready = self._setup_hardware()

        timer_period = 1.0 / max(self.publish_rate_hz, 0.01)
        self.timer = self.create_timer(timer_period, self.publish_scan)

        self.get_logger().info("esibot_sensor_node started")
        self.get_logger().info(f"Publishing LaserScan on {self.topic_name}")
        self.get_logger().info(
            "Scan geometry: servo angles=%s, sensor offsets=%s, sensor FOV=%.1f deg"
            % (self.servo_scan_angles_deg, self.sensor_offsets_deg, self.sensor_fov_deg)
        )

    def _read_float_list(self, name: str) -> List[float]:
        return [float(value) for value in self.get_parameter(name).value]

    def _read_int_list(self, name: str) -> List[int]:
        return [int(value) for value in self.get_parameter(name).value]

    def _validate_parameters(self) -> None:
        sensor_count = len(self.sensor_offsets_deg)

        if sensor_count != 4:
            raise ValueError("This node is configured for exactly 4 ultrasonic sensors")

        if len(self.sensor_types) != sensor_count:
            raise ValueError("sensor_types must contain exactly 4 values")

        if len(self.sensor_trigger_pins) != sensor_count:
            raise ValueError("sensor_trigger_pins must contain exactly 4 values")

        if len(self.sensor_echo_pins) != sensor_count:
            raise ValueError("sensor_echo_pins must contain exactly 4 values")

        for sensor_type in self.sensor_types:
            if sensor_type not in ("trig_echo", "sig"):
                raise ValueError('Each sensor type must be either "trig_echo" or "sig"')

        if len(self.servo_scan_angles_deg) != 3:
            self.get_logger().warning(
                "Expected 3 servo scan angles for your design: [0, 30, 60]. "
                f"Current value is {self.servo_scan_angles_deg}"
            )

        if not self.active_sensor_indices:
            raise ValueError("active_sensor_indices must not be empty")

        if self.angle_increment <= 0.0:
            raise ValueError("angle_increment_deg must be positive")

    def _setup_hardware(self) -> bool:
        self._close_hardware()  # Force la fermeture des anciennes connexions avant de commencer
        if AngularServo is None or DistanceSensor is None:
            self.get_logger().warning(
                "gpiozero is not installed. Falling back to mock scan data. "
                "Install python3-gpiozero on the Raspberry Pi."
            )
            return False

        try:
            self.servo = AngularServo(
                self.servo_gpio_pin,
                min_angle=self.servo_min_angle_deg,
                max_angle=self.servo_max_angle_deg,
            )

            self.sensors = []
            # 2. Initialisation des 4 capteurs
            for index in range(len(self.sensor_types)):
                sensor_type = self.sensor_types[index]
                trigger_pin = self.sensor_trigger_pins[index]
                echo_pin = self.sensor_echo_pins[index]

                if sensor_type == "trig_echo":
                    # Capteurs HC-SR04 (2 fils : TRIG et ECHO)
                    sensor = DistanceSensor(
                        echo=echo_pin,
                        trigger=trigger_pin,
                        max_distance=self.sensor_max_distance_m,
                        queue_len=self.sensor_queue_len
                    )
                else:
                    # Capteurs Ultra V2 / SIG (1 fil : SIG branché sur trigger et echo)
                    # On utilise TA classe OneWireUltrasonicSensor pour éviter le conflit de pin
                    if trigger_pin == echo_pin:
                        sensor = OneWireUltrasonicSensorSinglePin(
                            gpio_pin=trigger_pin,
                            max_distance_m=self.sensor_max_distance_m,
                            samples=self.sig_sensor_samples,
                        )
                    else:
                        sensor = OneWireUltrasonicSensor(
                            trigger_gpio=trigger_pin,
                            echo_gpio=echo_pin,
                            max_distance_m=self.sensor_max_distance_m,
                            samples=self.sig_sensor_samples,
                        )

                self.sensors.append(sensor)

            self.get_logger().info("Hardware prêt : Servo et 4 capteurs initialisés.")
            return True

        except Exception as exc:
            self.get_logger().warning(f"Erreur hardware : {exc}. Mode simulation activé.")
            self._close_hardware()
            return False

    def _close_hardware(self) -> None:
        for sensor in self.sensors:
            try:
                sensor.close()
            except Exception:
                pass
        self.sensors = []

        if self.servo is not None:
            try:
                self.servo.detach()
                self.servo.close()
            except Exception:
                pass
            self.servo = None

    @staticmethod
    def _normalize_angle_rad(angle_rad: float) -> float:
        return math.atan2(math.sin(angle_rad), math.cos(angle_rad))

    @staticmethod
    def _normalize_angle_0_to_2pi(angle_rad: float) -> float:
        value = angle_rad % (2.0 * math.pi)
        if value < 0.0:
            value += 2.0 * math.pi
        return value

    def _clamp_servo_angle(self, angle_deg: float) -> float:
        return min(max(angle_deg, self.servo_min_angle_deg), self.servo_max_angle_deg)

    def _read_sensor_distance_m(self, sensor_index: int) -> float:
        if sensor_index < 0 or sensor_index >= len(self.sensors):
            return math.inf

        sensor = self.sensors[sensor_index]
        sensor_type = self.sensor_types[sensor_index]

        try:
            if sensor_type == "trig_echo":
                # gpiozero DistanceSensor.distance returns a value from 0.0 to 1.0
                # relative to max_distance.
                distance_m = float(sensor.distance) * self.sensor_max_distance_m
            else:
                distance_m = float(sensor.distance())
        except Exception as exc:
            self.get_logger().warning(f"Failed to read sensor {sensor_index}: {exc}")
            return math.inf

        if distance_m < self.range_min_m or distance_m > self.range_max_m:
            return math.inf

        return distance_m

    def _perform_hardware_sweep(self) -> List[UltrasonicMeasurement]:
        measurements: List[UltrasonicMeasurement] = []

        if not self.hardware_ready or self.servo is None:
            return measurements

        angles = self.servo_scan_angles_deg if self._sweep_forward else list(reversed(self.servo_scan_angles_deg))
        self._sweep_forward = not self._sweep_forward

        for servo_angle_deg in angles:
            absolute_servo_angle_deg = self.base_angle_deg + servo_angle_deg
            servo_command_deg = self._clamp_servo_angle(absolute_servo_angle_deg)

            self.servo.angle = servo_command_deg
            time.sleep(self.servo_settle_time_sec)

            for sensor_index in self.active_sensor_indices:
                if sensor_index < 0 or sensor_index >= len(self.sensor_offsets_deg):
                    continue

                center_angle_deg = absolute_servo_angle_deg + self.sensor_offsets_deg[sensor_index]
                distance_m = self._read_sensor_distance_m(sensor_index)

                measurements.append(
                    UltrasonicMeasurement(
                        center_angle_rad=math.radians(center_angle_deg),
                        fov_rad=math.radians(self.sensor_fov_deg),
                        distance_m=distance_m,
                    )
                )

        return measurements

    def _build_mock_sweep(self) -> List[UltrasonicMeasurement]:
        measurements: List[UltrasonicMeasurement] = []

        # Mock pattern: each sensor returns a deterministic distance so you can test RViz.
        mock_distances_m = [0.8, 1.2, 1.8, 2.4]

        for servo_angle_deg in self.servo_scan_angles_deg:
            absolute_servo_angle_deg = self.base_angle_deg + servo_angle_deg

            for sensor_index in self.active_sensor_indices:
                if sensor_index < 0 or sensor_index >= len(self.sensor_offsets_deg):
                    continue

                center_angle_deg = absolute_servo_angle_deg + self.sensor_offsets_deg[sensor_index]
                distance_m = mock_distances_m[sensor_index % len(mock_distances_m)]

                measurements.append(
                    UltrasonicMeasurement(
                        center_angle_rad=math.radians(center_angle_deg),
                        fov_rad=math.radians(self.sensor_fov_deg),
                        distance_m=distance_m,
                    )
                )

        return measurements

    def _measurement_covers_angle(self, angle_rad: float, measurement: UltrasonicMeasurement) -> bool:
        half_fov = measurement.fov_rad / 2.0
        delta = self._normalize_angle_rad(angle_rad - measurement.center_angle_rad)
        return -half_fov <= delta <= half_fov

    def publish_scan(self) -> None:
        scan = LaserScan()
        scan.header.stamp = self.get_clock().now().to_msg()
        scan.header.frame_id = self.frame_id

        scan.angle_min = self.angle_min
        scan.angle_max = self.angle_max
        scan.angle_increment = self.angle_increment
        scan.time_increment = 0.0
        scan.scan_time = 1.0 / max(self.publish_rate_hz, 0.01)
        scan.range_min = self.range_min_m
        scan.range_max = self.range_max_m

        count = int(math.floor((scan.angle_max - scan.angle_min) / scan.angle_increment)) + 1
        count = max(1, count)

        uncovered_value = math.inf if self.mark_uncovered_as_inf else self.range_max_m
        scan.ranges = [uncovered_value] * count
        scan.intensities = [0.0] * count

        if self.hardware_ready:
            measurements = self._perform_hardware_sweep()
        else:
            measurements = self._build_mock_sweep()
            if not self.use_mock_data and not self.hardware_warning_already_printed:
                self.get_logger().warning("Publishing mock data because hardware is unavailable")
                self.hardware_warning_already_printed = True

        # Fill LaserScan bins. Each 30-degree ultrasonic measurement occupies its FOV.
        for i in range(count):
            angle = scan.angle_min + i * scan.angle_increment
            normalized_angle = self._normalize_angle_0_to_2pi(angle)

            best_distance = math.inf
            covered = False

            for measurement in measurements:
                measurement_center = UltrasonicMeasurement(
                    center_angle_rad=self._normalize_angle_0_to_2pi(measurement.center_angle_rad),
                    fov_rad=measurement.fov_rad,
                    distance_m=measurement.distance_m,
                )

                if self._measurement_covers_angle(normalized_angle, measurement_center):
                    covered = True
                    if measurement.distance_m < best_distance:
                        best_distance = measurement.distance_m

            if covered:
                scan.ranges[i] = best_distance
                scan.intensities[i] = 1.0 if math.isfinite(best_distance) else 0.0

        self.publisher.publish(scan)

    def destroy_node(self) -> None:
        self._close_hardware()
        super().destroy_node()


def main(args: Optional[Sequence[str]] = None) -> None:
    rclpy.init(args=args)
    node = EsibotSensorNode()

    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
