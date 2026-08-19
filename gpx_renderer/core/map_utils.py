# -*- coding: utf-8 -*-
"""
地圖 Tile 下載 (contextily)、Raster 地圖處理、Overview 全程圖組裝與區域底圖增量快取 (LocalBasemapCache)。
"""

from __future__ import annotations
import sys
import json
from dataclasses import dataclass
from collections import OrderedDict
import numpy as np
import contextily as cx
from PIL import Image, ImageDraw

try:
    import cv2
    HAVE_CV2 = True
except Exception:
    cv2 = None
    HAVE_CV2 = False

from gpx_renderer import config
from gpx_renderer.core.data import RideData, compute_end_route_view
from gpx_renderer.core.cache_manager import CacheManager


@dataclass
class RasterMap:
    image: Image.Image
    west: float
    east: float
    south: float
    north: float
    np_image: np.ndarray | None = None
    dem_grid: np.ndarray | None = None

    def __post_init__(self):
        if self.image.mode != "RGB":
            self.image = self.image.convert("RGB")
        max_dim = max(self.image.width, self.image.height)
        if max_dim > 4096:
            scale = 4096.0 / float(max_dim)
            new_w = max(1, int(round(self.image.width * scale)))
            new_h = max(1, int(round(self.image.height * scale)))
            self.image = self.image.resize((new_w, new_h), Image.Resampling.BILINEAR)
        if self.np_image is None:
            self.np_image = np.asarray(self.image, dtype=np.uint8).copy()

    @property
    def width(self) -> int:
        return self.image.width

    @property
    def height(self) -> int:
        return self.image.height


def choose_map_style():
    print("\n請選擇地圖底圖風格：")
    for key, (label, _) in config.MAP_STYLE_OPTIONS.items():
        print(f"  {key}. {label}")

    choice = input("輸入編號 (直接 Enter 預設 1): ").strip() or "1"
    if choice not in config.MAP_STYLE_OPTIONS:
        print(f"輸入無效「{choice}」，改用預設 1。")
        choice = "1"

    label, provider = config.MAP_STYLE_OPTIONS[choice]
    print(f"已選擇：{label}\n")
    return choice, provider


def _fetch_raster(west: float, south: float, east: float, north: float, map_style, zoom, use_cache: bool | None = None) -> RasterMap:
    """下載指定 EPSG:3857 bbox 的 raster。帶有自動降階 (Zoom Fallback) 與指數退避重試保護機制。"""
    CacheManager.init_cache_system()
    if use_cache is None:
        use_cache = config.MAP_USE_CACHE
    if getattr(sys, "frozen", False) and use_cache and config.MAP_CONNECTIONS > 1:
        use_cache = False

    target_zooms = []
    if isinstance(zoom, int):
        target_zooms.append(zoom)
        if zoom > 1:
            target_zooms.append(zoom - 1)
        if zoom > 2:
            target_zooms.append(zoom - 2)
    else:
        target_zooms.append(zoom)

    last_exc = None

    for z_try in target_zooms:
        max_attempts = 3 if z_try == target_zooms[0] else 2
        for attempt in range(1, max_attempts + 1):
            try:
                img_np, extent = cx.bounds2img(
                    west,
                    south,
                    east,
                    north,
                    zoom=z_try,
                    source=map_style,
                    ll=False,
                    wait=1,
                    max_retries=3,
                    n_connections=config.MAP_CONNECTIONS,
                    use_cache=False,  # 停用 contextily joblib，由 CacheManager 自訂原子 PNG 攔截器安全接管
                )
                left, right, bottom, top = map(float, extent)
                image = Image.fromarray(np.asarray(img_np)).convert("RGB")
                return RasterMap(image, left, right, bottom, top)
            except Exception as exc:
                last_exc = exc
                if attempt < max_attempts:
                    import time
                    time.sleep(0.8 * (2 ** (attempt - 1)))

    if last_exc is not None:
        raise last_exc
    raise RuntimeError("底圖下載失敗。")


