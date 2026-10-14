
import math

import rclpy
from rclpy.node import Node
from sensor_msgs.msg import LaserScan
from geometry_msgs.msg import Twist


class ObstacleAvoidance(Node):
    def __init__(self):
        super().__init__('obstacle_avoidance')

        self.stop_distance = 0.6
        self.forward_speed = 0.15
        self.turn_speed = 0.6

        self.scan_subscriber = self.create_subscription(
            LaserScan,
            '/scan',
            self.scan_callback,
            10
        )

        self.cmd_publisher = self.create_publisher(
            Twist,
            '/cmd_vel',
            10
        )

        self.get_logger().info('Obstacle avoidance node started.')

    def scan_callback(self, scan):
        command = Twist()

        # Stop only if the LiDAR message contains no readings at all.
        if not scan.ranges:
            self.cmd_publisher.publish(command)
            self.get_logger().warn('LiDAR scan is empty. Robot stopped.')
            return

        # Check objects in front, within +/- 30 degrees.
        front_ranges = [
            distance
            for i, distance in enumerate(scan.ranges)
            if (
                math.isfinite(distance)
                and scan.range_min <= distance <= scan.range_max
                and abs(
                    scan.angle_min + i * scan.angle_increment
                ) < math.radians(30)
            )
        ]

        # No detected object in front means the path appears clear.
        # Infinite LiDAR readings are normal when nothing is detected.
        if not front_ranges:
            command.linear.x = self.forward_speed
            command.angular.z = 0.0
            self.cmd_publisher.publish(command)
            return

        nearest_obstacle = min(front_ranges)

        if nearest_obstacle < self.stop_distance:
            # Turn left until the front path is clear.
            command.linear.x = 0.0
            command.angular.z = self.turn_speed
            self.get_logger().info(
                f'Obstacle at {nearest_obstacle:.2f} m. Turning left.'
            )
        else:
            command.linear.x = self.forward_speed
            command.angular.z = 0.0

        self.cmd_publisher.publish(command)


def main(args=None):
    rclpy.init(args=args)
    node = ObstacleAvoidance()

    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        # Ensure the simulated robot receives a stop command on shutdown.
        node.cmd_publisher.publish(Twist())
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
