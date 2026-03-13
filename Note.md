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

## 2026-03-13（续）

### 今日新增进度

- 完成 `Day 2`：独立 Python VLA 环境搭建与验证。
- 完成 `Day 3`：单张图像预处理链路打通。
- 完成 `Day 4` 的教学版最小推理壳子：`图片 + 指令 -> 统一动作结果`。

### 今天实际打通的能力

- `vla/.venv` 可作为独立虚拟环境使用。
- `check_env.py` 可检查：
  - 当前 Python 是否来自目标虚拟环境
  - `rclpy`、`numpy`、`cv2`、`PIL`
  - `torch` 与 CUDA 是否可见
- `preprocess_image.py` 已能完成：
  - 单图读取
  - resize
  - normalize
  - 输出 preview、`.npy`、元数据 JSON
- `infer_once.py` 已能完成：
  - 接收 `--input`
  - 接收 `--instruction`
  - 加载图片并转换为 RGB
  - 执行教学版 `fake_infer`
  - 输出统一 JSON 结构
  - 通过退出码区分成功、图片加载失败、推理失败等情况

### 今日解决的问题

#### 问题 2：虚拟环境默认激活路径写错

**现象**

- 命令行提示里看起来像进入了 `(.venv)`。
- 但 `check_env.py` 显示：
  - `Python executable: /usr/bin/python3`
  - `Using venv: False`

**根因**

- `vla/README.md` 里还保留着旧项目目录 `/root/workspace/6-AxisRobotArm` 的绝对路径。
- 当前真实项目目录已经变成 `/root/workspace/6-AxisRobotArm-VLA`。

**修复方式**

- 更新了 `vla/README.md` 中的默认命令：
  - 先 `cd /root/workspace/6-AxisRobotArm-VLA`
  - 再 `source vla/.venv/bin/activate`
  - 使用相对路径运行脚本

**修复后正确用法**

```bash
cd /root/workspace/6-AxisRobotArm-VLA
source vla/.venv/bin/activate
python3 vla/check_env.py
```

#### 问题 3：`infer_once.py` 从“能编译”到“能正确运行”的修正过程

**先后修掉的问题**

- 没有真正调用 `main()`
- `args.imput` 拼写错误，应为 `args.input`
- 图片加载失败后仍继续推理
- OpenCV 默认读取为 BGR，后续推理接口更适合统一成 RGB
- 文本指令大小写未统一，关键词匹配不稳
- 输出只打印 Python 字典，不利于后续日志和程序消费
- 教学版 `fake_infer` 的接口形状不够像未来真模型接口

**当前 `infer_once.py` 的工程意义**

- 它不是“真 VLA 模型”
- 它是未来真模型接入前的“统一推理壳”
- 后面只需要替换 `fake_infer(...)` 的内部逻辑，不需要重写整个主程序结构

### 今天学到的关键理解

- 看命令行前缀 `(.venv)` 不够，判断虚拟环境是否正确，要看：
  - `which python3`
  - `echo $VIRTUAL_ENV`
- 图像链路中，OpenCV 读出来默认是 BGR；如果后续模型期望 RGB，最好在入口统一转换。
- 教学阶段先用“规则脑”代替“神经网络脑”是很好的练习：
  - 先把接口和数据流做对
  - 再把内部逻辑从假规则替换成真模型
- 输出结构要尽早稳定，后面才能平滑挂 ROS topic、日志记录和动作映射。

### 当前结论

- 已经具备进入 `Day 5` 的条件。
- 当前最有价值的成果不是“模型变强了”，而是接口变稳定了。
- `infer_once.py` 已经是一个合格的教学版推理壳子。

### 下一步计划

- 进入 `Day 5`：
  - 不再直接返回裸字典
  - 设计更稳定的 `ActionChunk`
  - 统一字段类型、默认值和输出方式
