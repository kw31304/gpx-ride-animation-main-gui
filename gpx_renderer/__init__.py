# -*- coding: utf-8 -*-
"""
GPX Ride Renderer 核心套件初始化。
"""

from gpx_renderer.utils import _force_utf8_stdio

# Run at module import time so PyInstaller multiprocessing children are fixed
# before freeze_support() diverts execution to the worker target.
_force_utf8_stdio()

__version__ = "1.3.1"

from gpx_renderer.gui import launch_gui
from gpx_renderer.core import render_job, performance_benchmark_job

__all__ = [
    "__version__",
    "launch_gui",
    "render_job",
    "performance_benchmark_job",
]

