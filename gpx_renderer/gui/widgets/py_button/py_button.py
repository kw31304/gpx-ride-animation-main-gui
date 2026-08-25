# gui/widgets/py_button/py_button.py

from qt_core import *
from gui.core.functions import Functions

# PY UNIFIED BUTTON
# 整合了原有的 PyIconButton 與 PyPushButton 雙重優勢
# ///////////////////////////////////////////////////////////////
class PyButton(QPushButton):
    """
    自定義統一按鈕元件 (Py Unified Button)
    
    整合了純圖示按鈕 (IconButton) 與一般文字按鈕 (PushButton) 的功能。
    
    主要功能與特色：
    1. 支援圖文並存或單一顯示：可僅設定 `text` (純文字)、僅設定 `icon_path` (純圖示)，或同時設定。
    2. 動態圖示染色 (Dynamic Icon Tinting)：自動根據按鈕狀態 (Hover, Pressed, Active) 對 SVG 圖示進行重新染色 (SourceIn)。
    3. 狀態管理 (Active State)：提供 `set_active` 方法，可用於側邊欄選單或頁籤切換時的高亮顯示。
    4. 內建自定義 ToolTip：提供獨立且樣式一致的浮動提示框 (`_ToolTip`)，並具備防呆機制避免超出視窗邊界。
    5. 自動路徑解析：`icon_path` 可直接傳入檔名，會自動透過 `Functions.set_svg_icon` 轉換為完整資源路徑。
    """
    def __init__(
        self,
        text="",                # 按鈕文字 (若為空字串則視為純圖示按鈕)
        icon_path=None,         # 圖示路徑 (若為 None 則視為純文字按鈕)
        parent=None,
        app_parent=None,
        tooltip_text="",
        btn_id=None,
        width=None,             # 最大寬度
        height=None,            # 最小高度
        radius=8,
        bg_color="#343b48",
        bg_color_hover="#3c4454",
        bg_color_pressed="#2c313c",
        bg_color_active="#568af2",  # 整合了 context_color 作為 active 的背景
        icon_color="#c3ccdf",
        icon_color_hover="#dce1ec",
        icon_color_pressed="#edf0f5",
        icon_color_active="#f5f6f9",
        text_color="#8a95aa",
        text_color_hover="#dce1ec",
        text_color_pressed="#edf0f5",
        text_color_active="#f5f6f9",
        dark_one="#1b1e23",     # Tooltip 背景色
        text_foreground="#8a95aa", # Tooltip 文字色
        top_margin=40,          # Tooltip 頂部邊距
        is_active=False,
        font_size=12,
        font_family="Segoe UI",
        icon_size=None,
        padding_left=10,
        padding_right=5,
        text_align="center"
    ):
        super().__init__()

        # 基本設定
        if btn_id is not None:
            self.setObjectName(btn_id)
        self.setCursor(Qt.PointingHandCursor)
        if parent is not None:
            self.setParent(parent)

        # 設定尺寸
        if width is not None:
            self.setMaximumWidth(width)
        if height is not None:
            self.setFixedHeight(height)

        # 保存內部狀態變數
        self._is_hovered = False
        self._is_pressed = False
        self._is_active = is_active
        self._icon_path = self._process_icon_path(icon_path)

        # 保存顏色與樣式屬性
        self._radius = radius
        self._font_size = font_size
        self._font_family = font_family
        self._text_align = text_align
        
        self._bg_color = bg_color
        self._bg_color_hover = bg_color_hover
        self._bg_color_pressed = bg_color_pressed
        self._bg_color_active = bg_color_active

        self._icon_color = icon_color
        self._icon_color_hover = icon_color_hover
        self._icon_color_pressed = icon_color_pressed
        self._icon_color_active = icon_color_active

        self._text_color = text_color
        self._text_color_hover = text_color_hover
        self._text_color_pressed = text_color_pressed
        self._text_color_active = text_color_active

        # 智慧判定內邊距 (若無文字則預設邊距歸零，確保圖示置中)
        if text == "":
            self._padding_left = 0
            self._padding_right = 0
        else:
            self._padding_left = padding_left
            self._padding_right = padding_right

        # 初始化 ToolTip
        self._parent = parent
        self._app_parent = app_parent
        self._tooltip_text = tooltip_text
        self._top_margin = top_margin
        self._tooltip = None
        
        if tooltip_text and app_parent:
            self._tooltip = _ToolTip(
                app_parent,
                tooltip_text,
                dark_one,
                text_foreground
            )
            self._tooltip.hide()

        # 設定圖示大小
        if icon_size is not None:
            if isinstance(icon_size, QSize):
                self._icon_size = icon_size
            else:
                self._icon_size = QSize(icon_size, icon_size)
        else:
            # 防呆：如果未給定大小，以按鈕尺寸縮減 10 作為圖示大小
            iw = (width - 10) if width is not None else 24
            ih = (height - 10) if height is not None else 24
            self._icon_size = QSize(iw, ih)

        # 套用設定
        self.setText(text)
        self.setIconSize(self._icon_size)
        self.setProperty("active", self._is_active)
        
        self._apply_style()
        self._update_icon()

    # APPLY CSS STYLE
    # ///////////////////////////////////////////////////////////////
    def _apply_style(self):
        """根據目前的屬性產生並套用 StyleSheet"""
        style = f"""
        QPushButton {{
            border: none;
            padding-left: {self._padding_left}px;
            padding-right: {self._padding_right}px;
            color: {self._text_color};
            border-radius: {self._radius}px;	
            background-color: {self._bg_color};
            font-size: {self._font_size}px;
            font-family: "{self._font_family}";
            text-align: {self._text_align};
        }}
        QPushButton:hover {{
            background-color: {self._bg_color_hover};
            color: {self._text_color_hover};
        }}
        QPushButton:pressed {{	
            background-color: {self._bg_color_pressed};
            color: {self._text_color_pressed};
        }}
        QPushButton[active="true"] {{	
            background-color: {self._bg_color_active};
            color: {self._text_color_active};
        }}
        QPushButton[active="true"]:hover {{	
            background-color: {self._bg_color_active};
            color: {self._text_color_active};
        }}
        QPushButton[active="true"]:pressed {{	
            background-color: {self._bg_color_active};
            color: {self._text_color_active};
        }}
        """
        self.setStyleSheet(style)

    # PATH PROCESSING
    # ///////////////////////////////////////////////////////////////
    def _process_icon_path(self, icon_path):
        """自動將單純的檔名轉換為完整的資源系統路徑"""
        if not icon_path:
            return None
        
        # 若已經是資源路徑 (:/) 或是包含斜線的絕對/相對路徑，則不作處理
        if str(icon_path).startswith(":/") or "/" in str(icon_path) or "\\" in str(icon_path):
            return icon_path
            
        # 否則自動套用 Functions 的路徑轉換
        return Functions.set_svg_icon(icon_path)

    # DYNAMIC ICON UPDATE (TINTING)
    # ///////////////////////////////////////////////////////////////
    def _update_icon(self):
        """依據按鈕當下狀態 (Hover, Pressed, Active) 動態重新繪製圖示顏色"""
        if not self._icon_path:
            self.setIcon(QIcon())
            return

        # 1. 決定目標顏色
        if self._is_active:
            color = self._icon_color_active
        elif self._is_pressed:
            color = self._icon_color_pressed
        elif self._is_hovered:
            color = self._icon_color_hover
        else:
            color = self._icon_color

        # 2. 建立並縮放 Pixmap
        icon_pixmap = QPixmap(self._icon_path)
        if icon_pixmap.isNull():
            return
            
        icon_pixmap = icon_pixmap.scaled(
            self._icon_size.width(), 
            self._icon_size.height(), 
            Qt.KeepAspectRatio, 
            Qt.SmoothTransformation
        )

        # 3. 如果是 SVG，對其進行染色 (SourceIn)
        if self._icon_path.lower().endswith('.svg'):
            painter = QPainter(icon_pixmap)
            painter.setCompositionMode(QPainter.CompositionMode_SourceIn)
            painter.fillRect(icon_pixmap.rect(), QColor(color))
            painter.end()

        # 4. 更新按鈕圖示
        self.setIcon(QIcon(icon_pixmap))

    # PUBLIC METHODS
    # ///////////////////////////////////////////////////////////////
    def set_active(self, is_active):
        """設定元件為啟用(Active)狀態"""
        self._is_active = is_active
        self.setProperty("active", is_active)
        self.style().unpolish(self)
        self.style().polish(self) # 強制更新 CSS
        self._update_icon()

    def is_active(self):
        """回傳目前元件是否為啟用狀態"""
        return self._is_active

    def set_icon(self, icon_path):
        """動態變更圖示"""
        self._icon_path = self._process_icon_path(icon_path)
        self._update_icon()
        
    def setIconSize(self, size):
        """覆寫原生方法，使圖示尺寸改變時重新染色"""
        super().setIconSize(size)
        self._icon_size = size
        self._update_icon()

    # EVENT HANDLERS
    # ///////////////////////////////////////////////////////////////
    def enterEvent(self, event):
        self._is_hovered = True
        self._update_icon()
        if self._tooltip:
            self.move_tooltip()
            self._tooltip.show()
        super().enterEvent(event)

    def leaveEvent(self, event):
        self._is_hovered = False
        self._update_icon()
        if self._tooltip:
            self._tooltip.hide()
        super().leaveEvent(event)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._is_pressed = True
            self._update_icon()
        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._is_pressed = False
            self._update_icon()
        super().mouseReleaseEvent(event)

    # TOOLTIP LOGIC
    # ///////////////////////////////////////////////////////////////
    def move_tooltip(self):
        if not self._tooltip or not self._app_parent: 
            return
        
        # 取得全域座標
        gp = self.mapToGlobal(QPoint(0, 0))

        # 轉換為 ToolTip 父層 (app_parent) 的相對座標
        pos = self._app_parent.mapFromGlobal(gp)

        # 預設：置中於按鈕上方
        pos_x = (pos.x() - (self._tooltip.width() // 2)) + (self.width() // 2)
        pos_y = pos.y() - self._top_margin

        # 防呆機制：避免 ToolTip 超出左右邊界被截斷
        if self._app_parent:
            if pos_x < 0:
                pos_x = 5
            app_width = self._app_parent.width()
            if (pos_x + self._tooltip.width()) > app_width:
                pos_x = app_width - self._tooltip.width() - 5
        
        self._tooltip.move(pos_x, pos_y)

    def set_tooltip_text(self, text):
        """安全地動態更新 ToolTip 文字，並重新計算大小與位置"""
        self._tooltip_text = text
        if self._tooltip:
            self._tooltip.setText(text)
            self._tooltip.adjustSize()
            if self._tooltip.isVisible():
                self.move_tooltip()


# TOOLTIP CLASS
# ///////////////////////////////////////////////////////////////
class _ToolTip(QLabel):
    # TOOLTIP StyleSheet
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

        # LABEL 設定
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

        # 設定陰影效果
        self.shadow = QGraphicsDropShadowEffect(self)
        self.shadow.setBlurRadius(30)
        self.shadow.setXOffset(0)
        self.shadow.setYOffset(0)
        self.shadow.setColor(QColor(0, 0, 0, 80))
        self.setGraphicsEffect(self.shadow)