import math

import rclpy
from rclpy.node import Node
from rclpy.qos import qos_profile_sensor_data
from sensor_msgs.msg import LaserScan
from geometry_msgs.msg import Twist

# Timer ticks needed per phase (timer runs at 10 Hz)
_REVERSE_TICKS = 15   # 1.5 s reverse
_TURN_TICKS    = 15   # 1.5 s turn (~69 ° at 0.8 rad/s)


class ObstacleAvoidance(Node):
    def __init__(self):
        super().__init__('obstacle_avoidance')

        self.forward_speed = 0.7
        self.slow_speed    = 0.3
        self.turn_speed    = 0.8

        self.emergency_distance   = 0.8
        self.caution_distance     = 1.20
        self.target_side_distance = 0.85
        self.centering_gain       = 1.0

        # State machine: 'forward' | 'reverse' | 'turn'
        self._phase              = 'forward'
        self._phase_ticks_left   = 0
        self._turn_direction     = 1.0   # +1 = left, -1 = right

        self.scan_subscriber = self.create_subscription(
            LaserScan, '/scan_fixed', self.scan_callback, qos_profile_sensor_data)
        self.cmd_publisher = self.create_publisher(Twist, '/cmd_vel', 10)

        self._last_cmd = Twist()
        self.create_timer(0.1, self._tick)

        self.get_logger().info('Obstacle avoidance started.')

    # ------------------------------------------------------------------ #
    #  10 Hz timer — drives the state machine and keeps cmd_vel alive     #
    # ------------------------------------------------------------------ #
    def _tick(self):
        if self._phase == 'reverse':
            self._phase_ticks_left -= 1
            if self._phase_ticks_left <= 0:
                self._phase = 'turn'
                self._phase_ticks_left = _TURN_TICKS
                cmd = Twist()
                cmd.angular.z = self.turn_speed * self._turn_direction
                self._last_cmd = cmd

        elif self._phase == 'turn':
            self._phase_ticks_left -= 1
            if self._phase_ticks_left <= 0:
                self._phase = 'forward'
                self._last_cmd = Twist()   # stop; next scan will steer

        self.cmd_publisher.publish(self._last_cmd)

    # ------------------------------------------------------------------ #
    #  Scan callback — only acts when in 'forward' phase                  #
    # ------------------------------------------------------------------ #
    def scan_callback(self, scan):
        if not scan.ranges:
            return

        # Don't interrupt an active emergency maneuver
        if self._phase != 'forward':
            return

        front      = self.get_sector_distance(scan,   0, 30)
        left       = self.get_sector_distance(scan,  90, 20)
        right      = self.get_sector_distance(scan, -90, 20)
        front_left = self.get_sector_distance(scan,  45, 20)
        front_right= self.get_sector_distance(scan, -45, 20)

        # ── Emergency: too close ahead ──────────────────────────────── #
        if front is not None and front < self.emergency_distance:
            # Pick direction with more clearance using diagonal readings
            def clearance(*vals):
                valid = [v for v in vals if v is not None]
                return min(valid) if valid else 10.0

            left_clear  = clearance(left,  front_left)
            right_clear = clearance(right, front_right)
            self._turn_direction = 1.0 if left_clear >= right_clear else -1.0

            self._phase = 'reverse'
            self._phase_ticks_left = _REVERSE_TICKS

            cmd = Twist()
            cmd.linear.x = -0.3
            self._last_cmd = cmd
            self.cmd_publisher.publish(cmd)
            self.get_logger().info(
                f'Emergency! front={front:.2f}m  turning {"left" if self._turn_direction>0 else "right"}'
            )
            return

        # ── Normal forward navigation ───────────────────────────────── #
        cmd = Twist()
        cmd.linear.x = self.forward_speed

        if front is not None and front < self.caution_distance:
            cmd.linear.x = self.slow_speed

        if left is not None and right is not None:
            if right < self.target_side_distance:
                cmd.angular.z = self.turn_speed * min(
                    1.0, (self.target_side_distance - right) / 0.5)
            elif left < self.target_side_distance:
                cmd.angular.z = -self.turn_speed * min(
                    1.0, (self.target_side_distance - left) / 0.5)
            else:
                error = right - left
                cmd.angular.z = max(-0.25, min(0.25, self.centering_gain * error))

        elif right is not None and right < self.target_side_distance:
            cmd.angular.z = self.turn_speed * min(
                1.0, (self.target_side_distance - right) / 0.5)

        elif left is not None and left < self.target_side_distance:
            cmd.angular.z = -self.turn_speed * min(
                1.0, (self.target_side_distance - left) / 0.5)

        self._last_cmd = cmd
        self.cmd_publisher.publish(cmd)

    # ------------------------------------------------------------------ #
    def get_sector_distance(self, scan, center_deg, width_deg):
        distances = []
        for i, distance in enumerate(scan.ranges):
            angle = math.degrees(scan.angle_min + i * scan.angle_increment)
            diff  = ((angle - center_deg + 180) % 360) - 180
            if abs(diff) <= width_deg:
                if math.isfinite(distance) and scan.range_min <= distance <= scan.range_max:
                    distances.append(distance)
        return min(distances) if distances else None


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