def build_overview_raster_map(data: RideData, map_style) -> RasterMap:
    """只供結尾 zoom-out 使用的全程低/中解析總覽圖。"""
    end_view_x, end_view_y, end_margin = compute_end_route_view(data)
    aspect = config.FRAME_WIDTH / float(config.FRAME_HEIGHT)
    import math
    diag_factor = math.sqrt(1.0 + aspect * aspect) if getattr(config, "CAMERA_MODE", "North-Up") == "Heading-Up" else 1.0
    if aspect >= 1.0:
        end_margin_x, end_margin_y = end_margin * aspect * diag_factor, end_margin * diag_factor
        view_margin_x, view_margin_y = config.VIEW_MARGIN * aspect * diag_factor, config.VIEW_MARGIN * diag_factor
    else:
        end_margin_x, end_margin_y = end_margin * diag_factor, (end_margin / aspect) * diag_factor
        view_margin_x, view_margin_y = config.VIEW_MARGIN * diag_factor, (config.VIEW_MARGIN / aspect) * diag_factor

    west = min(float(data.xs.min() - view_margin_x), end_view_x - end_margin_x)
    east = max(float(data.xs.max() + view_margin_x), end_view_x + end_margin_x)
    south = min(float(data.ys.min() - view_margin_y), end_view_y - end_margin_y)
    north = max(float(data.ys.max() + view_margin_y), end_view_y + end_margin_y)

    if not config.ENABLE_BASEMAP:
        image = Image.new("RGB", (2048, 2048), (17, 17, 17))
        return RasterMap(image, west, east, south, north)

    print("[MAP] 下載 / 組裝全程 overview 底圖（只做一次，供結尾 zoom-out）...")
    try:
        rm = _fetch_raster(west, south, east, north, map_style, config.OVERVIEW_MAP_ZOOM)
        print(f"[OK] Overview raster：{rm.width}x{rm.height} px")
        return rm
    except Exception as exc:
        print(f"[WARN] Overview 底圖下載失敗，改純色背景：{exc}")
        image = Image.new("RGB", (2048, 2048), (17, 17, 17))
        return RasterMap(image, west, east, south, north)


@dataclass
class LocalChunkState:
    raster: RasterMap
    track_upto: int = 0  # 已燒入的 segment 數量；segment id 範圍 [0, track_upto)


def _get_max_view_margins():
    aspect = config.FRAME_WIDTH / float(config.FRAME_HEIGHT)
    margin = float(config.VIEW_MARGIN)
    if getattr(config, "CAMERA_MODE", "North-Up") == "3D-Terrain":
        import math
        margin = margin * 1.35 * math.sqrt(1.0 + aspect * aspect)
    elif getattr(config, "CAMERA_MODE", "North-Up") == "Heading-Up":
        import math
        margin = margin * math.sqrt(1.0 + aspect * aspect)
    if aspect >= 1.0:
        return margin * aspect, margin
    return margin, margin / aspect


