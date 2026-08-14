# -*- coding: utf-8 -*-
"""
Tkinter GUI 主應用程式視窗、設定輸入監控與子程序即時 Log 讀取線程。
"""

from __future__ import annotations
import os
import sys
import re
import json
import tempfile
import threading
import subprocess
from pathlib import Path

import tkinter as tk
from tkinter import ttk, filedialog, messagebox

from gpx_renderer import config
from gpx_renderer.utils import _background_subprocess_kwargs, _self_subprocess_command
from gpx_renderer.core.data import quick_gpx_distance_km, auto_duration_seconds, format_seconds_human
from gpx_renderer.core.parallel import _default_benchmark_candidates
from gpx_renderer.gui.help import help_button, show_setting_help
from gpx_renderer.gui.components import add_check_with_help, RenderProgressDashboard


def launch_gui():
    """Tkinter GUI。真正渲染放在獨立 Python subprocess，避免 GUI 被 multiprocessing 拖死。"""
    root = tk.Tk()
    root.title("GPX Ride Renderer V1.2.0")
    root.geometry("980x860")
    root.minsize(860, 760)

    style = ttk.Style(root)
    try:
        style.theme_use("vista")
    except Exception:
        pass

    state = {
        "proc": None, "proc_mode": None, "config_path": None,
        "gpx_distance_km": None, "gpx_distance_path": None,
        "benchmark_result": None,
    }

    # ---------- variables ----------
    gpx_var = tk.StringVar(value=str(Path(config.gpx_filename).resolve()))
    out_var = tk.StringVar(value=str(Path(config.output_filename).resolve()))
    map_var = tk.StringVar(value="1")
    profile_var = tk.StringVar(value="高畫質")
    width_var = tk.IntVar(value=config.FRAME_WIDTH)
    height_var = tk.IntVar(value=config.FRAME_HEIGHT)
    fps_var = tk.IntVar(value=config.FPS)
    duration_var = tk.DoubleVar(value=config.VIDEO_DURATION)
    auto_duration_var = tk.BooleanVar(value=config.AUTO_DURATION_DEFAULT)
    seconds_per_100km_var = tk.StringVar(value=f"{config.AUTO_SECONDS_PER_100KM:g}")
    distance_info_var = tk.StringVar(value="GPX 距離：尚未讀取")
    zoomout_var = tk.DoubleVar(value=config.ZOOM_OUT_DURATION)
    hold_var = tk.DoubleVar(value=config.END_HOLD_DURATION)
    margin_var = tk.DoubleVar(value=config.VIEW_MARGIN)
    local_zoom_var = tk.StringVar(value=str(config.LOCAL_MAP_ZOOM))
    workers_var = tk.IntVar(value=config.RENDER_WORKERS)
    chunks_var = tk.IntVar(value=config.CHUNKS_PER_WORKER)
    connections_var = tk.IntVar(value=config.MAP_CONNECTIONS)
    bitrate_var = tk.StringVar(value=config.NVENC_BITRATE)
    preset_var = tk.StringVar(value=config.NVENC_PRESET)
    parallel_var = tk.BooleanVar(value=config.PARALLEL_RENDER)
    basemap_var = tk.BooleanVar(value=config.ENABLE_BASEMAP)
    preview_var = tk.BooleanVar(value=config.PREVIEW_MODE)
    cache_var = tk.BooleanVar(value=config.MAP_USE_CACHE)
    disable_parallel_cache_var = tk.BooleanVar(value=config.PARALLEL_DISABLE_TILE_CACHE)
    media_var = tk.StringVar(value=config.MEDIA_PATH)
    enable_media_var = tk.BooleanVar(value=config.ENABLE_MEDIA)
    media_duration_var = tk.DoubleVar(value=config.MEDIA_POPUP_DURATION)
    media_offset_var = tk.DoubleVar(value=config.MEDIA_TIME_OFFSET_SEC)
    hide_start_var = tk.DoubleVar(value=config.HIDE_START_DISTANCE_KM)
    hide_end_var = tk.DoubleVar(value=config.HIDE_END_DISTANCE_KM)
    real_speed_var = tk.BooleanVar(value=config.USE_REAL_SPEED)
    camera_mode_var = tk.StringVar(value=getattr(config, "CAMERA_MODE", "North-Up"))
    progress_var = tk.DoubleVar(value=0.0)
    status_var = tk.StringVar(value="就緒")
    benchmark_result_var = tk.StringVar(value="Auto Tune：尚未測試")

    outer = ttk.Frame(root, padding=12)
    outer.pack(fill="both", expand=True)
    outer.columnconfigure(0, weight=1)
    outer.rowconfigure(2, weight=1)

    # ---------- GPX distance / auto duration ----------
    def _apply_cached_auto_duration():
        if not auto_duration_var.get():
            return
        distance = state.get("gpx_distance_km")
        if distance is None:
            return
        try:
            rate = float(seconds_per_100km_var.get())
            if rate <= 0:
                return
        except Exception:
            return
        seconds = auto_duration_seconds(distance, rate)
        duration_var.set(round(seconds, 1))
        distance_info_var.set(
            f"GPX 距離：{distance:.2f} km  →  主動畫 {seconds:.1f}s ({format_seconds_human(seconds)})"
        )

    def refresh_gpx_distance(show_error: bool = False):
        raw = gpx_var.get().strip()
        if not raw:
            state["gpx_distance_km"] = None
            state["gpx_distance_path"] = None
            distance_info_var.set("GPX 距離：尚未選擇檔案")
            return
        path = str(Path(raw).expanduser().resolve())
        if not Path(path).is_file():
            state["gpx_distance_km"] = None
            state["gpx_distance_path"] = None
            distance_info_var.set("GPX 距離：找不到檔案")
            return

        if state.get("gpx_distance_path") == path and state.get("gpx_distance_km") is not None:
            _apply_cached_auto_duration()
            return

        distance_info_var.set("GPX 距離：讀取中…")

        def worker(expected_path: str):
            try:
                distance = quick_gpx_distance_km(expected_path)
            except Exception as exc:
                err_text = str(exc)
                def failed(err_text=err_text):
                    if str(Path(gpx_var.get().strip()).expanduser().resolve()) != expected_path:
                        return
                    state["gpx_distance_km"] = None
                    state["gpx_distance_path"] = None
                    distance_info_var.set(f"GPX 距離：讀取失敗 ({err_text})")
                    if show_error:
                        messagebox.showerror("GPX 讀取失敗", err_text)
                root.after(0, failed)
                return

            def success():
                try:
                    current = str(Path(gpx_var.get().strip()).expanduser().resolve())
                except Exception:
                    return
                if current != expected_path:
                    return
                state["gpx_distance_km"] = distance
                state["gpx_distance_path"] = expected_path
                _apply_cached_auto_duration()
                if not auto_duration_var.get():
                    distance_info_var.set(f"GPX 距離：{distance:.2f} km")
            root.after(0, success)

        threading.Thread(target=worker, args=(path,), daemon=True).start()

    def on_auto_duration_toggle():
        duration_entry.configure(state="disabled" if auto_duration_var.get() else "normal")
        if auto_duration_var.get():
            refresh_gpx_distance()
        elif state.get("gpx_distance_km") is not None:
            distance_info_var.set(f"GPX 距離：{state['gpx_distance_km']:.2f} km（手動秒數）")

    def on_duration_rate_change(*_):
        _apply_cached_auto_duration()

    # ---------- files ----------
    files_box = ttk.LabelFrame(outer, text="檔案", padding=10)
    files_box.grid(row=0, column=0, sticky="ew")
    files_box.columnconfigure(1, weight=1)

    ttk.Label(files_box, text="GPX").grid(row=0, column=0, sticky="w", padx=(0, 8), pady=4)
    ttk.Entry(files_box, textvariable=gpx_var).grid(row=0, column=1, sticky="ew", pady=4)
    def browse_gpx():
        p = filedialog.askopenfilename(title="選擇 GPX", filetypes=[("GPX", "*.gpx"), ("所有檔案", "*.*")])
        if p:
            gpx_var.set(p)
            if not out_var.get().strip() or Path(out_var.get()).name == "ride_animation.mp4":
                out_var.set(str(Path(p).with_name(Path(p).stem + "_animation.mp4")))
            state["gpx_distance_km"] = None
            state["gpx_distance_path"] = None
            refresh_gpx_distance()
    ttk.Button(files_box, text="瀏覽…", command=browse_gpx).grid(row=0, column=2, padx=(8, 0), pady=4)

    ttk.Label(files_box, text="輸出").grid(row=1, column=0, sticky="w", padx=(0, 8), pady=4)
    ttk.Entry(files_box, textvariable=out_var).grid(row=1, column=1, sticky="ew", pady=4)
    def browse_out():
        p = filedialog.asksaveasfilename(title="輸出 MP4", defaultextension=".mp4", filetypes=[("MP4", "*.mp4")])
        if p:
            out_var.set(p)
    ttk.Button(files_box, text="瀏覽…", command=browse_out).grid(row=1, column=2, padx=(8, 0), pady=4)

    ttk.Label(files_box, text="媒體檔/資料夾").grid(row=2, column=0, sticky="w", padx=(0, 8), pady=4)
    ttk.Entry(files_box, textvariable=media_var).grid(row=2, column=1, sticky="ew", pady=4)
    def browse_media():
        p = filedialog.askdirectory(title="選擇照片/影片資料夾")
        if not p:
            p = filedialog.askopenfilename(title="選擇照片或影片", filetypes=[("媒體檔案", "*.jpg;*.jpeg;*.png;*.webp;*.mp4;*.mov"), ("所有檔案", "*.*")])
        if p:
            media_var.set(p)
            enable_media_var.set(True)
    media_btn_box = ttk.Frame(files_box)
    media_btn_box.grid(row=2, column=2, padx=(8, 0), pady=4)
    ttk.Button(media_btn_box, text="瀏覽…", command=browse_media).pack(side="left")
    ttk.Button(media_btn_box, text="媒體管理", command=lambda: open_media_dialog()).pack(side="left", padx=(6, 0))
    help_button(media_btn_box, root, "media_path").pack(side="left", padx=(5, 0))

    # ---------- settings ----------
    settings = ttk.LabelFrame(outer, text="渲染設定", padding=10)
    settings.grid(row=1, column=0, sticky="ew", pady=(10, 0))
    for c in range(6):
        settings.columnconfigure(c, weight=1 if c in (1, 3, 5) else 0)

    map_labels = [f"{k}. {v[0]}" for k, v in config.MAP_STYLE_OPTIONS.items()]
    map_combo_var = tk.StringVar(value=map_labels[0])
    ttk.Label(settings, text="地圖風格").grid(row=0, column=0, sticky="w", padx=(0, 6), pady=4)
    map_field = ttk.Frame(settings)
    map_field.grid(row=0, column=1, columnspan=3, sticky="ew", pady=4)
    map_field.columnconfigure(0, weight=1)
    map_combo = ttk.Combobox(map_field, textvariable=map_combo_var, values=map_labels, state="readonly", width=28)
    map_combo.grid(row=0, column=0, sticky="ew")
    help_button(map_field, root, "map_style").grid(row=0, column=1, padx=(5, 0))
    def on_map_change(_=None):
        map_var.set(map_combo_var.get().split(".", 1)[0])
    map_combo.bind("<<ComboboxSelected>>", on_map_change)

    ttk.Label(settings, text="模式").grid(row=0, column=4, sticky="e", padx=(12, 6))
    profile_field = ttk.Frame(settings)
    profile_field.grid(row=0, column=5, sticky="ew")
    profile_field.columnconfigure(0, weight=1)
    profile_combo = ttk.Combobox(profile_field, textvariable=profile_var, values=["快速", "平衡", "高畫質"], state="readonly", width=10)
    profile_combo.grid(row=0, column=0, sticky="ew")
    help_button(profile_field, root, "profile").grid(row=0, column=1, padx=(5, 0))

    RESOLUTION_PRESETS = [
        ("1080p 直式 9:16 (1080×1920) - 社群媒體", 1080, 1920),
        ("1080p 橫式 16:9 (1920×1080) - YouTube", 1920, 1080),
        ("1080p 正方形 1:1 (1080×1080) - 標準方形", 1080, 1080),
        ("720p  直式 9:16 (720×1280)  - 社群媒體", 720, 1280),
        ("720p  橫式 16:9 (1280×720)", 1280, 720),     
        ("IG 貼文直式 4:5 (1080×1350)", 1080, 1350),
        ("1440p 正方形 1:1 (1440×1440) - 高畫質方形", 1440, 1440),
        ("2K 橫式 16:9 (2560×1440)", 2560, 1440),
        ("640×360  超低 16:9 測試 (極速)", 640, 360),
        ("480×480  超低 1:1  測試 (極速)", 480, 480),
        ("360×640  超低 直式 測試 (極速)", 360, 640),
        ("自訂解析度...", None, None),
    ]

    res_combo_labels = [p[0] for p in RESOLUTION_PRESETS]

    def _find_matching_preset(w, h):
        for label, pw, ph in RESOLUTION_PRESETS:
            if pw == w and ph == h:
                return label
        return "✏️ 自訂解析度..."

    res_combo_var = tk.StringVar(value=_find_matching_preset(width_var.get(), height_var.get()))

    ttk.Label(settings, text="解析度預設").grid(row=1, column=0, sticky="w", pady=4)
    res_field = ttk.Frame(settings)
    res_field.grid(row=1, column=1, sticky="ew", pady=4)

    res_combo = ttk.Combobox(res_field, textvariable=res_combo_var, values=res_combo_labels, state="readonly", width=26)
    res_combo.pack(side="left", fill="x", expand=True)

    def on_res_preset_change(_=None):
        sel = res_combo_var.get()
        for label, pw, ph in RESOLUTION_PRESETS:
            if label == sel and pw is not None and ph is not None:
                width_var.set(pw)
                height_var.set(ph)
                break

    res_combo.bind("<<ComboboxSelected>>", on_res_preset_change)

    ttk.Label(settings, text="自訂(寬×高)").grid(row=1, column=2, sticky="e", padx=(12, 6))
    res_custom_frame = ttk.Frame(settings)
    res_custom_frame.grid(row=1, column=3, sticky="w")
    ttk.Entry(res_custom_frame, textvariable=width_var, width=5).pack(side="left")
    ttk.Label(res_custom_frame, text="×").pack(side="left")
    ttk.Entry(res_custom_frame, textvariable=height_var, width=5).pack(side="left")
    help_button(res_custom_frame, root, "resolution").pack(side="left", padx=(5, 0))

    def on_custom_dim_change(*args):
        try:
            w, h = int(width_var.get()), int(height_var.get())
            matched = _find_matching_preset(w, h)
            if res_combo_var.get() != matched:
                res_combo_var.set(matched)
        except Exception:
            pass

    width_var.trace_add("write", on_custom_dim_change)
    height_var.trace_add("write", on_custom_dim_change)

    ttk.Label(settings, text="FPS").grid(row=1, column=4, sticky="e", padx=(12, 6))
    fps_field = ttk.Frame(settings)
    fps_field.grid(row=1, column=5, sticky="w")
    ttk.Spinbox(fps_field, from_=24, to=120, textvariable=fps_var, width=8).pack(side="left")
    help_button(fps_field, root, "fps").pack(side="left", padx=(5, 0))

    ttk.Label(settings, text="主動畫秒數").grid(row=2, column=0, sticky="w", pady=4)
    duration_field = ttk.Frame(settings)
    duration_field.grid(row=2, column=1, sticky="ew")
    duration_entry = ttk.Entry(duration_field, textvariable=duration_var, width=10)
    duration_entry.pack(side="left", fill="x", expand=True)
    help_button(duration_field, root, "duration").pack(side="left", padx=(5, 0))

    auto_row = ttk.Frame(settings)
    auto_row.grid(row=2, column=2, columnspan=4, sticky="ew", pady=(3, 5))
    auto_row.columnconfigure(5, weight=1)
    auto_toggle_box = ttk.Frame(auto_row)
    auto_toggle_box.grid(row=0, column=0, sticky="w", padx=(0, 12))
    ttk.Checkbutton(
        auto_toggle_box,
        text="依 GPX 距離自動設定秒數",
        variable=auto_duration_var,
        command=on_auto_duration_toggle,
    ).pack(side="left")
    help_button(auto_toggle_box, root, "auto_duration").pack(side="left", padx=(5, 0))
    ttk.Label(auto_row, text="每 100 km").grid(row=0, column=1, sticky="e", padx=(0, 5))
    rate_field = ttk.Frame(auto_row)
    rate_field.grid(row=0, column=2, sticky="w")
    ttk.Spinbox(rate_field, from_=5, to=600, increment=5, textvariable=seconds_per_100km_var, width=7).pack(side="left")
    help_button(rate_field, root, "seconds_per_100km").pack(side="left", padx=(5, 0))
    ttk.Label(auto_row, text="秒").grid(row=0, column=3, sticky="w", padx=(4, 12))
    ttk.Label(auto_row, textvariable=distance_info_var).grid(row=0, column=5, sticky="w")

    CAMERA_MODE_LABELS = {
        "North-Up": "正北朝上 (North-Up)",
        "Heading-Up": "跟隨行進方向 (Heading-Up)",
        "3D-Terrain": "3D 真地形 (3D-Terrain)",
    }
    camera_mode_combo_var = tk.StringVar(value=CAMERA_MODE_LABELS.get(camera_mode_var.get(), "正北朝上 (North-Up)"))
    ttk.Label(settings, text="視角模式").grid(row=3, column=0, sticky="w", pady=4)
    camera_mode_field = ttk.Frame(settings)
    camera_mode_field.grid(row=3, column=1, sticky="w")
    camera_mode_combo = ttk.Combobox(camera_mode_field, textvariable=camera_mode_combo_var, values=list(CAMERA_MODE_LABELS.values()), state="readonly", width=22)
    camera_mode_combo.pack(side="left")
    help_button(camera_mode_field, root, "camera_mode").pack(side="left", padx=(5, 0))

    def on_camera_mode_change(_=None):
        sel = camera_mode_combo_var.get()
        if "3D-Terrain" in sel:
            camera_mode_var.set("3D-Terrain")
        elif "Heading-Up" in sel:
            camera_mode_var.set("Heading-Up")
        else:
            camera_mode_var.set("North-Up")
    camera_mode_combo.bind("<<ComboboxSelected>>", on_camera_mode_change)

    ttk.Label(settings, text="Local Zoom").grid(row=3, column=2, sticky="e", padx=(12, 6))
    local_zoom_field = ttk.Frame(settings)
    local_zoom_field.grid(row=3, column=3, sticky="w")
    ttk.Combobox(local_zoom_field, textvariable=local_zoom_var, values=["auto", "15", "16", "17", "18"], state="readonly", width=8).pack(side="left")
    help_button(local_zoom_field, root, "local_zoom").pack(side="left", padx=(5, 0))

    ttk.Label(settings, text="View Margin").grid(row=3, column=4, sticky="e", padx=(12, 6))
    margin_field = ttk.Frame(settings)
    margin_field.grid(row=3, column=5, sticky="w")
    ttk.Entry(margin_field, textvariable=margin_var, width=10).pack(side="left")
    help_button(margin_field, root, "view_margin").pack(side="left", padx=(5, 0))

    ttk.Label(settings, text="Workers").grid(row=3, column=4, sticky="e", padx=(12, 6))
    workers_field = ttk.Frame(settings)
    workers_field.grid(row=3, column=5, sticky="w")
    ttk.Spinbox(workers_field, from_=1, to=max(2, os.cpu_count() or 8), textvariable=workers_var, width=8).pack(side="left")
    help_button(workers_field, root, "workers").pack(side="left", padx=(5, 0))

    ttk.Label(settings, text="NVENC bitrate").grid(row=4, column=0, sticky="w", pady=4)
    bitrate_field = ttk.Frame(settings)
    bitrate_field.grid(row=4, column=1, sticky="w")
    ttk.Combobox(bitrate_field, textvariable=bitrate_var, values=["8M", "12M", "20M", "24M", "30M", "40M", "60M"], width=8).pack(side="left")
    help_button(bitrate_field, root, "bitrate").pack(side="left", padx=(5, 0))

    ttk.Label(settings, text="NVENC preset").grid(row=4, column=2, sticky="e", padx=(12, 6))
    preset_field = ttk.Frame(settings)
    preset_field.grid(row=4, column=3, sticky="w")
    ttk.Combobox(preset_field, textvariable=preset_var, values=["p1", "p2", "p3", "p4", "p5", "p6", "p7"], state="readonly", width=8).pack(side="left")
    help_button(preset_field, root, "nvenc_preset").pack(side="left", padx=(5, 0))

    ttk.Label(settings, text="Tile connections").grid(row=4, column=4, sticky="e", padx=(12, 6))
    connections_field = ttk.Frame(settings)
    connections_field.grid(row=4, column=5, sticky="w")
    ttk.Spinbox(connections_field, from_=1, to=16, textvariable=connections_var, width=8).pack(side="left")
    help_button(connections_field, root, "tile_connections").pack(side="left", padx=(5, 0))

    ttk.Label(settings, text="Zoom-out 秒").grid(row=5, column=0, sticky="w", pady=4)
    zoomout_field = ttk.Frame(settings)
    zoomout_field.grid(row=5, column=1, sticky="w")
    ttk.Entry(zoomout_field, textvariable=zoomout_var, width=8).pack(side="left")
    help_button(zoomout_field, root, "zoomout").pack(side="left", padx=(5, 0))

    ttk.Label(settings, text="結尾停留秒").grid(row=5, column=2, sticky="e", padx=(12, 6))
    hold_field = ttk.Frame(settings)
    hold_field.grid(row=5, column=3, sticky="w")
    ttk.Entry(hold_field, textvariable=hold_var, width=8).pack(side="left")
    help_button(hold_field, root, "end_hold").pack(side="left", padx=(5, 0))

    ttk.Label(settings, text="Chunks / Worker").grid(row=5, column=4, sticky="e", padx=(12, 6))
    chunks_field = ttk.Frame(settings)
    chunks_field.grid(row=5, column=5, sticky="w")
    ttk.Spinbox(chunks_field, from_=1, to=12, textvariable=chunks_var, width=8).pack(side="left")
    help_button(chunks_field, root, "chunks").pack(side="left", padx=(5, 0))

    ttk.Label(settings, text="隱藏起點 (km)").grid(row=6, column=0, sticky="w", pady=4)
    hide_start_field = ttk.Frame(settings)
    hide_start_field.grid(row=6, column=1, sticky="w")
    ttk.Spinbox(hide_start_field, from_=0.0, to=50.0, increment=0.1, textvariable=hide_start_var, width=8).pack(side="left")
    help_button(hide_start_field, root, "hide_start").pack(side="left", padx=(5, 0))

    ttk.Label(settings, text="隱藏終點 (km)").grid(row=6, column=2, sticky="e", padx=(12, 6))
    hide_end_field = ttk.Frame(settings)
    hide_end_field.grid(row=6, column=3, sticky="w")
    ttk.Spinbox(hide_end_field, from_=0.0, to=50.0, increment=0.1, textvariable=hide_end_var, width=8).pack(side="left")
    help_button(hide_end_field, root, "hide_end").pack(side="left", padx=(5, 0))

    def open_media_dialog():
        media_path = media_var.get().strip()
        gpx_path = gpx_var.get().strip()

        if not media_path:
            messagebox.showwarning("提示", "請先在主介面選擇路線媒體路徑。")
            return
        if not gpx_path or not Path(gpx_path).is_file():
            messagebox.showwarning("提示", "請先選擇有效的 GPX 軌跡檔案。")
            return

        try:
            from gpx_renderer.core.data import load_gpx
            from gpx_renderer.core.media import scan_media_files
            from gpx_renderer.gui.media_dialog import MediaManagerDialog

            data = load_gpx(
                gpx_path,
                hide_start_km=float(hide_start_var.get()),
                hide_end_km=float(hide_end_var.get()),
            )
            scanned = scan_media_files(media_path, time_offset_sec=float(media_offset_var.get()))

            if not scanned:
                messagebox.showinfo("提示", "在指定的媒體路徑下未找到相應的照片或影片。")
                return

            def on_media_applied(updated_items, new_dur, new_offset):
                media_duration_var.set(new_dur)
                media_offset_var.set(new_offset)

                overrides = {}
                for item in updated_items:
                    if item.caption or (item.manual_distance_km is not None and item.manual_distance_km >= 0):
                        overrides[item.filename] = {
                            "caption": item.caption,
                            "manual_distance_km": item.manual_distance_km,
                        }
                json_str = json.dumps(overrides, ensure_ascii=False)
                config.MEDIA_OVERRIDES_JSON = json_str
                state["media_overrides_json"] = json_str
                append_log(f"[INFO] 已儲存 {len(overrides)} 個媒體檔案的手動微調里程與說明文字 (停留秒數={new_dur}s, 時間校正={new_offset}s)。")

            MediaManagerDialog(
                root, scanned, data,
                media_duration=float(media_duration_var.get()),
                media_offset_sec=float(media_offset_var.get()),
                media_path=media_path,
                on_apply=on_media_applied,
            )

        except Exception as exc:
            messagebox.showerror("錯誤", f"無法開啟媒體微調視窗：{exc}")

    checks = ttk.Frame(settings)
    checks.grid(row=7, column=0, columnspan=6, sticky="w", pady=(6, 0))

    add_check_with_help(checks, root, "多程序", parallel_var, "parallel")
    add_check_with_help(checks, root, "底圖", basemap_var, "basemap")
    add_check_with_help(checks, root, "跟隨 GPX 實際速度", real_speed_var, "use_real_speed")
    add_check_with_help(checks, root, "路線媒體卡片", enable_media_var, "enable_media")
    add_check_with_help(checks, root, "Preview（仍使用多程序）", preview_var, "preview")
    add_check_with_help(checks, root, "Contextily cache", cache_var, "contextily_cache")
    add_check_with_help(checks, root, "並行時停用 joblib cache", disable_parallel_cache_var, "parallel_cache")

    tune_row = ttk.Frame(settings)
    tune_row.grid(row=8, column=0, columnspan=6, sticky="ew", pady=(8, 0))
    tune_row.columnconfigure(2, weight=1)
    benchmark_btn = ttk.Button(tune_row, text="效能測試 / Auto Tune", command=lambda: start_benchmark())
    benchmark_btn.grid(row=0, column=0, sticky="w")
    help_button(tune_row, root, "autotune").grid(row=0, column=1, sticky="w", padx=(5, 10))
    ttk.Label(tune_row, textvariable=benchmark_result_var).grid(row=0, column=2, sticky="w")
    apply_benchmark_btn = ttk.Button(tune_row, text="套用建議", command=lambda: apply_benchmark_recommendation(), state="disabled")
    apply_benchmark_btn.grid(row=0, column=3, sticky="e", padx=(10, 0))

    def apply_profile(_=None):
        mode = profile_var.get()
        if mode == "快速":
            width_var.set(1000); height_var.set(1000); local_zoom_var.set("auto")
            bitrate_var.set("12M"); preset_var.set("p3"); workers_var.set(6); chunks_var.set(4)
        elif mode == "高畫質":
            width_var.set(1440); height_var.set(1440); local_zoom_var.set("17")
            bitrate_var.set("30M"); preset_var.set("p5"); workers_var.set(6); chunks_var.set(4)
        else:
            width_var.set(1080); height_var.set(1080); local_zoom_var.set("16")
            bitrate_var.set("20M"); preset_var.set("p4"); workers_var.set(6); chunks_var.set(4)
    profile_combo.bind("<<ComboboxSelected>>", apply_profile)
    seconds_per_100km_var.trace_add("write", on_duration_rate_change)
    duration_entry.configure(state="disabled" if auto_duration_var.get() else "normal")
    root.after(150, refresh_gpx_distance)

    # ---------- Render Progress Dashboard (包含置頂主進度條、ETA 與各 Worker 子進度) ----------
    worker_dashboard = RenderProgressDashboard(
        outer, worker_count=workers_var.get(),
        progress_var=progress_var, status_var=status_var,
    )
    worker_dashboard.grid(row=2, column=0, sticky="ew", pady=(10, 0))

    buttons = ttk.Frame(outer)
    buttons.grid(row=3, column=0, sticky="ew", pady=(10, 0))
    buttons.columnconfigure(0, weight=1)

    def refresh_config_summary(*args):
        try:
            cfg = collect_config()
            worker_dashboard.update_config_summary(cfg)
        except Exception:
            pass

    for var in (
        width_var, height_var, fps_var, duration_var, auto_duration_var,
        map_var, camera_mode_var, workers_var, chunks_var, parallel_var,
        disable_parallel_cache_var, bitrate_var, preset_var, enable_media_var,
    ):
        try: var.trace_add("write", refresh_config_summary)
        except Exception: pass

    def _on_workers_var_changed(*args):
        try:
            w_count = int(workers_var.get())
            worker_dashboard.reset(new_worker_count=w_count)
            refresh_config_summary()
        except Exception:
            pass
    workers_var.trace_add("write", _on_workers_var_changed)
    root.after(200, refresh_config_summary)

    def get_log_file_path(mode: str = "app") -> Path:
        from gpx_renderer.utils import application_dir
        from datetime import datetime
        log_dir = application_dir() / "logs"
        log_dir.mkdir(parents=True, exist_ok=True)
        ts_str = datetime.now().strftime("%Y%m%d_%H%M%S")
        return log_dir / f"{mode}_{ts_str}.log"

    def append_log(line: str):
        if line.startswith("[PROGRESS_JSON]"):
            return
        log_path = state.get("current_log_path")
        if not log_path:
            log_path = get_log_file_path("session")
            state["current_log_path"] = log_path
        try:
            from datetime import datetime
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            with open(log_path, "a", encoding="utf-8", errors="replace") as f:
                f.write(f"[{timestamp}] {line.rstrip()}\n")
        except Exception:
            pass

    def parse_progress(line: str):
        if line.startswith("[PROGRESS_JSON]"):
            try:
                data = json.loads(line[len("[PROGRESS_JSON]"):].strip())
                pct = float(data.get("pct", 0.0))
                progress_var.set(pct)
                status_var.set(f"主動畫 {pct:.1f}%")

                eta_sec = data.get("eta_seconds")
                live_fps = float(data.get("fps", 0.0))
                rendered = int(data.get("rendered", 0))
                total = int(data.get("total", 0))
                worker_dashboard.update_eta(eta_sec, live_fps, rendered, total)

                workers_data = data.get("workers", [])
                if len(workers_data) != len(worker_dashboard.worker_rows):
                    worker_dashboard.set_worker_count(len(workers_data))

                for w in workers_data:
                    wid = int(w.get("id", 1)) - 1
                    wpct = float(w.get("pct", 0.0))
                    wstatus = str(w.get("status", ""))
                    worker_dashboard.update_worker(wid, wpct, wstatus)
                return
            except Exception:
                pass

        bm = re.search(r"效能測試\s+\[(\d+)/(\d+)\]", line)
        if bm:
            current, total = int(bm.group(1)), max(1, int(bm.group(2)))
            pct = max(0.0, min(100.0, (current - 1) * 100.0 / total))
            progress_var.set(pct)
            status_var.set(f"Auto Tune {current}/{total}")
            worker_dashboard.update_eta(None, 0.0, current, total)
            return

        m = re.search(r"主動畫\s+([0-9.]+)%", line)
        if m:
            pct = max(0.0, min(100.0, float(m.group(1))))
            progress_var.set(pct)
            status_var.set(f"主動畫 {pct:.1f}%")
        elif "準備結尾 overview" in line:
            progress_var.set(98.0); status_var.set("結尾地圖")
        elif "合併 segments" in line or "合併 chunks" in line:
            progress_var.set(99.0); status_var.set("合併影片")
        elif line.startswith("[DONE] 完成："):
            progress_var.set(100.0); status_var.set("完成")
            worker_dashboard.update_eta(0, 0, 100, 100)

    def collect_config():
        try:
            w = int(width_var.get()); h = int(height_var.get()); fps = int(fps_var.get())
            workers = int(workers_var.get()); chunks = int(chunks_var.get())
            if w < 320 or h < 320 or fps <= 0 or workers <= 0 or chunks <= 0:
                raise ValueError

            auto_enabled = bool(auto_duration_var.get())
            if auto_enabled:
                rate = float(seconds_per_100km_var.get())
                if rate <= 0:
                    raise ValueError
                gpx_path_for_duration = str(Path(gpx_var.get().strip()).expanduser().resolve())
                if state.get("gpx_distance_path") == gpx_path_for_duration and state.get("gpx_distance_km") is not None:
                    distance_km = float(state["gpx_distance_km"])
                else:
                    distance_km = quick_gpx_distance_km(gpx_path_for_duration)
                    state["gpx_distance_km"] = distance_km
                    state["gpx_distance_path"] = gpx_path_for_duration
                dur = auto_duration_seconds(distance_km, rate)
                duration_var.set(round(dur, 1))
            else:
                try:
                    rate = float(seconds_per_100km_var.get())
                except Exception:
                    rate = float(config.AUTO_SECONDS_PER_100KM)
                distance_km = state.get("gpx_distance_km")
                dur = float(duration_var.get())
            if dur <= 0:
                raise ValueError
        except Exception as exc:
            raise ValueError(f"解析度、FPS、動畫秒數、Workers、Chunks/Worker 與自動時長設定必須有效。\n{exc}")
        return {
            "gpx_filename": str(Path(gpx_var.get().strip()).expanduser().resolve()),
            "output_filename": str(Path(out_var.get().strip()).expanduser().resolve()),
            "map_style_key": map_var.get(),
            "FRAME_WIDTH": w,
            "FRAME_HEIGHT": h,
            "FPS": fps,
            "VIDEO_DURATION": dur,
            "AUTO_DURATION_ENABLED": auto_enabled,
            "AUTO_SECONDS_PER_100KM": rate,
            "GPX_DISTANCE_KM": distance_km,
            "ZOOM_OUT_DURATION": float(zoomout_var.get()),
            "END_HOLD_DURATION": float(hold_var.get()),
            "VIEW_MARGIN": float(margin_var.get()),
            "LOCAL_MAP_ZOOM": config._normalize_zoom(local_zoom_var.get()),
            "RENDER_WORKERS": workers,
            "CHUNKS_PER_WORKER": chunks,
            "MAP_CONNECTIONS": int(connections_var.get()),
            "NVENC_BITRATE": bitrate_var.get().strip(),
            "NVENC_PRESET": preset_var.get().strip(),
            "PARALLEL_RENDER": bool(parallel_var.get()),
            "ENABLE_BASEMAP": bool(basemap_var.get()),
            "PREVIEW_MODE": bool(preview_var.get()),
            "MAP_USE_CACHE": bool(cache_var.get()),
            "PARALLEL_DISABLE_TILE_CACHE": bool(disable_parallel_cache_var.get()),
            "ENABLE_MEDIA": bool(enable_media_var.get()),
            "MEDIA_PATH": str(Path(media_var.get().strip()).expanduser().resolve()) if media_var.get().strip() else "",
            "MEDIA_POPUP_DURATION": float(media_duration_var.get()),
            "MEDIA_TIME_OFFSET_SEC": float(media_offset_var.get()),
            "MEDIA_OVERRIDES_JSON": state.get("media_overrides_json", getattr(config, "MEDIA_OVERRIDES_JSON", "{}")),
            "USE_REAL_SPEED": bool(real_speed_var.get()),
            "HIDE_START_DISTANCE_KM": float(hide_start_var.get()),
            "HIDE_END_DISTANCE_KM": float(hide_end_var.get()),
            "CAMERA_MODE": camera_mode_var.get(),
        }

    def set_running(running: bool):
        start_btn.configure(state="disabled" if running else "normal")
        benchmark_btn.configure(state="disabled" if running else "normal")
        stop_btn.configure(state="normal" if running else "disabled")
        if running:
            apply_benchmark_btn.configure(state="disabled")
        elif state.get("benchmark_result"):
            apply_benchmark_btn.configure(state="normal")

    def _consume_benchmark_result(line: str):
        prefix = "AUTO_TUNE_RESULT:"
        if not line.startswith(prefix):
            return
        try:
            result = json.loads(line[len(prefix):].strip())
            recommended = int(result["recommended_workers"])
            peak = float(result.get("peak_fps", 0.0))
            rec_fps = float(result.get("recommended_fps", 0.0))
            state["benchmark_result"] = result
            benchmark_result_var.set(
                f"建議 {recommended} Workers  |  約 {rec_fps:.1f} fps  |  峰值 {peak:.1f} fps"
            )
            if state.get("proc") is None:
                apply_benchmark_btn.configure(state="normal")
        except Exception as exc:
            append_log(f"[WARN] GUI：解析 Auto Tune 結果失敗：{exc}")

    def apply_benchmark_recommendation():
        result = state.get("benchmark_result")
        if not result:
            messagebox.showinfo("Auto Tune", "尚未有可套用的效能測試結果。")
            return
        recommended = int(result.get("recommended_workers", workers_var.get()))
        workers_var.set(recommended)
        parallel_var.set(recommended > 1)
        benchmark_result_var.set(benchmark_result_var.get() + "  (已套用)")
        append_log(f"[INFO] 已套用 Auto Tune 建議：Workers={recommended}")

    def finish_proc(returncode: int):
        mode = state.get("proc_mode") or "render"
        state["proc"] = None
        state["proc_mode"] = None
        cfg = state.get("config_path")
        if cfg:
            try: Path(cfg).unlink(missing_ok=True)
            except Exception: pass
        state["config_path"] = None
        set_running(False)
        if mode == "benchmark":
            if returncode == 0 and state.get("benchmark_result"):
                progress_var.set(100.0); status_var.set("Auto Tune 完成")
                append_log("[DONE] GUI：效能測試完成，可按『套用建議』。")
            elif returncode == 0:
                status_var.set("Auto Tune 完成，但無結果")
                append_log("[WARN] GUI：效能測試程序正常結束，但沒有收到結果。")
            else:
                status_var.set(f"Auto Tune 失敗 (exit {returncode})")
                append_log(f"[ERROR] GUI：效能測試程序結束碼 {returncode}")
        else:
            if returncode == 0:
                progress_var.set(100.0); status_var.set("完成")
                append_log("[DONE] GUI：渲染程序正常結束。")
            else:
                status_var.set(f"失敗 (exit {returncode})")
                append_log(f"[ERROR] GUI：渲染程序結束碼 {returncode}")

    def reader_thread(proc):
        buf = ""
        try:
            assert proc.stdout is not None
            while True:
                ch = proc.stdout.read(1)
                if ch == "":
                    if buf:
                        root.after(0, append_log, buf)
                        root.after(0, parse_progress, buf)
                        root.after(0, _consume_benchmark_result, buf)
                    break
                if ch in "\r\n":
                    if buf.strip():
                        line = buf
                        root.after(0, append_log, line)
                        root.after(0, parse_progress, line)
                        root.after(0, _consume_benchmark_result, line)
                    buf = ""
                else:
                    buf += ch
        finally:
            rc = proc.wait()
            root.after(0, finish_proc, rc)

    def _spawn_job(cfg: dict, mode: str):
        fd, cfg_path = tempfile.mkstemp(prefix=f"gpx_renderer_{mode}_", suffix=".json")
        os.close(fd)
        Path(cfg_path).write_text(json.dumps(cfg, ensure_ascii=False, indent=2), encoding="utf-8")
        state["config_path"] = cfg_path
        flag = "--benchmark-config" if mode == "benchmark" else "--render-config"
        cmd = _self_subprocess_command(flag, cfg_path)
        env = os.environ.copy()
        env["PYTHONIOENCODING"] = "utf-8"
        env["PYTHONUTF8"] = "1"
        kwargs = dict(
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True,
            encoding="utf-8", errors="replace", bufsize=1, env=env,
        )
        if os.name == "nt":
            if getattr(sys, "frozen", False):
                kwargs["creationflags"] = getattr(subprocess, "CREATE_NO_WINDOW", 0)
            else:
                kwargs["creationflags"] = getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0)
        else:
            kwargs["start_new_session"] = True
        try:
            proc = subprocess.Popen(cmd, **kwargs)
        except Exception:
            try: Path(cfg_path).unlink(missing_ok=True)
            except Exception: pass
            state["config_path"] = None
            raise
        state["proc"] = proc
        state["proc_mode"] = mode
        set_running(True)
        threading.Thread(target=reader_thread, args=(proc,), daemon=True).start()
        return cmd

    def start_benchmark():
        if state["proc"] is not None:
            return
        try:
            cfg = collect_config()
        except Exception as exc:
            messagebox.showerror("設定錯誤", str(exc)); return
        if not Path(cfg["gpx_filename"]).is_file():
            messagebox.showerror("找不到 GPX", cfg["gpx_filename"]); return

        logical = max(1, int(os.cpu_count() or 1))
        cfg["BENCHMARK_CANDIDATES"] = _default_benchmark_candidates(cfg.get("RENDER_WORKERS"))
        cfg["BENCHMARK_FRAMES"] = max(240, min(360, int(round(int(cfg["FPS"]) * 5.0))))
        state["benchmark_result"] = None
        state["current_log_path"] = get_log_file_path("benchmark")
        benchmark_result_var.set("Auto Tune：測試中…")
        apply_benchmark_btn.configure(state="disabled")
        progress_var.set(0.0); status_var.set("Auto Tune 啟動中")
        worker_dashboard.reset(new_worker_count=len(cfg["BENCHMARK_CANDIDATES"]))
        worker_dashboard.update_config_summary(cfg)
        append_log("=" * 72)
        append_log(
            "[TEST] Auto Tune：將測試 " + ", ".join(str(x) for x in cfg["BENCHMARK_CANDIDATES"]) +
            f" Workers（CPU logical={logical}）。"
        )
        append_log("   為了讓結果穩定，benchmark 不下載底圖；正式渲染的底圖設定不會被修改。")
        try:
            cmd = _spawn_job(cfg, "benchmark")
            append_log(f"[INFO] 啟動效能測試：{cmd[0]} --benchmark-config ...")
        except Exception as exc:
            benchmark_result_var.set("Auto Tune：啟動失敗")
            set_running(False)
            messagebox.showerror("效能測試啟動失敗", str(exc))

    def start_render():
        if state["proc"] is not None:
            return
        try:
            cfg = collect_config()
        except Exception as exc:
            messagebox.showerror("設定錯誤", str(exc)); return
        if not Path(cfg["gpx_filename"]).is_file():
            messagebox.showerror("找不到 GPX", cfg["gpx_filename"]); return
        if not cfg["output_filename"].lower().endswith(".mp4"):
            cfg["output_filename"] += ".mp4"
            out_var.set(cfg["output_filename"])

        state["current_log_path"] = get_log_file_path("render")
        progress_var.set(0.0); status_var.set("啟動中")
        worker_dashboard.reset(new_worker_count=int(cfg["RENDER_WORKERS"]))
        worker_dashboard.update_config_summary(cfg)
        append_log("=" * 72)
        try:
            cmd = _spawn_job(cfg, "render")
            append_log(f"[INFO] 啟動：{cmd[0]} --render-config ...")
        except Exception as exc:
            set_running(False)
            messagebox.showerror("啟動失敗", str(exc)); return

    def stop_render():
        proc = state.get("proc")
        if proc is None:
            return
        mode = state.get("proc_mode") or "render"
        title = "停止效能測試" if mode == "benchmark" else "停止渲染"
        question = "確定要停止目前效能測試？" if mode == "benchmark" else "確定要停止目前渲染？"
        if not messagebox.askyesno(title, question):
            return
        status_var.set("停止中")
        try:
            if os.name == "nt":
                subprocess.run(
                    ["taskkill", "/PID", str(proc.pid), "/T", "/F"],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    **_background_subprocess_kwargs(),
                )
            else:
                import signal
                os.killpg(os.getpgid(proc.pid), signal.SIGTERM)
        except Exception:
            try: proc.terminate()
            except Exception: pass

    def open_log_folder():
        from gpx_renderer.utils import application_dir
        log_dir = application_dir() / "logs"
        log_dir.mkdir(parents=True, exist_ok=True)
        try:
            if os.name == "nt":
                os.startfile(str(log_dir))
            elif sys.platform == "darwin":
                subprocess.Popen(["open", str(log_dir)])
            else:
                subprocess.Popen(["xdg-open", str(log_dir)])
        except Exception as exc:
            messagebox.showerror("開啟失敗", f"無法開啟 Log 資料夾：\n{log_dir}\n{exc}")

    start_btn = ttk.Button(buttons, text="開始渲染", command=start_render)
    start_btn.pack(side="left")
    stop_btn = ttk.Button(buttons, text="停止", command=stop_render, state="disabled")
    stop_btn.pack(side="left", padx=(8, 0))
    ttk.Button(buttons, text="📁 開啟 Log 資料夾", command=open_log_folder).pack(side="left", padx=(8, 0))

    def on_close():
        if state.get("proc") is not None:
            running_name = "效能測試" if state.get("proc_mode") == "benchmark" else "渲染"
            if not messagebox.askyesno("關閉", f"{running_name}仍在執行。要一起停止並關閉嗎？"):
                return
            stop_render()
        root.destroy()
    root.protocol("WM_DELETE_WINDOW", on_close)

    root.mainloop()
