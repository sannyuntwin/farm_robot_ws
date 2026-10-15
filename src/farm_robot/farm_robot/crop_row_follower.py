import math
from enum import Enum

import rclpy
from rclpy.node import Node
from rclpy.qos import qos_profile_sensor_data
from sensor_msgs.msg import LaserScan
from geometry_msgs.msg import Twist


class State(Enum):
    FOLLOWING = 'following'
    TURNING   = 'turning'


class CropRowFollower(Node):
    def __init__(self):
        super().__init__('crop_row_follower')

        self.forward_speed   = 0.5
        self.turn_speed      = 0.60
        self.centering_gain  = 1.2
        self.wall_range      = 1.5   # max distance to count as wall present
        self.turn_duration   = 5.5   # seconds for ~180° at 0.6 rad/s

        self.state        = State.FOLLOWING
        self.turn_end     = None
        self.turn_dir     = 1.0   # +1 = left, −1 = right; flips each row

        self._sub = self.create_subscription(
            LaserScan, '/scan_fixed', self._scan_cb, qos_profile_sensor_data)
        self._pub = self.create_publisher(Twist, '/cmd_vel', 10)

        self._last_cmd = Twist()
        self.create_timer(0.1, self._republish)

        self.get_logger().info('Crop row follower started.')

    def _republish(self):
        self._pub.publish(self._last_cmd)

    def _sector_min(self, scan, center_deg, half_width_deg):
        dists = []
        for i, d in enumerate(scan.ranges):
            ang = math.degrees(scan.angle_min + i * scan.angle_increment)
            if abs(((ang - center_deg + 180) % 360) - 180) <= half_width_deg:
                if math.isfinite(d) and scan.range_min <= d <= scan.range_max:
                    dists.append(d)
        return min(dists) if dists else None

    def _scan_cb(self, scan):
        cmd   = Twist()
        front = self._sector_min(scan,   0, 25)
        left  = self._sector_min(scan,  90, 20)
        right = self._sector_min(scan, -90, 20)

        if self.state == State.FOLLOWING:
            left_open  = left  is None or left  > self.wall_range
            right_open = right is None or right > self.wall_range

            if left_open and right_open:
                self.get_logger().info('Row end detected — starting U-turn.')
                self.state    = State.TURNING
                self.turn_end = self.get_clock().now().nanoseconds / 1e9 + self.turn_duration
                self.turn_dir *= -1.0
            else:
                cmd.linear.x = self.forward_speed

                if front is not None and front < 0.4:
                    cmd.linear.x = 0.0

                if left is not None and right is not None:
                    error = right - left
                    cmd.angular.z = -self.centering_gain * error
                elif left is not None:
                    cmd.angular.z = self.centering_gain * 0.3
                elif right is not None:
                    cmd.angular.z = -self.centering_gain * 0.3

        elif self.state == State.TURNING:
            if self.get_clock().now().nanoseconds / 1e9 < self.turn_end:
                cmd.angular.z = self.turn_speed * self.turn_dir
                cmd.linear.x  = 0.04
            else:
                self.get_logger().info('U-turn complete — resuming row follow.')
                self.state = State.FOLLOWING

        self._last_cmd = cmd
        self._pub.publish(cmd)


def main(args=None):
    rclpy.init(args=args)
    node = CropRowFollower()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node._pub.publish(Twist())
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
