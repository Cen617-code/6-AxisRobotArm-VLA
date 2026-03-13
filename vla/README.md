# VLA 环境工作区

这个目录专门给后续视觉-语言-动作模型使用，不和当前 ROS 2 `ament_cmake` 包混在一起。

## 设计原则

- Python 跑视觉、任务理解、VLA 推理
- C++ 跑底层控制、MoveIt 执行、逆运动学
- 通过 ROS 2 topic / service 通信，不直接耦合进现有 C++ 包

## 当前阶段

当前处于 `Day 2`：

- 建立独立虚拟环境
- 确认 `rclpy` 与深度学习环境可共存
- 为后续单图推理和 ROS 节点预留工作区

目前已经进入 `Day 3`：

- 准备 1 到 3 张测试图
- 完成单图读取、resize、normalize
- 保存可视化结果和 `.npy` 张量
- 定义 Day 3 的统一输入 / 输出接口

## 建议用法

先进入项目根目录：

```bash
cd /root/workspace/6-AxisRobotArm-VLA
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

## 当前文件说明

- `check_env.py`
  - Day 2 环境自检脚本
  - 用来检查虚拟环境、ROS Python 包和 torch / CUDA 状态
- `preprocess_image.py`
  - Day 3 单图预处理脚本
  - 输入一张本地图像，输出 preview、`.npy` 和元数据 JSON
