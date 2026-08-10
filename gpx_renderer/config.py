# -*- coding: utf-8 -*-
"""
全域渲染與畫質效能設定參數、動態設定套用與快照管理。
"""

from __future__ import annotations
import contextily as cx
from PIL import Image

# ===========================================================
# CONFIG
# ===========================================================
gpx_filename = "your_ride.gpx"
output_filename = "ride_animation.mp4"

# 畫面 / 動畫
FRAME_WIDTH = 1440
FRAME_HEIGHT = 1440
FPS = 60
VIDEO_DURATION = 180.0
ZOOM_OUT_DURATION = 2.5
END_HOLD_DURATION = 4.0

VIEW_MARGIN = 1600.0
CAMERA_SMOOTH = 0.15
END_PADDING_FRAC = 0.18

# 結尾版面
SUMMARY_PANEL_TOP_FRAC = 0.72
SUMMARY_PANEL_BOTTOM_FRAC = 0.985
END_ROUTE_SAFE_LEFT_FRAC = 0.055
END_ROUTE_SAFE_RIGHT_FRAC = 0.945
END_ROUTE_SAFE_TOP_FRAC = 0.045
END_ROUTE_SAFE_BOTTOM_FRAC = 0.685
END_ROUTE_EXTRA_PADDING = 1.04

# 地圖 / 路線
ENABLE_BASEMAP = True
TRACK_CMAP = "plasma"
MAP_STYLE = cx.providers.CartoDB.DarkMatter
OVERVIEW_MAP_ZOOM = "auto"
LOCAL_MAP_ZOOM = 17
LOCAL_CHUNK_STEP_M = 2200.0
LOCAL_CHUNK_BUFFER_M = 350.0
LOCAL_CACHE_CHUNKS = 6
MAP_CONNECTIONS = 4
MAP_USE_CACHE = True
MAP_RESAMPLE = Image.Resampling.BILINEAR
USE_OPENCV_FAST_PATH = True
TRACK_LINE_WIDTH = 5

# 多程序渲染
PARALLEL_RENDER = True
RENDER_WORKERS = 6
CHUNKS_PER_WORKER = 4
MIN_CHUNK_SECONDS = 3.0
CV2_THREADS_PER_WORKER = 1
KEEP_TEMP_SEGMENTS = False
PARALLEL_DISABLE_TILE_CACHE = True

# 元件更新頻率
HUD_UPDATE_HZ = 30

# 輸出 / 編碼
USE_GPU_IF_AVAILABLE = True
NVENC_BITRATE = "30M"
NVENC_PRESET = "p5"
CPU_CRF = 18
CPU_PRESET = "veryfast"
FFMPEG_LOGLEVEL = "error"

# 開發預覽
PREVIEW_MODE = False
PREVIEW_FPS = 30
PREVIEW_DURATION = 20.0

# GUI 自動影片時長
AUTO_DURATION_DEFAULT = True
AUTO_SECONDS_PER_100KM = 60.0
AUTO_DURATION_MIN_SECONDS = 20.0

MAP_STYLE_OPTIONS = {
    "1": ("CartoDB.DarkMatter（深色，彩色軌跡對比最強）", cx.providers.CartoDB.DarkMatter),
    "2": ("CartoDB.Voyager（全彩，接近 Relive / Google Maps 質感）", cx.providers.CartoDB.Voyager),
    "3": ("CartoDB.Positron（淺灰白，極簡）", cx.providers.CartoDB.Positron),
    "4": ("Esri.WorldImagery（衛星空拍）", cx.providers.Esri.WorldImagery),
}

# 路線媒體照片/影片
ENABLE_MEDIA = False
MEDIA_PATH = ""
MEDIA_POPUP_DURATION = 3.0
MEDIA_TIME_OFFSET_SEC = 0.0
MEDIA_THUMB_SIZE = 240

RUNTIME_CONFIG_KEYS = {
    "FRAME_WIDTH", "FRAME_HEIGHT", "FPS", "VIDEO_DURATION",
    "ZOOM_OUT_DURATION", "END_HOLD_DURATION", "VIEW_MARGIN", "CAMERA_SMOOTH",
    "END_PADDING_FRAC", "ENABLE_BASEMAP", "TRACK_CMAP", "OVERVIEW_MAP_ZOOM",
    "LOCAL_MAP_ZOOM", "LOCAL_CHUNK_STEP_M", "LOCAL_CHUNK_BUFFER_M",
    "LOCAL_CACHE_CHUNKS", "MAP_CONNECTIONS", "MAP_USE_CACHE",
    "USE_OPENCV_FAST_PATH", "TRACK_LINE_WIDTH", "PARALLEL_RENDER",
    "RENDER_WORKERS", "CHUNKS_PER_WORKER", "MIN_CHUNK_SECONDS",
    "CV2_THREADS_PER_WORKER", "KEEP_TEMP_SEGMENTS",
    "PARALLEL_DISABLE_TILE_CACHE", "HUD_UPDATE_HZ", "USE_GPU_IF_AVAILABLE",
    "NVENC_BITRATE", "NVENC_PRESET", "CPU_CRF", "CPU_PRESET",
    "FFMPEG_LOGLEVEL", "PREVIEW_MODE", "PREVIEW_FPS", "PREVIEW_DURATION",
    "ENABLE_MEDIA", "MEDIA_PATH", "MEDIA_POPUP_DURATION", "MEDIA_TIME_OFFSET_SEC", "MEDIA_THUMB_SIZE",
}

# 顏色
ORANGE = (255, 87, 34)
ORANGE_LIGHT = (255, 112, 67)
GREEN = (76, 175, 80)
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)


def _normalize_zoom(value):
    if isinstance(value, str):
        s = value.strip().lower()
        if s == "auto" or s == "":
            return "auto"
        try:
            return int(s)
        except ValueError:
            return value
    return value


def apply_render_config(config: dict | None):
    """把 GUI / config JSON 的設定套到本模組 globals。"""
    if not config:
        return
    g = globals()
    for key, value in config.items():
        if key not in RUNTIME_CONFIG_KEYS:
            continue
        if key in {"LOCAL_MAP_ZOOM", "OVERVIEW_MAP_ZOOM"}:
            value = _normalize_zoom(value)
        g[key] = value


def snapshot_render_config() -> dict:
    g = globals()
    return {key: g[key] for key in RUNTIME_CONFIG_KEYS}
