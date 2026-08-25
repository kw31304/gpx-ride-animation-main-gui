# STYLE
# ///////////////////////////////////////////////////////////////
style = '''
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
'''
