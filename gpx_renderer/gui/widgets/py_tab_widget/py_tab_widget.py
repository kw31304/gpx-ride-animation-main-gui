# gui\widgets\py_tab_widget\py_tab_widget.py
# 說明: 參考 py_table_widget.py 風格的自定義 QTabWidget
# 更新: 支援雙擊修改標籤名稱 (EditableTabBar)
# 更新: 支援動態新增、刪除標籤頁
# 更新: 增加 is_customizable 參數，預設關閉編輯與新增功能，保護全域共用元件

from qt_core import *

# STYLE
# ///////////////////////////////////////////////////////////////
style = """
QTabWidget::pane {{
    border: 1px solid {_bottom_line_color};
    border-radius: {_radius}px;
    background-color: {_bg_color};
}}

QTabWidget::tab-bar {{
    left: 5px; 
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
    color: {_selection_color};  
    border: 1px solid {_context_color};
    border-bottom: none;
}}

/* 滑鼠懸停未選取 Tab */
QTabBar::tab:hover:!selected {{
    background-color: {_header_vertical_color};
    color: {_color};
}}

/* 關閉按鈕樣式 */
QTabBar::close-button {{
    background-color: transparent;
    padding: 2px;
}}
QTabBar::close-button:hover {{
    background-color: #ff4c4c;
    border-radius: 4px;
}}

/* ===============================================
   垂直捲動軸 (Vertical)
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
    border: 6px solid transparent;
    background-clip: content-box;
}}

QScrollBar:vertical:hover QScrollBar::handle:vertical,
QScrollBar::handle:vertical:hover {{
    border: 0px solid transparent; 
}}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ border: none; background: none; }}
QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{ background: none; }}

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
    border: 6px solid transparent;
    background-clip: content-box;
}}

QScrollBar:horizontal:hover QScrollBar::handle:horizontal,
QScrollBar::handle:horizontal:hover {{
    border: 0px solid transparent;
}}

QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{ border: none; background: none; }}
QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal {{ background: none; }}
"""

# EDITABLE TAB BAR (支援雙擊改名)
# ///////////////////////////////////////////////////////////////
class EditableTabBar(QTabBar):
    tabRenamed = Signal(int, str)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.editor = QLineEdit(self)
        self.editor.setWindowFlags(Qt.FramelessWindowHint | Qt.Widget)
        self.editor.setAlignment(Qt.AlignCenter)
        self.editor.hide()
        self.editor.editingFinished.connect(self.finish_edit)
        self.editing_idx = -1
        
    def mouseDoubleClickEvent(self, event):
        idx = self.tabAt(event.pos())
        if idx >= 0:
            self.editing_idx = idx
            rect = self.tabRect(idx)
            # 預留右側 20px 的空間，避免遮擋到 'x' 關閉按鈕
            self.editor.setGeometry(rect.adjusted(2, 2, -20, -2))
            self.editor.setText(self.tabText(idx))
            self.editor.show()
            self.editor.selectAll()
            self.editor.setFocus()
            
    def finish_edit(self):
        if self.editing_idx >= 0:
            new_text = self.editor.text().strip()
            if new_text:
                self.setTabText(self.editing_idx, new_text)
                self.tabRenamed.emit(self.editing_idx, new_text)
            self.editor.hide()
            self.editing_idx = -1


# PY TAB WIDGET
# ///////////////////////////////////////////////////////////////
class PyTabWidget(QTabWidget):
    addTabRequested = Signal()
    tabRenamed = Signal(int, str)
    
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
        is_customizable = False, # 🌟 新增參數，預設為 False
        parent = None
    ):
        super().__init__(parent)
        
        self.is_customizable = is_customizable

        # 若開啟自訂功能，則掛載編輯標籤列與新增/關閉按鈕
        if self.is_customizable:
            self.editable_tab_bar = EditableTabBar(self)
            self.setTabBar(self.editable_tab_bar)
            self.editable_tab_bar.tabRenamed.connect(self.tabRenamed.emit)
            
            # 啟用標籤關閉功能 ('x' 按鈕)
            self.setTabsClosable(True)
            
            # 加入右上角「新增機台」按鈕
            self.add_btn = QPushButton(" + 新增機台 ")
            self.add_btn.setCursor(Qt.PointingHandCursor)
            self.add_btn.clicked.connect(self.addTabRequested.emit)
            self.setCornerWidget(self.add_btn, Qt.TopRightCorner)

        # SET STYLESHEET
        self.set_stylesheet(
            radius, color, bg_color, header_horizontal_color,
            header_vertical_color, selection_color, bottom_line_color,
            grid_line_color, scroll_bar_bg_color, scroll_bar_btn_color,
            context_color
        )

    def set_stylesheet(
        self, radius, color, bg_color, header_horizontal_color,
        header_vertical_color, selection_color, bottom_line_color,
        grid_line_color, scroll_bar_bg_color, scroll_bar_btn_color, context_color
    ):
        style_format = style.format(
            _radius = radius, _color = color, _bg_color = bg_color,
            _header_horizontal_color = header_horizontal_color,
            _header_vertical_color = header_vertical_color,
            _selection_color = selection_color, _bottom_line_color = bottom_line_color,
            _grid_line_color = grid_line_color, _scroll_bar_bg_color = scroll_bar_bg_color,
            _scroll_bar_btn_color = scroll_bar_btn_color, _context_color = context_color
        )
        self.setStyleSheet(style_format)
        
        # 僅當開啟自訂功能時，才設定編輯框與新增按鈕的專屬樣式
        if self.is_customizable:
            self.editable_tab_bar.editor.setStyleSheet(f"""
                QLineEdit {{
                    background-color: {bg_color};
                    color: {color};
                    border: 1px solid {context_color};
                    border-radius: 4px;
                }}
            """)
            
            self.add_btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: transparent;
                    color: {color};
                    border: 1px solid {context_color};
                    border-radius: 4px;
                    padding: 4px 10px;
                    margin: 4px 5px;
                    font-weight: bold;
                }}
                QPushButton:hover {{
                    background-color: {context_color};
                    color: {selection_color};
                }}
            """)