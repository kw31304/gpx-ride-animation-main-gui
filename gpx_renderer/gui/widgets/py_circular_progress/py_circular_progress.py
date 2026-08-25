# -*- coding: utf-8 -*-
"""
PyCircularProgress 自定義圓形進度條元件。
支援正圓置中繪製、圓角端點、背景軌道、陰影特效、自定義文字以及標準 QProgressBar API 相容。
"""

from __future__ import annotations
try:
    from qt_core import *
except ImportError:
    from PySide6.QtCore import Qt, QRectF
    from PySide6.QtGui import QPainter, QPen, QColor, QFont
    from PySide6.QtWidgets import QWidget, QGraphicsDropShadowEffect


class PyCircularProgress(QWidget):
    """自定義 Qt 圓形進度條 (Circular Progress Bar / Progress Ring)"""

    def __init__(
        self,
        value: int | float = 0,
        progress_width: int = 10,
        is_rounded: bool = True,
        min_value: int | float = 0,
        max_value: int | float = 100,
        progress_color: str = "#2196F3",
        enable_text: bool = True,
        font_family: str = "Segoe UI",
        font_size: int = 14,
        suffix: str = "%",
        text_color: str = "#ffffff",
        enable_bg: bool = True,
        bg_color: str = "#2c313c",
        parent: QWidget | None = None,
    ):
        super().__init__(parent)

        # 數值屬性
        self._min_value = min_value
        self._max_value = max_value
        self._value = value
        
        # 繪圖樣式屬性
        self.progress_width = progress_width
        self.progress_rounded_cap = is_rounded
        self.progress_color = progress_color
        
        # 文字設定
        self.enable_text = enable_text
        self.font_family = font_family
        self.font_size = font_size
        self.suffix = suffix
        self.text_color = text_color
        
        # 背景軌道設定
        self.enable_bg = enable_bg
        self.bg_color = bg_color
        self.shadow: QGraphicsDropShadowEffect | None = None

    # =========================================================================
    # QProgressBar API 相容介面
    # =========================================================================
    def setValue(self, value: int | float) -> None:
        """標準 Qt QProgressBar 相容 API：設定進度值並非同步觸發重繪"""
        self.set_value(value)

    def set_value(self, value: int | float) -> None:
        """設定進度值"""
        clamped = max(self._min_value, min(self._max_value, value))
        if self._value != clamped:
            self._value = clamped
            self.update()

    def value(self) -> int | float:
        """取得當前進度值"""
        return self._value

    def setMaximum(self, max_value: int | float) -> None:
        """設定最大值"""
        self._max_value = max(self._min_value + 1e-6, max_value)
        self.set_value(self._value)
        self.update()

    def maximum(self) -> int | float:
        return self._max_value

    def setMinimum(self, min_value: int | float) -> None:
        """設定最小值"""
        self._min_value = min_value
        self.set_value(self._value)
        self.update()

    def minimum(self) -> int | float:
        return self._min_value

    def reset(self) -> None:
        """重置進度值至最小值"""
        self.set_value(self._min_value)

    # =========================================================================
    # 樣式與外觀設定
    # =========================================================================
    def set_progress_color(self, color: str) -> None:
        self.progress_color = color
        self.update()

    def set_bg_color(self, color: str) -> None:
        self.bg_color = color
        self.update()

    def set_text_color(self, color: str) -> None:
        self.text_color = color
        self.update()

    def add_shadow(self, enable: bool = True) -> None:
        """開啟或關閉柔和邊緣陰影"""
        if enable:
            if not self.shadow:
                self.shadow = QGraphicsDropShadowEffect(self)
                self.shadow.setBlurRadius(15)
                self.shadow.setXOffset(0)
                self.shadow.setYOffset(0)
                self.shadow.setColor(QColor(0, 0, 0, 90))
            self.setGraphicsEffect(self.shadow)
        else:
            self.setGraphicsEffect(None)

    # =========================================================================
    # 繪圖事件
    # =========================================================================
    def paintEvent(self, event) -> None:
        if self.width() <= 0 or self.height() <= 0:
            return

        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        # 保證正圓：取寬高中較小的一邊，並置中繪製
        side = min(self.width(), self.height()) - self.progress_width
        if side <= 0:
            painter.end()
            return

        offset_x = (self.width() - side) / 2.0
        offset_y = (self.height() - side) / 2.0
        arc_rect = QRectF(offset_x, offset_y, side, side)

        # 畫筆設定
        pen = QPen()
        pen.setWidth(self.progress_width)
        if self.progress_rounded_cap:
            pen.setCapStyle(Qt.RoundCap)

        # 1. 繪製背景底軌
        if self.enable_bg:
            pen.setColor(QColor(self.bg_color))
            painter.setPen(pen)
            painter.drawArc(arc_rect, 0, 360 * 16)

        # 2. 繪製進度弧線 (從 12 點鐘方向 90 度開始順時針旋轉)
        range_span = max(1e-6, float(self._max_value - self._min_value))
        ratio = max(0.0, min(1.0, float(self._value - self._min_value) / range_span))
        if ratio > 0:
            span_angle = int(-ratio * 360.0 * 16)
            pen.setColor(QColor(self.progress_color))
            painter.setPen(pen)
            painter.drawArc(arc_rect, 90 * 16, span_angle)

        # 3. 繪製中心文字 (顯示百分比)
        if self.enable_text:
            painter.setFont(QFont(self.font_family, self.font_size, QFont.Bold))
            painter.setPen(QColor(self.text_color))
            val_display = int(round(self._value))
            text = f"{val_display}{self.suffix}"
            painter.drawText(self.rect(), Qt.AlignCenter, text)

        painter.end()