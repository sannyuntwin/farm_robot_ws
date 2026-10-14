import math

import rclpy
from rclpy.node import Node
from sensor_msgs.msg import LaserScan
from geometry_msgs.msg import Twist


class ObstacleAvoidance(Node):
    def __init__(self):
        super().__init__('obstacle_avoidance')

        # Robot movement settings
        self.forward_speed = 0.12
        self.turn_speed = 0.45
        self.stop_distance = 0.60

        # Crop-row navigation settings
        self.target_side_distance = 1.0
        self.centering_gain = 0.8

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

        self.get_logger().info(
            'Smart crop-row navigation started.'
        )

    def get_sector_distance(self, scan, center_deg, width_deg=15):
        """Return the nearest valid LiDAR distance in a sector."""
        distances = []

        for i, distance in enumerate(scan.ranges):
            angle = scan.angle_min + i * scan.angle_increment
            angle_deg = math.degrees(angle)

            angle_difference = (
                (angle_deg - center_deg + 180) % 360
            ) - 180

            if abs(angle_difference) <= width_deg:
                if (
                    math.isfinite(distance)
                    and scan.range_min <= distance <= scan.range_max
                ):
                    distances.append(distance)

        return min(distances) if distances else None

    def scan_callback(self, scan):
        command = Twist()

        if not scan.ranges:
            self.cmd_publisher.publish(command)
            return

        # Detect obstacles in front and on both sides.
        front = self.get_sector_distance(scan, 0, 25)
        left = self.get_sector_distance(scan, 90, 20)
        right = self.get_sector_distance(scan, -90, 20)

        # Priority 1: Avoid an obstacle directly ahead.
        if front is not None and front < self.stop_distance:
            command.linear.x = 0.0

            if left is not None and right is not None:
                command.angular.z = (
                    self.turn_speed if left > right
                    else -self.turn_speed
                )
            elif left is not None:
                command.angular.z = (
                    -self.turn_speed
                    if left < self.stop_distance
                    else self.turn_speed
                )
            else:
                command.angular.z = self.turn_speed

            self.cmd_publisher.publish(command)
            return

        # Priority 2: Stay centered between two detected crop rows.
        if left is not None and right is not None:
            error = left - right

            # Positive angular velocity turns the robot left.
            command.angular.z = max(
                -self.turn_speed,
                min(self.turn_speed, self.centering_gain * error)
            )

        # If only one side is visible, keep a safe distance from it.
        elif left is not None:
            error = left - self.target_side_distance
            command.angular.z = max(
                -self.turn_speed,
                min(self.turn_speed, self.centering_gain * error)
            )

        elif right is not None:
            error = self.target_side_distance - right
            command.angular.z = max(
                -self.turn_speed,
                min(self.turn_speed, self.centering_gain * error)
            )

        # Move forward when the path is clear.
        command.linear.x = self.forward_speed
        self.cmd_publisher.publish(command)


def main(args=None):
    rclpy.init(args=args)
    node = ObstacleAvoidance()

    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.cmd_publisher.publish(Twist())
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
