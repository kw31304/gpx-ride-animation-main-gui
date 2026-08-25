# py_text_browser.py
# 說明: 參考 py_table_widget.py 風格的自定義 QTextBrowser
# 更新: 套用與 py_plain_text_edit 相同的高反差捲動軸樣式

# IMPORT QT CORE
# ///////////////////////////////////////////////////////////////
from qt_core import *

# STYLE
# ///////////////////////////////////////////////////////////////
style = """
QTextBrowser {{
    background-color: {_bg_color};
    border-radius: {_radius}px;
    border: 1px solid {_bottom_line_color};
    padding: 10px;
    selection-background-color: {_context_color};
    selection-color: {_selection_color};
    color: {_color};
    outline: 0;
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
    min-height: 20px;
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
    min-width: 20px;
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

# PY TEXT BROWSER
# ///////////////////////////////////////////////////////////////
class PyTextBrowser(QTextBrowser):
    def __init__(
        self, 
        radius = 8,
        color = "#FFF",
        bg_color = "#444",
        selection_color = "#FFF",
        header_horizontal_color = "#333", # 保留參數以維持介面呼叫一致性
        header_vertical_color = "#444",   # 保留參數
        bottom_line_color = "#555",
        grid_line_color = "#555",         # 保留參數
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
            header_horizontal_color,
            header_vertical_color,
            selection_color,
            bottom_line_color,
            grid_line_color,
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
        header_horizontal_color,
        header_vertical_color,
        selection_color,
        bottom_line_color,
        grid_line_color,
        scroll_bar_bg_color,
        scroll_bar_btn_color,
        context_color
    ):
        # APPLY STYLESHEET
        style_format = style.format(
            _radius = radius,          
            _color = color,
            _bg_color = bg_color,
            _header_horizontal_color = header_horizontal_color,
            _header_vertical_color = header_vertical_color,
            _selection_color = selection_color,
            _bottom_line_color = bottom_line_color,
            _grid_line_color = grid_line_color,
            _scroll_bar_bg_color = scroll_bar_bg_color,
            _scroll_bar_btn_color = scroll_bar_btn_color,
            _context_color = context_color
        )
        self.setStyleSheet(style_format)