# -*- coding: utf-8 -*-
"""
媒體微調與文字標籤手動設定模態視窗 (MediaManagerDialog)，包含互動式 GPX 路線預覽地圖 (可縮放/平移/標記連動) 與媒體參數設定。
"""

from __future__ import annotations
import tkinter as tk
from tkinter import ttk, messagebox
from typing import List, Callable, Optional
from pathlib import Path
import numpy as np
from PIL import Image, ImageTk

from gpx_renderer.core.media import MediaItem, match_media_to_ride, scan_media_files, prepare_thumbnail
from gpx_renderer.core.data import RideData


class RoutePreviewCanvas(tk.Frame):
    """向量路線預覽 Canvas，支援滑鼠滾輪縮放、平移與動態標記連動。"""

    def __init__(self, parent: tk.Widget, ride_data: RideData, **kwargs):
        super().__init__(parent, **kwargs)
        self.ride_data = ride_data

        # 視野狀態 (Mercator 米)
        self.view_center_x = ride_data.route_center_x
        self.view_center_y = ride_data.route_center_y

        min_x, max_x = float(ride_data.xs.min()), float(ride_data.xs.max())
        min_y, max_y = float(ride_data.ys.min()), float(ride_data.ys.max())
        self.route_w = max(max_x - min_x, 100.0)
        self.route_h = max(max_y - min_y, 100.0)

        self.scale = 1.0  # pixels per meter
        self.drag_start_x = 0
        self.drag_start_y = 0
        self.is_dragging = False

        self.media_items: List[MediaItem] = []
        self.selected_index: int = -1
        self.active_km: float = -1.0

        # 抽樣軌跡點以確保 60 FPS 流暢度
        step = max(1, len(ride_data.xs) // 600)
        self.sampled_xs = ride_data.xs[::step]
        self.sampled_ys = ride_data.ys[::step]

        self._init_canvas()

    def _init_canvas(self):
        # 頂部控制列
        tb = ttk.Frame(self, padding=(5, 4))
        tb.pack(fill="x", side="top")

        ttk.Label(tb, text="🗺️ 路線與媒體位置預覽", font=("Segoe UI", 9, "bold")).pack(side="left", padx=(5, 10))
        ttk.Button(tb, text="➕ 放大", width=6, command=lambda: self.zoom(1.25)).pack(side="left", padx=2)
        ttk.Button(tb, text="➖ 縮小", width=6, command=lambda: self.zoom(0.8)).pack(side="left", padx=2)
        ttk.Button(tb, text="🔍 全覽", width=6, command=self.reset_view).pack(side="left", padx=2)
        ttk.Button(tb, text="📍 聚焦照片", width=9, command=self.focus_active).pack(side="left", padx=(6, 2))

        ttk.Label(tb, text="(滑鼠滾輪縮放 / 拖曳平移地圖)", font=("Segoe UI", 8), foreground="#777777").pack(side="right", padx=5)

        # Canvas
        self.canvas = tk.Canvas(self, bg="#121820", highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)

        # 事件綁定
        self.canvas.bind("<Configure>", self._on_resize)
        self.canvas.bind("<ButtonPress-1>", self._on_drag_start)
        self.canvas.bind("<B1-Motion>", self._on_drag_motion)
        self.canvas.bind("<ButtonRelease-1>", self._on_drag_stop)

        self.canvas.bind("<ButtonPress-3>", self._on_drag_start)
        self.canvas.bind("<B3-Motion>", self._on_drag_motion)
        self.canvas.bind("<ButtonRelease-3>", self._on_drag_stop)

        # 滾輪縮放 (Windows & Linux)
        self.canvas.bind("<MouseWheel>", self._on_mousewheel)
        self.canvas.bind("<Button-4>", lambda e: self.zoom(1.15, (e.x, e.y)))
        self.canvas.bind("<Button-5>", lambda e: self.zoom(0.85, (e.x, e.y)))

    def _on_resize(self, event):
        if self.scale == 1.0:
            self.reset_view()
        else:
            self.redraw()

    def reset_view(self):
        cw = max(self.canvas.winfo_width(), 200)
        ch = max(self.canvas.winfo_height(), 200)

        scale_x = (cw * 0.82) / self.route_w
        scale_y = (ch * 0.82) / self.route_h
        self.scale = min(scale_x, scale_y)

        self.view_center_x = self.ride_data.route_center_x
        self.view_center_y = self.ride_data.route_center_y
        self.redraw()

    def focus_active(self):
        if self.active_km < 0:
            return
        dists = np.abs(self.ride_data.distances - self.active_km)
        best_i = int(np.argmin(dists))
        self.view_center_x = float(self.ride_data.xs[best_i])
        self.view_center_y = float(self.ride_data.ys[best_i])
        self.redraw()

    def zoom(self, factor: float, center_px: Optional[tuple[int, int]] = None):
        if center_px is not None:
            mx, my = center_px
            wx, wy = self._canvas_to_world(mx, my)
            self.scale *= factor
            self.view_center_x = wx - (mx - self.canvas.winfo_width() / 2.0) / self.scale
            self.view_center_y = wy + (my - self.canvas.winfo_height() / 2.0) / self.scale
        else:
            self.scale *= factor

        self.redraw()

    def _on_mousewheel(self, event):
        factor = 1.2 if event.delta > 0 else 0.8
        self.zoom(factor, (event.x, event.y))

    def _on_drag_start(self, event):
        self.drag_start_x = event.x
        self.drag_start_y = event.y
        self.is_dragging = True

    def _on_drag_motion(self, event):
        if not self.is_dragging:
            return
        dx = event.x - self.drag_start_x
        dy = event.y - self.drag_start_y
        self.drag_start_x = event.x
        self.drag_start_y = event.y

        self.view_center_x -= dx / max(self.scale, 1e-6)
        self.view_center_y += dy / max(self.scale, 1e-6)
        self.redraw()

    def _on_drag_stop(self, event):
        self.is_dragging = False

    def _world_to_canvas(self, x: float, y: float) -> tuple[float, float]:
        cw = self.canvas.winfo_width() / 2.0
        ch = self.canvas.winfo_height() / 2.0
        px = cw + (x - self.view_center_x) * self.scale
        py = ch - (y - self.view_center_y) * self.scale
        return px, py

    def _canvas_to_world(self, px: float, py: float) -> tuple[float, float]:
        cw = self.canvas.winfo_width() / 2.0
        ch = self.canvas.winfo_height() / 2.0
        wx = self.view_center_x + (px - cw) / max(self.scale, 1e-6)
        wy = self.view_center_y - (py - ch) / max(self.scale, 1e-6)
        return wx, wy

    def set_data(self, media_items: List[MediaItem], selected_index: int, active_km: float):
        self.media_items = media_items
        self.selected_index = selected_index
        self.active_km = active_km
        self.redraw()

    def redraw(self):
        self.canvas.delete("all")

        # 1. 繪製 GPX 軌跡線
        pts = []
        for x, y in zip(self.sampled_xs, self.sampled_ys):
            px, py = self._world_to_canvas(x, y)
            pts.extend([px, py])

        if len(pts) >= 4:
            self.canvas.create_line(pts, fill="#2a3848", width=5, capstyle="round", joinstyle="round")
            self.canvas.create_line(pts, fill="#ff7043", width=3, capstyle="round", joinstyle="round")

        # 2. 繪製所有媒體項目的標記點 Pins (包含自動帶入之拍攝時間/GPS 對齊點)
        for i, item in enumerate(self.media_items):
            matched_i = item.matched_index
            if item.manual_distance_km is not None and item.manual_distance_km >= 0:
                dists = np.abs(self.ride_data.distances - item.manual_distance_km)
                matched_i = int(np.argmin(dists))

            if matched_i < 0 or matched_i >= self.ride_data.total_points:
                continue

            mx = float(self.ride_data.xs[matched_i])
            my = float(self.ride_data.ys[matched_i])
            px, py = self._world_to_canvas(mx, my)

            # 一般相片標記 (白色圓圈 + 數字)
            is_active = (i == self.selected_index)
            if not is_active:
                r = 6
                self.canvas.create_oval(px - r, py - r, px + r, py + r, fill="#ffffff", outline="#222222", width=1.5)
                self.canvas.create_text(px, py - 11, text=f"{i+1}", fill="#e0e0e0", font=("Segoe UI", 9, "bold"))

        # 3. 繪製當前選中/滑動中的高亮橘光標記 Pin
        if self.active_km >= 0:
            dists = np.abs(self.ride_data.distances - self.active_km)
            best_i = int(np.argmin(dists))
            ax = float(self.ride_data.xs[best_i])
            ay = float(self.ride_data.ys[best_i])
            apx, apy = self._world_to_canvas(ax, ay)

            r_outer = 13
            self.canvas.create_oval(apx - r_outer, apy - r_outer, apx + r_outer, apy + r_outer, fill="", outline="#ffab40", width=3)
            r_inner = 7
            self.canvas.create_oval(apx - r_inner, apy - r_inner, apx + r_inner, apy + r_inner, fill="#ff5722", outline="#ffffff", width=2)

            self.canvas.create_rectangle(apx - 28, apy - 32, apx + 28, apy - 14, fill="#0a0f14", outline="#ff7043", width=1)
            self.canvas.create_text(apx, apy - 23, text=f"{self.active_km:.1f} km", fill="#ffffff", font=("Segoe UI", 8, "bold"))


class MediaManagerDialog(tk.Toplevel):
    """彈出式媒體管理與手動微調視窗。"""

    def __init__(
        self,
        parent: tk.Tk | tk.Toplevel,
        media_items: List[MediaItem],
        ride_data: RideData,
        media_duration: float = 3.5,
        media_offset_sec: float = 0.0,
        media_path: str = "",
        on_apply: Optional[Callable[[List[MediaItem], float, float], None]] = None,
    ):
        super().__init__(parent)
        self.title("路線媒體管理")
        self.geometry("1200x700")
        self.minsize(1000, 600)
        self.transient(parent)
        self.grab_set()

        self.media_items = media_items
        self.ride_data = ride_data
        self.media_path = media_path
        self.total_distance_km = max(0.1, float(ride_data.distances[-1]))
        self.on_apply = on_apply
        self.selected_index: int = -1
        self.selected_item: Optional[MediaItem] = None

        # 媒體通用參數
        self.var_media_duration = tk.DoubleVar(value=float(media_duration))
        self.var_media_offset = tk.DoubleVar(value=float(media_offset_sec))

        # 初次載入時自動帶入拍攝時間/GPS進行全數配對
        match_media_to_ride(self.media_items, self.ride_data, self.ride_data.gpx_times)

        self._init_ui()
        self._populate_tree()

    def _init_ui(self):
        # 頂部控制與全域媒體設定區
        top_bar = ttk.LabelFrame(self, text=" 媒體播放與相機時間校正 ", padding=(15, 8))
        top_bar.pack(fill="x", padx=15, pady=(10, 5))

        # 第一列：標題與說明
        header_sub = ttk.Frame(top_bar)
        header_sub.pack(fill="x", pady=(0, 6))
        ttk.Label(
            header_sub,
            text="路線媒體對齊與文字標籤編輯器",
            font=("Segoe UI", 12, "bold"),
        ).pack(side="left")
        ttk.Label(
            header_sub,
            text="（相片已自動依拍攝時間/GPS進行預設配對，可在地圖上拖拉微調並自訂下方文字標籤）",
            font=("Segoe UI", 9),
            foreground="#666666",
        ).pack(side="left", padx=(10, 0))

        # 第二列：將原本主介面的「媒體停留秒數」與「相機時間校正」移入於此
        settings_row = ttk.Frame(top_bar)
        settings_row.pack(fill="x", pady=2)

        ttk.Label(settings_row, text="媒體停留秒數：").pack(side="left", padx=(0, 4))
        spin_dur = ttk.Spinbox(settings_row, from_=1.0, to=30.0, increment=0.5, textvariable=self.var_media_duration, width=6)
        spin_dur.pack(side="left", padx=(0, 20))

        ttk.Label(settings_row, text="相機時間校正 (秒)：").pack(side="left", padx=(0, 4))
        entry_offset = ttk.Entry(settings_row, textvariable=self.var_media_offset, width=8)
        entry_offset.pack(side="left", padx=(0, 8))
        ttk.Button(settings_row, text="⏱️ 重新對齊時間", command=self._recalculate_time_offset).pack(side="left")
        ttk.Label(
            settings_row,
            text="💡 相機時間慢1分鐘請填 60 秒；快1分鐘請填 -60 秒",
            font=("Segoe UI", 8),
            foreground="#666666",
        ).pack(side="left", padx=(15, 0))

        # 主工作區 (三欄分割面板: 左側清單 | 中央地圖預覽 | 右側編輯屬性)
        main_paned = ttk.PanedWindow(self, orient="horizontal")
        main_paned.pack(fill="both", expand=True, padx=15, pady=5)

        # 1. 左側：媒體檔案 Treeview 清單
        tree_frame = ttk.Frame(main_paned)
        main_paned.add(tree_frame, weight=3)

        columns = ("id", "filename", "status", "caption")
        self.tree = ttk.Treeview(tree_frame, columns=columns, show="headings", selectmode="browse")
        self.tree.heading("id", text="#")
        self.tree.heading("filename", text="檔案名稱")
        self.tree.heading("status", text="對齊里程 (km)")
        self.tree.heading("caption", text="自訂說明文字")

        self.tree.column("id", width=32, minwidth=25, anchor="center")
        self.tree.column("filename", width=140, minwidth=90)
        self.tree.column("status", width=110, minwidth=80)
        self.tree.column("caption", width=120, minwidth=80)

        scrollbar = ttk.Scrollbar(tree_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        self.tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        self.tree.bind("<<TreeviewSelect>>", self._on_tree_select)

        # 2. 中央：互動式 GPX 路線預覽地圖 Canvas
        map_frame = ttk.Frame(main_paned)
        main_paned.add(map_frame, weight=4)
        self.preview_map = RoutePreviewCanvas(map_frame, self.ride_data)
        self.preview_map.pack(fill="both", expand=True)

        # 3. 右側：詳細編輯與縮圖預覽面板
        edit_frame = ttk.LabelFrame(main_paned, text=" 編輯選取的媒體屬性 ", padding=12)
        main_paned.add(edit_frame, weight=3)

        # 縮圖預覽 Label
        self.thumb_label = ttk.Label(edit_frame, text="[點選左側項目以預覽縮圖]", anchor="center")
        self.thumb_label.pack(fill="x", pady=(0, 8))

        # 檔名與偵測資訊
        self.lbl_filename = ttk.Label(edit_frame, text="檔案：-", font=("Segoe UI", 9, "bold"))
        self.lbl_filename.pack(anchor="w", pady=(0, 2))
        self.lbl_auto_info = ttk.Label(edit_frame, text="偵測：-", foreground="#555555")
        self.lbl_auto_info.pack(anchor="w", pady=(0, 10))

        # 手動里程覆寫模式
        override_frame = ttk.LabelFrame(edit_frame, text=" 里程對齊點微調 ", padding=10)
        override_frame.pack(fill="x", pady=(0, 10))

        self.var_override = tk.BooleanVar(value=False)
        chk_override = ttk.Checkbutton(
            override_frame,
            text="啟用手動覆寫里程點 (Override Distance)",
            variable=self.var_override,
            command=self._on_override_toggle,
        )
        chk_override.pack(anchor="w", pady=(0, 5))

        dist_input_frame = ttk.Frame(override_frame)
        dist_input_frame.pack(fill="x", pady=2)
        ttk.Label(dist_input_frame, text="里程 (km)：").pack(side="left")

        self.var_dist_km = tk.DoubleVar(value=0.0)
        self.entry_dist = ttk.Entry(dist_input_frame, textvariable=self.var_dist_km, width=8, state="disabled")
        self.entry_dist.pack(side="left", padx=(0, 5))
        self.lbl_max_km = ttk.Label(dist_input_frame, text=f"/ {self.total_distance_km:.2f} km")
        self.lbl_max_km.pack(side="left")

        self.slider_dist = ttk.Scale(
            override_frame,
            from_=0.0,
            to=self.total_distance_km,
            variable=self.var_dist_km,
            orient="horizontal",
            command=self._on_slider_move,
            state="disabled",
        )
        self.slider_dist.pack(fill="x", pady=(5, 0))

        # 照片自訂說明文字
        caption_frame = ttk.LabelFrame(edit_frame, text=" 照片下方說明文字 (Caption) ", padding=10)
        caption_frame.pack(fill="x", pady=(0, 12))

        self.var_caption = tk.StringVar(value="")
        self.entry_caption = ttk.Entry(caption_frame, textvariable=self.var_caption)
        self.entry_caption.pack(fill="x", pady=(0, 4))
        self.entry_caption.bind("<KeyRelease>", self._on_caption_change)
        ttk.Label(
            caption_frame,
            text="提示：動畫播放時將以黑透卡片浮雕顯示於照片下方。",
            font=("Segoe UI", 8),
            foreground="#777777",
        ).pack(anchor="w")

        # 套用單項微調按鈕
        btn_apply_single = ttk.Button(edit_frame, text="更新此項設定", command=self._apply_current_edit)
        btn_apply_single.pack(anchor="e")

        # 底部按鈕欄
        bottom_frame = ttk.Frame(self, padding=(15, 10))
        bottom_frame.pack(fill="x")

        ttk.Button(bottom_frame, text="🔄 重置全部為自動對齊", command=self._reset_all).pack(side="left")
        ttk.Button(bottom_frame, text="取消 (Cancel)", command=self.destroy).pack(side="right", padx=(5, 0))
        ttk.Button(bottom_frame, text="💾 儲存並套用設定", command=self._on_save_and_apply).pack(side="right")

    def _recalculate_time_offset(self):
        """根據輸入的相機時間校正秒數，重新與 GPX 時間軸對齊。"""
        if not self.media_path:
            return
        try:
            offset_sec = float(self.var_media_offset.get())
            new_items = scan_media_files(self.media_path, time_offset_sec=offset_sec)
            if new_items:
                # 重新對齊
                match_media_to_ride(new_items, self.ride_data, self.ride_data.gpx_times)
                # 保留既有的 manual_distance_km 與 caption
                old_map = {item.filename: (item.manual_distance_km, item.caption) for item in self.media_items}
                for item in new_items:
                    if item.filename in old_map:
                        item.manual_distance_km, item.caption = old_map[item.filename]
                self.media_items = new_items
                self._populate_tree()
                messagebox.showinfo("時間校正", f"已成功套用 {offset_sec} 秒相機時間校正並更新路線圖標記！")
        except Exception as exc:
            messagebox.showerror("時間校正錯誤", f"時間校正計算失敗：{exc}")

    def _populate_tree(self):
        for item in self.tree.get_children():
            self.tree.delete(item)

        for i, item in enumerate(self.media_items):
            matched_km = 0.0
            if item.manual_distance_km is not None and item.manual_distance_km >= 0:
                matched_km = item.manual_distance_km
                status_str = f"手動 {matched_km:.2f} km"
            elif item.matched_index >= 0 and item.matched_index < len(self.ride_data.distances):
                matched_km = float(self.ride_data.distances[item.matched_index])
                status_str = f"自動 {matched_km:.2f} km"
            else:
                status_str = "未對齊"

            cap_str = item.caption if item.caption else "-"
            self.tree.insert("", "end", iid=str(i), values=(i + 1, item.filename, status_str, cap_str))

        if self.media_items:
            self.preview_map.set_data(self.media_items, self.selected_index, self.preview_map.active_km)

    def _on_tree_select(self, event):
        selected = self.tree.selection()
        if not selected:
            return

        idx = int(selected[0])
        self.selected_index = idx
        self.selected_item = self.media_items[idx]
        item = self.selected_item

        self.lbl_filename.config(text=f"檔案：{item.filename}")
        info_str = "無"
        if item.timestamp:
            info_str = f"時間 {item.timestamp.strftime('%Y-%m-%d %H:%M:%S')}"
        if item.lat is not None and item.lon is not None:
            info_str += f" | GPS ({item.lat:.5f}, {item.lon:.5f})"
        self.lbl_auto_info.config(text=f"偵測：{info_str}")

        cur_km = 0.0
        if item.manual_distance_km is not None and item.manual_distance_km >= 0:
            self.var_override.set(True)
            cur_km = float(item.manual_distance_km)
        elif item.matched_index >= 0 and item.matched_index < len(self.ride_data.distances):
            self.var_override.set(False)
            cur_km = float(self.ride_data.distances[item.matched_index])

        self.var_dist_km.set(round(cur_km, 2))
        self._on_override_toggle()
        self.var_caption.set(item.caption or "")

        self.preview_map.set_data(self.media_items, self.selected_index, cur_km)
        self.preview_map.focus_active()

        try:
            p = Path(item.file_path)
            if p.is_file() and item.media_type == "image":
                with Image.open(p) as img:
                    img.thumbnail((200, 130))
                    photo = ImageTk.PhotoImage(img)
                    self.thumb_label.config(image=photo, text="")
                    self.thumb_label.image = photo
            else:
                self.thumb_label.config(image="", text=f"[{item.media_type.upper()} 媒體檔案]")
        except Exception:
            self.thumb_label.config(image="", text="[無法載入預覽縮圖]")

    def _on_override_toggle(self):
        state = "normal" if self.var_override.get() else "disabled"
        self.entry_dist.config(state=state)
        self.slider_dist.config(state=state)

    def _on_slider_move(self, val):
        try:
            v = float(val)
            round_v = round(v, 2)
            self.var_dist_km.set(round_v)
            self.preview_map.active_km = round_v
            self.preview_map.redraw()
        except Exception:
            pass

    def _on_caption_change(self, event):
        pass

    def _apply_current_edit(self):
        if not self.selected_item:
            return

        item = self.selected_item
        if self.var_override.get():
            val = max(0.0, min(self.total_distance_km, float(self.var_dist_km.get())))
            item.manual_distance_km = round(val, 2)
        else:
            item.manual_distance_km = None

        item.caption = self.var_caption.get().strip()
        self._populate_tree()

    def _reset_all(self):
        if messagebox.askyesno("確認重置", "確定要清空所有相片的手動微調里程與自訂文字標籤嗎？"):
            for item in self.media_items:
                item.manual_distance_km = None
                item.caption = ""
            self._populate_tree()

    def _on_save_and_apply(self):
        self._apply_current_edit()
        try:
            dur = float(self.var_media_duration.get())
            offset_sec = float(self.var_media_offset.get())
            if self.on_apply:
                self.on_apply(self.media_items, dur, offset_sec)
            messagebox.showinfo("套用成功", "已成功更新媒體微調設定、對齊里程與全域媒體參數！")
            self.destroy()
        except Exception as exc:
            messagebox.showerror("套用失敗", f"更新媒體設定時發生錯誤：{exc}")
