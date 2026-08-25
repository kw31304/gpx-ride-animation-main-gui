# -*- coding: utf-8 -*-
"""
ClickablePreviewLabel 元件：支援滑鼠點擊放大預覽之圖片標籤。
"""

from __future__ import annotations
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QCursor
from PySide6.QtWidgets import QLabel


class ClickablePreviewLabel(QLabel):
    """支援點擊開啟原圖之預覽圖片標籤元件。"""
    clicked = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setCursor(QCursor(Qt.PointingHandCursor))

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.clicked.emit()
        super().mousePressEvent(event)


__all__ = [
    "ClickablePreviewLabel",
]
