# 🤖 6-Axis Robot Arm — ROS2 Jazzy + Gazebo + MoveIt2

一个完整的 6 轴机械臂学习项目，涵盖 URDF 建模、正/逆运动学(C++)、Gazebo Harmonic 物理仿真、MoveIt2 运动规划与避障。

![演示](assets/演示-1862155.gif)

## 技术栈

| 层级 | 技术 |
|------|------|
| 操作系统 | Ubuntu 24.04 |
| 机器人框架 | ROS2 Jazzy |
| 仿真引擎 | Gazebo Harmonic (via `ros_gz`) |
| 运动规划 | MoveIt2 + OMPL (RRTConnect) |
| 控制器 | ros2_control (`joint_trajectory_controller`) |
| 数学库 | Eigen3 |
| 编程语言 | C++17 / Python 3 |

## 项目结构

```
6-AxisRobotArm-VLA/
├── README.md               # 本文件
├── Note.md                 # 知识点 + 问题记录
├── Plan.md                 # 学习计划
└── src/
    ├── robot_arm_demo/             # 核心包
    │   ├── urdf/
    │   │   ├── 6_axis_arm.urdf          # 原始 URDF
    │   │   └── 6_axis_arm.urdf.xacro    # Xacro 版本（含 ros2_control）
    │   ├── config/
    │   │   └── controllers.yaml         # ros2_control 控制器配置
    │   ├── launch/
    │   │   ├── display.launch.py        # RViz 可视化
    │   │   └── gazebo.launch.py         # Gazebo 仿真
    │   └── src/
    │       ├── kinematics_solver.cpp    # FK/IK 求解节点 (Eigen)
    │       └── add_obstacles.cpp        # 障碍物发布节点
    │
    └── robot_arm_moveit_config/        # MoveIt2 配置包
        ├── config/
        │   ├── 6_axis_arm.srdf          # 规划组 + 碰撞矩阵
        │   ├── kinematics.yaml          # KDL 运动学求解器
        │   ├── joint_limits.yaml        # 关节速度/加速度限制
        │   ├── moveit_controllers.yaml  # MoveIt → ros2_control 映射
        │   └── ompl_planning.yaml       # OMPL 规划器配置
        └── launch/
            ├── move_group.launch.py     # MoveIt move_group 节点
            └── moveit_rviz.launch.py    # MoveIt + RViz 一键启动
```

## 安装教程

### 1. 安装 ROS2 Jazzy

```bash
# 参照 ROS2 官方文档安装 ROS2 Jazzy
# https://docs.ros.org/en/jazzy/Installation.html
sudo apt update && sudo apt install ros-jazzy-desktop
```

### 2. 安装依赖

```bash
# Gazebo 相关
sudo apt install ros-jazzy-ros-gz ros-jazzy-gz-ros2-control

# ros2_control
sudo apt install ros-jazzy-joint-state-broadcaster ros-jazzy-joint-trajectory-controller

# MoveIt2
sudo apt install ros-jazzy-moveit

# Eigen3
sudo apt install libeigen3-dev

# xacro
sudo apt install ros-jazzy-xacro
```

### 3. 克隆与编译

```bash
cd /home/cen123/workspace/6-AxisRobotArm-VLA
colcon build
source install/setup.bash
```

## 使用方法

### A. RViz 可视化（仅查看模型）

```bash
source /home/cen123/workspace/6-AxisRobotArm-VLA/install/setup.bash
ros2 launch robot_arm_demo display.launch.py
```

### B. Gazebo 仿真 + MoveIt 运动规划

```bash
# 终端 1 — 启动物理仿真
ros2 daemon stop && killall -9 gz ruby 2>/dev/null; sleep 1
source /home/cen123/workspace/6-AxisRobotArm-VLA/install/setup.bash
ros2 launch robot_arm_demo gazebo.launch.py
# 等待 "Successfully loaded controller arm_controller into state active"

# 终端 2 — 启动 MoveIt + RViz
source /home/cen123/workspace/6-AxisRobotArm-VLA/install/setup.bash
ros2 launch robot_arm_moveit_config moveit_rviz.launch.py
# 等待 "You can start planning now!"
# 在 RViz 中：Fixed Frame → world，Add → RobotModel + MotionPlanning
# 拖动交互球 → Plan & Execute
```

### C. 添加障碍物体验避障

```bash
# 终端 3（Gazebo + MoveIt 运行中）
source /home/cen123/workspace/6-AxisRobotArm-VLA/install/setup.bash
ros2 run robot_arm_demo add_obstacles
# 在 RViz 中会出现 3 个障碍物，MoveIt 规划时自动绕开
```

## 项目进度

- [x] Phase 1: URDF 建模 + RViz 可视化
- [x] Phase 2: C++ 正/逆运动学 (Eigen + Jacobian)
- [x] Phase 3: Gazebo Harmonic 仿真 + ros2_control
- [x] Phase 4: MoveIt2 运动规划集成
- [x] Phase 5: 避障（Planning Scene 碰撞对象）
