#!/usr/bin/env python3
"""
Day 2 环境自检脚本。

这个脚本的职责很单纯：
1. 确认当前 Python 是否来自独立虚拟环境
2. 确认 ROS 侧 Python 包是否还能导入
3. 确认后续视觉/VLA 常用基础库是否可用
4. 如果已安装 torch，检查 CUDA 是否可见
"""

from __future__ import annotations

import importlib
import platform
import sys
from pathlib import Path


def check_module(name: str) -> tuple[bool, str]:
    try:
        module = importlib.import_module(name)
        version = getattr(module, "__version__", "unknown")
        return True, str(version)
    except Exception as exc:  # pragma: no cover - 这里只做环境探测
        return False, f"{type(exc).__name__}: {exc}"


def main() -> int:
    project_root = Path(__file__).resolve().parents[1]
    venv_path = project_root / "vla" / ".venv"

    print("=== 基础信息 ===")
    print(f"Python executable: {sys.executable}")
    print(f"Python version   : {sys.version.split()[0]}")
    print(f"Platform         : {platform.platform()}")
    print(f"Expected venv    : {venv_path}")
    print(f"Using venv       : {sys.executable.startswith(str(venv_path))}")

    print("\n=== 模块检查 ===")
    modules = ["rclpy", "numpy", "cv2", "PIL", "torch"]
    results: dict[str, tuple[bool, str]] = {}
    for module_name in modules:
        ok, detail = check_module(module_name)
        results[module_name] = (ok, detail)
        status = "OK" if ok else "FAIL"
        print(f"{module_name:>8}: {status} -> {detail}")

    # torch 是 Day 2 的关键观察项，如果还没安装，就只给提示，不让脚本报错退出。
    torch_ok, _ = results["torch"]
    if torch_ok:
        import torch

        print("\n=== CUDA 检查 ===")
        print(f"torch.cuda.is_available(): {torch.cuda.is_available()}")
        print(f"torch.cuda.device_count(): {torch.cuda.device_count()}")
        if torch.cuda.is_available():
            print(f"torch current device    : {torch.cuda.current_device()}")
            print(
                "torch device name       : "
                f"{torch.cuda.get_device_name(torch.cuda.current_device())}"
            )
    else:
        print("\n=== CUDA 检查 ===")
        print("torch 尚未安装，今天先把环境底座搭好；CUDA 详细检测可在安装 torch 后复查。")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
