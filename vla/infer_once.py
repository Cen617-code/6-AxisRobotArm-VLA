import argparse
import cv2
import json
import sys
from datetime import datetime


def parse_args() -> argparse.Namespace:
    """
    解析命令行参数
    设计思路：
    --input: 输入图片的路径
    --instruction: 对图片的操作指令
    """

    parser = argparse.ArgumentParser(
        description='图片推理程序 - 接收图片和程序进行推理',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    #必须参数
    parser.add_argument(
        '--input',
        type=str,
        required=True,
        help='输入本地文件的路径'
    )

    parser.add_argument(
        '--instruction',
        type=str,
        required=True,
        help='对图片的操作指令'
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
        print(f"警告：无法读取图片{image_path}")
        return None, 0, 0
    
    image_rgb = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2RGB)
    
    #获取图片尺寸
    height, width = image_rgb.shape[:2]

    print(f"图片加载成功：{width}×{height}")
    return image_rgb, height, width


def fake_infer(image, instruction):
    """
    假推理函数，返回一组假动作（当前仅支持单关键词规则）
    参数:
        image: 图片数据
        instruction: 指令文本
    返回:
        dict: 标准格式的动作结果
    """
    

    height, width = image.shape[:2]
    cmd = instruction.lower()

    if "closer" in cmd:
        delta_xyz = [0.01, 0.0, 0.0]
        confidence = 0.8
        terminate = False
    
    elif "left" in cmd:
        delta_xyz = [0.0, -0.01, 0.0]
        confidence = 0.8
        terminate = False
    
    elif "up" in cmd:
        delta_xyz = [0.0, 0.0, 0.01]
        confidence = 0.8
        terminate = False

    else:
        delta_xyz = [0.0, 0.0, 0.0]
        confidence = 0.2
        terminate = False

    output = {
        "timestamp": datetime.now().isoformat(),
        "delta_xyz": delta_xyz,
        "delta_rpy": [0.0, 0.0, 0.0],    # 第一版固定为0
        "confidence": confidence,
        "terminate": terminate,
        "metadata": {
            "instruction": instruction,
            "image_width": width,
            "image_height": height,
            "backend": "fake_rule_based"
        }
    }
    return output

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
            4 - 一般错误

            130 - 用户中断
    """

    try:
        print("步骤1：解析命令行参数")
        try:
            args = parse_args()
            print(f"    input: {args.input}")
            print(f"    instruction: {args.instruction}")
        except SystemExit as e:
            return 1
        except Exception as e:
            return 1
        print("\n步骤2：加载图片")
        image, height, width = load_image(args.input)
        if image is None:
            return 2

        print("\n步骤3：执行假推理")
        try:
            result = fake_infer(image, args.instruction)
            if result is None:
                return 3
        except Exception as e:
            return 3

        print("\n步骤4：输出结果")
        print(json.dumps(result, indent=2, ensure_ascii=False))
        
        return 0
    
    except KeyboardInterrupt:
        return 130
    except Exception as e:
        return 4
if __name__ == "__main__":
    exit_code = main()

    print(f"\n退出码：{exit_code}")

    sys.exit(exit_code)