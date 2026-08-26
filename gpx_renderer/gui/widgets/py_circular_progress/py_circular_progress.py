# -*- coding: utf-8 -*-
"""
PyCircularProgress 自定義圓形進度條元件。
支援正圓置中繪製、圓角端點、背景軌道、陰影特效、自定義文字、
自動偵測 Windows / Qt 深色/淺色主題自適應百分比文字配色，以及標準 QProgressBar API 相容。
"""

from __future__ import annotations
import sys

try:
    from qt_core import *
except ImportError:
    from PySide6.QtCore import Qt, QRectF, QSize, QEvent, Property
    from PySide6.QtGui import QPainter, QPen, QColor, QFont, QPalette
    from PySide6.QtWidgets import QWidget, QApplication, QGraphicsDropShadowEffect


def is_dark_mode(widget: QWidget | None = None) -> bool:
    """
    精確偵測當前系統或視窗是否處於深色模式 (Dark Theme)。
    優先順序：
    1. Qt 6.5+ QApplication.styleHints().colorScheme()
    2. 元件當前 Palette 背景亮度 (Window Background Lightness)
    3. Windows 系統登錄檔 (AppsUseLightTheme)
    """
    # 1. 透過 Qt 6.5+ 官方 API
    app = QApplication.instance()
    if app is not None:
        hints = app.styleHints()
        if hasattr(hints, "colorScheme"):
            scheme = hints.colorScheme()
            if scheme == Qt.ColorScheme.Dark:
                return True
            if scheme == Qt.ColorScheme.Light:
                return False

    # 2. 透過 Widget Palette 亮度判定
    if widget is not None:
        try:
            window_color = widget.palette().color(widget.backgroundRole())
            # 亮度小於 128 代表深色背景
            return window_color.lightness() < 128
        except Exception:
            pass

    # 3. 透過 Windows 系統登錄檔 (Registry)
    if sys.platform.startswith("win"):
        try:
            import winreg
            key = winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                r"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize"
            )
            val, _ = winreg.QueryValueEx(key, "AppsUseLightTheme")
            winreg.CloseKey(key)
            return val == 0
        except Exception:
            pass

    return False


class PyCircularProgress(QWidget):
    """自定義 Qt 圓形進度條 (Circular Progress Bar / Progress Ring)"""

    def __init__(
        self,
        parent: QWidget | None = None,
        value: int | float = 0,
        progress_width: int = 8,
        is_rounded: bool = True,
        min_value: int | float = 0,
        max_value: int | float = 100,
        progress_color: str = "#00adb5",
        enable_text: bool = True,
        font_family: str = "Segoe UI",
        font_size: int = 12,
        suffix: str = "%",
        text_color: str = "auto",
        enable_bg: bool = True,
        bg_color: str = "auto",
        **kwargs,
    ):
        if isinstance(parent, (int, float)):
            value = parent
            parent = kwargs.get("parent", None)

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
        self._shadow_enabled: bool = False

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

    def sizeHint(self) -> QSize:
        return QSize(80, 80)

    def minimumSizeHint(self) -> QSize:
        return QSize(40, 40)

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
        self._shadow_enabled = enable
        if enable:
            if not self.shadow:
                self.shadow = QGraphicsDropShadowEffect(self)
                self.shadow.setBlurRadius(15)
                self.shadow.setXOffset(0)
                self.shadow.setYOffset(0)
            
            # 依深淺模式調整陰影濃度
            if is_dark_mode(self):
                self.shadow.setColor(QColor(0, 0, 0, 90))
            else:
                self.shadow.setColor(QColor(0, 0, 0, 30))
            self.setGraphicsEffect(self.shadow)
        else:
            self.setGraphicsEffect(None)

    def _get_effective_text_color(self) -> QColor:
        """根據系統/視窗主題自動計算文字顏色"""
        if self.text_color and self.text_color.lower() != "auto":
            return QColor(self.text_color)
        
        # 自動偵測主題：深色背景使用純白，淺色背景使用高對比深墨藍黑 (#1e293b)
        if is_dark_mode(self):
            return QColor("#ffffff")
        else:
            return QColor("#1e293b")

    def _get_effective_bg_color(self) -> QColor:
        """根據系統/視窗主題自動計算底軌顏色"""
        if self.bg_color and self.bg_color.lower() != "auto":
            return QColor(self.bg_color)
        
        # 自動偵測主題：深色背景使用 #2b2d42，淺色背景使用俐落淺灰 #e2e8f0
        if is_dark_mode(self):
            return QColor("#2b2d42")
        else:
            return QColor("#e2e8f0")

    def changeEvent(self, event: QEvent) -> None:
        """響應系統或應用程式主題/調色盤動態變更"""
        super().changeEvent(event)
        if event.type() in (QEvent.PaletteChange, QEvent.ApplicationPaletteChange, QEvent.StyleChange):
            if self._shadow_enabled and self.shadow:
                if is_dark_mode(self):
                    self.shadow.setColor(QColor(0, 0, 0, 90))
                else:
                    self.shadow.setColor(QColor(0, 0, 0, 30))
            self.update()

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

        # 1. 繪製背景底軌 (自動自適應主題)
        if self.enable_bg:
            pen.setColor(self._get_effective_bg_color())
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

        # 3. 繪製中心文字 (顯示百分比，自動自適應主題)
        if self.enable_text:
            painter.setFont(QFont(self.font_family, self.font_size, QFont.Bold))
            painter.setPen(self._get_effective_text_color())
            val_display = int(round(self._value))
            text = f"{val_display}{self.suffix}"
            painter.drawText(self.rect(), Qt.AlignCenter, text)

        painter.end()


__all__ = ["PyCircularProgress", "is_dark_mode"]