def prefetch_route_basemap_chunks(data: RideData, map_style, zoom=None, callback=None) -> int:
    """在多程序渲染前，預先掃描全路線所需之所有 LocalBasemapCache 網格，並一次性下載與快取所有切片。"""
    if not config.ENABLE_BASEMAP:
        return 0

    if zoom is None:
        zoom = config.LOCAL_MAP_ZOOM

    margin_x, margin_y = _get_max_view_margins()
    max_margin = max(margin_x, margin_y)
    step = max(float(config.LOCAL_CHUNK_STEP_M), max_margin * 1.25)

    # 收集整條 GPX 路線上所有經過的網格 (gx, gy)
    gxs = np.rint(data.xs / step).astype(np.int64)
    gys = np.rint(data.ys / step).astype(np.int64)

    unique_keys = []
    seen = set()
    for gx, gy in zip(gxs, gys):
        k = (int(gx), int(gy))
        if k not in seen:
            seen.add(k)
            unique_keys.append(k)

    total_chunks = len(unique_keys)
    if total_chunks == 0:
        return 0

    print(f"\n[PREFETCH] 掃描到路線涵蓋 {total_chunks} 個局部底圖區塊 (Zoom {zoom})，開始預熱快取...")

    # 輸出初始 0% 進度 JSON
    initial_payload = {
        "stage": "prefetch",
        "status": f"預先下載底圖中 (0/{total_chunks})",
        "pct": 0.0,
        "chunks_done": 0,
        "chunks_total": total_chunks,
        "rendered": 0,
        "total": total_chunks,
        "fps": None,
        "eta_seconds": None,
        "workers": [
            {
                "id": w + 1,
                "status": "等待底圖預熱",
                "pct": 0.0,
            }
            for w in range(min(6, max(1, int(getattr(config, "RENDER_WORKERS", 1)))))
        ],
    }
    print("\n[PROGRESS_JSON]" + json.dumps(initial_payload, ensure_ascii=False), flush=True)

    half_x = margin_x + step * 0.5 + float(config.LOCAL_CHUNK_BUFFER_M)
    half_y = margin_y + step * 0.5 + float(config.LOCAL_CHUNK_BUFFER_M)
    is_3d = (getattr(config, "CAMERA_MODE", "North-Up") == "3D-Terrain")

    for i, (gx, gy) in enumerate(unique_keys, 1):
        cx0 = gx * step
        cy0 = gy * step
        west, east = cx0 - half_x, cx0 + half_x
        south, north = cy0 - half_y, cy0 + half_y

        try:
            # 啟用 cache=True 下載並快取到磁碟
            _ = _fetch_raster(west, south, east, north, map_style, zoom, use_cache=True)
            if is_3d:
                try:
                    from gpx_renderer.core.dem_utils import get_elevation_grid
                    _ = get_elevation_grid(west, south, east, north, rows=24, cols=24)
                except Exception:
                    pass
        except Exception as exc:
            print(f"[WARN] 預抓底圖區塊 ({gx}, {gy}) 失敗：{exc}")

        pct = (i / float(total_chunks)) * 100.0
        if callback:
            callback(i, total_chunks, f"預熱底圖 ({i}/{total_chunks})")
        else:
            progress_payload = {
                "stage": "prefetch",
                "status": f"預先下載底圖中 ({i}/{total_chunks})",
                "pct": round(pct, 1),
                "chunks_done": i,
                "chunks_total": total_chunks,
                "rendered": i,
                "total": total_chunks,
                "fps": None,
                "eta_seconds": None,
                "workers": [
                    {
                        "id": w + 1,
                        "status": "預熱底圖中",
                        "pct": round(pct, 1),
                    }
                    for w in range(min(6, max(1, int(getattr(config, "RENDER_WORKERS", 1)))))
                ],
            }
            print("\n[PROGRESS_JSON]" + json.dumps(progress_payload, ensure_ascii=False), flush=True)

        if i % max(1, total_chunks // 10) == 0 or i == total_chunks:
            print(f"   預熱進度：{i}/{total_chunks} ({pct:.1f}%)")

    print(f"[OK] 路線 {total_chunks} 個底圖區塊已全部預先快取完成！所有 Worker 均可 100% 本機離線讀取。\n")
    CacheManager.prune_if_exceeds()
    return total_chunks


class LocalBasemapCache:
    """主動畫局部高解析底圖 + 已完成軌跡的增量 raster cache。"""
    def __init__(
        self,
        map_style,
        seg_x0: np.ndarray,
        seg_x1: np.ndarray,
        seg_y0: np.ndarray,
        seg_y1: np.ndarray,
        seg_min_x: np.ndarray,
        seg_max_x: np.ndarray,
        seg_min_y: np.ndarray,
        seg_max_y: np.ndarray,
        track_colors,
        use_cv2: bool,
        tile_cache_enabled: bool = True,
    ):
        self.map_style = map_style
        self.tile_cache_enabled = bool(tile_cache_enabled)
        self.cache = OrderedDict()
        self.seg_x0 = seg_x0
        self.seg_x1 = seg_x1
        self.seg_y0 = seg_y0
        self.seg_y1 = seg_y1
        self.seg_min_x = seg_min_x
        self.seg_max_x = seg_max_x
        self.seg_min_y = seg_min_y
        self.seg_max_y = seg_max_y
        self.track_colors = track_colors
        self.use_cv2 = bool(use_cv2 and HAVE_CV2)

    def _key(self, view_x: float, view_y: float):
        margin_x, margin_y = _get_max_view_margins()
        max_margin = max(margin_x, margin_y)
        step = max(float(config.LOCAL_CHUNK_STEP_M), max_margin * 1.25)
        gx = int(round(view_x / step))
        gy = int(round(view_y / step))
        return gx, gy

    def _build_chunk(self, key) -> LocalChunkState:
        gx, gy = key
        margin_x, margin_y = _get_max_view_margins()
        max_margin = max(margin_x, margin_y)
        step = max(float(config.LOCAL_CHUNK_STEP_M), max_margin * 1.25)
        cx0 = gx * step
        cy0 = gy * step

        half_x = margin_x + step * 0.5 + float(config.LOCAL_CHUNK_BUFFER_M)
        half_y = margin_y + step * 0.5 + float(config.LOCAL_CHUNK_BUFFER_M)
        west, east = cx0 - half_x, cx0 + half_x
        south, north = cy0 - half_y, cy0 + half_y

        if not config.ENABLE_BASEMAP:
            image = Image.new("RGB", (1024, 1024), (17, 17, 17))
            return LocalChunkState(RasterMap(image, west, east, south, north))

        try:
            rm = _fetch_raster(west, south, east, north, self.map_style, config.LOCAL_MAP_ZOOM, use_cache=self.tile_cache_enabled)
        except Exception as exc:
            print(f"\n[WARN] 局部底圖 chunk {key} 下載失敗，使用純色背景：{exc}")
            image = Image.new("RGB", (1024, 1024), (17, 17, 17))
            rm = RasterMap(image, west, east, south, north)

        if getattr(config, "CAMERA_MODE", "North-Up") == "3D-Terrain":
            try:
                from gpx_renderer.core.dem_utils import get_elevation_grid
                rm.dem_grid = get_elevation_grid(west, south, east, north, rows=24, cols=24)
            except Exception:
                pass

        return LocalChunkState(rm)

    @staticmethod
    def _world_to_raster_px(rm: RasterMap, xs: np.ndarray, ys: np.ndarray):
        px = (xs - rm.west) / max(rm.east - rm.west, 1e-9) * (rm.width - 1)
        py = (rm.north - ys) / max(rm.north - rm.south, 1e-9) * (rm.height - 1)
        return np.rint(px).astype(np.int32), np.rint(py).astype(np.int32)

    def _source_track_width(self, rm: RasterMap) -> int:
        margin_x, _ = _get_max_view_margins()
        src_ppm_x = (rm.width - 1) / max(rm.east - rm.west, 1e-9)
        out_ppm_x = config.FRAME_WIDTH / max(2.0 * margin_x, 1e-9)
        ui_scale = min(config.FRAME_WIDTH, config.FRAME_HEIGHT) / 1000.0
        effective_line_w = max(2.0, float(config.TRACK_LINE_WIDTH) * ui_scale)
        width = effective_line_w * src_ppm_x / max(out_ppm_x, 1e-9)
        return max(2, int(round(width)))

    def _ensure_track(self, state: LocalChunkState, idx: int):
        rm = state.raster
        seg_count = min(max(int(idx), 0), len(self.seg_x0))
        start = min(max(int(state.track_upto), 0), seg_count)
        if seg_count <= start:
            return

        sl = slice(start, seg_count)
        mask = (
            (self.seg_max_x[sl] >= rm.west)
            & (self.seg_min_x[sl] <= rm.east)
            & (self.seg_max_y[sl] >= rm.south)
            & (self.seg_min_y[sl] <= rm.north)
        )
        local_ids = np.flatnonzero(mask)
        if local_ids.size:
            ids = local_ids + start
            width = self._source_track_width(rm)

            if self.use_cv2:
                arr = rm.np_image
                # 判定是否為單一純色 (如 Strava 橘 / 螢光綠等)，若為純色則組合成 polyline 批次繪製
                first_color = self.track_colors[int(ids[0])]
                is_single_color = True
                if len(ids) > 1:
                    # 抽樣快速比對顏色
                    for seg_id in ids[1:]:
                        if self.track_colors[int(seg_id)] != first_color:
                            is_single_color = False
                            break

                if is_single_color:
                    # 連續線段分組並批次以 cv2.polylines 繪製
                    diffs = np.diff(ids)
                    break_pts = np.flatnonzero(diffs != 1)
                    splits = np.split(ids, break_pts + 1)
                    for chunk_ids in splits:
                        if len(chunk_ids) == 0:
                            continue
                        cx0, cy0 = self._world_to_raster_px(rm, self.seg_x0[chunk_ids], self.seg_y0[chunk_ids])
                        cx1, cy1 = self._world_to_raster_px(rm, self.seg_x1[chunk_ids[-1:]], self.seg_y1[chunk_ids[-1:]])
                        pts_x = np.concatenate([cx0, cx1])
                        pts_y = np.concatenate([cy0, cy1])
                        pts = np.column_stack((pts_x, pts_y)).reshape((-1, 1, 2))
                        cv2.polylines(arr, [pts], isClosed=False, color=first_color, thickness=width, lineType=cv2.LINE_AA)
                else:
                    x0, y0 = self._world_to_raster_px(rm, self.seg_x0[ids], self.seg_y0[ids])
                    x1, y1 = self._world_to_raster_px(rm, self.seg_x1[ids], self.seg_y1[ids])
                    for j, seg_id in enumerate(ids):
                        cv2.line(
                            arr,
                            (int(x0[j]), int(y0[j])),
                            (int(x1[j]), int(y1[j])),
                            self.track_colors[int(seg_id)],
                            thickness=width,
                            lineType=cv2.LINE_AA,
                        )
            else:
                x0, y0 = self._world_to_raster_px(rm, self.seg_x0[ids], self.seg_y0[ids])
                x1, y1 = self._world_to_raster_px(rm, self.seg_x1[ids], self.seg_y1[ids])
                draw = ImageDraw.Draw(rm.image)
                for j, seg_id in enumerate(ids):
                    draw.line(
                        [(int(x0[j]), int(y0[j])), (int(x1[j]), int(y1[j]))],
                        fill=self.track_colors[int(seg_id)],
                        width=width,
                    )
                rm.np_image = np.asarray(rm.image, dtype=np.uint8).copy()

        state.track_upto = seg_count

    def get(self, view_x: float, view_y: float, idx: int) -> RasterMap:
        key = self._key(view_x, view_y)
        if key in self.cache:
            state = self.cache.pop(key)
            self.cache[key] = state
        else:
            state = self._build_chunk(key)
            self.cache[key] = state
            max_c = 2 if (not self.tile_cache_enabled or getattr(config, "CAMERA_MODE", "North-Up") == "3D-Terrain") else max(1, int(config.LOCAL_CACHE_CHUNKS))
            while len(self.cache) > max_c:
                self.cache.popitem(last=False)

        self._ensure_track(state, idx)
        return state.raster
