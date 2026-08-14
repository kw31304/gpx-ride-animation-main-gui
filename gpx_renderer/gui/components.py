# -*- coding: utf-8 -*-
"""
Tkinter 介面輔助元件與帶說明按鈕的複用 UI 元件。
包含可摺疊收合的 Worker 儀表板與 ETA 時間預估元件。
"""

import math
from datetime import datetime, timedelta
import tkinter as tk
from tkinter import ttk
from gpx_renderer.gui.help import help_button


def add_check_with_help(parent, root, text, variable, key):
    box = ttk.Frame(parent)
    box.pack(side="left", padx=(0, 10))
    ttk.Checkbutton(box, text=text, variable=variable).pack(side="left")
    help_button(box, root, key).pack(side="left", padx=(4, 0))
    return box


class CollapsibleWorkerDashboard(ttk.Frame):
    """
    可摺疊收合的 Worker 子進度條儀表板與 ETA 預估完成時間容器。
    """
    def __init__(self, parent, worker_count: int = 6, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        self.is_expanded = True
        self.worker_rows = []

        # ---------- 標題欄 (可點擊收合/展開) ----------
        self.header_frame = ttk.Frame(self)
        self.header_frame.pack(fill="x", expand=True)

        self.toggle_btn = ttk.Button(
            self.header_frame,
            text="▼ 各 Worker 渲染儀表板與預估完成時間 (ETA)",
            command=self.toggle,
            width=42,
        )
        self.toggle_btn.pack(side="left", padx=(0, 10))

        self.header_summary_var = tk.StringVar(value="預估完成時間: -- | 渲染速度: -- fps")
        self.header_summary_label = ttk.Label(
            self.header_frame,
            textvariable=self.header_summary_var,
            font=("Microsoft JhengHei UI", 9),
            foreground="#555555",
        )
        self.header_summary_label.pack(side="left", fill="x", expand=True)

        # ---------- 可摺疊主體內容 ----------
        self.body = ttk.LabelFrame(self, text="Worker 狀態與預估時間", padding=8)
        self.body.pack(fill="x", expand=True, pady=(4, 0))
        self.body.columnconfigure(0, weight=1)

        # 0. 渲染設定參數摘要區
        self.summary_card = ttk.LabelFrame(self.body, text="渲染設定摘要", padding=6)
        self.summary_card.pack(fill="x", expand=True, pady=(0, 6))
        self.summary_card.columnconfigure(0, weight=1)
        self.summary_card.columnconfigure(1, weight=1)

        self.cfg_res_var = tk.StringVar(value="畫面規格: --x-- @ -- FPS")
        self.cfg_map_var = tk.StringVar(value="地圖視角: --")
        self.cfg_perf_var = tk.StringVar(value="效能模式: --")
        self.cfg_enc_var = tk.StringVar(value="編碼設定: --")

        f_left = ttk.Frame(self.summary_card)
        f_left.grid(row=0, column=0, sticky="nw", padx=4)
        ttk.Label(f_left, textvariable=self.cfg_res_var, font=("Microsoft JhengHei UI", 9)).pack(anchor="w")
        ttk.Label(f_left, textvariable=self.cfg_map_var, font=("Microsoft JhengHei UI", 9)).pack(anchor="w")

        f_right = ttk.Frame(self.summary_card)
        f_right.grid(row=0, column=1, sticky="nw", padx=4)
        ttk.Label(f_right, textvariable=self.cfg_perf_var, font=("Microsoft JhengHei UI", 9)).pack(anchor="w")
        ttk.Label(f_right, textvariable=self.cfg_enc_var, font=("Microsoft JhengHei UI", 9)).pack(anchor="w")

        # 1. ETA 資訊卡片區
        self.eta_card = ttk.Frame(self.body, padding=4)
        self.eta_card.pack(fill="x", expand=True, pady=(0, 6))

        self.eta_var = tk.StringVar(value="預估剩餘時間: --")
        self.clock_var = tk.StringVar(value="預計完成時刻: --:--:--")
        self.fps_var = tk.StringVar(value="渲染速度: -- frame/s")
        self.frame_stat_var = tk.StringVar(value="已完成幀數: 0 / 0")

        ttk.Label(self.eta_card, textvariable=self.eta_var, font=("Microsoft JhengHei UI", 9, "bold")).pack(side="left", padx=(0, 15))
        ttk.Label(self.eta_card, textvariable=self.clock_var, font=("Microsoft JhengHei UI", 9)).pack(side="left", padx=(0, 15))
        ttk.Label(self.eta_card, textvariable=self.fps_var, font=("Microsoft JhengHei UI", 9)).pack(side="left", padx=(0, 15))
        ttk.Label(self.eta_card, textvariable=self.frame_stat_var, font=("Microsoft JhengHei UI", 9)).pack(side="right")

        # 分隔線
        ttk.Separator(self.body, orient="horizontal").pack(fill="x", pady=(2, 6))

        # 2. 各 Worker 子進度條容器
        self.workers_frame = ttk.Frame(self.body)
        self.workers_frame.pack(fill="x", expand=True)
        self.workers_frame.columnconfigure(1, weight=1)

        self.set_worker_count(worker_count)

    def toggle(self):
        """展開/收合切換"""
        self.is_expanded = not self.is_expanded
        if self.is_expanded:
            self.body.pack(fill="x", expand=True, pady=(4, 0))
            self.toggle_btn.configure(text="▼ 各 Worker 渲染儀表板與預估完成時間 (ETA)")
        else:
            self.body.pack_forget()
            self.toggle_btn.configure(text="▶ 各 Worker 渲染儀表板與預估完成時間 (ETA)")

    def set_worker_count(self, count: int):
        """根據指定的 Worker 數量動態建立/重建子進度條"""
        count = max(1, min(16, int(count)))
        for row in self.worker_rows:
            row["frame"].destroy()
        self.worker_rows.clear()

        for i in range(count):
            row_frame = ttk.Frame(self.workers_frame)
            row_frame.pack(fill="x", expand=True, pady=2)
            row_frame.columnconfigure(1, weight=1)

            lbl_name = ttk.Label(row_frame, text=f"Worker {i + 1}:", width=10, anchor="w")
            lbl_name.grid(row=0, column=0, sticky="w", padx=(0, 6))

            pvar = tk.DoubleVar(value=0.0)
            pbar = ttk.Progressbar(row_frame, variable=pvar, maximum=100)
            pbar.grid(row=0, column=1, sticky="ew", padx=(0, 8))

            svar = tk.StringVar(value="待命")
            lbl_status = ttk.Label(row_frame, textvariable=svar, width=18, anchor="e")
            lbl_status.grid(row=0, column=2, sticky="e")

            self.worker_rows.append({
                "frame": row_frame,
                "var": pvar,
                "status_var": svar,
            })

    def update_worker(self, worker_id: int, pct: float, status_text: str):
        """更新單一 Worker 的進度百分比與狀態文字"""
        if 0 <= worker_id < len(self.worker_rows):
            self.worker_rows[worker_id]["var"].set(max(0.0, min(100.0, float(pct))))
            self.worker_rows[worker_id]["status_var"].set(status_text)

    def update_eta(self, eta_seconds: float | None, live_fps: float, rendered: int, total: int):
        """更新整體 ETA 與速度統計資訊"""
        if live_fps > 0:
            self.fps_var.set(f"渲染速度: {live_fps:.1f} frame/s")
        else:
            self.fps_var.set("渲染速度: -- frame/s")

        self.frame_stat_var.set(f"已完成幀數: {rendered} / {total}")

        if eta_seconds is not None and math.isfinite(eta_seconds) and eta_seconds >= 0:
            eta_sec = int(round(eta_seconds))
            hours, remainder = divmod(eta_sec, 3600)
            minutes, seconds = divmod(remainder, 60)
            if hours > 0:
                eta_str = f"{hours}時{minutes}分{seconds}秒"
            elif minutes > 0:
                eta_str = f"{minutes}分{seconds}秒"
            else:
                eta_str = f"{seconds}秒"

            finish_time = datetime.now() + timedelta(seconds=eta_sec)
            clock_str = finish_time.strftime("%H:%M:%S")

            self.eta_var.set(f"預估剩餘時間: {eta_str}")
            self.clock_var.set(f"預計完成時刻: {clock_str}")
            self.header_summary_var.set(f"預估剩餘: {eta_str} ({clock_str} 完成) | 速度: {live_fps:.1f} fps")
        else:
            if rendered >= total and total > 0:
                self.eta_var.set("預估剩餘時間: 已完成")
                self.clock_var.set(f"完成時刻: {datetime.now().strftime('%H:%M:%S')}")
                self.header_summary_var.set(f"渲染完成 | 平均速度: {live_fps:.1f} fps")
            else:
                self.eta_var.set("預估剩餘時間: 計算中…")
                self.clock_var.set("預計完成時刻: --:--:--")
                self.header_summary_var.set(f"計算中… | 速度: {live_fps:.1f} fps")

    def reset(self, new_worker_count: int | None = None):
        """重置所有 Worker 進度條與 ETA 狀態"""
        if new_worker_count is not None and new_worker_count != len(self.worker_rows):
            self.set_worker_count(new_worker_count)
        else:
            for row in self.worker_rows:
                row["var"].set(0.0)
                row["status_var"].set("待命")
        self.eta_var.set("預估剩餘時間: --")
        self.clock_var.set("預計完成時刻: --:--:--")
        self.fps_var.set("渲染速度: -- frame/s")
        self.frame_stat_var.set("已完成幀數: 0 / 0")
        self.header_summary_var.set("預估完成時間: -- | 渲染速度: -- fps")

    def update_config_summary(self, cfg: dict):
        """根據傳入的設定字典更新摘要資訊卡片"""
        if not cfg:
            return
        w = cfg.get("FRAME_WIDTH", "--")
        h = cfg.get("FRAME_HEIGHT", "--")
        fps = cfg.get("FPS", "--")
        dur = float(cfg.get("VIDEO_DURATION", 0.0))
        auto_dur = "自動時長" if cfg.get("AUTO_DURATION_ENABLED") else "固定時長"
        self.cfg_res_var.set(f"畫面規格: {w}x{h} @ {fps} FPS  ({auto_dur} {dur:.1f}s)")

        map_key = str(cfg.get("map_style_key", "1"))
        cam = str(cfg.get("CAMERA_MODE", "North-Up"))
        zoom = str(cfg.get("LOCAL_MAP_ZOOM", "auto"))
        self.cfg_map_var.set(f"地圖視角: 風格 [{map_key}] | {cam} | Zoom: {zoom}")

        workers = cfg.get("RENDER_WORKERS", 1)
        chunks = cfg.get("CHUNKS_PER_WORKER", 4)
        parallel = "多程序" if cfg.get("PARALLEL_RENDER") and workers > 1 else "單程序"
        cache_str = "停用 Cache" if cfg.get("PARALLEL_DISABLE_TILE_CACHE") else "啟用 Cache"
        self.cfg_perf_var.set(f"效能模式: {parallel} ({workers} Workers × {chunks} chunks) | {cache_str}")

        bitrate = cfg.get("NVENC_BITRATE", "--")
        preset = cfg.get("NVENC_PRESET", "--")
        media = "媒體 Overlay [開啟]" if cfg.get("ENABLE_MEDIA") else "無媒體 Overlay"
        self.cfg_enc_var.set(f"編碼設定: NVENC {bitrate} (preset: {preset}) | {media}")


