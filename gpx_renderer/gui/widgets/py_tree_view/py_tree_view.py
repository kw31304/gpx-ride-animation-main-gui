# gui\widgets\py_tree_view\py_tree_view.py
# 說明: 
# 1. 參照 py_table_widget 建立的自定義 QTreeView
# 2. 調整 Item 的 padding 增加列高
# 3. 調整 Header 的 padding 增加標題高度
# 4. 套用高反差捲動軸樣式

# IMPORT QT CORE
# ///////////////////////////////////////////////////////////////
from qt_core import *

# STYLE
# ///////////////////////////////////////////////////////////////
style = """
QTreeView {{
    background-color: {_bg_color};
    border-radius: {_radius}px;
    border: 1px solid {_bottom_line_color};
    padding: 5px;
    selection-background-color: {_context_color};
    color: {_color};
    outline: 0;
    show-decoration-selected: 1; /* 讓選取範圍包含展開/折疊的箭頭區域 */
}}

/* 設定 Item 高度與 Padding */
QTreeView::item {{
    padding: 3px; 
    border: 0px;
    background-color: transparent; 
}}

/* 選取項目的樣式 */
QTreeView::item:selected {{
    background-color: {_context_color};
    color: #FFFFFF;
    border-radius: 5px;
}}

/* 滑鼠懸停樣式 */
QTreeView::item:hover {{
    background-color: {_header_vertical_color};
    border-radius: 5px;
    color: {_color};
}}

/* 確保 hover 且 selected 時的樣式優先權 */
QTreeView::item:selected:hover {{
    background-color: {_context_color};
    color: #FFFFFF;
}}

/* 失去焦點時的選取樣式 */
QTreeView::item:selected:!active {{
    background-color: {_header_horizontal_color};
    color: {_color};
}}

/* 針對 TreeView 展開/折疊區域 (branch) 的背景色同步處理 */
QTreeView::branch:selected {{
    background-color: {_context_color};
}}
QTreeView::branch:hover {{
    background-color: {_header_vertical_color};
}}
QTreeView::branch:selected:hover {{
    background-color: {_context_color};
}}
QTreeView::branch:selected:!active {{
    background-color: {_header_horizontal_color};
}}

/* 表頭樣式 */
QHeaderView::section {{
    background-color: {_header_horizontal_color};
    color: {_color};
    border: none;
    border-bottom: 1px solid {_bottom_line_color};
    border-right: 1px solid {_bottom_line_color};
    padding: 3px; 
    font-weight: bold;
}}

QHeaderView::section:horizontal {{
    border-top: 1px solid {_bg_color};
}}

QHeaderView::section:vertical {{
    border-left: 1px solid {_bg_color};
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

# PY TREE VIEW
# ///////////////////////////////////////////////////////////////
class PyTreeView(QTreeView):
    def __init__(
        self, 
        radius = 8,
        color = "#FFF",
        bg_color = "#444",
        selection_color = "#FFF",
        header_horizontal_color = "#333",
        header_vertical_color = "#444",
        bottom_line_color = "#555",
        grid_line_color = "#555",
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