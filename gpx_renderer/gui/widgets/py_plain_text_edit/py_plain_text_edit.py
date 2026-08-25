# py_plain_text_edit.py
# 說明: 參考 py_text_browser.py 風格的自定義 QPlainTextEdit (可編輯)
# 更新: 套用 Designer 中測試完成的「高反差 (High Contrast)」捲動軸互動樣式

# IMPORT QT CORE
# ///////////////////////////////////////////////////////////////
from qt_core import *

# STYLE
# ///////////////////////////////////////////////////////////////
style = """
QPlainTextEdit {{
    background-color: {_bg_color}; /* 編輯框背景顏色 */
    border-radius: {_radius}px;    /* 邊框圓角半徑 */
    border: 1px solid {_bottom_line_color}; /* 整體邊框顏色 */
    padding: 10px;
    selection-background-color: {_context_color}; /* 被選取文字的背景色 (反白) */
    selection-color: {_selection_color}; /* 被選取文字的字體顏色 */
    color: {_color}; /* 一般文字顏色 */
    outline: 0;
}}

/* ===============================================
   垂直捲動軸 (Vertical)
   策略：使用 border + background-clip 
   讓感應區維持 14px，但視覺區縮小
   =============================================== */
QScrollBar:vertical {{
    border: none;
    background: {_scroll_bar_bg_color}; /* 捲動軸軌道背景色 */
    width: 14px;            /* 固定寬度 14px，確保感應區夠大 */
    margin: 0px;
    border-radius: 7px;
}}

QScrollBar::handle:vertical {{
    background-color: {_scroll_bar_btn_color}; /* 捲動軸滑塊顏色 */
    min-height: 20px;
    border-radius: 7px;     
    
    /* [高反差設定 - 預設] */
    /* 6px 透明邊框 -> 視覺寬度只剩 14 - 6 - 6 = 2px (極細) */
    border: 6px solid transparent;
    
    background-clip: content-box;
}}

/* 當滑鼠「懸停在捲動軸」或「懸停在滑塊」時 */
QScrollBar:vertical:hover QScrollBar::handle:vertical,
QScrollBar::handle:vertical:hover {{
    /* [高反差設定 - 懸停] */
    /* 0px 透明邊框 -> 視覺寬度恢復 14px (全寬) */
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
    background: {_scroll_bar_bg_color}; /* 捲動軸軌道背景色 */
    height: 14px;           
    margin: 0px;
    border-radius: 7px;
}}

QScrollBar::handle:horizontal {{
    background-color: {_scroll_bar_btn_color}; /* 捲動軸滑塊顏色 */
    min-width: 20px;
    border-radius: 7px;
    
    /* [高反差設定 - 預設] */
    /* 6px 透明邊框 -> 視覺高度只剩 2px (極細) */
    border: 6px solid transparent;
    background-clip: content-box;
}}

QScrollBar:horizontal:hover QScrollBar::handle:horizontal,
QScrollBar::handle:horizontal:hover {{
    /* [高反差設定 - 懸停] */
    /* 0px 透明邊框 -> 視覺高度恢復 14px (全寬) */
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

# PY PLAIN TEXT EDIT
# ///////////////////////////////////////////////////////////////
class PyPlainTextEdit(QPlainTextEdit):
    def __init__(
        self, 
        radius = 8,                      # 邊框圓角半徑 (CSS: border-radius)
        color = "#FFF",                  # 一般文字顏色 (CSS: color)
        bg_color = "#444",               # 編輯框背景顏色 (CSS: background-color)
        selection_color = "#FFF",        # 被選取文字的字體顏色 (CSS: selection-color)
        header_horizontal_color = "#333", # [保留參數] 未使用，僅為維持與表格元件 API 一致
        header_vertical_color = "#444",   # [保留參數] 未使用
        bottom_line_color = "#555",       # 整體邊框顏色 (CSS: border)，雖變數名為 bottom 但用於四邊
        grid_line_color = "#555",         # [保留參數] 未使用
        scroll_bar_bg_color = "#FFF",     # 捲動軸軌道背景色 (CSS: QScrollBar background)
        scroll_bar_btn_color = "#3333",   # 捲動軸滑塊/拉桿顏色 (CSS: QScrollBar::handle background)
        context_color = "#00ABE8",        # 被選取文字的背景色/反白顏色 (CSS: selection-background-color)
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
            _radius = radius,                           # 注入 CSS {_radius}: 圓角
            _color = color,                             # 注入 CSS {_color}: 文字色
            _bg_color = bg_color,                       # 注入 CSS {_bg_color}: 背景色
            _header_horizontal_color = header_horizontal_color, # (無作用)
            _header_vertical_color = header_vertical_color,     # (無作用)
            _selection_color = selection_color,         # 注入 CSS {_selection_color}: 選取文字色
            _bottom_line_color = bottom_line_color,     # 注入 CSS {_bottom_line_color}: 邊框色
            _grid_line_color = grid_line_color,         # (無作用)
            _scroll_bar_bg_color = scroll_bar_bg_color, # 注入 CSS {_scroll_bar_bg_color}: 軸底色
            _scroll_bar_btn_color = scroll_bar_btn_color, # 注入 CSS {_scroll_bar_btn_color}: 滑塊色
            _context_color = context_color              # 注入 CSS {_context_color}: 反白背景色
        )
        self.setStyleSheet(style_format)