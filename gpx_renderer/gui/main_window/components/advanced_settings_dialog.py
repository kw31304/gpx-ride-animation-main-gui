# -*- coding: utf-8 -*-
"""
進階渲染參數設定對話框 (AdvancedSettingsDialog)
提供使用者自訂解析度、並行運算進程、圖資連線數、NVENC 編碼參數、底圖快取保存方式與效能測試 (Auto Tune) 等進階設定。
"""

from __future__ import annotations
from pathlib import Path
from typing import Optional, Tuple
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QGroupBox, QLabel, QSpinBox, QComboBox, QCheckBox, QPushButton,
    QDialogButtonBox, QScrollArea, QFrame, QMessageBox
)
from gpx_renderer import config
from gpx_renderer.core.cache_manager import CacheManager


class AdvancedSettingsDialog(QDialog):
    """
    進階渲染參數設定對話框。
    """
    def __init__(
        self,
        parent: Optional[QWidget] = None,
        custom_width: int = 1440,
        custom_height: int = 1440,
        workers: int = 6,
        chunks: int = 4,
        connections: int = 16,
        preset: str = "p4",
        bitrate: str = "20M",
        basemap: bool = True,
        parallel: bool = True,
        enable_media: bool = True,
        preview_mode: bool = False,
        cache_mode: str = "session",
        benchmark_result: Optional[dict] = None,
        is_benchmarking: bool = False,
    ):
        super().__init__(parent)
        self._main_window = parent
        self.setWindowTitle("進階渲染參數詳細設定")
        self.resize(540, 680)
        self.setModal(True)

        # 儲存傳入的初始值
        self._init_w = custom_width
        self._init_h = custom_height
        self._init_workers = workers
        self._init_chunks = chunks
        self._init_conn = connections
        self._init_preset = preset
        self._init_bitrate = bitrate
        self._init_basemap = basemap
        self._init_parallel = parallel
        self._init_enable_media = enable_media
        self._init_preview_mode = preview_mode
        self._init_cache_mode = cache_mode or getattr(config, "MAP_CACHE_MODE", "session")
        self._init_benchmark_result = benchmark_result
        self._is_benchmarking = is_benchmarking
        self._last_recommended_workers: Optional[int] = None

        self._setup_ui()

    def _setup_ui(self):
        outer_layout = QVBoxLayout(self)
        outer_layout.setContentsMargins(10, 10, 10, 10)
        outer_layout.setSpacing(8)

        # 可捲動區域，防止不同螢幕解析度下被截斷
        scroll = QScrollArea(self)
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        container = QWidget()
        main_layout = QVBoxLayout(container)
        main_layout.setSpacing(12)
        main_layout.setContentsMargins(4, 4, 8, 4)

        # 1. 自訂畫面解析度
        grp_res = QGroupBox("自訂畫面解析度 (Custom Resolution)", container)
        res_layout = QGridLayout(grp_res)
        res_layout.addWidget(QLabel("寬度 (Width):"), 0, 0)
        self.spin_w = QSpinBox(grp_res)
        self.spin_w.setRange(240, 7680)
        self.spin_w.setSingleStep(2)
        self.spin_w.setValue(self._init_w)
        self.spin_w.setSuffix(" px")
        res_layout.addWidget(self.spin_w, 0, 1)

        res_layout.addWidget(QLabel("高度 (Height):"), 0, 2)
        self.spin_h = QSpinBox(grp_res)
        self.spin_h.setRange(240, 7680)
        self.spin_h.setSingleStep(2)
        self.spin_h.setValue(self._init_h)
        self.spin_h.setSuffix(" px")
        res_layout.addWidget(self.spin_h, 0, 3)

        btn_preset_1080p = QPushButton("1080p (1920×1080)")
        btn_preset_1080p.clicked.connect(lambda: (self.spin_w.setValue(1920), self.spin_h.setValue(1080)))
        btn_preset_sq = QPushButton("方形 (1440×1440)")
        btn_preset_sq.clicked.connect(lambda: (self.spin_w.setValue(1440), self.spin_h.setValue(1440)))
        btn_preset_vert = QPushButton("直式 (1080×1920)")
        btn_preset_vert.clicked.connect(lambda: (self.spin_w.setValue(1080), self.spin_h.setValue(1920)))

        h_presets = QHBoxLayout()
        h_presets.addWidget(btn_preset_1080p)
        h_presets.addWidget(btn_preset_sq)
        h_presets.addWidget(btn_preset_vert)
        res_layout.addLayout(h_presets, 1, 0, 1, 4)

        main_layout.addWidget(grp_res)

        # 2. 並行運算與圖資下載
        grp_perf = QGroupBox("並行算力與網路連線", container)
        perf_layout = QGridLayout(grp_perf)

        perf_layout.addWidget(QLabel("工作進程數 (Workers):"), 0, 0)
        self.spin_workers = QSpinBox(grp_perf)
        self.spin_workers.setRange(1, 32)
        self.spin_workers.setValue(self._init_workers)
        perf_layout.addWidget(self.spin_workers, 0, 1)

        perf_layout.addWidget(QLabel("每進程切片數 (Chunks):"), 0, 2)
        self.spin_chunks = QSpinBox(grp_perf)
        self.spin_chunks.setRange(1, 16)
        self.spin_chunks.setValue(self._init_chunks)
        perf_layout.addWidget(self.spin_chunks, 0, 3)

        perf_layout.addWidget(QLabel("圖資並行下載數:"), 1, 0)
        self.spin_conn = QSpinBox(grp_perf)
        self.spin_conn.setRange(1, 64)
        self.spin_conn.setValue(self._init_conn)
        self.spin_conn.setSuffix(" 條連線")
        perf_layout.addWidget(self.spin_conn, 1, 1)

        main_layout.addWidget(grp_perf)

        # 3. 效能測試與自動調校 (Auto Tune Benchmark)
        grp_benchmark = QGroupBox("效能測試與自動調校 (Auto Tune Benchmark)", container)
        bm_layout = QGridLayout(grp_benchmark)

        lbl_bm_desc = QLabel("用途：用短基準測試實測不同 Workers 數量的等效 FPS，自動推薦接近峰值效能的最佳工作進程數。", grp_benchmark)
        lbl_bm_desc.setStyleSheet("color: #94a3b8; font-size: 11px;")
        lbl_bm_desc.setWordWrap(True)
        bm_layout.addWidget(lbl_bm_desc, 0, 0, 1, 4)

        self.btn_autotune = QPushButton("⚡ 執行效能測試", grp_benchmark)
        self.btn_autotune.setToolTip("開始執行 Workers 效能基準測試 (Auto Tune)")
        self.btn_autotune.clicked.connect(self._on_run_autotune)
        bm_layout.addWidget(self.btn_autotune, 1, 0)

        self.lbl_autotune_result = QLabel("尚未測試", grp_benchmark)
        self.lbl_autotune_result.setStyleSheet("color: #e2e8f0; font-size: 11px; font-weight: bold;")
        bm_layout.addWidget(self.lbl_autotune_result, 1, 1, 1, 2)

        self.btn_apply_autotune = QPushButton("套用建議", grp_benchmark)
        self.btn_apply_autotune.setEnabled(False)
        self.btn_apply_autotune.setToolTip("將推薦的最佳 Workers 數值直接套用至上方設定")
        self.btn_apply_autotune.clicked.connect(self._on_apply_autotune)
        bm_layout.addWidget(self.btn_apply_autotune, 1, 3)

        if self._init_benchmark_result:
            self.update_benchmark_result(self._init_benchmark_result)
        elif self._is_benchmarking:
            self.lbl_autotune_result.setText("測試中，請稍候…")
            self.btn_autotune.setEnabled(False)

        main_layout.addWidget(grp_benchmark)

        # 4. 底圖快取管理 (Basemap Cache)
        grp_cache = QGroupBox("底圖快取管理 (Basemap Cache)", container)
        cache_layout = QGridLayout(grp_cache)

        cache_layout.addWidget(QLabel("快取保存方式:"), 0, 0)
        self.combo_cache_mode = QComboBox(grp_cache)
        self.combo_cache_mode.addItem("自動暫存 (關閉清除)", "session")
        self.combo_cache_mode.addItem("永久保留 (保留快取)", "persistent")
        self.combo_cache_mode.setCurrentIndex(1 if str(self._init_cache_mode).lower() == "persistent" else 0)
        self.combo_cache_mode.setToolTip("用途：切換底圖磁碟快取模式。自動暫存模式於關閉程式時清除；永久保留模式則保留以加速日後渲染。")
        cache_layout.addWidget(self.combo_cache_mode, 0, 1)

        self.lbl_cache_size = QLabel(grp_cache)
        self.lbl_cache_size.setStyleSheet("color: #94a3b8; font-size: 11px;")
        self._refresh_cache_size_label()
        cache_layout.addWidget(self.lbl_cache_size, 0, 2)

        self.btn_clear_cache = QPushButton("清除快取", grp_cache)
        self.btn_clear_cache.setToolTip("清除本機下載的所有底圖切片與高程快取檔案")
        self.btn_clear_cache.clicked.connect(self._on_clear_cache)
        cache_layout.addWidget(self.btn_clear_cache, 0, 3)

        main_layout.addWidget(grp_cache)

        # 5. NVENC 硬體編碼器
        grp_enc = QGroupBox("NVENC 硬體編碼器設定", container)
        enc_layout = QGridLayout(grp_enc)

        enc_layout.addWidget(QLabel("編碼預設檔 (Preset):"), 0, 0)
        self.combo_preset = QComboBox(grp_enc)
        self.combo_preset.addItems(["p1", "p2", "p3", "p4", "p5", "p6", "p7"])
        self.combo_preset.setCurrentText(self._init_preset)
        enc_layout.addWidget(self.combo_preset, 0, 1)

        enc_layout.addWidget(QLabel("影片位元率 (Bitrate):"), 0, 2)
        self.combo_bitrate = QComboBox(grp_enc)
        self.combo_bitrate.addItems(["8M", "12M", "20M", "24M", "30M", "40M", "60M"])
        self.combo_bitrate.setCurrentText(self._init_bitrate)
        enc_layout.addWidget(self.combo_bitrate, 0, 3)

        main_layout.addWidget(grp_enc)

        # 6. 渲染功能開關
        grp_switches = QGroupBox("渲染功能開關", container)
        sw_layout = QGridLayout(grp_switches)

        self.chk_basemap = QCheckBox("啟用地圖底圖 (Basemap)", grp_switches)
        self.chk_basemap.setChecked(self._init_basemap)
        sw_layout.addWidget(self.chk_basemap, 0, 0)

        self.chk_parallel = QCheckBox("啟用多進程並行渲染", grp_switches)
        self.chk_parallel.setChecked(self._init_parallel)
        sw_layout.addWidget(self.chk_parallel, 0, 1)

        self.chk_enable_media = QCheckBox("啟用相片與影片插入", grp_switches)
        self.chk_enable_media.setChecked(self._init_enable_media)
        sw_layout.addWidget(self.chk_enable_media, 1, 0)

        self.chk_preview = QCheckBox("預覽模式 (快速低畫質測試)", grp_switches)
        self.chk_preview.setChecked(self._init_preview_mode)
        sw_layout.addWidget(self.chk_preview, 1, 1)

        main_layout.addWidget(grp_switches)

        scroll.setWidget(container)
        outer_layout.addWidget(scroll)

        # 按鈕列
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel, self)
        button_box.button(QDialogButtonBox.Ok).setText("套用並儲存")
        button_box.button(QDialogButtonBox.Cancel).setText("取消")
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        outer_layout.addWidget(button_box)

    def _refresh_cache_size_label(self):
        try:
            mb = CacheManager.get_cache_size_mb()
            self.lbl_cache_size.setText(f"快取容量: {mb:.1f} MB")
        except Exception:
            self.lbl_cache_size.setText("快取容量: 0.0 MB")

    def _on_clear_cache(self):
        try:
            deleted, freed_mb = CacheManager.clear_cache()
            self._refresh_cache_size_label()
            if self._main_window and hasattr(self._main_window, "refresh_cache_size_display"):
                self._main_window.refresh_cache_size_display()
            QMessageBox.information(self, "快取已清除", f"已成功清除本機底圖快取，釋放約 {freed_mb:.1f} MB 空間。")
        except Exception as exc:
            QMessageBox.warning(self, "清除快取失敗", f"清理快取時發生錯誤: {exc}")

    def _on_run_autotune(self):
        if not self._main_window:
            return
        gpx_path = self._main_window.lineEdit_gpx.text().strip() if hasattr(self._main_window, "lineEdit_gpx") else ""
        if not gpx_path or not Path(gpx_path).is_file():
            QMessageBox.warning(self, "尚未載入 GPX", "請先在主畫面選取有效的 GPX 路線檔案以進行效能測試。")
            return
        self.lbl_autotune_result.setText("測試中，請稍候…")
        self.btn_autotune.setEnabled(False)
        self._main_window.start_benchmark()

    def update_benchmark_result(self, res: dict):
        rec = int(res.get("recommended_workers", self.spin_workers.value()))
        peak = float(res.get("peak_fps", 0.0))
        self._last_recommended_workers = rec
        self.lbl_autotune_result.setText(f"建議 {rec} Workers | 峰值 {peak:.1f} FPS")
        self.btn_apply_autotune.setEnabled(True)
        self.btn_autotune.setEnabled(True)

    def on_benchmark_finished(self):
        self.btn_autotune.setEnabled(True)
        if self.lbl_autotune_result.text() == "測試中，請稍候…":
            self.lbl_autotune_result.setText("測試已完成")

    def _on_apply_autotune(self):
        if self._last_recommended_workers is not None:
            self.spin_workers.setValue(self._last_recommended_workers)
            self.chk_parallel.setChecked(self._last_recommended_workers > 1)
            QMessageBox.information(self, "已套用", f"已將 Workers 數量設為推薦之 {self._last_recommended_workers}。")

    def get_values(self) -> dict:
        cache_data = self.combo_cache_mode.currentData()
        if not cache_data:
            cache_data = "session" if self.combo_cache_mode.currentIndex() == 0 else "persistent"
        return {
            "custom_width": self.spin_w.value(),
            "custom_height": self.spin_h.value(),
            "workers": self.spin_workers.value(),
            "chunks": self.spin_chunks.value(),
            "connections": self.spin_conn.value(),
            "preset": self.combo_preset.currentText().strip(),
            "bitrate": self.combo_bitrate.currentText().strip(),
            "basemap": self.chk_basemap.isChecked(),
            "parallel": self.chk_parallel.isChecked(),
            "enable_media": self.chk_enable_media.isChecked(),
            "preview_mode": self.chk_preview.isChecked(),
            "cache_mode": cache_data,
        }
