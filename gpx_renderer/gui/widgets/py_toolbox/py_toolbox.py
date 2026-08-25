# gui\widgets\py_toolbox\py_toolbox.py
# 說明: 
# 1. 參考 py_table_widget 建立自定義 QToolBox
# 2. 設定 Tab (頁籤) 的基礎、懸停(hover)與選取(selected)樣式
# 3. 套用高反差捲動軸樣式以維持全域視覺一致性

# IMPORT QT CORE
# ///////////////////////////////////////////////////////////////
from qt_core import *

# STYLE
# ///////////////////////////////////////////////////////////////
style = """
/* ToolBox 主體背景與邊框 */
QToolBox {{
    background-color: {_bg_color};
    border-radius: {_radius}px;
    border: 1px solid {_bottom_line_color};
    color: {_color};
}}

/* 頁籤 (Tab) 基本樣式 */
QToolBox::tab {{
    background-color: {_tab_color};
    color: {_color};
    border-radius: 5px;
    padding-left: 10px;
    font-weight: bold;
    border: 1px solid {_bottom_line_color};
}}

/* 滑鼠懸停頁籤樣式 */
QToolBox::tab:hover {{
    background-color: {_tab_hover_color};
    color: {_color};
}}

/* 被選取 (展開) 的頁籤樣式 */
QToolBox::tab:selected {{
    background-color: {_context_color};
    color: #FFFFFF;
    border: none;
}}

/* Toolbox 內部頁面的預設背景 (去除原生邊框) */
QToolBox > QWidget > QWidget {{
    background-color: transparent;
}}

/* ===============================================
   垂直捲動軸 (Vertical)
   策略：使用 border + background-clip 
   讓感應區維持 14px，但視覺區縮小
   =============================================== */
QScrollBar:vertical {{
    border: none;
    background: {_scroll_bar_bg_color};
    width: 14px;
    margin: 0px 0 0px 0;
    border-radius: 7px;
}}

QScrollBar::handle:vertical {{
    background-color: {_scroll_bar_btn_color};
    min-height: 25px;
    border-radius: 7px;
    
    /* [高反差設定 - 預設] 6px 透明邊框 -> 視覺寬度只剩 2px */
    border: 6px solid transparent;
    background-clip: content-box;
}}

/* 當滑鼠「懸停在捲動軸」或「懸停在滑塊」時 */
QScrollBar:vertical:hover QScrollBar::handle:vertical,
QScrollBar::handle:vertical:hover {{
    /* [高反差設定 - 懸停] 0px 透明邊框 -> 視覺寬度恢復 14px */
    border: 0px solid transparent; 
}}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    border: none;
    background: none;
}}
QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{
    background: none;
}}

/* ===============================================
   水平捲動軸 (Horizontal)
   =============================================== */
QScrollBar:horizontal {{
    border: none;
    background: {_scroll_bar_bg_color};
    height: 14px;
    margin: 0px 0 0px 0;
    border-radius: 7px;
}}

QScrollBar::handle:horizontal {{
    background-color: {_scroll_bar_btn_color};
    min-width: 25px;
    border-radius: 7px;
    
    /* [高反差設定 - 預設] 6px 透明邊框 -> 視覺高度只剩 2px */
    border: 6px solid transparent;
    background-clip: content-box;
}}

QScrollBar:horizontal:hover QScrollBar::handle:horizontal,
QScrollBar::handle:horizontal:hover {{
    /* [高反差設定 - 懸停] 0px 透明邊框 -> 視覺高度恢復 14px */
    border: 0px solid transparent;
}}

QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
    border: none;
    background: none;
}}
QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal {{
    background: none;
}}
"""

# PY TOOL BOX WIDGET
# ///////////////////////////////////////////////////////////////
class PyToolBox(QToolBox):
    def __init__(
        self, 
        radius = 8,
        color = "#FFF",
        bg_color = "#444",
        tab_color = "#333",          # 對應原先的 header_horizontal_color
        tab_hover_color = "#444",    # 對應原先的 header_vertical_color
        bottom_line_color = "#555",
        scroll_bar_bg_color = "#FFF",
        scroll_bar_btn_color = "#3333",
        context_color = "#00ABE8",
        parent = None 
    ):
        super().__init__(parent) 

        # PARAMETERS
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        # SET STYLESHEET
        self.set_stylesheet(
            radius,
            color,
            bg_color,
            tab_color,
            tab_hover_color,
            bottom_line_color,
            scroll_bar_bg_color,
            scroll_bar_btn_color,
            context_color
        )

    # SET STYLESHEET
    def set_stylesheet(
        self,
        radius,
        color,
        bg_color,
        tab_color,
        tab_hover_color,
        bottom_line_color,
        scroll_bar_bg_color,
        scroll_bar_btn_color,
        context_color
    ):
        # APPLY STYLESHEET
        style_format = style.format(
            _radius = radius,          
            _color = color,
            _bg_color = bg_color,
            _tab_color = tab_color,
            _tab_hover_color = tab_hover_color,
            _bottom_line_color = bottom_line_color,
            _scroll_bar_bg_color = scroll_bar_bg_color,
            _scroll_bar_btn_color = scroll_bar_btn_color,
            _context_color = context_color
        )
        self.setStyleSheet(style_format)