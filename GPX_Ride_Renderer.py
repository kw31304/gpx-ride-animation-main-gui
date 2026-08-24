# -*- coding: utf-8 -*-
"""
GPX_Ride_Renderer.py
=====================================
高速 GPX / Strava 風格動畫渲染器（重構進入點）。

此檔案作為主進入點，轉接至 `gpx_renderer` 模組：
  - GUI 模式 (預設)：啟動 Tkinter GUI
  - Subprocess 渲染模式 (`--render-config <json>`)
  - Subprocess 測試模式 (`--benchmark-config <json>`)
  - CLI 模式 (`--cli`)
"""

import sys
import multiprocessing as mp

from gpx_renderer.utils import _force_utf8_stdio, _load_config_file, _hide_frozen_console_for_gui

_force_utf8_stdio()


def main():
    # PyInstaller spec 使用 noconsole bootloader。保留 WinAPI hide，讓舊版 build
    # 或直接以 console bootloader 執行時也不會留下主視窗終端。
    if len(sys.argv) == 1:
        _hide_frozen_console_for_gui()

    # 預設直接開 GUI；--render-config 只給 GUI 啟動的 render subprocess 使用。
    if len(sys.argv) >= 3 and sys.argv[1] == "--render-config":
        from gpx_renderer.core import render_job
        render_job(_load_config_file(sys.argv[2]))
        return
    if len(sys.argv) >= 3 and sys.argv[1] == "--benchmark-config":
        from gpx_renderer.core import performance_benchmark_job
        performance_benchmark_job(_load_config_file(sys.argv[2]))
        return
    if len(sys.argv) >= 2 and sys.argv[1] == "--cli":
        from gpx_renderer.core import render_job
        # CLI 使用目前預設設定，不詢問地圖選單。
        render_job({"map_style_key": "1"})
        return

    from gpx_renderer.gui import launch_gui
    launch_gui()


if __name__ == "__main__":
    mp.freeze_support()
    try:
        main()
    except KeyboardInterrupt:
        print("\n[INFO] 已取消。")
    except Exception as exc:
        print(f"\n[ERROR] {type(exc).__name__}: {exc}")
        raise
