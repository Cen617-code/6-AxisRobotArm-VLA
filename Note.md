# 学习记录

## 2026-03-13

### 今日进度

- 完成 `Day 1`：确认现有 ROS 2 机械臂仿真基线可复现。
- 已确认 `robot_arm_demo` 与 `robot_arm_moveit_config` 可以正常编译。
- 已确认 Gazebo、MoveIt、轨迹控制器、避障链路可用。

### 今天验证通过的能力

- `colcon build --packages-select robot_arm_demo robot_arm_moveit_config` 通过。
- Gazebo 能加载 6 轴机械臂模型。
- MoveIt 能进行 `Plan & Execute`。
- 障碍物发布后，规划结果可以避障。

### 关键 topic 认识

- `/robot_description`
  - 机器人模型描述，说明机器人本体已经成功加载。
- `/joint_states`
  - 当前关节状态，是后续状态感知的基础输入。
- `/arm_controller/joint_trajectory`
  - 轨迹控制器的执行入口之一，说明底层控制链路已经存在。
- `/planning_scene`
  - MoveIt 的世界模型输入，障碍物就是通过这条链路进入规划器。
- `/monitored_planning_scene`
  - MoveIt 内部监控后的规划场景。

### 今日解决的问题

#### 问题 1：Gazebo 打开了，但看不到机械臂

**现象**

- Gazebo 能启动。
- GUI 能打开。
- 但场景里没有机械臂模型。

**根因**

- `ros_gz_sim create` 原先通过 `-topic /robot_description` 等待模型描述。
- 实际运行时，创建器一直在等待 `/robot_description` 话题消息，导致实体没有真正生成到 Gazebo 世界里。

**修复方式**

- 修改了 [gazebo.launch.py](/root/workspace/6-AxisRobotArm/src/robot_arm_demo/launch/gazebo.launch.py)，不再依赖 `-topic /robot_description`。
- 改为直接把 `xacro` 生成出的 URDF 字符串传给 `ros_gz_sim create` 的 `-string` 参数。

**修复后验证信号**

- 日志中出现 `Entity creation successful`
- 日志中出现 `Configured and activated arm_controller`

### 今天学到的工程理解

- 机械臂系统可以类比为“身体”：
  - Gazebo 是身体所在的物理世界。
  - MoveIt 是运动规划大脑里的“路径设计师”。
  - `joint_trajectory_controller` 是真正执行动作的“肌肉控制器”。
- VLA 不应该一上来直接控制每个关节。
- 更稳妥的做法是：
  - Python 负责“看图 + 理解任务 + 给出动作建议”
  - C++ / MoveIt 负责“把动作建议翻译成安全可执行轨迹”

### 当前结论

- 现有 6 轴机械臂仿真底盘健康。
- 已具备进入 `Day 2` 的条件。
- 下一步重点不是继续调 Gazebo，而是建立独立 Python VLA 环境。

### 明日计划

- 建立 `vla/` 目录。
- 创建独立 Python 虚拟环境。
- 验证 `rclpy` 与深度学习框架能否共存。
- 检查 GPU 是否可见，至少保底 CPU 可运行。
