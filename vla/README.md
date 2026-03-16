# VLA 环境工作区

这个目录专门给后续视觉-语言-动作模型使用，不和当前 ROS 2 `ament_cmake` 包混在一起。

## 设计原则

- Python 跑视觉、任务理解、VLA 推理
- C++ 跑底层控制、MoveIt 执行、逆运动学
- 通过 ROS 2 topic / service 通信，不直接耦合进现有 C++ 包

## 当前阶段

当前已完成：

- `Day 2`
  - 建立独立虚拟环境
  - 确认 `rclpy` 与深度学习环境可共存
- `Day 3`
  - 完成单图读取、resize、normalize
  - 保存 preview、`.npy` 和元数据 JSON
- `Day 4`
  - 建立教学版离线推理壳
  - 打通 `图片 + 指令 -> ActionChunk`
- `Day 5`
  - 统一动作输出格式
  - 固定 `delta_xyz / delta_rpy / confidence / terminate`
- `Day 6`
  - 建立 ROS 2 Python 推理节点
  - 订阅 `/vla/task_text`
  - 发布 `/vla/action_delta`

下一步将进入 `Day 7`：

- 读取当前 `/end_effector_pose`
- 将 `delta_xyz` 映射成安全 `/vla/goal_pose`
- 增加单步位移裁剪和工作空间边界限制

## 建议用法

先进入项目根目录：

```bash
cd /home/cen123/workspace/6-AxisRobotArm-VLA
```

先激活虚拟环境：

```bash
source vla/.venv/bin/activate
```

如果后续需要和 ROS 2 节点交互，再额外 source：

```bash
source /opt/ros/jazzy/setup.bash
source install/setup.bash
```

运行环境自检：

```bash
python3 vla/check_env.py
```

运行单图预处理：

```bash
python3 vla/preprocess_image.py \
  --input vla/data/raw/sample_01.png \
  --stem sample_01
```

运行一次离线推理：

```bash
python3 vla/infer_once.py \
  --input vla/data/raw/sample_01.png \
  --instruction "move right"
```

## Day 6 验收方式

终端 1：启动 ROS 2 推理节点

```bash
cd /home/cen123/workspace/6-AxisRobotArm-VLA
source /opt/ros/jazzy/setup.bash
source vla/.venv/bin/activate
python3 vla/vla_action_node.py
```

终端 2：监听动作输出

```bash
source /opt/ros/jazzy/setup.bash
ros2 topic echo /vla/action_delta geometry_msgs/msg/TwistStamped --once
```

终端 3：发送任务文本

```bash
source /opt/ros/jazzy/setup.bash
ros2 topic pub --once /vla/task_text std_msgs/msg/String "{data: 'move right'}"
```

### Day 6 常见现象

- 如果直接运行：

```bash
ros2 topic echo /vla/action_delta
```

可能会看到：

```text
WARNING: topic [/vla/action_delta] does not appear to be published yet
Could not determine the type for the passed topic
```

这通常不是代码报错，而是因为：

- 节点还没启动
- 节点已经完成单次任务后退出
- `echo` 没有显式写出消息类型，ROS 2 一时无法自动推断

更稳妥的方式是显式写出类型：

```bash
ros2 topic echo /vla/action_delta geometry_msgs/msg/TwistStamped --once
```

## 当前文件说明

- `check_env.py`
  - Day 2 环境自检脚本
  - 用来检查虚拟环境、ROS Python 包和 torch / CUDA 状态
- `preprocess_image.py`
  - Day 3 单图预处理脚本
  - 输入一张本地图像，输出 preview、`.npy` 和元数据 JSON
- `infer_once.py`
  - Day 4 / Day 5 教学版推理壳
  - 输入图片和文本，输出统一 `ActionChunk`
- `vla_action_node.py`
  - Day 6 ROS 2 Python 节点
  - 接收 `/vla/task_text`
  - 发布 `/vla/action_delta`
