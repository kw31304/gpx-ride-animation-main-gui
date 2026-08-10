# -*- coding: utf-8 -*-
"""
Tkinter custom component helpers.
"""

from tkinter import ttk
from gpx_renderer.gui.help import help_button


def add_check_with_help(parent, root, text, variable, key):
    box = ttk.Frame(parent)
    box.pack(side="left", padx=(0, 10))
    ttk.Checkbutton(box, text=text, variable=variable).pack(side="left")
    help_button(box, root, key).pack(side="left", padx=(4, 0))
    return box
