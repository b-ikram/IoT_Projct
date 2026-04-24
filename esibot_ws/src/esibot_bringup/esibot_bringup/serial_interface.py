import serial
import time

class SerialInterface:
    def __init__(self, port="/dev/ttyUSB0", baudrate=115200, timeout=1):
        # Connexion UART réelle
        self.ser = serial.Serial(port, baudrate, timeout=timeout)
        print(f"[INFO] Serial port {port} opened at {baudrate} baud.")

    def read_line(self):
        line = self.ser.readline().decode().strip()
        return line

    def send_command(self, left_speed, right_speed):
        # Exemple protocole simple : "L100,R100\n"
        msg = f"L{left_speed},R{right_speed}\n"
        self.ser.write(msg.encode())

    def close(self):
        self.ser.close()