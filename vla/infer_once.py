import argparse
import cv2
import json
import sys
import math
from datetime import datetime
from dataclasses import dataclass, field
from typing import Any


def parse_args() -> argparse.Namespace:
    """
    解析命令行参数
    设计思路：
    --input: 输入图片的路径
    --instruction: 对图片的操作指令
    """

    parser = argparse.ArgumentParser(
        description="图片推理程序 - 接收图片和程序进行推理",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    #必须参数
    parser.add_argument(
        "--input",
        type=str,
        required=True,
        help="输入本地文件的路径"
    )

    parser.add_argument(
        "--instruction",
        type=str,
        required=True,
        help="对图片的操作指令"
    )

    return parser.parse_args()

def load_image(image_path):
    """
    打开图片，确认尺寸
    参数:
        image_path: 图片路径
    返回:
        tuple: (image, height, width) 或 (None, 0, 0) 如果读取失败
    """
    # 尝试读取图片
    image_bgr = cv2.imread(image_path)
    if image_bgr is None:
        log(f"警告：无法读取图片 {image_path}")
        return None, 0, 0
    
    image_rgb = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2RGB)
    
    #获取图片尺寸
    height, width = image_rgb.shape[:2]

    log(f"图片加载成功：{width}×{height}")
    return image_rgb, height, width

def is_finite_number(value: Any) -> bool:
    if isinstance(value, bool):
        return False
    if not isinstance(value, (int, float)):
        return False
    return math.isfinite(value)

def validate_vector(vector: Any, field_name: str):
    """
    校验长度为3的向量字段
    """
    if not isinstance(vector, (list, tuple)):
        return False, f"{field_name}必须是列表或元组"
    if len(vector) != 3:
        return False, f"{field_name}长度必须为3"
    if not all(is_finite_number(x) for x in vector):
        return False, f"{field_name}的元素必须为int或float" 
    return True, "验证通过"

@dataclass
class ActionChunk:
    """
    Day 5 的统一动作结构
    未来无论后端是规则、Octo 还是其他 VLA，都先汇总成这个结构。
    """

    delta_xyz: list[float]
    delta_rpy: list[float] = field(default_factory=lambda: [0.0, 0.0, 0.0])
    confidence: float = 0.0
    terminate: bool = False
    metadata: dict[str, Any] = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda:datetime.now().isoformat())

    def validate(self):
        """
        集中校验动作协议，避免非法值流向下游控制模块
        """
        is_valid, msg = validate_vector(self.delta_xyz, "delta_xyz")
        if not is_valid:
            return False, msg
        
        is_valid, msg = validate_vector(self.delta_rpy, "delta_rpy")
        if not is_valid:
            return False, msg
        
        if not is_finite_number(self.confidence):
            return False, "confidence必须为实数"
        if not 0.0 <= float(self.confidence) <= 1.0:
            return False, "confidence必须为[0,1]范围内的实数"
        
        if not isinstance(self.terminate, bool):
            return False, "terminate必须为布尔值"
        
        if not isinstance(self.metadata, dict):
            return False, "metadata必须为字典类型"
        
        return True, "验证通过"
    
    def to_dict(self) -> dict[str, Any]:
        """
        统一输出成可序列化字典，并在出口再次做一次强校验
        """
        is_valid, msg = self.validate()
        if not is_valid:
            raise ValueError(msg)
        
        return {
            "timestamp": self.timestamp,
            "delta_xyz": [float(x) for x in self.delta_xyz],
            "delta_rpy": [float(x) for x in self.delta_rpy],
            "confidence": float(self.confidence),
            "terminate": self.terminate,
            "metadata": self.metadata, 
        }

