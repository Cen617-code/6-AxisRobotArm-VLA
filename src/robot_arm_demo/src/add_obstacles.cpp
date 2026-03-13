/**
 * add_obstacles.cpp
 *
 * 向 MoveIt2 Planning Scene 添加障碍物的 ROS2 节点。
 * MoveIt 的 OMPL 规划器会自动绕开这些障碍物进行路径规划。
 *
 * 避障核心逻辑：
 *   1. 构建 CollisionObject 消息（形状 + 位姿 + ADD 操作）
 *   2. 打包进 PlanningScene 消息
 *   3. 发布到 /planning_scene 话题
 *   4. move_group 收到后更新内部世界模型
 *   5. OMPL 采样路径点时检测碰撞 → 自动避开障碍物
 */

#include <geometry_msgs/msg/pose.hpp>
#include <moveit_msgs/msg/collision_object.hpp>
#include <moveit_msgs/msg/planning_scene.hpp>
#include <rclcpp/rclcpp.hpp>
#include <shape_msgs/msg/solid_primitive.hpp>

class ObstaclePublisher : public rclcpp::Node {
public:
  ObstaclePublisher() : Node("obstacle_publisher") {
    // 发布到 /planning_scene 话题，move_group 会订阅此话题
    planning_scene_pub_ =
        this->create_publisher<moveit_msgs::msg::PlanningScene>(
            "/planning_scene", 10);

    // 等待 2 秒让 move_group 先就绪
    timer_ = this->create_wall_timer(
        std::chrono::seconds(2),
        std::bind(&ObstaclePublisher::publish_obstacles, this));

    RCLCPP_INFO(this->get_logger(),
                "ObstaclePublisher 节点已启动，2秒后发布障碍物...");
  }

private:
  void publish_obstacles() {
    // 只发布一次
    timer_->cancel();

    moveit_msgs::msg::PlanningScene planning_scene_msg;
    planning_scene_msg.is_diff = true; // 增量更新，不替换整个场景

    // --- 障碍物 1: Box（桌面） ---
    {
      moveit_msgs::msg::CollisionObject obj;
      obj.header.frame_id = "world";
      obj.header.stamp = this->now();
      obj.id = "table";
      obj.operation = moveit_msgs::msg::CollisionObject::ADD;

      // 形状：0.6 x 0.4 x 0.02 的薄板
      shape_msgs::msg::SolidPrimitive box;
      box.type = shape_msgs::msg::SolidPrimitive::BOX;
      box.dimensions = {0.6, 0.4, 0.02}; // 长, 宽, 高 (x, y, z)

      // 位姿：放在机械臂前方
      geometry_msgs::msg::Pose pose;
      pose.position.x = 0.4;
      pose.position.y = 0.0;
      pose.position.z = 0.3;
      pose.orientation.w = 1.0;

      obj.primitives.push_back(box);
      obj.primitive_poses.push_back(pose);
      planning_scene_msg.world.collision_objects.push_back(obj);

      RCLCPP_INFO(this->get_logger(),
                  "添加障碍物: table (Box 0.6x0.4x0.02) @ (0.4, 0.0, 0.3)");
    }

    // --- 障碍物 2: Cylinder（柱子） ---
    {
      moveit_msgs::msg::CollisionObject obj;
      obj.header.frame_id = "world";
      obj.header.stamp = this->now();
      obj.id = "pillar";
      obj.operation = moveit_msgs::msg::CollisionObject::ADD;

      // 形状：高 0.5m，半径 0.05m 的圆柱
      shape_msgs::msg::SolidPrimitive cylinder;
      cylinder.type = shape_msgs::msg::SolidPrimitive::CYLINDER;
      cylinder.dimensions = {0.5, 0.05}; // 高度, 半径

      // 位姿：放在机械臂侧面
      geometry_msgs::msg::Pose pose;
      pose.position.x = 0.2;
      pose.position.y = 0.3;
      pose.position.z = 0.25;
      pose.orientation.w = 1.0;

      obj.primitives.push_back(cylinder);
      obj.primitive_poses.push_back(pose);
      planning_scene_msg.world.collision_objects.push_back(obj);

      RCLCPP_INFO(
          this->get_logger(),
          "添加障碍物: pillar (Cylinder h=0.5 r=0.05) @ (0.2, 0.3, 0.25)");
    }

    // --- 障碍物 3: Sphere（球体） ---
    {
      moveit_msgs::msg::CollisionObject obj;
      obj.header.frame_id = "world";
      obj.header.stamp = this->now();
      obj.id = "ball";
      obj.operation = moveit_msgs::msg::CollisionObject::ADD;

      // 形状：半径 0.08m 的球
      shape_msgs::msg::SolidPrimitive sphere;
      sphere.type = shape_msgs::msg::SolidPrimitive::SPHERE;
      sphere.dimensions = {0.08}; // 半径

      // 位姿：放在工作空间中
      geometry_msgs::msg::Pose pose;
      pose.position.x = 0.3;
      pose.position.y = -0.2;
      pose.position.z = 0.5;
      pose.orientation.w = 1.0;

      obj.primitives.push_back(sphere);
      obj.primitive_poses.push_back(pose);
      planning_scene_msg.world.collision_objects.push_back(obj);

      RCLCPP_INFO(this->get_logger(),
                  "添加障碍物: ball (Sphere r=0.08) @ (0.3, -0.2, 0.5)");
    }

    // 发布规划场景
    planning_scene_pub_->publish(planning_scene_msg);
    RCLCPP_INFO(this->get_logger(),
                "✅ 已发布 3 个障碍物到 /planning_scene，MoveIt 将自动避障！");
  }

  rclcpp::Publisher<moveit_msgs::msg::PlanningScene>::SharedPtr
      planning_scene_pub_;
  rclcpp::TimerBase::SharedPtr timer_;
};

int main(int argc, char **argv) {
  rclcpp::init(argc, argv);
  auto node = std::make_shared<ObstaclePublisher>();
  rclcpp::spin(node);
  rclcpp::shutdown();
  return 0;
}
