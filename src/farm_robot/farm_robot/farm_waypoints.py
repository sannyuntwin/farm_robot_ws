import math

import rclpy
from rclpy.action import ActionClient
from rclpy.node import Node

from geometry_msgs.msg import PoseStamped
from nav2_msgs.action import FollowWaypoints


# Farm patrol route — edit these positions to match your map
WAYPOINTS = [
    (1.0, -3.5, 1.57),   # spawn position
    (1.0,  0.0, 1.57),   # mid field
    (1.0,  3.5, 1.57),   # far end
    (-1.0, 3.5, -1.57),  # next row far end
    (-1.0, 0.0, -1.57),  # next row mid
    (-1.0, -3.5, -1.57), # next row start
]


class FarmWaypointNavigator(Node):
    def __init__(self):
        super().__init__('farm_waypoint_navigator')
        self._client = ActionClient(self, FollowWaypoints, 'follow_waypoints')
        self.get_logger().info('Waiting for Nav2 waypoint follower...')
        self._client.wait_for_server()
        self.get_logger().info('Ready. Sending patrol route...')
        self._send_waypoints()

    def _make_pose(self, x, y, yaw):
        pose = PoseStamped()
        pose.header.frame_id = 'map'
        pose.header.stamp = self.get_clock().now().to_msg()
        pose.pose.position.x = float(x)
        pose.pose.position.y = float(y)
        pose.pose.orientation.z = math.sin(yaw / 2.0)
        pose.pose.orientation.w = math.cos(yaw / 2.0)
        return pose

    def _send_waypoints(self):
        goal = FollowWaypoints.Goal()
        goal.poses = [self._make_pose(x, y, yaw) for x, y, yaw in WAYPOINTS]
        self.get_logger().info(f'Sending {len(goal.poses)} waypoints...')
        future = self._client.send_goal_async(
            goal, feedback_callback=self._on_feedback
        )
        future.add_done_callback(self._on_goal_response)

    def _on_goal_response(self, future):
        handle = future.result()
        if not handle.accepted:
            self.get_logger().error('Patrol rejected by Nav2.')
            return
        self.get_logger().info('Patrol accepted.')
        handle.get_result_async().add_done_callback(self._on_result)

    def _on_feedback(self, feedback_msg):
        idx = feedback_msg.feedback.current_waypoint
        self.get_logger().info(f'Waypoint {idx + 1}/{len(WAYPOINTS)}')

    def _on_result(self, future):
        missed = future.result().result.missed_waypoints
        if missed:
            self.get_logger().warn(f'Missed waypoints: {list(missed)}')
        else:
            self.get_logger().info('Patrol complete — all waypoints reached.')


def main(args=None):
    rclpy.init(args=args)
    node = FarmWaypointNavigator()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
