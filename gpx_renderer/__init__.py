# -*- coding: utf-8 -*-
"""
GPX Ride Renderer 核心套件初始化。
"""

from gpx_renderer.utils import _force_utf8_stdio

# Run at module import time so PyInstaller multiprocessing children are fixed
# before freeze_support() diverts execution to the worker target.
_force_utf8_stdio()

__version__ = "1.4.0"


def launch_gui():
    from gpx_renderer.gui import launch_gui as _launch_gui

    return _launch_gui()


def render_job(*args, **kwargs):
    from gpx_renderer.core import render_job as _render_job

    return _render_job(*args, **kwargs)


def performance_benchmark_job(*args, **kwargs):
    from gpx_renderer.core import performance_benchmark_job as _performance_benchmark_job

    return _performance_benchmark_job(*args, **kwargs)


__all__ = [
    "__version__",
    "launch_gui",
    "render_job",
    "performance_benchmark_job",
]

