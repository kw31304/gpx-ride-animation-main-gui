# gui\widgets\py_radio_button\py_radio_button.py
from qt_core import *

class PyRadioButton(QRadioButton):
    def __init__(
        self,
        width=18,       # 指示器(圓圈)的寬度
        height=18,      # 指示器(圓圈)的高度
        bg_color="#8a95aa",
        circle_color="#00BCFF",
        active_color="#00BCFF",
        animation_curve=QEasingCurve.OutBounce,
        parent=None,
        app_parent=None,
        text="",             # [新增] 預設文字
        tooltip_text="",
        dark_one="#1b1e23",
        text_foreground="#8a95aa",
        top_margin=40
    ):
        
        # 確保 parent 是 QWidget (與 PyToggle 邏輯相同)
        real_parent = parent
        if parent and not isinstance(parent, QWidget):
             if hasattr(parent, 'centralWidget'):
                 real_parent = parent.centralWidget()
             elif hasattr(parent, 'ui') and hasattr(parent.ui, 'central_widget'):
                 real_parent = parent.ui.central_widget
        
        QRadioButton.__init__(self, real_parent)
        self.setText(text)
        
        # [修改] 不再設定固定尺寸，而是保存指示器的尺寸
        self._indicator_width = width
        self._indicator_height = height
        self.setMinimumSize(width, height) # 最小尺寸至少要能顯示指示器
        
        self.setCursor(Qt.PointingHandCursor)

        # COLORS
        self._bg_color = bg_color
        self._circle_color = circle_color
        self._active_color = active_color
        self._text_foreground = text_foreground # 保存文字顏色供 paintEvent 使用

        # 內部參數
        self._margin = 4          # 外框與內圓的距離
        self._circle_size = 0.0   # 動畫進度 (0.0 到 1.0)

        # ANIMATION setup
        self.animation = QPropertyAnimation(self, b"circle_size")
        self.animation.setEasingCurve(animation_curve)
        self.animation.setDuration(500)
        
        # 連接 toggled 信號來觸發動畫
        self.toggled.connect(self.setup_animation)

        # Parent & Tooltip setup
        self._parent = parent
        self._app_parent = app_parent
        self._top_margin = top_margin
        self._tooltip_text = tooltip_text
        self._tooltip = _ToolTip(
            app_parent,
            tooltip_text,
            dark_one,
            text_foreground
        )
        self._tooltip.hide()

    # [新增] 覆寫 sizeHint 以確保 layout 預留足夠空間給文字
    def sizeHint(self):
        text_width = self.fontMetrics().horizontalAdvance(self.text())
        spacing = 8 if self.text() else 0
        total_width = self._indicator_width + spacing + text_width
        # 高度取 指示器高度 與 文字高度 的最大值
        total_height = max(self._indicator_height, self.fontMetrics().height())
        return QSize(total_width, total_height)

    # PROPERTY FOR ANIMATION
    @Property(float)
    def circle_size(self):
        return self._circle_size

    @circle_size.setter
    def circle_size(self, size_factor):
        self._circle_size = size_factor
        self.update()

    # SETUP ANIMATION
    def setup_animation(self, checked):
        self.animation.stop()
        if checked:
            self.animation.setEndValue(1.0) # 放大內圓
        else:
            self.animation.setEndValue(0.0) # 縮小內圓
        self.animation.start()
    
    # CLICK AREA
    def hitButton(self, pos: QPoint):
        return self.contentsRect().contains(pos)

    # PAINT EVENT
    def paintEvent(self, e):

        # 如果按鈕還沒被排版(大小為0)，直接跳過不畫
        if self.width() <= 0 or self.height() <= 0:
            return

        p = QPainter(self)

        p.setRenderHint(QPainter.Antialiasing)

        # 指示器垂直居中的 Y 座標
        indicator_y = (self.height() - self._indicator_height) / 2.0

        # 1. 繪製背景 (外圈)
        pen_width = 2
        if self.isChecked():
            p.setPen(QPen(QColor(self._active_color), pen_width))
        else:
            p.setPen(QPen(QColor(self._bg_color), pen_width))
        
        p.setBrush(Qt.NoBrush)
        
        # 繪製圓形邊框，考慮 pen width 避免被裁切
        rect_outer = QRectF(pen_width/2.0, indicator_y + pen_width/2.0, 
                            self._indicator_width - pen_width, self._indicator_height - pen_width)
        p.drawEllipse(rect_outer)

        # 2. 繪製內圓 (指示器)
        # 內圓最大直徑
        max_diameter = self._indicator_height - (self._margin * 2)
        
        # 當前直徑 (根據動畫進度 _circle_size 計算)
        current_diameter = max_diameter * self._circle_size

        if current_diameter > 0:
            p.setPen(Qt.NoPen)
            p.setBrush(QColor(self._circle_color))
            
            # 計算置中位置 (相對於指示器區域)
            center_x = self._indicator_width / 2.0
            center_y = indicator_y + (self._indicator_height / 2.0)
            pos_x = center_x - (current_diameter / 2.0)
            pos_y = center_y - (current_diameter / 2.0)
            
            p.drawEllipse(QRectF(pos_x, pos_y, current_diameter, current_diameter))

        # 3. [新增] 繪製文字
        if self.text():
            p.setFont(self.font())
            p.setPen(QColor(self._text_foreground))
            
            # 文字區域：從指示器右邊開始，延伸到元件邊緣
            spacing = 8
            text_x = self._indicator_width + spacing
            text_w = self.width() - text_x
            rect_text = QRect(text_x, 0, text_w, self.height())
            
            p.drawText(rect_text, Qt.AlignLeft | Qt.AlignVCenter, self.text())

        p.end()

    # MOUSE EVENTS (Tooltip Logic)
    def enterEvent(self, event):
        if self._tooltip_text:
            self.move_tooltip()
            self._tooltip.show()
        super().enterEvent(event)

    def leaveEvent(self, event):
        if self._tooltip.isVisible():
            self._tooltip.hide()
        super().leaveEvent(event)

    def move_tooltip(self):
        if not self._parent: return
        
        gp = self.mapToGlobal(QPoint(0, 0))

        try:
            if isinstance(self._parent, QWidget):
                pos = self._parent.mapFromGlobal(gp)
            else:
                 if self._app_parent:
                      pos = self._app_parent.mapFromGlobal(gp)
                 else:
                      return
        except:
             return

        pos_x = (pos.x() - (self._tooltip.width() // 2)) + (self._indicator_width // 2)
        pos_y = pos.y() - self._top_margin
        self._tooltip.move(pos_x, pos_y)

# TOOLTIP CLASS
class _ToolTip(QLabel):
    style_tooltip = """ 
    QLabel {{		
        background-color: {_dark_one};	
        color: {_text_foreground};
        padding-left: 10px;
        padding-right: 10px;
        border-radius: 17px;
        border: 0px solid transparent;
        font: 800 9pt "Segoe UI";
    }}
    """
    def __init__(
        self,
        parent, 
        tooltip,
        dark_one,
        text_foreground
    ):
        QLabel.__init__(self)

        style = self.style_tooltip.format(
            _dark_one = dark_one,
            _text_foreground = text_foreground
        )
        self.setObjectName(u"label_tooltip")
        self.setStyleSheet(style)
        self.setMinimumHeight(34)
        self.setParent(parent)
        self.setText(tooltip)
        self.adjustSize()

        self.shadow = QGraphicsDropShadowEffect(self)
        self.shadow.setBlurRadius(30)
        self.shadow.setXOffset(0)
        self.shadow.setYOffset(0)
        self.shadow.setColor(QColor(0, 0, 0, 80))
        self.setGraphicsEffect(self.shadow)
