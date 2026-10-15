import math
from enum import Enum

import rclpy
from rclpy.node import Node
from sensor_msgs.msg import LaserScan
from geometry_msgs.msg import Twist


class State(Enum):
    FOLLOWING = 'following'
    TURN_1    = 'turn_1'    # 90° toward next lane
    ADVANCE   = 'advance'   # one lane width forward
    TURN_2    = 'turn_2'    # 90° to face opposite row direction
    DONE      = 'done'


class FieldCoverage(Node):
    def __init__(self):
        super().__init__('field_coverage')

        self.forward_speed   = 0.15
        self.turn_speed      = 0.50
        self.centering_gain  = 1.2
        self.wall_range      = 1.5    # max dist to count as wall present
        self.row_end_front   = 0.50   # stop when front wall closer than this

        # 90° turn and one lane-width advance (time-based)
        self.turn_duration    = (math.pi / 2) / self.turn_speed   # ≈ 3.14 s
        self.lane_width       = 0.60
        self.advance_duration = self.lane_width / self.forward_speed  # 4.0 s
        self.max_rows         = 8

        self.state     = State.FOLLOWING
        self.phase_end = None
        self.turn_dir  = 1.0   # +1=left, -1=right; same for TURN_1+TURN_2; flips after TURN_2
        self.row_count = 0

        self._sub = self.create_subscription(LaserScan, '/scan_fixed', self._scan_cb, 10)
        self._pub = self.create_publisher(Twist, '/cmd_vel', 10)
        self.get_logger().info('Field coverage started.')

    def _sector_min(self, scan, center_deg, half_width_deg):
        dists = []
        for i, d in enumerate(scan.ranges):
            ang = math.degrees(scan.angle_min + i * scan.angle_increment)
            if abs(((ang - center_deg + 180) % 360) - 180) <= half_width_deg:
                if math.isfinite(d) and scan.range_min <= d <= scan.range_max:
                    dists.append(d)
        return min(dists) if dists else None

    def _now(self):
        return self.get_clock().now().nanoseconds / 1e9

    def _scan_cb(self, scan):
        cmd   = Twist()
        front = self._sector_min(scan,   0, 25)
        left  = self._sector_min(scan,  90, 20)
        right = self._sector_min(scan, -90, 20)

        if self.state == State.FOLLOWING:
            front_blocked = front is not None and front < self.row_end_front
            left_open     = left  is None or left  > self.wall_range
            right_open    = right is None or right > self.wall_range
            row_end       = front_blocked or (left_open and right_open)

            if row_end:
                self.row_count += 1
                if self.row_count >= self.max_rows:
                    self.get_logger().info('Field coverage complete.')
                    self.state = State.DONE
                else:
                    self.get_logger().info(
                        f'Row {self.row_count} done — starting lane change.')
                    self.state = State.TURN_1
                    self.phase_end = self._now() + self.turn_duration
            else:
                cmd.linear.x = self.forward_speed
                if front is not None and front < 0.4:
                    cmd.linear.x = 0.0
                if left is not None and right is not None:
                    cmd.angular.z = -self.centering_gain * (right - left)
                elif left is not None:
                    cmd.angular.z =  self.centering_gain * 0.3
                elif right is not None:
                    cmd.angular.z = -self.centering_gain * 0.3

        elif self.state == State.TURN_1:
            if self._now() < self.phase_end:
                cmd.angular.z = self.turn_speed * self.turn_dir
            else:
                self.state = State.ADVANCE
                self.phase_end = self._now() + self.advance_duration

        elif self.state == State.ADVANCE:
            if self._now() < self.phase_end:
                cmd.linear.x = self.forward_speed
            else:
                self.state = State.TURN_2
                self.phase_end = self._now() + self.turn_duration

        elif self.state == State.TURN_2:
            if self._now() < self.phase_end:
                cmd.angular.z = self.turn_speed * self.turn_dir
            else:
                self.turn_dir *= -1.0   # flip direction for the next lane change
                self.state = State.FOLLOWING

        elif self.state == State.DONE:
            pass   # cmd stays zero — robot stops

        self._pub.publish(cmd)


def main(args=None):
    rclpy.init(args=args)
    node = FieldCoverage()
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
