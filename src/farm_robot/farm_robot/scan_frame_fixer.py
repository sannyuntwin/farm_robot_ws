import rclpy
from rclpy.node import Node
from rclpy.qos import qos_profile_sensor_data
from sensor_msgs.msg import LaserScan


class ScanFrameFixer(Node):
    def __init__(self):
        super().__init__('scan_frame_fixer')

        self.declare_parameter('frame_id', 'lidar_link')
        self.frame_id = self.get_parameter('frame_id').get_parameter_value().string_value

        self.subscription = self.create_subscription(
            LaserScan,
            '/scan',
            self.scan_callback,
            qos_profile_sensor_data
        )
        self.publisher = self.create_publisher(LaserScan, '/scan_fixed', qos_profile_sensor_data)

        self.get_logger().info(
            f'Scan frame fixer started: rewriting frame_id to "{self.frame_id}"'
        )

    def scan_callback(self, msg):
        msg.header.frame_id = self.frame_id
        self.publisher.publish(msg)


def main(args=None):
    rclpy.init(args=args)
    node = ScanFrameFixer()

    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
