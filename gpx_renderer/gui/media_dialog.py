# -*- coding: utf-8 -*-
"""
媒體微調與文字標籤手動設定模態視窗 (MediaManagerDialog)。
"""

from __future__ import annotations
import tkinter as tk
from tkinter import ttk, messagebox
from typing import List, Callable, Optional
from pathlib import Path
from PIL import Image, ImageTk

from gpx_renderer.core.media import MediaItem, prepare_thumbnail


class MediaManagerDialog(tk.Toplevel):
    """彈出式媒體管理與手動微調視窗。"""

    def __init__(
        self,
        parent: tk.Tk | tk.Toplevel,
        media_items: List[MediaItem],
        total_distance_km: float,
        on_apply: Callable[[List[MediaItem]], None],
    ):
        super().__init__(parent)
        self.title("📷 路線媒體微調與文字標籤管理")
        self.geometry("960x600")
        self.minsize(840, 520)
        self.transient(parent)
        self.grab_set()

        self.media_items = media_items
        self.total_distance_km = max(0.1, float(total_distance_km))
        self.on_apply = on_apply
        self.selected_item: Optional[MediaItem] = None

        self._init_ui()
        self._populate_tree()

    def _init_ui(self):
        # 標題區
        header_frame = ttk.Frame(self, padding=(15, 10))
        header_frame.pack(fill="x")
        ttk.Label(
            header_frame,
            text="📷 路線媒體微調與文字標籤編輯器",
            font=("Segoe UI", 13, "bold"),
        ).pack(anchor="w")
        ttk.Label(
            header_frame,
            text="可手動微調每張相片/影片出現在路線上的里程點 (km)，並為照片加入下方說明文字。",
            font=("Segoe UI", 9),
            foreground="#666666",
        ).pack(anchor="w", pady=(2, 0))

        # 主工作區 (分開左右面板)
        main_paned = ttk.PanedWindow(self, orient="horizontal")
        main_paned.pack(fill="both", expand=True, padx=15, pady=5)

        # 左側：媒體檔案 Treeview 清單
        tree_frame = ttk.Frame(main_paned)
        main_paned.add(tree_frame, weight=3)

        columns = ("filename", "auto_info", "status", "caption")
        self.tree = ttk.Treeview(tree_frame, columns=columns, show="headings", selectmode="browse")
        self.tree.heading("filename", text="檔案名稱")
        self.tree.heading("auto_info", text="EXIF 自動偵測資訊")
        self.tree.heading("status", text="對齊模式與里程 (km)")
        self.tree.heading("caption", text="自訂照片說明文字")

        self.tree.column("filename", width=160, minwidth=100)
        self.tree.column("auto_info", width=180, minwidth=120)
        self.tree.column("status", width=140, minwidth=100)
        self.tree.column("caption", width=160, minwidth=100)

        scrollbar = ttk.Scrollbar(tree_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        self.tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        self.tree.bind("<<TreeviewSelect>>", self._on_tree_select)

        # 右側：詳細編輯與縮圖預覽面板
        edit_frame = ttk.LabelFrame(main_paned, text=" 編輯選取的媒體屬性 ", padding=15)
        main_paned.add(edit_frame, weight=2)

        # 縮圖預覽 Canvas
        self.thumb_label = ttk.Label(edit_frame, text="[點選左側項目以預覽縮圖]", anchor="center")
        self.thumb_label.pack(fill="x", pady=(0, 10))

        # 檔名與偵測資訊
        self.lbl_filename = ttk.Label(edit_frame, text="檔案：-", font=("Segoe UI", 9, "bold"))
        self.lbl_filename.pack(anchor="w", pady=(0, 2))
        self.lbl_auto_info = ttk.Label(edit_frame, text="偵測：-", foreground="#555555")
        self.lbl_auto_info.pack(anchor="w", pady=(0, 12))

        # 手動里程覆寫模式
        override_frame = ttk.LabelFrame(edit_frame, text=" 里程對齊點微調 ", padding=10)
        override_frame.pack(fill="x", pady=(0, 12))

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
        caption_frame.pack(fill="x", pady=(0, 15))

        self.var_caption = tk.StringVar(value="")
        self.entry_caption = ttk.Entry(caption_frame, textvariable=self.var_caption)
        self.entry_caption.pack(fill="x", pady=(0, 5))
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

    def _populate_tree(self):
        for item in self.tree.get_children():
            self.tree.delete(item)

        for i, item in enumerate(self.media_items):
            info_str = ""
            if item.timestamp:
                info_str = f"🕒 {item.timestamp.strftime('%H:%M:%S')}"
            elif item.lat is not None and item.lon is not None:
                info_str = f"📍 ({item.lat:.4f}, {item.lon:.4f})"
            else:
                info_str = "無 EXIF"

            status_str = "自動對齊"
            if item.manual_distance_km is not None and item.manual_distance_km >= 0:
                status_str = f"手動 ({item.manual_distance_km:.2f} km)"

            cap_str = item.caption if item.caption else "-"
            self.tree.insert("", "end", iid=str(i), values=(item.filename, info_str, status_str, cap_str))

    def _on_tree_select(self, event):
        selected = self.tree.selection()
        if not selected:
            return

        idx = int(selected[0])
        self.selected_item = self.media_items[idx]
        item = self.selected_item

        self.lbl_filename.config(text=f"檔案：{item.filename}")
        info_str = "無"
        if item.timestamp:
            info_str = f"時間 {item.timestamp.strftime('%Y-%m-%d %H:%M:%S')}"
        if item.lat is not None and item.lon is not None:
            info_str += f" | GPS ({item.lat:.5f}, {item.lon:.5f})"
        self.lbl_auto_info.config(text=f"偵測：{info_str}")

        # 設定手動公里數狀態
        if item.manual_distance_km is not None and item.manual_distance_km >= 0:
            self.var_override.set(True)
            self.var_dist_km.set(float(item.manual_distance_km))
        else:
            self.var_override.set(False)
            self.var_dist_km.set(0.0)

        self._on_override_toggle()

        # 設定 Caption
        self.var_caption.set(item.caption or "")

        # 預覽縮圖
        try:
            p = Path(item.file_path)
            if p.is_file() and item.media_type == "image":
                with Image.open(p) as img:
                    img.thumbnail((200, 140))
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
            self.var_dist_km.set(round(v, 2))
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
            self.on_apply(self.media_items)
            messagebox.showinfo("套用成功", "已成功更新媒體微調設定！")
            self.destroy()
        except Exception as exc:
            messagebox.showerror("套用失敗", f"更新媒體設定時發生錯誤：{exc}")
