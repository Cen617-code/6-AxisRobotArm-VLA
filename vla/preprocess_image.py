#!/usr/bin/env python3
"""
Day 3: 单张图像预处理脚本

目标很明确：
1. 读入一张本地图像
2. 统一成 RGB
3. resize 到固定尺寸
4. 归一化为 float32
5. 保存中间结果，方便人眼检查

这里故意不做得太“深度学习平台化”，因为 Day 3 的重点是看清楚数据流。
可以把它理解为：先把一堆原始零件摆正，再交给后面的 VLA“大脑”。
"""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass
from pathlib import Path

import numpy as np
from PIL import Image


@dataclass
class ImageInputSpec:
    """Day 3 统一输入接口。"""

    image_path: str
    instruction: str
    target_width: int
    target_height: int
    normalize_mode: str


@dataclass
class ImageOutputSpec:
    """Day 3 统一输出接口。"""

    original_width: int
    original_height: int
    output_width: int
    output_height: int
    channels: int
    dtype: str
    min_value: float
    max_value: float
    npy_path: str
    preview_path: str


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="单张图像预处理")
    parser.add_argument(
        "--input",
        required=True,
        help="输入图像路径。若是 GIF，会默认读取第 1 帧。",
    )
    parser.add_argument(
        "--instruction",
        default="move the end effector closer to the target",
        help="给未来 VLA 使用的任务文本。Day 3 先只记录，不参与计算。",
    )
    parser.add_argument(
        "--width",
        type=int,
        default=256,
        help="目标宽度，默认 256。",
    )
    parser.add_argument(
        "--height",
        type=int,
        default=256,
        help="目标高度，默认 256。",
    )
    parser.add_argument(
        "--normalize-mode",
        choices=["zero_one", "imagenet"],
        default="zero_one",
        help="归一化策略。Day 3 默认先用最直观的 [0,1] 归一化。",
    )
    parser.add_argument(
        "--output-dir",
        default="vla/data/processed",
        help="输出目录，默认 vla/data/processed。",
    )
    parser.add_argument(
        "--stem",
        default="sample",
        help="输出文件名前缀。",
    )
    return parser.parse_args()


def load_rgb_image(image_path: Path) -> Image.Image:
    """
    统一读取图像。

    如果输入是 GIF，这里只取第 1 帧。
    这样做的原因很简单：Day 3 只做“单张图像推理前的准备”，不做视频序列。
    """

    with Image.open(image_path) as image:
        # 多帧图片（例如 GIF）默认取第一帧，避免后续处理逻辑分叉。
        if getattr(image, "n_frames", 1) > 1:
            image.seek(0)
        return image.convert("RGB")


def resize_image(image: Image.Image, width: int, height: int) -> Image.Image:
    # Bilinear 对 Day 3 足够温和，既简单又常见。
    return image.resize((width, height), Image.BILINEAR)


def normalize_image(image: Image.Image, normalize_mode: str) -> np.ndarray:
    """
    把图像从“人眼习惯的 0~255 整数像素”整理成“模型习惯的浮点输入”。

    可以把 normalize 想象成“统一量尺”：
    原图像像是毫米、厘米混着记；
    归一化后，模型看到的是统一单位的数据。
    """

    array = np.asarray(image, dtype=np.float32) / 255.0

    if normalize_mode == "imagenet":
        mean = np.array([0.485, 0.456, 0.406], dtype=np.float32)
        std = np.array([0.229, 0.224, 0.225], dtype=np.float32)
        array = (array - mean) / std

    return array


def save_preview(image: Image.Image, preview_path: Path) -> None:
    preview_path.parent.mkdir(parents=True, exist_ok=True)
    image.save(preview_path)


def save_npy(array: np.ndarray, npy_path: Path) -> None:
    npy_path.parent.mkdir(parents=True, exist_ok=True)
    np.save(npy_path, array)


def save_metadata(
    input_spec: ImageInputSpec,
    output_spec: ImageOutputSpec,
    metadata_path: Path,
) -> None:
    metadata_path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "input": asdict(input_spec),
        "output": asdict(output_spec),
        "tensor_layout": "HWC",
        "color_order": "RGB",
    }
    metadata_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def main() -> int:
    args = parse_args()

    image_path = Path(args.input).expanduser().resolve()
    output_dir = Path(args.output_dir).expanduser().resolve()

    if not image_path.exists():
        raise FileNotFoundError(f"找不到输入图像: {image_path}")

    input_spec = ImageInputSpec(
        image_path=str(image_path),
        instruction=args.instruction,
        target_width=args.width,
        target_height=args.height,
        normalize_mode=args.normalize_mode,
    )

    original = load_rgb_image(image_path)
    resized = resize_image(original, args.width, args.height)
    tensor = normalize_image(resized, args.normalize_mode)

    npy_path = output_dir / f"{args.stem}.npy"
    preview_path = output_dir / f"{args.stem}.preview.png"
    metadata_path = output_dir / f"{args.stem}.meta.json"

    save_preview(resized, preview_path)
    save_npy(tensor, npy_path)

    output_spec = ImageOutputSpec(
        original_width=original.width,
        original_height=original.height,
        output_width=args.width,
        output_height=args.height,
        channels=3,
        dtype=str(tensor.dtype),
        min_value=float(tensor.min()),
        max_value=float(tensor.max()),
        npy_path=str(npy_path),
        preview_path=str(preview_path),
    )
    save_metadata(input_spec, output_spec, metadata_path)

    print("=== Day 3 预处理完成 ===")
    print(f"输入图像       : {image_path}")
    print(f"原始尺寸       : {original.width} x {original.height}")
    print(f"输出尺寸       : {args.width} x {args.height}")
    print(f"归一化策略     : {args.normalize_mode}")
    print(f"张量布局       : HWC / RGB / {tensor.dtype}")
    print(f"数值范围       : [{tensor.min():.6f}, {tensor.max():.6f}]")
    print(f"预览图输出     : {preview_path}")
    print(f"张量文件输出   : {npy_path}")
    print(f"元数据输出     : {metadata_path}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