def build_action_chunk(raw_action: dict[str, Any], instruction: str, image) -> ActionChunk:
    """
    把后端的原始动作建议包装成统一协议结构
    """

    if not isinstance(raw_action, dict):
        raise TypeError("raw_action必须是字典")
    
    height, width = image.shape[:2]

    return ActionChunk(
        delta_xyz=raw_action.get("delta_xyz", [0.0, 0.0, 0.0]),
        delta_rpy=raw_action.get("delta_rpy", [0.0, 0.0, 0.0]),
        confidence=raw_action.get("confidence", 0.0),
        terminate=raw_action.get("terminate", False),
        metadata={
            "instruction": instruction,
            "image_width": width,
            "image_height": height,
            "backend": raw_action.get("backend", "fake_rule_based"),
            "delta_xyz_unit": "meter",
            "delta_rpy_unit": "radian",
        },
    )
    
def fake_infer(image, instruction):
    """
    假推理函数，返回一组假动作（当前仅支持单关键词规则）
    参数:
        image: 图片数据
        instruction: 指令文本
    返回:
        dict: 原始动作建议
    """
    

    _ = image.shape[:2]
    cmd = instruction.strip().lower()

    if "stop" in cmd or "done" in cmd:
        delta_xyz = [0.0, 0.0, 0.0]
        confidence = 0.95
        terminate = True

    elif "closer" in cmd:
        delta_xyz = [0.01, 0.0, 0.0]
        confidence = 0.8
        terminate = False
    

    elif "farther" in cmd or "back" in cmd:
        delta_xyz = [-0.01, 0.0, 0.0]
        confidence = 0.8
        terminate = False

    elif "left" in cmd:
        delta_xyz = [0.0, -0.01, 0.0]
        confidence = 0.8
        terminate = False
    
    elif "right" in cmd:
        delta_xyz = [0.0, 0.01, 0.0]
        confidence = 0.8
        terminate = False

    elif "up" in cmd:
        delta_xyz = [0.0, 0.0, 0.01]
        confidence = 0.8
        terminate = False

    elif "down" in cmd:
        delta_xyz = [0.0, 0.0, -0.01]
        confidence = 0.8
        terminate = False

    else:
        delta_xyz = [0.0, 0.0, 0.0]
        confidence = 0.2
        terminate = False

    return {
        "delta_xyz": delta_xyz,
        "delta_rpy": [0.0, 0.0, 0.0], 
        "confidence": confidence,
        "terminate": terminate,
    }

def log(message: str):
    print(message, file=sys.stderr)

def main():
    """
    主函数：串接整个流程
    1. 解析参数
    2. 加载图片（自动转换为RGB）
    3. 假推理
    4. 打印结果
    
    返回:
        int: 退出码
            0 - 成功
            1 - 参数错误
            2 - 图片加载失败
            3 - 推理失败
            4 - 动作协议校验失败
            5 - 一般错误

            130 - 用户中断
    """

    try:
        log("步骤1：解析命令行参数")
        try:
            args = parse_args()
            log(f"    input: {args.input}")
            log(f"    instruction: {args.instruction}")
        except SystemExit:
            return 1
        except Exception as e:
            log(f"参数解析失败 {e}")
            return 1
        log("\n步骤2：加载图片")
        image, _, _ = load_image(args.input)
        if image is None:
            return 2

        log("\n步骤3：执行假推理")
        try:
            raw_action = fake_infer(image, args.instruction)
        except Exception as e:
            log(f"推理阶段失败：{e}")
            return 3

        log("\n步骤4：组装并校验ActionChunk")
        try:
            action_chunk = build_action_chunk(raw_action, args.instruction, image)
            result = action_chunk.to_dict()
            log("动作协议检查：验证通过")
        except Exception as e:
            log(f"动作协议检查失败：{e}")
            return 4
        
        log("\n步骤5,输出结果")
        print(json.dumps(result, indent=2, ensure_ascii=False))
        
        return 0
    
    except KeyboardInterrupt:
        return 130
    except Exception as e:
        log(f"未处理异常：{e}")
        return 5
if __name__ == "__main__":
    exit_code = main()

    log(f"\n退出码：{exit_code}")

    sys.exit(exit_code)