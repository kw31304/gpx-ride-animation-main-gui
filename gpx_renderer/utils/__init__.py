# -*- coding: utf-8 -*-
"""
共用工具模組套件初始化。
"""

from gpx_renderer.utils.env import (
    _force_utf8_stdio,
    _background_subprocess_kwargs,
    application_dir,
    _font_candidates,
    load_font,
    _hide_frozen_console_for_gui,
)
from gpx_renderer.utils.config_io import (
    _load_config_file,
    _self_subprocess_command,
)

__all__ = [
    "_force_utf8_stdio",
    "_background_subprocess_kwargs",
    "application_dir",
    "_font_candidates",
    "load_font",
    "_hide_frozen_console_for_gui",
    "_load_config_file",
    "_self_subprocess_command",
]
