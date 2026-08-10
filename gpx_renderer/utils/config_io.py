# -*- coding: utf-8 -*-
"""
JSON 設定檔讀寫與子程序執行命令生成工具。
"""

import sys
import json
from pathlib import Path


def _load_config_file(path: str) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        obj = json.load(f)
    if not isinstance(obj, dict):
        raise ValueError("render config 必須是 JSON object。")
    return obj


def _self_subprocess_command(flag: str, config_path: str) -> list[str]:
    """GUI 啟動 renderer/benchmark 子程序。Frozen EXE 直接重啟自己，亮點在於不再傳 .py 路徑。"""
    if getattr(sys, "frozen", False):
        return [sys.executable, flag, config_path]
    entry_script = Path(sys.argv[0]).resolve() if sys.argv and sys.argv[0].endswith(".py") else Path(__file__).resolve().parent.parent.parent / "GPX_Ride_Renderer.py"
    return [sys.executable, "-u", str(entry_script), flag, config_path]
