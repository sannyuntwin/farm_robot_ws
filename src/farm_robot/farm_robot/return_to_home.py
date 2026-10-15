import math

import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist
from nav_msgs.msg import Odometry
from std_msgs.msg import Bool


class ReturnToHome(Node):
    def __init__(self):
        super().__init__('return_to_home')

        self._home_x   = 0.0
        self._home_y   = 0.0
        self._x        = 0.0
        self._y        = 0.0
        self._yaw      = 0.0
        self._active   = False
        self._home_set = False

        self._forward_speed    = 0.15
        self._turn_speed       = 0.50
        self._arrival_radius   = 0.20   # m — stop when within this distance
        self._angle_threshold  = 0.10   # rad — switch to driving once aligned

        self.create_subscription(Odometry, '/odom',        self._odom_cb,    10)
        self.create_subscription(Bool,     '/return_home', self._trigger_cb, 10)
        self._pub = self.create_publisher(Twist, '/cmd_vel', 10)
        self.create_timer(0.1, self._control_loop)   # 10 Hz

        self.get_logger().info(
            'Return to home ready — publish True to /return_home to activate.')

    def _odom_cb(self, msg):
        self._x   = msg.pose.pose.position.x
        self._y   = msg.pose.pose.position.y
        q         = msg.pose.pose.orientation
        self._yaw = 2.0 * math.atan2(q.z, q.w)
        if not self._home_set:
            self._home_x   = self._x
            self._home_y   = self._y
            self._home_set = True
            self.get_logger().info(
                f'Home recorded: ({self._home_x:.3f}, {self._home_y:.3f})')

    def _trigger_cb(self, msg):
        if msg.data and not self._active:
            self._active = True
            self.get_logger().info(
                f'Returning to ({self._home_x:.3f}, {self._home_y:.3f})…')

    def _control_loop(self):
        cmd = Twist()
        if not self._active or not self._home_set:
            self._pub.publish(cmd)
            return

        dx   = self._home_x - self._x
        dy   = self._home_y - self._y
        dist = math.sqrt(dx * dx + dy * dy)

        if dist < self._arrival_radius:
            self._active = False
            self.get_logger().info('Arrived at home.')
            self._pub.publish(cmd)
            return

        heading   = math.atan2(dy, dx)
        angle_err = (heading - self._yaw + math.pi) % (2 * math.pi) - math.pi

        if abs(angle_err) > self._angle_threshold:
            cmd.angular.z = self._turn_speed * (1.0 if angle_err > 0 else -1.0)
        else:
            cmd.linear.x  = self._forward_speed
            cmd.angular.z = 1.0 * angle_err   # proportional heading correction

        self._pub.publish(cmd)


def main(args=None):
    rclpy.init(args=args)
    node = ReturnToHome()
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
