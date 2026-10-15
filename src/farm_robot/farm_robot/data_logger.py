import csv
import math
import os
from datetime import datetime

import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist
from nav_msgs.msg import Odometry
from sensor_msgs.msg import LaserScan


class DataLogger(Node):
    def __init__(self):
        super().__init__('data_logger')

        self._x     = 0.0
        self._y     = 0.0
        self._yaw   = 0.0
        self._lin   = 0.0
        self._ang   = 0.0
        self._front = float('nan')
        self._left  = float('nan')
        self._right = float('nan')
        self._rows  = 0

        log_dir = os.path.expanduser('~/farm_robot_logs')
        os.makedirs(log_dir, exist_ok=True)
        ts       = datetime.now().strftime('%Y%m%d_%H%M%S')
        log_path = os.path.join(log_dir, f'robot_log_{ts}.csv')

        self._file   = open(log_path, 'w', newline='')
        self._writer = csv.writer(self._file)
        self._writer.writerow([
            'timestamp', 'x', 'y', 'yaw_deg',
            'linear_vel', 'angular_vel',
            'front_dist', 'left_dist', 'right_dist',
        ])
        self.get_logger().info(f'Logging to {log_path}')

        self.create_subscription(Odometry,  '/odom',       self._odom_cb,  10)
        self.create_subscription(Twist,     '/cmd_vel',    self._vel_cb,   10)
        self.create_subscription(LaserScan, '/scan_fixed', self._scan_cb,  10)
        self.create_timer(0.2, self._write_row)   # 5 Hz

    def _odom_cb(self, msg):
        self._x   = msg.pose.pose.position.x
        self._y   = msg.pose.pose.position.y
        q         = msg.pose.pose.orientation
        self._yaw = math.degrees(2.0 * math.atan2(q.z, q.w))

    def _vel_cb(self, msg):
        self._lin = msg.linear.x
        self._ang = msg.angular.z

    def _sector_min(self, scan, center_deg, half_width_deg):
        dists = []
        for i, d in enumerate(scan.ranges):
            ang = math.degrees(scan.angle_min + i * scan.angle_increment)
            if abs(((ang - center_deg + 180) % 360) - 180) <= half_width_deg:
                if math.isfinite(d) and scan.range_min <= d <= scan.range_max:
                    dists.append(d)
        return min(dists) if dists else float('nan')

    def _scan_cb(self, scan):
        self._front = self._sector_min(scan,   0, 25)
        self._left  = self._sector_min(scan,  90, 20)
        self._right = self._sector_min(scan, -90, 20)

    def _fmt(self, v, decimals=3):
        return f'{v:.{decimals}f}' if math.isfinite(v) else ''

    def _write_row(self):
        now = self.get_clock().now().nanoseconds / 1e9
        self._writer.writerow([
            f'{now:.3f}',
            f'{self._x:.4f}',
            f'{self._y:.4f}',
            f'{self._yaw:.2f}',
            f'{self._lin:.4f}',
            f'{self._ang:.4f}',
            self._fmt(self._front),
            self._fmt(self._left),
            self._fmt(self._right),
        ])
        self._rows += 1
        if self._rows % 50 == 0:   # flush every 10 s
            self._file.flush()

    def destroy_node(self):
        self._file.flush()
        self._file.close()
        self.get_logger().info(f'Log closed — {self._rows} rows written.')
        super().destroy_node()


def main(args=None):
    rclpy.init(args=args)
    node = DataLogger()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
