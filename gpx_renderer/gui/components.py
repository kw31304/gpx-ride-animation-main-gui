# -*- coding: utf-8 -*-
"""
Tkinter 介面輔助元件與帶說明按鈕的複用 UI 元件。
"""

from tkinter import ttk
from gpx_renderer.gui.help import help_button


def add_check_with_help(parent, root, text, variable, key):
    box = ttk.Frame(parent)
    box.pack(side="left", padx=(0, 10))
    ttk.Checkbutton(box, text=text, variable=variable).pack(side="left")
    help_button(box, root, key).pack(side="left", padx=(4, 0))
    return box
