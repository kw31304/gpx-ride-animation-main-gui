# -*- coding: utf-8 -*-
"""
ProgressDashboardWidget
結合 PyCircularProgress 圓形進度環與狀態呈現的進度儀表板組件。
"""

from __future__ import annotations
from PySide6.QtCore import Qt, QSize
from PySide6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QGridLayout, QLabel, QFrame, QSizePolicy
)
from gpx_renderer.gui.widgets.py_circular_progress import PyCircularProgress


class ProgressDashboardWidget(QWidget):
    """
    儀表板進度條組件，封裝 PyCircularProgress，提供與 QProgressBar 相容之介面。
    可依需求切換圓環大小、色調與中央進度文字。
    """

    def __init__(
        self,
        progress_size: int = 120,
        progress_width: int = 10,
        progress_color: str = "#00adb5",
        bg_color: str = "#222831",
        text_color: str = "#eeeeee",
        parent: QWidget | None = None,
    ):
        super().__init__(parent)

        self.circular_progress = PyCircularProgress(
            value=0,
            progress_width=progress_width,
            is_rounded=True,
            progress_color=progress_color,
            bg_color=bg_color,
            text_color=text_color,
            font_size=15,
            suffix="%",
            parent=self,
        )
        self.circular_progress.setFixedSize(progress_size, progress_size)
        self.circular_progress.add_shadow(True)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.circular_progress)

    # -------------------------------------------------------------------------
    # QProgressBar 相容轉發介面
    # -------------------------------------------------------------------------
    def setValue(self, value: int | float) -> None:
        self.circular_progress.setValue(value)

    def set_value(self, value: int | float) -> None:
        self.circular_progress.set_value(value)

    def value(self) -> int | float:
        return self.circular_progress.value()

    def setMaximum(self, max_val: int | float) -> None:
        self.circular_progress.setMaximum(max_val)

    def setMinimum(self, min_val: int | float) -> None:
        self.circular_progress.setMinimum(min_val)

    def reset(self) -> None:
        self.circular_progress.reset()

    def set_progress_color(self, color: str) -> None:
        self.circular_progress.set_progress_color(color)


__all__ = [
    "ProgressDashboardWidget",
]
