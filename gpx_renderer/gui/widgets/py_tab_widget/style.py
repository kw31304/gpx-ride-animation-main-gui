# STYLE
# ///////////////////////////////////////////////////////////////
style = '''
/* /////////////////////////////////////////////////////////////////////////////////////////////////
QTabWidget::pane {{
    border: 1px solid {_bottom_line_color};
    border-radius: {_radius}px;
    background-color: {_bg_color};
}}

QTabWidget::tab-bar {{
    left: 5px; /* 讓第一個 Tab 稍微右移，不貼齊邊框 */
}}

/* Tab 標籤樣式 */
QTabBar::tab {{
    background-color: {_bg_color};
    color: {_color};
    padding: 8px 20px;
    border-top-left-radius: {_radius}px;
    border-top-right-radius: {_radius}px;
    border: 1px solid {_bottom_line_color};
    border-bottom: none;
    margin-right: 2px;
}}

/* 選取狀態 (Active Tab) */
QTabBar::tab:selected {{
    background-color: {_context_color};
    color: {_selection_color};  /* [修正] 改用變數，確保與 context_color 對比明顯 */
    border: 1px solid {_context_color};
    border-bottom: none;
}}

/* 滑鼠懸停未選取 Tab */
QTabBar::tab:hover:!selected {{
    background-color: {_header_vertical_color};
    color: {_color};
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
}}'''