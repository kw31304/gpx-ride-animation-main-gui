# -*- coding: utf-8 -*-
"""
DEM (Digital Elevation Model) 免費高程圖資下載、RGB 解碼與 3D 高程網格快取管理。
使用 AWS S3 免費公開圖源 Terrarium Format (無須 API Key)。
"""

from __future__ import annotations
import math
import os
from pathlib import Path
from collections import OrderedDict
import urllib.request
import numpy as np
from PIL import Image

from gpx_renderer.core.cache_manager import CacheManager

_DEM_MEMORY_CACHE = OrderedDict()
MAX_DEM_MEM_CACHE = 64
MERCATOR_R = 6378137.0
HALF_CIRCUMFERENCE = math.pi * MERCATOR_R


def _mercator_to_tile(x: float, y: float, zoom: int):
    """EPSG:3857 世界座標 (meters) -> Tile Index (tx, ty) 與 Tile 内相對比例 (px_frac, py_frac)。"""
    n = 1 << zoom
    u = (x + HALF_CIRCUMFERENCE) / (2.0 * HALF_CIRCUMFERENCE)
    v = (HALF_CIRCUMFERENCE - y) / (2.0 * HALF_CIRCUMFERENCE)

    u = max(0.0, min(0.999999, u))
    v = max(0.0, min(0.999999, v))

    tx = int(u * n)
    ty = int(v * n)

    px_frac = (u * n) - tx
    py_frac = (v * n) - ty
    return tx, ty, px_frac, py_frac


def fetch_dem_tile(tx: int, ty: int, zoom: int) -> np.ndarray:
    """從 AWS S3 下載 Terrarium DEM PNG 並解碼為 256x256 的 float32 高程陣列 (單位：公尺)。"""
    key = (zoom, tx, ty)
    if key in _DEM_MEMORY_CACHE:
        _DEM_MEMORY_CACHE.move_to_end(key)
        return _DEM_MEMORY_CACHE[key]

    dem_dir = CacheManager.get_dem_dir()
    file_path = dem_dir / f"dem_{zoom}_{tx}_{ty}.png"

    if not file_path.exists():
        CacheManager.record_dem_miss()
        url = f"https://s3.amazonaws.com/elevation-tiles-prod/terrarium/{zoom}/{tx}/{ty}.png"
        req = urllib.request.Request(url, headers={"User-Agent": "GPX-Ride-Renderer/2.0"})
        tmp_file = dem_dir / f"dem_{zoom}_{tx}_{ty}.tmp_{os.getpid()}"
        try:
            with urllib.request.urlopen(req, timeout=5.0) as resp:
                data = resp.read()
                tmp_file.write_bytes(data)
                tmp_file.replace(file_path)
                CacheManager.touch_file(file_path)
        except Exception:
            if tmp_file.exists():
                try:
                    tmp_file.unlink(missing_ok=True)
                except Exception:
                    pass
            # 下載失敗時建立預設平坦 0m 陣列
            elev_flat = np.zeros((256, 256), dtype=np.float32)
            _DEM_MEMORY_CACHE[key] = elev_flat
            return elev_flat
    else:
        CacheManager.touch_file(file_path)
        CacheManager.record_dem_hit()

    try:
        with Image.open(file_path) as img:
            rgb = np.asarray(img.convert("RGB"), dtype=np.float32)
            # Terrarium 格式解碼算式：(R * 256 + G + B / 256) - 32768
            elev = (rgb[:, :, 0] * 256.0 + rgb[:, :, 1] + rgb[:, :, 2] / 256.0) - 32768.0
    except Exception:
        elev = np.zeros((256, 256), dtype=np.float32)

    _DEM_MEMORY_CACHE[key] = elev
    if len(_DEM_MEMORY_CACHE) > MAX_DEM_MEM_CACHE:
        _DEM_MEMORY_CACHE.popitem(last=False)

    return elev


def get_elevation_grid(west: float, south: float, east: float, north: float, rows: int = 64, cols: int = 64, zoom: int = 11) -> np.ndarray:
    """在指定 EPSG:3857 Bounding Box 內產生高解析 2D 高程矩陣 (rows x cols)，單位為公尺。"""
    x_coords = np.linspace(west, east, cols, dtype=np.float64)
    y_coords = np.linspace(north, south, rows, dtype=np.float64)  # 從北到南

    grid = np.zeros((rows, cols), dtype=np.float32)

    for r, y in enumerate(y_coords):
        for c, x in enumerate(x_coords):
            tx, ty, px_f, py_f = _mercator_to_tile(x, y, zoom)
            tile_elev = fetch_dem_tile(tx, ty, zoom)
            px = min(255, max(0, int(px_f * 256.0)))
            py = min(255, max(0, int(py_f * 256.0)))
            grid[r, c] = tile_elev[py, px]

    return grid
