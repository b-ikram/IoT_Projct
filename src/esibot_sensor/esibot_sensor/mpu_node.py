import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Imu
from mpu6050 import mpu6050
import math

class MpuNode(Node):
    def __init__(self):
        super().__init__('mpu_sensor_node')
        
        # Initialisation du capteur (adresse 0x68 par défaut)
        try:
            self.sensor = mpu6050(0x68)
            self.get_logger().info("MPU-6050 connecté avec succès !")
        except Exception as e:
            self.get_logger().error(f"Erreur de connexion au MPU-6050: {e}")

        self.publisher_ = self.create_publisher(Imu, '/esibot/imu', 10)
        
        # PARAMÈTRES DE STABILISATION
        self.alpha = 0.2        # Facteur de lissage (entre 0.1 et 0.5)
        self.deadzone = 0.5    # Ignore les rotations < 0.5 deg/sec
        
        # Stockage des anciennes valeurs pour le filtre
        self.prev_gx = 0.0
        self.prev_gy = 0.0
        self.prev_gz = 0.0

        # Timer pour publier à 20Hz
        self.timer = self.create_timer(0.05, self.timer_callback)

    def timer_callback(self):
        msg = Imu()
        msg.header.stamp = self.get_clock().now().to_msg()
        msg.header.frame_id = 'imu_link'

        try:
            # 1. Lecture des données brutes
            accel_data = self.sensor.get_accel_data()
            gyro_data = self.sensor.get_gyro_data()

            # 2. Application de la Zone Morte sur l'axe Z (le lacet / Yaw)
            raw_gz = gyro_data['z']
            if abs(raw_gz) < self.deadzone:
                raw_gz = 0.0

            # 3. Application du Filtre Passe-Bas (Smoothing)
            # Formule : Valeur_Filtrée = (Alpha * Nouvelle) + (1-Alpha * Ancienne)
            filtered_gx = (self.alpha * gyro_data['x']) + (1.0 - self.alpha) * self.prev_gx
            filtered_gy = (self.alpha * gyro_data['y']) + (1.0 - self.alpha) * self.prev_gy
            filtered_gz = (self.alpha * raw_gz) + (1.0 - self.alpha) * self.prev_gz

            # Sauvegarde pour la prochaine itération
            self.prev_gx, self.prev_gy, self.prev_gz = filtered_gx, filtered_gy, filtered_gz

            # 4. Remplissage du message IMU (Conversion deg/s en rad/s)
            deg_to_rad = math.pi / 180.0
            msg.angular_velocity.x = filtered_gx * deg_to_rad
            msg.angular_velocity.y = filtered_gy * deg_to_rad
            msg.angular_velocity.z = filtered_gz * deg_to_rad

            # Accélération linéaire (convertie en m/s²)
            msg.linear_acceleration.x = accel_data['x']
            msg.linear_acceleration.y = accel_data['y']
            msg.linear_acceleration.z = accel_data['z']

            self.publisher_.publish(msg)

        except Exception as e:
            self.get_logger().warn(f"Erreur de lecture : {e}")

def main(args=None):
    rclpy.init(args=args)
    node = MpuNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
