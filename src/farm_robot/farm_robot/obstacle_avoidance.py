import math

import rclpy
from rclpy.node import Node
from rclpy.qos import qos_profile_sensor_data
from sensor_msgs.msg import LaserScan
from geometry_msgs.msg import Twist


class ObstacleAvoidance(Node):
    def __init__(self):
        super().__init__('obstacle_avoidance')

        self.forward_speed = 0.12
        self.slow_speed = 0.05
        self.turn_speed = 0.45

        # Stop only when something is very close in front.
        self.emergency_distance = 0.45
        self.caution_distance = 1.00

        # Keep a little distance from crop rows.
        self.target_side_distance = 0.85
        self.centering_gain = 1.0

        self.scan_subscriber = self.create_subscription(
            LaserScan,
            '/scan_fixed',
            self.scan_callback,
            qos_profile_sensor_data
        )

        self.cmd_publisher = self.create_publisher(
            Twist,
            '/cmd_vel',
            10
        )

        self._last_cmd = Twist()
        self.create_timer(0.1, self._republish_cmd)

        self.get_logger().info(
            'Obstacle avoidance started.'
        )

    def get_sector_distance(self, scan, center_deg, width_deg):
        distances = []

        for i, distance in enumerate(scan.ranges):
            angle = math.degrees(
                scan.angle_min + i * scan.angle_increment
            )

            difference = (
                (angle - center_deg + 180) % 360
            ) - 180

            if abs(difference) <= width_deg:
                if (
                    math.isfinite(distance)
                    and scan.range_min <= distance <= scan.range_max
                ):
                    distances.append(distance)

        return min(distances) if distances else None

    def scan_callback(self, scan):
        command = Twist()

        if not scan.ranges:
            self._last_cmd = command
            self.cmd_publisher.publish(command)
            return

        front = self.get_sector_distance(scan, 0, 30)
        left = self.get_sector_distance(scan, 90, 20)
        right = self.get_sector_distance(scan, -90, 20)

        # Emergency: stop forward movement and turn toward
        # the side with more clearance.
        if front is not None and front < self.emergency_distance:
            command.linear.x = 0.0

            if left is not None and right is not None:
                command.angular.z = (
                    self.turn_speed if left > right
                    else -self.turn_speed
                )
            elif left is not None:
                command.angular.z = self.turn_speed
            else:
                command.angular.z = -self.turn_speed

            self._last_cmd = command
            self.cmd_publisher.publish(command)
            return

        # Default: move forward.
        command.linear.x = self.forward_speed

        # Slow down if an obstacle is approaching.
        if front is not None and front < self.caution_distance:
            command.linear.x = self.slow_speed

        # Steer away from a nearby side obstacle.
        if left is not None and right is not None:
            if right < self.target_side_distance:
                command.angular.z = self.turn_speed * min(
                    1.0,
                    (self.target_side_distance - right) / 0.5
                )
            elif left < self.target_side_distance:
                command.angular.z = -self.turn_speed * min(
                    1.0,
                    (self.target_side_distance - left) / 0.5
                )
            else:
                # Center between both sides.
                error = right - left
                command.angular.z = max(
                    -0.25,
                    min(0.25, self.centering_gain * error)
                )

        elif right is not None and right < self.target_side_distance:
            command.angular.z = self.turn_speed * min(
                1.0,
                (self.target_side_distance - right) / 0.5
            )

        elif left is not None and left < self.target_side_distance:
            command.angular.z = -self.turn_speed * min(
                1.0,
                (self.target_side_distance - left) / 0.5
            )

        self._last_cmd = command
        self.cmd_publisher.publish(command)

    def _republish_cmd(self):
        self.cmd_publisher.publish(self._last_cmd)


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