# gui\widgets\py_toggle\py_toggle.py
from qt_core import *

class PyToggle(QCheckBox):
    def __init__(
        self,
        width=60,   # [已修改] 預設寬度
        height=28,  # [新增] 預設高度，所有計算將基於此數值
        bg_color="#777",
        circle_color="#DDD",
        active_color="#00BCFF",
        animation_curve=QEasingCurve.OutBounce,
        parent=None,
        app_parent=None,
        tooltip_text="",
        dark_one="#1b1e23",
        text_foreground="#8a95aa",
        top_margin=40
    ):
        
        # 確保 parent 是 QWidget，如果傳入的是 MainWindow wrapper，嘗試取其 widget
        real_parent = parent
        if parent and not isinstance(parent, QWidget):
             if hasattr(parent, 'centralWidget'):
                 real_parent = parent.centralWidget()
             elif hasattr(parent, 'ui') and hasattr(parent.ui, 'central_widget'):
                 real_parent = parent.ui.central_widget
        
        QCheckBox.__init__(self, real_parent)
        
        # [核心修改 1] 設定固定尺寸，後續繪圖都依賴這兩個值
        self.setFixedSize(width, height)
        self.setCursor(Qt.PointingHandCursor)

        # COLORS
        self._bg_color = bg_color
        self._circle_color = circle_color
        self._active_color = active_color

        # [核心修改 2] 定義內距 (圓點與邊框的距離)
        # 您可以修改這個值來決定圓球要離邊框多遠
        self._y_margin = 3 
        
        # 初始位置
        self._position = self._y_margin

        self.animation = QPropertyAnimation(self, b"position")
        self.animation.setEasingCurve(animation_curve)
        self.animation.setDuration(500)
        self.stateChanged.connect(self.setup_animation)

        # Parent
        self._parent = parent
        self._app_parent = app_parent
        self._top_margin = top_margin

        # TOOLTIP
        self._tooltip_text = tooltip_text
        self._tooltip = _ToolTip(
            app_parent,
            tooltip_text,
            dark_one,
            text_foreground
        )
        self._tooltip.hide()

    @Property(float)
    def position(self):
        return self._position

    @position.setter
    def position(self, pos):
        self._position = pos
        self.update()

    # START STOP ANIMATION
    def setup_animation(self, value):
        self.animation.stop()
        
        # [核心修改 3] 動畫結束點的動態計算
        # 圓球直徑 = 高度 - (上下邊距 * 2)
        circle_diameter = self.height() - (self._y_margin * 2)
        # 結束位置 X = 總寬度 - 右邊距 - 圓球直徑
        end_pos = self.width() - self._y_margin - circle_diameter

        if value:
            self.animation.setEndValue(end_pos)
        else:
            self.animation.setEndValue(self._y_margin)
            
        self.animation.start()
    
    def hitButton(self, pos: QPoint):
        return self.contentsRect().contains(pos)

    def paintEvent(self, e):

        # 如果按鈕還沒被排版(大小為0)，直接跳過不畫
        if self.width() <= 0 or self.height() <= 0:
            return

        p = QPainter(self)

        p.setRenderHint(QPainter.Antialiasing)
        p.setFont(QFont("Segoe UI", 9))

        # SET PEN
        p.setPen(Qt.NoPen)

        # [核心修改 4] 繪圖參數全部動態化
        rect = QRect(0, 0, self.width(), self.height())
        
        # 圓角半徑自動設為高度的一半 (保持膠囊形狀)
        radius = self.height() / 2
        
        # 圓球直徑
        circle_diameter = self.height() - (self._y_margin * 2)

        if not self.isChecked():
            # 背景 (未選中)
            p.setBrush(QColor(self._bg_color))
            p.drawRoundedRect(0, 0, rect.width(), self.height(), radius, radius)
            
            # 圓球
            p.setBrush(QColor(self._circle_color))
            # 參數: x, y, w, h
            p.drawEllipse(self._position, self._y_margin, circle_diameter, circle_diameter)
        else:
            # 背景 (選中)
            p.setBrush(QColor(self._active_color))
            p.drawRoundedRect(0, 0, rect.width(), self.height(), radius, radius)
            
            # 圓球
            p.setBrush(QColor(self._circle_color))
            p.drawEllipse(self._position, self._y_margin, circle_diameter, circle_diameter)

        p.end()

    # MOUSE OVER
    def enterEvent(self, event):
        # [修正] 只有當有提示文字時才顯示及計算位置，解決空字串出現空框的問題
        if self._tooltip_text:
            self.move_tooltip()
            self._tooltip.show()
        super().enterEvent(event)

    # MOUSE LEAVE
    def leaveEvent(self, event):
        if self._tooltip.isVisible():
            self._tooltip.hide()
        super().leaveEvent(event)

    def move_tooltip(self):
        if not self._parent: return
        
        # GET GLOBAL POSITION
        gp = self.mapToGlobal(QPoint(0, 0))

        # SET WIDGET TO GET POSTION
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

        # FORMAT POSITION
        pos_x = (pos.x() - (self._tooltip.width() // 2)) + (self.width() // 2)
        pos_y = pos.y() - self._top_margin

        # SET POSITION TO WIDGET
        self._tooltip.move(pos_x, pos_y)

# 這裡是 _ToolTip 類別定義，必須包含在同一個檔案中
class _ToolTip(QLabel):
    # TOOLTIP / LABEL StyleSheet
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

        # LABEL SETUP
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

        # SET DROP SHADOW
        self.shadow = QGraphicsDropShadowEffect(self)
        self.shadow.setBlurRadius(30)
        self.shadow.setXOffset(0)
        self.shadow.setYOffset(0)
        self.shadow.setColor(QColor(0, 0, 0, 80))
        self.setGraphicsEffect(self.shadow)