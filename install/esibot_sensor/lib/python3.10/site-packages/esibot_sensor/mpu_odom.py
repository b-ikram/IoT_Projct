import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Imu
from nav_msgs.msg import Odometry
import math

class MpuOdomNode(Node):
    def __init__(self):
        super().__init__('mpu_odom_node')
        
        # On s'abonne au topic que tu as créé précédemment
        self.subscription = self.create_subscription(Imu, 'esibot/imu', self.imu_callback, 10)
        
        # On publie l'angle calculé (ou une odométrie filtrée)
        self.odom_pub = self.create_publisher(Odometry, 'esibot/odom_imu', 10)

        self.yaw = 0.0
        self.last_time = self.get_clock().now()

    def imu_callback(self, msg):
        current_time = self.get_clock().now()
        dt = (current_time - self.last_time).nanoseconds / 1e9  # Delta temps en secondes
        
        # Récupération de la vitesse angulaire Z (rad/s)
        gz = msg.angular_velocity.z

        # INTEGRATION : Angle = Angle + (Vitesse * Temps)
        # On ajoute un petit filtre pour ignorer le bruit quand le robot est immobile
        if abs(gz) > 0.01: 
            self.yaw += gz * dt

        # Création du message d'odométrie simplifié
        odom = Odometry()
        odom.header.stamp = current_time.to_msg()
        odom.header.frame_id = "odom"
        odom.child_frame_id = "base_link"

        # Conversion du Yaw (Euler) en Quaternion (Format ROS 2)
        odom.pose.pose.orientation.z = math.sin(self.yaw / 2.0)
        odom.pose.pose.orientation.w = math.cos(self.yaw / 2.0)

        self.odom_pub.publish(odom)
        self.last_time = current_time
        
        # Log pour debug
        self.get_logger().info(f"Angle Yaw actuel: {math.degrees(self.yaw):.2f}°")

def main(args=None):
    rclpy.init(args=args)
    node = MpuOdomNode()
    rclpy.spin(node)
    rclpy.shutdown()
