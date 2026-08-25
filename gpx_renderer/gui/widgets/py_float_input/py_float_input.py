# gui\widgets\py_float_input\py_float_input.py

import sys
from PySide6.QtCore import Qt, QVariantAnimation, QEasingCurve, QEvent, QRect, Signal
from PySide6.QtGui import QFont, QColor, QFontMetrics
from PySide6.QtWidgets import QApplication, QWidget, QLineEdit, QLabel, QVBoxLayout

style = '''
QLineEdit {{
    background-color: {_bg_color};
    border-radius: {_radius}px;
    border: {_border_size}px solid transparent;
    padding-left: {_h_padding}px;
    padding-right: {_h_padding}px;
    selection-color: {_selection_color};
    selection-background-color: {_context_color};
    color: {_color};
    font-size: {_font_size}px;
    font-family: "Segoe UI";    
}}
QLineEdit:focus {{
    border: {_border_size}px solid {_context_color};
    background-color: {_bg_color_active};
}}
'''

class PyFloatInput(QWidget):
    """
    自定義的浮動標籤輸入框 (Floating Label Input)
    
    這是一個將 QLineEdit 與 QLabel 組合而成的外層容器 (QWidget)，
    用來實作類似 Material Design 的浮動標籤特效，並具備以下核心特色：
    
    1. 平滑過渡動畫：當取得焦點或輸入框內有文字時，標籤會平滑往上移動並縮小字體。
    2. 動態折返防閃爍：透過記錄動畫當下進度，解決在多個分頁 (如 QTabWidget) 切換時，
       因短暫焦點轉移造成的標籤瞬移或上下跳動問題。
    3. 完美半圓邊框：會根據當下元件的動態高度，自動計算並維持完美的半圓形邊框 (radius = height / 2)。
    4. 邊框遮蓋效果：標籤浮動至頂部時，會動態套用與父層相同的背景色，在視覺上完美截斷背後的邊框線條。
    5. 原生行為封裝：封裝並轉發了 `returnPressed`、`textChanged` 訊號，
       以及 `setEchoMode`、`selectAll` 等方法，使其在邏輯層可以被當作原生的 QLineEdit 直接使用。
    """
    # 定義對外拋出的訊號，使它行為更像 QLineEdit
    returnPressed = Signal()
    textChanged = Signal(str)

    def __init__(
        self, 
        text = "", # 新增預設文字參數
        label_text = "Username",
        width = int(80),
        height = int(40),
        font_size = 14,
        #radius = 8,
        border_size = 2,
        color = "#FFF",
        selection_color = "#FFF",
        bg_color = "#333",
        bg_color_active = "#222",
        context_color = "#00ABE8",
        parent_bg_color = "#1e1e1e", # 用來讓標籤遮蓋邊框時與背景融合
        idle_color = "#888888" # 未選取時標籤的顏色
    ):
        super().__init__()
        
        # 參數儲存
        self.font_size = font_size
        self.context_color = context_color
        self.parent_bg_color = parent_bg_color
        self.idle_color = idle_color

        # 狀態標記與進度追蹤
        self._is_floated = False
        self._current_progress = 0.0
        self._last_line_edit_height = -1 # 用於快取高度，避免頻繁更新樣式

        # 保存樣式參數以供動態更新使用
        self._style_params = {
            "border_size": border_size,
            "color": color,
            "selection_color": selection_color,
            "bg_color": bg_color,
            "bg_color_active": bg_color_active,
            "context_color": context_color
        }

        # 設定容器最小高度，預留頂部空間給浮動的標籤
        self.setMinimumSize(250, 60)

        # 1. 建立並套用樣式到輸入框
        self.line_edit = QLineEdit(self)
        
        # 轉發訊號
        self.line_edit.returnPressed.connect(self.returnPressed.emit)
        self.line_edit.textChanged.connect(self.textChanged.emit)

        # 這裡改用無參數的新方法，它會自動抓取當前高度來計算 radius
        self.update_line_edit_stylesheet()
        
        # 安裝事件過濾器來捕捉焦點事件
        self.line_edit.installEventFilter(self)

        # 2. 建立浮動標籤
        self.label = QLabel(label_text, self)
        # 讓滑鼠點擊可以穿透標籤，直接點到輸入框
        self.label.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents) 
        
        # 標籤字體設定 (統一使用 PixelSize 確保與 QSS font-size 同步)
        self.label_font = QFont("Segoe UI")
        self.label_font.setPixelSize(self.font_size)
        self.label.setFont(self.label_font)
        self.set_label_style(self.idle_color, is_floated=False)

        # 3. 動畫設定 (QVariantAnimation 可以讓我們同時計算數值比例，自己控制要改變什麼)
        self.anim = QVariantAnimation(self)
        self.anim.setEasingCurve(QEasingCurve.Type.OutQuad)
        self.anim.valueChanged.connect(self.update_animation)

        # 設定尺寸
        if width is not None:
            self.setFixedWidth(width)
        if height is not None:
            self.setFixedHeight(height)        

        # 4. 處理初始的預設文字
        if text:
            self.setText(text)
            # 強制將動畫瞬間完成到最後狀態，避免啟動時閃爍
            self.anim.stop()
            self._current_progress = 1.0
            self.update_animation(1.0)

    def update_line_edit_stylesheet(self):
        """動態根據高度計算 border-radius 並更新樣式"""
        current_height = self.line_edit.height()
        if current_height <= 0:
            return
            
        # [優化] 只有當高度真的改變時，才重新套用樣式，避免切換分頁時畫面閃爍
        if self._last_line_edit_height == current_height:
            return
        self._last_line_edit_height = current_height

        # 動態計算 radius (QLineEdit 高度的一半)
        radius = current_height // 2
        # 為了避免文字太靠近半圓邊緣，動態計算左右 padding
        h_padding = max(10, radius) 
        
        style_format = style.format(
            _radius = radius,
            _border_size = self._style_params["border_size"],           
            _color = self._style_params["color"],
            _selection_color = self._style_params["selection_color"],
            _bg_color = self._style_params["bg_color"],
            _bg_color_active = self._style_params["bg_color_active"],
            _context_color = self._style_params["context_color"],
            _font_size = self.font_size,
            _h_padding = h_padding
        )
        self.line_edit.setStyleSheet(style_format)

    def set_label_style(self, text_color, is_floated=False):
        """設定標籤樣式，動態決定背景色"""
        # 如果浮上去，使用 parent_bg_color 遮蓋邊框；如果在輸入框內，則背景透明
        bg_color = self.parent_bg_color if is_floated else "transparent"
        
        self.label.setStyleSheet(f"""
            QLabel {{
                color: {text_color};
                background-color: {bg_color};
                padding: 0 4px;
                border-radius: 4px;
            }}
        """)

    def resizeEvent(self, event):
        """當容器大小改變時，重新定位內部元件"""
        super().resizeEvent(event)
        
        # 讓 QLineEdit 佔滿中下方區域 (保留上方 10px 讓標籤浮動)
        padding_top = 10
        if self.height() <= padding_top:
            return
            
        self.line_edit.setGeometry(0, padding_top, self.width(), self.height() - padding_top)
        
        # 尺寸改變時，重新計算並套用半圓形圓角
        self.update_line_edit_stylesheet()
        
        # 如果目前沒有浮動且不在動畫中，將標籤動態置中於輸入框
        if not self._is_floated and self.anim.state() != QVariantAnimation.State.Running:
            idle_font = QFont("Segoe UI")
            idle_font.setPixelSize(self.font_size)
            idle_label_height = QFontMetrics(idle_font).height()
            
            label_y = padding_top + (self.line_edit.height() - idle_label_height) // 2
            self.label.move(12, label_y)
        elif self._is_floated and self.anim.state() != QVariantAnimation.State.Running:
            # 如果已經浮動，確保它停留在上方邊框處
            self.label.move(10, 0)

    def eventFilter(self, obj, event):
        """監聽輸入框的焦點狀態與文字變化"""
        if obj == self.line_edit:
            if event.type() == QEvent.Type.FocusIn:
                self.animate_label(float_up=True)
            elif event.type() == QEvent.Type.FocusOut:
                # 只有在沒有輸入任何文字時，標籤才降回去
                if not self.line_edit.text():
                    self.animate_label(float_up=False)
                else:
                    # 失去焦點但有文字：標籤保持在上方，但顏色變回灰色
                    self.set_label_style(self.idle_color, is_floated=True)
                    
        return super().eventFilter(obj, event)

    def animate_label(self, float_up: bool):
        """啟動平滑動畫 (支援動態折返，解決閃爍與跳動問題)"""
        self.anim.stop()
        
        if float_up:
            self._is_floated = True
            self.set_label_style(self.context_color, is_floated=True) # 獲得焦點時變成主題色(藍色)且有背景
            # [修正] 從「當前進度」開始動畫，防止焦點閃爍造成的瞬移
            self.anim.setStartValue(self._current_progress)
            self.anim.setEndValue(1.0)
        else:
            self._is_floated = False
            self.set_label_style(self.idle_color, is_floated=False) # 失去焦點變回灰色且背景透明
            self.anim.setStartValue(self._current_progress)
            self.anim.setEndValue(0.0)
            
        # 根據剩餘距離動態計算動畫時間，保持速度一致
        distance = abs(self.anim.endValue() - self.anim.startValue())
        duration = int(250 * distance)
        self.anim.setDuration(max(10, duration)) # 防呆，確保時間大於 10ms
        
        self.anim.start()

    def update_animation(self, progress):
        """根據動畫進度 (0.0 ~ 1.0) 同時更新 Y座標 與 字體大小"""
        self._current_progress = progress # 記錄當前進度
        padding_top = 10
        
        # 取得未浮動時的字體精確高度，用於計算完美置中
        idle_font = QFont("Segoe UI")
        idle_font.setPixelSize(self.font_size)
        idle_label_height = QFontMetrics(idle_font).height()
        
        # 定義起始與結束的數值
        idle_y = padding_top + (self.line_edit.height() - idle_label_height) // 2 # 原本置中的 Y
        float_y = 0 # 浮動到頂部的 Y
        
        idle_font_size = self.font_size
        float_font_size = max(8, self.font_size - 3) # 縮小字體 (例如 12 -> 9)
        
        # 內插計算當前進度的數值
        current_y = idle_y + (float_y - idle_y) * progress
        current_font_size = idle_font_size + (float_font_size - idle_font_size) * progress
        
        # 套用 Y 座標
        self.label.move(12, int(current_y))
        
        # 套用字體大小 (使用 PixelSize 確保單位一致)
        self.label_font.setPixelSize(int(current_font_size))
        self.label.setFont(self.label_font)
        self.label.adjustSize() # 根據新字體重新計算標籤寬度

    def setText(self, text):
        """設定輸入框文字並更新標籤狀態"""
        self.line_edit.setText(text)
        if text:
            if not self._is_floated:
                self.animate_label(float_up=True)
            if not self.line_edit.hasFocus():
                self.set_label_style(self.idle_color, is_floated=True)
            else:
                self.set_label_style(self.context_color, is_floated=True)
        else:
            if not self.line_edit.hasFocus():
                if self._is_floated:
                    self.animate_label(float_up=False)

    def text(self):
        """取得輸入框文字"""
        return self.line_edit.text()

    def clear(self):
        """清除輸入框文字"""
        self.setText("")

    def setEchoMode(self, mode):
        """封裝內部 QLineEdit 的 setEchoMode"""
        self.line_edit.setEchoMode(mode)

    def echoMode(self):
        """封裝內部 QLineEdit 的 echoMode"""
        return self.line_edit.echoMode()

    def selectAll(self):
        """封裝內部 QLineEdit 的 selectAll"""
        self.line_edit.selectAll()
        
    def setFocus(self):
        """確保焦點正確轉移給內部的輸入框"""
        self.line_edit.setFocus()

    def setReadOnly(self, read_only: bool):
        """封裝內部 QLineEdit 的 setReadOnly"""
        self.line_edit.setReadOnly(read_only)

    def isReadOnly(self) -> bool:
        """封裝內部 QLineEdit 的 isReadOnly"""
        return self.line_edit.isReadOnly()

# 測試用視窗
if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    # 建立主視窗 (模擬深色主題)
    main_window = QWidget()
    main_window.setFixedSize(400, 300)
    bg_color = "#1e1e1e"
    main_window.setStyleSheet(f"background-color: {bg_color};")
    
    layout = QVBoxLayout(main_window)
    layout.setSpacing(20)
    layout.setContentsMargins(50, 50, 50, 50)
    
    # 測試1：無預設文字
    input1 = PyFloatInput(label_text="Username", parent_bg_color=bg_color, width=200, height=30)
    
    # 測試2：有預設文字 (標籤會一開始就浮上去)
    input2 = PyFloatInput(label_text="連接埠", text="21", parent_bg_color=bg_color, width=200, height=40, font_size=16)
    
    # 測試3：密碼輸入
    input3 = PyFloatInput(label_text="Password", parent_bg_color=bg_color, width=200, height=50)
    input3.line_edit.setEchoMode(QLineEdit.EchoMode.Password)
    
    layout.addWidget(input1)
    layout.addWidget(input2)
    layout.addWidget(input3)
    layout.addStretch()
    
    main_window.show()
    sys.exit(app.exec())