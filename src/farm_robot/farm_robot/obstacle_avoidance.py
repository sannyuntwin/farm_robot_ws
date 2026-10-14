
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
        # Ignore invalid readings and readings outside sensor range.
        valid_ranges = [
            r for r in scan.ranges
            if math.isfinite(r)
            and scan.range_min <= r <= scan.range_max
        ]

        command = Twist()

        if not valid_ranges:
            # Fail safe: don't move if the sensor has no valid readings.
            self.cmd_publisher.publish(command)
            self.get_logger().warn(
                'No valid LiDAR readings. Robot stopped.'
            )
            return

        # The scan is arranged from -pi to +pi.
        # Find the readings in the front 60-degree sector.
        front_ranges = [
            r for i, r in enumerate(scan.ranges)
            if math.isfinite(r)
            and scan.range_min <= r <= scan.range_max
            and abs(
                scan.angle_min + i * scan.angle_increment
            ) < math.radians(30)
        ]

        if not front_ranges:
            self.cmd_publisher.publish(command)
            self.get_logger().warn(
                'No valid front readings. Robot stopped.'
            )
            return

        nearest_obstacle = min(front_ranges)

        if nearest_obstacle < self.stop_distance:
            # Stop forward motion and turn in place.
            command.linear.x = 0.0
            command.angular.z = self.turn_speed

            self.get_logger().info(
                f'Obstacle at {nearest_obstacle:.2f} m. Turning.'
            )
        else:
            # Clear path: move forward.
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
        # Stop the robot when this node exits.
        node.cmd_publisher.publish(Twist())
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
