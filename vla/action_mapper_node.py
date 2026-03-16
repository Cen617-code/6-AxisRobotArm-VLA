from dataclasses import dataclass
import math
import rclpy
from geometry_msgs.msg import PoseStamped, TwistStamped
from rclpy.executors import ExternalShutdownException
from rclpy.node import Node


@dataclass
class WorkspaceLimits:
    min_x: float
    max_x: float
    min_y: float
    max_y: float
    min_z: float
    max_z: float


class ActionMapperNode(Node):
    def __init__(self):
        super().__init__('action_mapper_node')

        # Day 7 先把工作空间近似成一个安全盒子，避免目标点直接越界。
        self.declare_parameter('expected_frame', 'base_link')
        self.declare_parameter('max_step_distance', 0.02)
        self.declare_parameter('workspace.min_x', 0.05)
        self.declare_parameter('workspace.max_x', 0.75)
        self.declare_parameter('workspace.min_y', -0.45)
        self.declare_parameter('workspace.max_y', 0.45)
        self.declare_parameter('workspace.min_z', 0.05)
        self.declare_parameter('workspace.max_z', 0.80)

        self.expected_frame = self.get_parameter(
            'expected_frame').get_parameter_value().string_value
        self.max_step_distance = self.get_parameter(
            'max_step_distance').get_parameter_value().double_value
        self.workspace = WorkspaceLimits(
            min_x=self.get_parameter('workspace.min_x').get_parameter_value().double_value,
            max_x=self.get_parameter('workspace.max_x').get_parameter_value().double_value,
            min_y=self.get_parameter('workspace.min_y').get_parameter_value().double_value,
            max_y=self.get_parameter('workspace.max_y').get_parameter_value().double_value,
            min_z=self.get_parameter('workspace.min_z').get_parameter_value().double_value,
            max_z=self.get_parameter('workspace.max_z').get_parameter_value().double_value,
        )

        self.current_pose = None

        self.goal_pose_publisher = self.create_publisher(
            PoseStamped,
            '/vla/goal_pose',
            10
        )
        self.pose_subscription = self.create_subscription(
            PoseStamped,
            '/end_effector_pose',
            self.on_pose,
            10
        )
        self.action_subscription = self.create_subscription(
            TwistStamped,
            '/vla/action_delta',
            self.on_action_delta,
            10
        )

        self.get_logger().info(
            'Action Mapper Node 已启动，等待 /end_effector_pose 与 /vla/action_delta...')

    def on_pose(self, msg: PoseStamped):
        if not self.is_supported_frame(msg.header.frame_id):
            self.get_logger().warn(
                f'忽略末端位姿：frame_id={msg.header.frame_id}，'
                f'期望={self.expected_frame}'
            )
            return

        self.current_pose = msg

    def on_action_delta(self, msg: TwistStamped):
        if self.current_pose is None:
            self.get_logger().warn('尚未收到 /end_effector_pose，暂不处理动作增量')
            return

        if not self.is_supported_frame(msg.header.frame_id):
            self.get_logger().warn(
                f'忽略动作增量：frame_id={msg.header.frame_id}，'
                f'期望={self.expected_frame}'
            )
            return

        delta_xyz = [
            float(msg.twist.linear.x),
            float(msg.twist.linear.y),
            float(msg.twist.linear.z),
        ]

        clipped_delta_xyz, was_step_clipped = self.clip_delta_step(delta_xyz)
        goal_pose = self.build_goal_pose(clipped_delta_xyz)
        boundary_clipped = self.apply_workspace_limits(goal_pose)

        self.goal_pose_publisher.publish(goal_pose)

        self.get_logger().info(
            '已发布 /vla/goal_pose | '
            f'delta_xyz={self.format_vector(delta_xyz)} | '
            f'clipped_delta_xyz={self.format_vector(clipped_delta_xyz)} | '
            f'step_clipped={was_step_clipped} | '
            f'boundary_clipped={boundary_clipped}'
        )

    def is_supported_frame(self, frame_id: str) -> bool:
        normalized_frame = frame_id or self.expected_frame
        return normalized_frame == self.expected_frame

    def clip_delta_step(self, delta_xyz: list[float]) -> tuple[list[float], bool]:
        distance = math.sqrt(sum(value * value for value in delta_xyz))
        if distance <= self.max_step_distance or distance == 0.0:
            return delta_xyz, False

        scale = self.max_step_distance / distance
        return [value * scale for value in delta_xyz], True

    def build_goal_pose(self, delta_xyz: list[float]) -> PoseStamped:
        goal_pose = PoseStamped()
        goal_pose.header.stamp = self.get_clock().now().to_msg()
        goal_pose.header.frame_id = self.expected_frame

        goal_pose.pose.position.x = self.current_pose.pose.position.x + delta_xyz[0]
        goal_pose.pose.position.y = self.current_pose.pose.position.y + delta_xyz[1]
        goal_pose.pose.position.z = self.current_pose.pose.position.z + delta_xyz[2]

        # Day 7 先保持当前姿态不变，只处理位置增量。
        goal_pose.pose.orientation = self.current_pose.pose.orientation
        return goal_pose

    def apply_workspace_limits(self, goal_pose: PoseStamped) -> bool:
        original_xyz = (
            goal_pose.pose.position.x,
            goal_pose.pose.position.y,
            goal_pose.pose.position.z,
        )

        goal_pose.pose.position.x = min(
            max(goal_pose.pose.position.x, self.workspace.min_x),
            self.workspace.max_x
        )
        goal_pose.pose.position.y = min(
            max(goal_pose.pose.position.y, self.workspace.min_y),
            self.workspace.max_y
        )
        goal_pose.pose.position.z = min(
            max(goal_pose.pose.position.z, self.workspace.min_z),
            self.workspace.max_z
        )

        clipped_xyz = (
            goal_pose.pose.position.x,
            goal_pose.pose.position.y,
            goal_pose.pose.position.z,
        )
        return clipped_xyz != original_xyz

    def format_vector(self, vector: list[float]) -> str:
        return '[' + ', '.join(f'{value:.4f}' for value in vector) + ']'


def main(args=None):
    rclpy.init(args=args)
    node = None

    try:
        node = ActionMapperNode()
        rclpy.spin(node)
    except (KeyboardInterrupt, ExternalShutdownException):
        pass
    finally:
        if node is not None:
            node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == '__main__':
    main()