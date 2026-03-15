from pathlib import Path
import rclpy
from rclpy.executors import ExternalShutdownException
from rclpy.node import Node
from std_msgs.msg import String
from geometry_msgs.msg import TwistStamped
from infer_once import load_image, fake_infer, build_action_chunk

DEFAULT_IMAGE_PATH = (
    Path(__file__).resolve().parent
    / 'data'
    / 'processed'
    / 'sample_01_test.preview.png'
)

class VLAActionNode(Node):
    def __init__(self):
        super().__init__('vla_action_node')

        self.declare_parameter('image_path', str(DEFAULT_IMAGE_PATH))
        image_path = self.get_parameter('image_path').get_parameter_value().string_value

        self.image, _, _ = load_image(image_path)
        if self.image is None:
            raise ValueError(f"图片加载失败: {image_path}")
        
        self.publisher = self.create_publisher(
            TwistStamped,
            '/vla/action_delta',
            10)
        
        self.subscription = self.create_subscription(
            String,
            '/vla/task_text',
            self.on_task_text,
            10
        )
        
        self.shutdown_timer = None

        self.get_logger().info(f'使用固定图片: {image_path}')
        self.get_logger().info('VLA Action Node 已启动，等待任务...')
        self.finished = False

    def on_task_text(self, msg):
        if self.finished:
            return
        self.get_logger().info(f"收到任务文本：{msg.data}")

        action_chunk = build_action_chunk(fake_infer(self.image, msg.data), msg.data, self.image)
        
        self.get_logger().info(f"confidence: {action_chunk.confidence}")
        self.get_logger().info(f"terminate: {action_chunk.terminate}")

        self.publish_twist(action_chunk)

        self.get_logger().info("任务完成，节点退出")
        self.finished = True

        if self.shutdown_timer is None:
            self.shutdown_timer = self.create_timer(0.5, self.shutdown_callback)

    def shutdown_callback(self):
        if self.shutdown_timer is not None:
            self.shutdown_timer.cancel()
            self.destroy_timer(self.shutdown_timer)
            self.shutdown_timer = None

        if rclpy.ok():
            rclpy.shutdown()

    def publish_twist(self, action_chunk):
        twist_msg = TwistStamped()
        twist_msg.header.stamp = self.get_clock().now().to_msg()
        twist_msg.header.frame_id = 'base_link'
        
        twist_msg.twist.linear.x = action_chunk.delta_xyz[0]
        twist_msg.twist.linear.y = action_chunk.delta_xyz[1]
        twist_msg.twist.linear.z = action_chunk.delta_xyz[2]

        twist_msg.twist.angular.x = action_chunk.delta_rpy[0]
        twist_msg.twist.angular.y = action_chunk.delta_rpy[1]
        twist_msg.twist.angular.z = action_chunk.delta_rpy[2]

        self.publisher.publish(twist_msg)
        self.get_logger().info('已发布 /vla/action_delta')

def main(args=None):
    rclpy.init(args=args)
    node = None

    try:
        node = VLAActionNode()
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
