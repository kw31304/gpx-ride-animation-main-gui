# STYLE
# ///////////////////////////////////////////////////////////////
style = '''
/* /////////////////////////////////////////////////////////////////////////////////////////////////
QTableWidget {{
    background-color: {_bg_color};
    border-radius: {_radius}px;
    border: 1px solid {_bottom_line_color};
    padding: 5px;
    selection-background-color: {_context_color};
    color: {_color};
    outline: 0;
}}

/* 設定 Item 高度與 Padding */
QTableWidget::item {{
    padding: 3px; /* [修改] 增加 padding 以增加列高 (原為 5px) */
    border: 0px;
    background-color: transparent; 
}}

/* 選取項目的樣式 */
QTableWidget::item:selected {{
    background-color: {_context_color};
    color: #FFFFFF;
    border-radius: 5px;
}}

/* 滑鼠懸停樣式 */
QTableWidget::item:hover {{
    background-color: {_header_vertical_color};
    border-radius: 5px;
    color: {_color};
}}

/* 確保 hover 且 selected 時的樣式優先權 */
QTableWidget::item:selected:hover {{
    background-color: {_context_color};
    color: #FFFFFF;
}}

/* 失去焦點時的選取樣式 */
QTableWidget::item:selected:!active {{
    background-color: {_header_horizontal_color};
    color: {_color};
}}

/* 表頭樣式 */
QHeaderView::section {{
    background-color: {_header_horizontal_color};
    color: {_color};
    border: none;
    border-bottom: 1px solid {_bottom_line_color};
    border-right: 1px solid {_bottom_line_color};
    padding: 3px; /* [修改] 增加 padding 以增加標題高度 (原為 4px) */
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
'''