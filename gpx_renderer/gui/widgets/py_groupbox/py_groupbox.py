# gui/widgets/py_groupbox/py_groupbox.py

from PySide6.QtCore import *
from PySide6.QtGui import *
from PySide6.QtWidgets import *

# ---------------------------------------------------------------------
# 樣式表模板
# ---------------------------------------------------------------------
style = """
QGroupBox {{
    background-color: transparent;
    border: 1px solid {_border_color};
    border-radius: {_radius}px;
    margin-top: 10px;
    color: {_text_color};
    font-weight: bold;
}}
QGroupBox::title {{
    subcontrol-origin: margin;
    {_align_css}
    padding: 0 5px;
    background-color: {_bg_color};
    color: {_title_color};
}}
"""

class PyGroupBox(QGroupBox):
    """
    標準化自訂 QGroupBox
    參數:
        title (str): 標題
        radius (int): 圓角半徑
        border_color (str): 邊框顏色
        bg_color (str): 標題背景顏色
        text_color (str): 內容文字顏色
        title_color (str): 標題文字顏色
        title_align (Qt.AlignmentFlag): 標題對齊方式 (支援 Qt.AlignLeft, Qt.AlignHCenter, Qt.AlignRight)
        themes (dict): 傳入主題字典自動配色
    """
    def __init__(
        self,
        title="",
        radius=5,
        border_color=None, 
        bg_color=None,     
        text_color=None,   
        title_color=None,
        title_align=Qt.AlignLeft,
        themes=None,
        parent=None
    ):
        super().__init__(title, parent)
        
        # 紀錄與套用對齊方式
        self.setAlignment(title_align)
        
        # 1. 嘗試從 themes 解析顏色
        theme_border = None
        theme_bg = None
        theme_text = None
        theme_title = None

        if themes:
            if "app_color" in themes:
                color_data = themes["app_color"]
            else:
                color_data = themes
            
            # 智慧映射: 支援標準名稱與舊版 JSON 名稱
            theme_border = color_data.get("border_color") or color_data.get("gr_color") or color_data.get("context_color")
            theme_bg = color_data.get("bg_color") or color_data.get("bg_one")
            theme_text = color_data.get("text_color") or color_data.get("text_foreground")
            theme_title = color_data.get("title_color") or color_data.get("text_title")

        # 2. 決定最終顏色 (優先順序: 參數指定 > themes > 預設值)
        final_border = border_color if border_color else (theme_border if theme_border else "#568af2")
        final_bg = bg_color if bg_color else (theme_bg if theme_bg else "#2C313C")
        final_text = text_color if text_color else (theme_text if theme_text else "#FFFFFF")
        final_title = title_color if title_color else (theme_title if theme_title else "#FFFFFF")

        # 套用樣式 (不再強制傳入 alignment，確保相容舊框架)
        self.set_stylesheet(
            radius,
            final_border,
            final_bg,
            final_text,
            final_title
        )

    def set_stylesheet(
        self,
        radius,
        border_color,
        bg_color,
        text_color,
        title_color
    ):
        # 🌟 內部動態解析：向自己詢問對齊方式，不依賴外部傳參
        align_css = "subcontrol-position: top left; left: 20px;"
        alignment = self.alignment()
        
        if alignment & Qt.AlignHCenter:
            align_css = "subcontrol-position: top center;"
        elif alignment & Qt.AlignRight:
            align_css = "subcontrol-position: top right; right: 20px;"

        custom_style = style.format(
            _radius = radius,
            _border_color = border_color,
            _bg_color = bg_color,
            _text_color = text_color,
            _title_color = title_color,
            _align_css = align_css
        )
        self.setStyleSheet(custom_style)

    @staticmethod
    def set_style(target, themes):
        """
        靜態方法：掃描目標容器，找出所有 QGroupBox 並套用 JSON 主題配色
        """
        if not target: return

        if "app_color" in themes:
            color = themes["app_color"]
        else:
            color = themes 

        border_c = color.get("border_color") or color.get("gr_color") or color.get("context_color", "#FF0000")
        bg_c = color.get("bg_one") or color.get("bg_one", "#2C313C")
        text_c = color.get("text_color") or color.get("text_foreground", "#FFFFFF")
        title_c = color.get("title_color") or color.get("text_title", "#FFFFFF")
        radius_val = 5

        def get_style_for_gb(gb):
            # 🌟 在套用主題顏色前，先讀取該 GroupBox 原本被設定的對齊方式
            align_css = "subcontrol-position: top left; left: 20px;"
            alignment = gb.alignment()
            
            if alignment & Qt.AlignHCenter:
                align_css = "subcontrol-position: top center;"
            elif alignment & Qt.AlignRight:
                align_css = "subcontrol-position: top right; right: 20px;"

            return style.format(
                _radius = radius_val,
                _border_color = border_c,
                _bg_color = bg_c,
                _text_color = text_c,
                _title_color = title_c,
                _align_css = align_css
            )

        styled_gbs = set()
        def apply_style(gb):
            if gb in styled_gbs:
                return
            styled_gbs.add(gb)
            gb.setStyleSheet(get_style_for_gb(gb))

        if isinstance(target, QGroupBox):
            apply_style(target)
        
        elif isinstance(target, QWidget):
            groupboxes = target.findChildren(QGroupBox)
            for gb in groupboxes:
                apply_style(gb)
            
        else:
            if hasattr(target, "__dict__"):
                for attr_name, attr_value in target.__dict__.items():
                    if isinstance(attr_value, QWidget):
                        if isinstance(attr_value, QGroupBox):
                            apply_style(attr_value)
                        else:
                            gbs = attr_value.findChildren(QGroupBox)
                            for gb in gbs:
                                apply_style(gb)