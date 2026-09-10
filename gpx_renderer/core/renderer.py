# -*- coding: utf-8 -*-
"""
Pillow / OpenCV 加速 RideRenderer 動畫畫格繪製引擎（包含 HUD 速度錶、小地圖、海拔圖與結尾統計卡片）。
"""

from __future__ import annotations
import math
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
import matplotlib
from matplotlib.colors import Normalize

try:
    import cv2
    HAVE_CV2 = True
except Exception:
    cv2 = None
    HAVE_CV2 = False

from gpx_renderer import config
from gpx_renderer.utils import load_font
from gpx_renderer.core.data import RideData, ease_smoothstep, compute_end_route_view
from gpx_renderer.core.map_utils import RasterMap, LocalBasemapCache


def _get_aspect_margins(margin: float):
    aspect = config.FRAME_WIDTH / float(config.FRAME_HEIGHT)
    if aspect >= 1.0:
        return margin * aspect, margin
    return margin, margin / aspect


def _blend_rgba_overlay_np(canvas: np.ndarray, overlay: np.ndarray, x: int, y: int):
    """將 (H, W, 4) 的 RGBA NumPy 陣列快速 Alpha 合成至 (H, W, 3) 的 RGB canvas NumPy 陣列。"""
    ch, cw = canvas.shape[:2]
    oh, ow = overlay.shape[:2]
    if x >= cw or y >= ch or x + ow <= 0 or y + oh <= 0:
        return

    x0 = max(0, x)
    y0 = max(0, y)
    x1 = min(cw, x + ow)
    y1 = min(ch, y + oh)
    ox0 = x0 - x
    oy0 = y0 - y
    ox1 = ox0 + (x1 - x0)
    oy1 = oy0 + (y1 - y0)

    src = overlay[oy0:oy1, ox0:ox1]
    dst = canvas[y0:y1, x0:x1]
    alpha = src[:, :, 3:4].astype(np.float32) / 255.0
    if np.all(alpha == 1.0):
        dst[:] = src[:, :, :3]
    elif np.any(alpha > 0.003):
        dst[:] = np.clip(src[:, :, :3].astype(np.float32) * alpha + dst.astype(np.float32) * (1.0 - alpha), 0, 255).astype(np.uint8)


def _compute_ease_curve(
    n_frames: int,
    ease_in: bool = True,
    ease_out: bool = True,
    fps: int = 60,
    ease_in_sec: float = 1.2,
    ease_out_sec: float = 1.5,
) -> np.ndarray:
    """產生 C1 平滑 Hermite 緩動曲線 (u in [0, 1])，支援進站平滑減速 (Ease-Out) 與出站平滑加速 (Ease-In)。"""
    if n_frames <= 3:
        return np.linspace(0.0, 1.0, n_frames)

    t_in = min(0.35, (ease_in_sec * fps) / n_frames) if ease_in else 0.0
    t_out = min(0.35, (ease_out_sec * fps) / n_frames) if ease_out else 0.0

    if t_in + t_out > 0.8:
        scale = 0.8 / (t_in + t_out)
        t_in *= scale
        t_out *= scale

    t_samples = np.linspace(0.0, 1.0, n_frames)
    v = np.ones(n_frames, dtype=np.float64)

    for idx, t in enumerate(t_samples):
        if t_in > 0 and t < t_in:
            p = t / t_in
            v[idx] = 3.0 * (p ** 2) - 2.0 * (p ** 3)
        elif t_out > 0 and t > (1.0 - t_out):
            p = (1.0 - t) / t_out
            v[idx] = 3.0 * (p ** 2) - 2.0 * (p ** 3)
        else:
            v[idx] = 1.0

    # 限制微小底速避免梯度完全歸零，保持陣列嚴格單調遞增
    v = np.clip(v, 0.001, 1.0)
    u = np.zeros(n_frames, dtype=np.float64)
    u[1:] = np.cumsum(0.5 * (v[:-1] + v[1:]))
    u /= u[-1]
    return u


class RideRenderer:
    def __init__(
        self,
        data: RideData,
        overview_map: RasterMap | None,
        map_style,
        fps: int,
        video_duration: float,
        zoom_out_duration: float,
        end_hold_duration: float,
        tile_cache_enabled: bool = True,
        media_items: list | None = None,
    ):
        self.d = data
        self.rm = overview_map
        self.fps = int(fps)
        self.video_duration = float(video_duration)
        self.zoom_out_duration = float(zoom_out_duration)
        self.end_hold_duration = float(end_hold_duration)
        self.tile_cache_enabled = bool(tile_cache_enabled)

        self.main_frames = max(1, int(round(self.video_duration * self.fps)))
        self.zoom_frames = max(0, int(round(self.zoom_out_duration * self.fps)))
        self.hold_frames = max(0, int(round(self.end_hold_duration * self.fps)))
        self.total_frames = self.main_frames + self.zoom_frames + self.hold_frames

        base_alpha = min(max(config.CAMERA_SMOOTH, 1e-6), 1.0)
        self.camera_alpha = 1.0 - (1.0 - base_alpha) ** (60.0 / self.fps)

        self.use_cv2 = bool(config.USE_OPENCV_FAST_PATH and HAVE_CV2)
        if not self.tile_cache_enabled:
            print("[INFO] Worker tile cache：OFF（避開 contextily/joblib 多程序 cache contention）")
        if self.use_cv2:
            print("[INFO] Renderer fast path：OpenCV warpAffine + local high-res tile chunks")
        elif config.USE_OPENCV_FAST_PATH:
            print("[INFO] 未安裝 OpenCV，鏡頭裁切改用 Pillow fallback。可執行：pip install opencv-python")

        self.media_popups = []
        if config.ENABLE_MEDIA and media_items:
            from gpx_renderer.core.media import prepare_thumbnail, extract_video_frames_for_popup

            valid_items = [m for m in media_items if m.matched_index >= 0]
            # 嚴格依據當前有效里程與點位索引進行升冪排序
            valid_items.sort(key=lambda m: (float(m.current_km), int(m.matched_index)))

            # 群組 (Cluster) 判別：僅對真正極近距離 (<= 50m / 0.05km) 且時間相近之相片進行同站合併
            clusters = []
            if valid_items:
                curr_cluster = [valid_items[0]]
                for idx_m in range(1, len(valid_items)):
                    prev_item = curr_cluster[-1]
                    curr_item = valid_items[idx_m]

                    # 計算兩張照片在路線上的實際里程差距 (km)
                    dist_diff_km = abs(float(curr_item.current_km) - float(prev_item.current_km))
                    close_gpx = dist_diff_km <= 0.05  # 50 公尺內視為同一打卡景點

                    close_time = False
                    if getattr(curr_item, "has_exif_time", False) and getattr(prev_item, "has_exif_time", False):
                        if curr_item.timestamp and prev_item.timestamp:
                            t_diff = abs((curr_item.timestamp.replace(tzinfo=None) - prev_item.timestamp.replace(tzinfo=None)).total_seconds())
                            close_time = (t_diff <= 15.0) and (dist_diff_km <= 0.10)

                    if close_gpx or close_time:
                        curr_cluster.append(curr_item)
                    else:
                        clusters.append(curr_cluster)
                        curr_cluster = [curr_item]
                if curr_cluster:
                    clusters.append(curr_cluster)

            base_ride_frames = max(1, int(round(self.video_duration * self.fps)))
            max_thumb_w = int(config.FRAME_WIDTH * 0.65)
            max_thumb_h = int(config.FRAME_HEIGHT * 0.60)
            fade_frames = max(1, int(round(0.35 * self.fps)))

            # 建立單調遞增無倒退之時間軸 (Segment-based monotonic timeline)
            spots = [0] + [clus[0].matched_index for clus in clusters] + [self.d.total_points - 1]
            spots = sorted(list(dict.fromkeys(spots)))

            # 依 spot 點位索引組織所有需播放的媒體清單 (防止同點位字典覆蓋)
            cluster_by_spot: dict[int, list] = {}
            for clus in clusters:
                spot_idx = clus[0].matched_index
                if spot_idx not in cluster_by_spot:
                    cluster_by_spot[spot_idx] = []
                cluster_by_spot[spot_idx].extend(clus)

            cluster_spot_processed = set()

            use_real = bool(config.USE_REAL_SPEED and self.d.gpx_times and len(self.d.gpx_times) == self.d.total_points and self.d.gpx_times[0] is not None)

            span_weights = []
            for k_idx in range(len(spots) - 1):
                s0, s1 = spots[k_idx], spots[k_idx + 1]
                if use_real:
                    try:
                        dt = (self.d.gpx_times[s1].replace(tzinfo=None) - self.d.gpx_times[s0].replace(tzinfo=None)).total_seconds()
                        span_weights.append(max(0.001, dt))
                    except Exception:
                        d0, d1 = float(self.d.distances[s0]), float(self.d.distances[s1])
                        span_weights.append(max(0.001, d1 - d0))
                else:
                    d0, d1 = float(self.d.distances[s0]), float(self.d.distances[s1])
                    span_weights.append(max(0.001, d1 - d0))

            total_weight = sum(span_weights)
            main_idx_list = []

            for k_idx in range(len(spots) - 1):
                s0, s1 = spots[k_idx], spots[k_idx + 1]
                seg_frames = max(1, int(round(base_ride_frames * (span_weights[k_idx] / total_weight))))

                # 判斷是否需要進站減速與出站加速
                is_s0_media = (s0 in cluster_by_spot) or (k_idx == 0)
                is_s1_media = (s1 in cluster_by_spot) or (k_idx == len(spots) - 2)

                u_curve = _compute_ease_curve(
                    seg_frames,
                    ease_in=is_s0_media,
                    ease_out=is_s1_media,
                    fps=self.fps,
                    ease_in_sec=1.2,
                    ease_out_sec=1.5,
                )

                if use_real:
                    try:
                        times_sub = self.d.gpx_times[s0:s1 + 1]
                        tb = times_sub[0].replace(tzinfo=None)
                        elapsed_sub = np.array([(t.replace(tzinfo=None) - tb).total_seconds() for t in times_sub], dtype=np.float64)
                        tot_t = elapsed_sub[-1]
                        if tot_t > 0:
                            t_targets = u_curve * tot_t
                            pts_sub = np.arange(s0, s1 + 1)
                            seg_indices = np.interp(t_targets, elapsed_sub, pts_sub).astype(np.int32)
                        else:
                            d0, d1 = float(self.d.distances[s0]), float(self.d.distances[s1])
                            target_dists = d0 + u_curve * (d1 - d0)
                            seg_indices = np.interp(target_dists, self.d.distances[s0:s1 + 1], np.arange(s0, s1 + 1)).astype(np.int32)
                    except Exception:
                        d0, d1 = float(self.d.distances[s0]), float(self.d.distances[s1])
                        target_dists = d0 + u_curve * (d1 - d0)
                        seg_indices = np.interp(target_dists, self.d.distances[s0:s1 + 1], np.arange(s0, s1 + 1)).astype(np.int32)
                else:
                    d0, d1 = float(self.d.distances[s0]), float(self.d.distances[s1])
                    target_dists = d0 + u_curve * (d1 - d0)
                    seg_indices = np.interp(target_dists, self.d.distances[s0:s1 + 1], np.arange(s0, s1 + 1)).astype(np.int32)

                if main_idx_list and len(seg_indices) > 0 and seg_indices[0] == main_idx_list[-1]:
                    seg_indices = seg_indices[1:]

                for pt_idx in seg_indices:
                    pt_val = int(pt_idx)
                    main_idx_list.append(pt_val)

                    if pt_val in cluster_by_spot and pt_val not in cluster_spot_processed:
                        cluster_spot_processed.add(pt_val)
                        items_at_spot = cluster_by_spot[pt_val]

                        for item in items_at_spot:
                            item_dur_sec = float(item.effective_duration)
                            item_dur_frames = max(1, int(round(item_dur_sec * self.fps)))

                            start_f = len(main_idx_list) - 1
                            end_f = start_f + item_dur_frames

                            video_reader = None
                            if getattr(item, "media_type", "") == "video":
                                from gpx_renderer.core.media import VideoPopupReader
                                video_reader = VideoPopupReader(
                                    item.file_path,
                                    start_time_sec=float(getattr(item, "clip_start_sec", 0.0) or 0.0),
                                    anim_fps=self.fps,
                                    max_w=max_thumb_w,
                                    max_h=max_thumb_h,
                                    ffmpeg_exe=getattr(config, "FFMPEG_EXE", None),
                                )
                                if item.thumbnail is None:
                                    item.thumbnail = prepare_thumbnail(item.file_path, max_w=max_thumb_w, max_h=max_thumb_h, is_video=True)
                            else:
                                if item.thumbnail is None:
                                    item.thumbnail = prepare_thumbnail(item.file_path, max_w=max_thumb_w, max_h=max_thumb_h)

                            if item.thumbnail is not None or video_reader is not None:
                                self.media_popups.append({
                                    "item": item,
                                    "start_frame": start_f,
                                    "end_frame": end_f,
                                    "fade_frames": fade_frames,
                                    "cluster_size": len(items_at_spot),
                                    "video_reader": video_reader,
                                })

                            main_idx_list.extend([pt_val] * item_dur_frames)

            ride_indices = np.array(main_idx_list, dtype=np.int32)
        else:
            self.media_popups = []
            main_f = max(1, int(round(self.video_duration * self.fps)))
            u_curve = _compute_ease_curve(main_f, ease_in=True, ease_out=True, fps=self.fps, ease_in_sec=1.0, ease_out_sec=1.2)
            use_real = bool(config.USE_REAL_SPEED and self.d.gpx_times and len(self.d.gpx_times) == self.d.total_points and self.d.gpx_times[0] is not None)
            if use_real:
                try:
                    tb = self.d.gpx_times[0].replace(tzinfo=None)
                    elapsed = np.array([(t.replace(tzinfo=None) - tb).total_seconds() for t in self.d.gpx_times], dtype=np.float64)
                    tot_t = elapsed[-1]
                    if tot_t > 0:
                        t_targets = u_curve * tot_t
                        ride_indices = np.interp(t_targets, elapsed, np.arange(self.d.total_points)).astype(np.int32)
                    else:
                        d0, d1 = float(self.d.distances[0]), float(self.d.distances[-1])
                        target_dists = d0 + u_curve * (d1 - d0)
                        ride_indices = np.interp(target_dists, self.d.distances, np.arange(self.d.total_points)).astype(np.int32)
                except Exception:
                    d0, d1 = float(self.d.distances[0]), float(self.d.distances[-1])
                    target_dists = d0 + u_curve * (d1 - d0)
                    ride_indices = np.interp(target_dists, self.d.distances, np.arange(self.d.total_points)).astype(np.int32)
            else:
                d0, d1 = float(self.d.distances[0]), float(self.d.distances[-1])
                target_dists = d0 + u_curve * (d1 - d0)
                ride_indices = np.interp(target_dists, self.d.distances, np.arange(self.d.total_points)).astype(np.int32)

        # 2. 若為 3D 地形模式，在最前段插入 2D 靜止 + 2D轉3D 俯衝過渡 (INTRO_HOLD_SEC + INTRO_TRANSITION_SEC)
        if getattr(config, "CAMERA_MODE", "North-Up") == "3D-Terrain":
            intro_hold_f = int(round(float(getattr(config, "INTRO_HOLD_SEC", 1.5)) * self.fps))
            intro_trans_f = int(round(float(getattr(config, "INTRO_TRANSITION_SEC", 2.0)) * self.fps))
            intro_total_f = intro_hold_f + intro_trans_f
            self.main_indices = np.concatenate([
                np.full(intro_total_f, 0, dtype=np.int32),
                ride_indices
            ])
            for popup in self.media_popups:
                popup["start_frame"] += intro_total_f
                popup["end_frame"] += intro_total_f
        else:
            self.main_indices = ride_indices

        self.main_frames = len(self.main_indices)

        self.zoom_frames = max(0, int(round(self.zoom_out_duration * self.fps)))
        self.hold_frames = max(0, int(round(self.end_hold_duration * self.fps)))
        self.total_frames = self.main_frames + self.zoom_frames + self.hold_frames

        self.track_colors = self._build_track_colors()
        self.seg_x0 = self.d.xs[:-1]
        self.seg_x1 = self.d.xs[1:]
        self.seg_y0 = self.d.ys[:-1]
        self.seg_y1 = self.d.ys[1:]
        self.seg_min_x = np.minimum(self.seg_x0, self.seg_x1)
        self.seg_max_x = np.maximum(self.seg_x0, self.seg_x1)
        self.seg_min_y = np.minimum(self.seg_y0, self.seg_y1)
        self.seg_max_y = np.maximum(self.seg_y0, self.seg_y1)
        self.local_maps = LocalBasemapCache(
            map_style=map_style,
            seg_x0=self.seg_x0,
            seg_x1=self.seg_x1,
            seg_y0=self.seg_y0,
            seg_y1=self.seg_y1,
            seg_min_x=self.seg_min_x,
            seg_max_x=self.seg_max_x,
            seg_min_y=self.seg_min_y,
            seg_max_y=self.seg_max_y,
            track_colors=self.track_colors,
            use_cv2=self.use_cv2,
            tile_cache_enabled=self.tile_cache_enabled,
        )
        self.cached_hold_frame: Image.Image | None = None

        ui_scale = min(config.FRAME_WIDTH, config.FRAME_HEIGHT) / 1000.0
        self.ui_scale = ui_scale
        aspect = config.FRAME_WIDTH / float(config.FRAME_HEIGHT)

        self.track_line_width = max(2, int(round(config.TRACK_LINE_WIDTH * ui_scale)))
        self.font_hud_kicker = load_font(max(8, int(round(10 * ui_scale))), bold=True)
        self.font_hud_speed = load_font(max(20, int(round(38 * ui_scale))), bold=True)
        self.font_hud_unit = load_font(max(9, int(round(13 * ui_scale))), bold=True)
        self.font_hud_label = load_font(max(8, int(round(9.5 * ui_scale))), bold=True)
        self.font_hud_metric = load_font(max(10, int(round(15 * ui_scale))), bold=True)
        self.font_hud_metric_unit = load_font(max(8, int(round(9.5 * ui_scale))), bold=True)
        self.font_panel_label = load_font(max(8, int(round(10 * ui_scale))), bold=True)
        self.font_panel_metric = load_font(max(10, int(round(15 * ui_scale))), bold=True)

        self.font_summary_title = load_font(max(16, int(round(26 * ui_scale))), bold=True)
        self.font_summary_label = load_font(max(8, int(round(10 * ui_scale))), bold=True)
        self.font_summary_value = load_font(max(14, int(round(24 * ui_scale))), bold=True)
        self.font_summary_unit = load_font(max(8, int(round(11 * ui_scale))), bold=True)
        default_caption_size = int(getattr(config, "MEDIA_CAPTION_FONT_SIZE", 22))
        self.font_caption = load_font(max(10, int(round(default_caption_size * ui_scale))), bold=True)

        self.hud_update_every = max(1, int(round(self.fps / max(1, config.HUD_UPDATE_HZ))))

        self.cached_hud: Image.Image | None = None
        self.cached_hud_idx = -1

        # 頂部雙面板與底部高度剖面圖幾何計算
        margin_x = max(14, int(round(24 * ui_scale)))
        margin_y = max(14, int(round(22 * ui_scale)))

        # 頂部面板高度 (速度面板與路線縮圖高度完全對齊)
        top_panel_h = max(110, int(round(136 * ui_scale)))

        # 速度面板 (左上角)
        if aspect >= 1.3:
            hud_w_ratio = 0.25
        elif aspect <= 0.75:
            hud_w_ratio = 0.44
        else:
            t = (aspect - 0.75) / (1.3 - 0.75)
            hud_w_ratio = 0.44 + (0.25 - 0.44) * t
        self.hud_x = margin_x
        self.hud_y = margin_y
        self.hud_w = int(round(config.FRAME_WIDTH * hud_w_ratio))
        self.hud_w = max(int(round(240 * ui_scale)), min(int(round(620 * ui_scale)), self.hud_w))
        self.hud_h = top_panel_h

        # 路線縮圖 (右上角，與速度面板頂部 Y 及高度完全對齊)
        if aspect <= 0.75:
            self.mini_w = self.hud_w
        else:
            self.mini_w = max(int(round(200 * ui_scale)), int(round(top_panel_h * 1.35)))
        self.mini_h = top_panel_h
        self.mini_x = config.FRAME_WIDTH - self.mini_w - margin_x
        self.mini_y = margin_y

        # 海拔高度剖面圖 (置中於下方並向兩側填滿)
        self.elev_x = margin_x
        self.elev_w = config.FRAME_WIDTH - 2 * margin_x
        self.elev_h = max(80, int(round(105 * ui_scale))) if aspect > 0.75 else max(90, int(round(115 * ui_scale)))
        self.elev_y = config.FRAME_HEIGHT - self.elev_h - margin_y

        self._init_hud_static()
        self._init_minimap()
        self._init_elevation()
        self._init_summary()
        self._terrain_out_buffer = np.full((config.FRAME_HEIGHT, config.FRAME_WIDTH, 3), 17, dtype=np.uint8)

        self.camera_x, self.camera_y, self.camera_h, self.camera_p, self.camera_m = self._precompute_camera()

    # ---------- geometry ----------
    def _precompute_camera(self):
        tx = self.d.xs[self.main_indices]
        ty = self.d.ys[self.main_indices]
        cx_arr = np.empty(self.main_frames, dtype=np.float64)
        cy_arr = np.empty(self.main_frames, dtype=np.float64)
        ch_arr = np.empty(self.main_frames, dtype=np.float64)
        cp_arr = np.empty(self.main_frames, dtype=np.float64)
        cm_arr = np.empty(self.main_frames, dtype=np.float64)

        is_3d = (getattr(config, "CAMERA_MODE", "North-Up") == "3D-Terrain")
        is_heading_up = (getattr(config, "CAMERA_MODE", "North-Up") in ("Heading-Up", "3D-Terrain"))
        has_headings = (is_heading_up and self.d.headings is not None and len(self.d.headings) > 0)

        target_pitch = float(getattr(config, "CAMERA_PITCH_DEG", 42.0)) if is_3d else 0.0
        base_margin = float(config.VIEW_MARGIN)
        target_margin = base_margin * 1.35 if is_3d else base_margin
        start_margin = target_margin * 1.5 if is_3d else target_margin

        intro_hold_f = int(round(float(getattr(config, "INTRO_HOLD_SEC", 1.5)) * self.fps)) if is_3d else 0
        intro_trans_f = int(round(float(getattr(config, "INTRO_TRANSITION_SEC", 2.0)) * self.fps)) if is_3d else 0
        intro_total_f = intro_hold_f + intro_trans_f
        outro_trans_f = int(round(float(getattr(config, "OUTRO_TRANSITION_SEC", 2.0)) * self.fps)) if is_3d else 0

        a = self.camera_alpha
        rot_base_alpha = min(max(getattr(config, "CAMERA_ROTATION_SMOOTH", 0.025), 1e-6), 1.0)
        rot_alpha = 1.0 - (1.0 - rot_base_alpha) ** (60.0 / self.fps)
        max_speed_deg = float(getattr(config, "CAMERA_MAX_ROTATION_SPEED_DEG", 25.0))
        max_step_rad = math.radians(max_speed_deg) / float(self.fps)
        deadband_rad = math.radians(1.5)

        # 1. Target rider position (rx, ry) with smooth IIR tracking
        rx_arr = np.empty(self.main_frames, dtype=np.float64)
        ry_arr = np.empty(self.main_frames, dtype=np.float64)
        rx_arr[0] = tx[0]
        ry_arr[0] = ty[0]
        for i in range(1, self.main_frames):
            if is_3d and i < intro_total_f:
                rx_arr[i] = tx[0]
                ry_arr[i] = ty[0]
            else:
                rx_arr[i] = rx_arr[i - 1] + (tx[i] - rx_arr[i - 1]) * a
                ry_arr[i] = ry_arr[i - 1] + (ty[i] - ry_arr[i - 1]) * a

        # 2. Dynamic Speed Zoom (速度動態鏡頭縮放倍率計算)
        enable_speed_zoom = bool(getattr(config, "ENABLE_DYNAMIC_SPEED_ZOOM", True))
        if enable_speed_zoom and self.d.speeds is not None and len(self.d.speeds) > 0:
            min_scale = float(getattr(config, "SPEED_ZOOM_MIN_SCALE", 0.75))
            max_scale = float(getattr(config, "SPEED_ZOOM_MAX_SCALE", 1.40))
            smooth_base = min(max(float(getattr(config, "SPEED_ZOOM_SMOOTH", 0.035)), 1e-6), 1.0)
            zoom_alpha = 1.0 - (1.0 - smooth_base) ** (60.0 / float(self.fps))

            def _speed_to_scale(spd: float) -> float:
                if not np.isfinite(spd) or spd < 0:
                    return 1.0
                if spd <= 10.0:
                    t = max(0.0, spd / 10.0)
                    base_10 = min_scale + (1.0 - min_scale) * 0.15
                    return min_scale + t * (base_10 - min_scale)
                elif spd <= 25.0:
                    base_10 = min_scale + (1.0 - min_scale) * 0.15
                    t = (spd - 10.0) / 15.0
                    return base_10 + t * (1.0 - base_10)
                elif spd <= 55.0:
                    t = (spd - 25.0) / 30.0
                    return 1.0 + t * (max_scale - 1.0)
                else:
                    excess = spd - 55.0
                    return min(max_scale + 0.12 * (1.0 - math.exp(-excess / 20.0)), max_scale * 1.15)

            raw_scales = np.array([_speed_to_scale(float(self.d.speeds[idx])) for idx in self.main_indices], dtype=np.float64)
            speed_zoom_scales = np.empty(self.main_frames, dtype=np.float64)
            speed_zoom_scales[0] = raw_scales[0]
            for i in range(1, self.main_frames):
                speed_zoom_scales[i] = speed_zoom_scales[i - 1] + (raw_scales[i] - speed_zoom_scales[i - 1]) * zoom_alpha
        else:
            speed_zoom_scales = np.ones(self.main_frames, dtype=np.float64)

        # 3. Camera pitch (cp) & margin (cm)
        for i in range(self.main_frames):
            cur_target_margin = target_margin * speed_zoom_scales[i]
            if is_3d:
                if i < intro_hold_f:
                    cp_arr[i] = 0.0
                    cm_arr[i] = start_margin
                elif i < intro_total_f and intro_trans_f > 0:
                    t = (i - intro_hold_f) / float(intro_trans_f)
                    alpha = ease_smoothstep(t)
                    cp_arr[i] = alpha * target_pitch
                    cm_arr[i] = start_margin + alpha * (cur_target_margin - start_margin)
                elif i >= self.main_frames - outro_trans_f and outro_trans_f > 0:
                    t = (i - (self.main_frames - outro_trans_f)) / float(outro_trans_f)
                    alpha = ease_smoothstep(t)
                    cp_arr[i] = target_pitch * (1.0 - alpha)
                    cm_arr[i] = cur_target_margin + alpha * (start_margin - cur_target_margin)
                else:
                    cp_arr[i] = target_pitch
                    cm_arr[i] = cur_target_margin
            else:
                cp_arr[i] = 0.0
                cm_arr[i] = cur_target_margin

        # 4. Camera heading (ch)
        if has_headings:
            target_h = self.d.headings[self.main_indices]
            initial_route_heading = float(target_h[intro_total_f if is_3d else 0])

            for i in range(self.main_frames):
                if is_3d and i < intro_hold_f:
                    ch_arr[i] = math.pi / 2.0
                elif is_3d and i < intro_total_f and intro_trans_f > 0:
                    t = (i - intro_hold_f) / float(intro_trans_f)
                    alpha = ease_smoothstep(t)
                    diff = (initial_route_heading - math.pi / 2.0 + math.pi) % (2.0 * math.pi) - math.pi
                    ch_arr[i] = math.pi / 2.0 + alpha * diff
                elif is_3d and i >= self.main_frames - outro_trans_f and outro_trans_f > 0:
                    t = (i - (self.main_frames - outro_trans_f)) / float(outro_trans_f)
                    alpha = ease_smoothstep(t)
                    base_h = ch_arr[self.main_frames - outro_trans_f - 1]
                    diff = (math.pi / 2.0 - base_h + math.pi) % (2.0 * math.pi) - math.pi
                    ch_arr[i] = base_h + alpha * diff
                else:
                    prev_angle = ch_arr[i - 1] if i > 0 else initial_route_heading
                    t_angle = float(target_h[i])
                    diff = (t_angle - prev_angle + math.pi) % (2.0 * math.pi) - math.pi
                    if abs(diff) < deadband_rad:
                        ch_arr[i] = prev_angle
                    else:
                        step = diff * rot_alpha
                        step = max(-max_step_rad, min(max_step_rad, step))
                        ch_arr[i] = prev_angle + step
        else:
            ch_arr.fill(math.pi / 2.0)

        # 4. 根據 3D 俯角計算相機後撤距離 d_behind，使騎乘指示點 100% 精準置於畫面正中央 (W/2, H/2)
        for i in range(self.main_frames):
            if is_3d and cp_arr[i] > 0.001:
                pitch_rad = math.radians(cp_arr[i])
                cam_alt = cm_arr[i] * 0.85
                d_behind = cam_alt * math.sin(pitch_rad)
                cx_arr[i] = rx_arr[i] - d_behind * math.cos(ch_arr[i])
                cy_arr[i] = ry_arr[i] - d_behind * math.sin(ch_arr[i])
            else:
                cx_arr[i] = rx_arr[i]
                cy_arr[i] = ry_arr[i]

        return cx_arr, cy_arr, ch_arr, cp_arr, cm_arr

    def _world_to_frame_px(self, x: float, y: float, view_x: float, view_y: float, margin: float, heading_rad: float = math.pi / 2.0, z: float = 0.0, pitch_deg: float = 0.0):
        if getattr(config, "CAMERA_MODE", "North-Up") == "3D-Terrain" and pitch_deg > 0.1:
            from gpx_renderer.core.terrain_3d import Camera3D, project_3d_points
            exaggeration = float(getattr(config, "ELEVATION_EXAGGERATION", 1.5))
            cam_alt = margin * 0.85
            pitch_rad = math.radians(pitch_deg)
            z_safe = max(0.0, float(z))
            cam = Camera3D(
                x=view_x, y=view_y, z=(z_safe * exaggeration) + cam_alt * math.cos(pitch_rad),
                heading_rad=heading_rad, pitch_deg=pitch_deg, exaggeration=exaggeration
            )
            px_arr, py_arr, _ = project_3d_points(np.array([x]), np.array([y]), np.array([z_safe]), cam, margin)
            return int(round(px_arr[0])), int(round(py_arr[0]))

        margin_x, margin_y = _get_aspect_margins(margin)
        alpha = heading_rad - math.pi / 2.0
        cos_a = math.cos(alpha)
        sin_a = math.sin(alpha)

        dx = x - view_x
        dy = y - view_y

        rx = dx * cos_a + dy * sin_a
        ry = -dx * sin_a + dy * cos_a

        px = config.FRAME_WIDTH / 2.0 + (rx / (2.0 * margin_x)) * config.FRAME_WIDTH
        py = config.FRAME_HEIGHT / 2.0 - (ry / (2.0 * margin_y)) * config.FRAME_HEIGHT
        return int(round(px)), int(round(py))

    def _build_track_colors(self):
        scheme = getattr(config, "TRACK_COLOR_SCHEME", "經典橘")
        n_points = max(1, len(self.d.speeds) - 1)

        if "速度漸層" in scheme:
            # 速度漸層熱圖 (Speed Rainbow / Plasma)
            cmap = matplotlib.colormaps[getattr(config, "TRACK_CMAP", "plasma")]
            normalized = self.d.speed_norm(self.d.speeds[1:])
            rgba = cmap(normalized, bytes=True)
            return [tuple(map(int, c[:3])) for c in rgba]
        elif "螢光綠" in scheme:
            return [(0, 255, 102)] * n_points
        elif "電光藍" in scheme:
            return [(0, 229, 255)] * n_points
        elif "熾熱紅" in scheme:
            return [(255, 42, 42)] * n_points
        elif "經典橘" in scheme or "橘" in scheme or "Strava" in scheme:
            # 經典橘 (#FC4C02 -> RGB(252, 76, 2))
            return [(252, 76, 2)] * n_points
        else:
            # 預設：經典橘 (#FC4C02 -> RGB(252, 76, 2))
            return [(252, 76, 2)] * n_points

    def _crop_raster(self, rm: RasterMap, view_x: float, view_y: float, margin: float, heading_rad: float = math.pi / 2.0, pitch_deg: float = 0.0, rider_z: float | None = None) -> Image.Image:
        if getattr(config, "CAMERA_MODE", "North-Up") == "3D-Terrain" and pitch_deg > 0.1:
            from gpx_renderer.core.terrain_3d import render_3d_terrain_frame
            exaggeration = float(getattr(config, "ELEVATION_EXAGGERATION", 1.5))
            return render_3d_terrain_frame(
                rm, view_x, view_y, margin, heading_rad,
                pitch_deg=pitch_deg, exaggeration=exaggeration,
                out_buffer=self._terrain_out_buffer,
                rider_z=rider_z,
            )

        margin_x, margin_y = _get_aspect_margins(margin)
        alpha = heading_rad - math.pi / 2.0
        cos_a = math.cos(alpha)
        sin_a = math.sin(alpha)

        W = float(config.FRAME_WIDTH)
        H = float(config.FRAME_HEIGHT)
        W2 = W * 0.5
        H2 = H * 0.5

        kx = W / (2.0 * margin_x)
        ky = H / (2.0 * margin_y)

        Sx = (rm.width - 1.0) / max(rm.east - rm.west, 1e-6)
        Sy = (rm.height - 1.0) / max(rm.north - rm.south, 1e-6)

        Uv = (view_x - rm.west) * Sx
        Vv = (rm.north - view_y) * Sy

        if self.use_cv2:
            m00 = (kx * cos_a) / Sx
            m01 = (-kx * sin_a) / Sy
            m02 = W2 - Uv * m00 - Vv * m01

            m10 = (ky * sin_a) / Sx
            m11 = (ky * cos_a) / Sy
            m12 = H2 - Uv * m10 - Vv * m11

            matrix = np.array([[m00, m01, m02], [m10, m11, m12]], dtype=np.float32)
            out = cv2.warpAffine(
                rm.np_image,
                matrix,
                (config.FRAME_WIDTH, config.FRAME_HEIGHT),
                flags=cv2.INTER_LINEAR,
                borderMode=cv2.BORDER_CONSTANT,
                borderValue=(135, 185, 235),
            )
            return out

        a = (Sx * cos_a) / kx
        b = (Sx * sin_a) / ky
        c = Uv - W2 * a - H2 * b
        d = (-Sy * sin_a) / kx
        e = (Sy * cos_a) / ky
        f = Vv - W2 * d - H2 * e

        return rm.image.transform(
            (config.FRAME_WIDTH, config.FRAME_HEIGHT),
            Image.Transform.AFFINE,
            (a, b, c, d, e, f),
            resample=config.MAP_RESAMPLE,
            fillcolor=(135, 185, 235),
        )

    def _draw_visible_track(self, frame: Image.Image | np.ndarray, idx: int, view_x: float, view_y: float, margin: float, heading_rad: float = math.pi / 2.0, pitch_deg: float = 0.0) -> Image.Image | np.ndarray:
        if getattr(config, "CAMERA_MODE", "North-Up") == "3D-Terrain" and pitch_deg > 0.1:
            return frame

        seg_count = min(max(int(idx), 0), len(self.seg_x0))
        if seg_count <= 0:
            return frame

        margin_x, margin_y = _get_aspect_margins(margin)
        left, right = view_x - margin_x, view_x + margin_x
        bottom, top = view_y - margin_y, view_y + margin_y
        mask = (
            (self.seg_max_x[:seg_count] >= left)
            & (self.seg_min_x[:seg_count] <= right)
            & (self.seg_max_y[:seg_count] >= bottom)
            & (self.seg_min_y[:seg_count] <= top)
        )
        ids = np.flatnonzero(mask)
        if ids.size == 0:
            return frame

        alpha = heading_rad - math.pi / 2.0
        cos_a = math.cos(alpha)
        sin_a = math.sin(alpha)

        W2 = config.FRAME_WIDTH * 0.5
        H2 = config.FRAME_HEIGHT * 0.5
        kx = config.FRAME_WIDTH / (2.0 * margin_x)
        ky = config.FRAME_HEIGHT / (2.0 * margin_y)

        dx0 = self.seg_x0[ids] - view_x
        dy0 = self.seg_y0[ids] - view_y
        dx1 = self.seg_x1[ids] - view_x
        dy1 = self.seg_y1[ids] - view_y

        rx0 = dx0 * cos_a + dy0 * sin_a
        ry0 = -dx0 * sin_a + dy0 * cos_a
        rx1 = dx1 * cos_a + dy1 * sin_a
        ry1 = -dx1 * sin_a + dy1 * cos_a

        px0 = np.rint(W2 + rx0 * kx).astype(np.int32)
        py0 = np.rint(H2 - ry0 * ky).astype(np.int32)
        px1 = np.rint(W2 + rx1 * kx).astype(np.int32)
        py1 = np.rint(H2 - ry1 * ky).astype(np.int32)

        if self.use_cv2:
            arr = frame if isinstance(frame, np.ndarray) else np.asarray(frame, dtype=np.uint8).copy()
            first_color = self.track_colors[int(ids[0])]
            is_single_color = True
            if len(ids) > 1:
                for seg_id in ids[1:]:
                    if self.track_colors[int(seg_id)] != first_color:
                        is_single_color = False
                        break

            if is_single_color:
                diffs = np.diff(ids)
                break_pts = np.flatnonzero(diffs != 1)
                splits = np.split(ids, break_pts + 1)
                for chunk_ids in splits:
                    if len(chunk_ids) == 0:
                        continue
                    pts = np.column_stack((px0[np.isin(ids, chunk_ids)], py0[np.isin(ids, chunk_ids)])).reshape((-1, 1, 2))
                    cv2.polylines(arr, [pts], isClosed=False, color=first_color, thickness=self.track_line_width, lineType=cv2.LINE_AA)
            else:
                for j, seg_id in enumerate(ids):
                    cv2.line(
                        arr,
                        (int(px0[j]), int(py0[j])),
                        (int(px1[j]), int(py1[j])),
                        self.track_colors[int(seg_id)],
                        thickness=self.track_line_width,
                        lineType=cv2.LINE_AA,
                    )
            return arr if isinstance(frame, np.ndarray) else Image.fromarray(arr)

        draw = ImageDraw.Draw(frame)
        for j, seg_id in enumerate(ids):
            i = int(seg_id)
            draw.line([(int(px0[j]), int(py0[j])), (int(px1[j]), int(py1[j]))], fill=self.track_colors[i], width=self.track_line_width)
        return frame

    # ---------- HUD ----------
    def _init_hud_static(self):
        s = self.ui_scale
        w = self.hud_w
        h = self.hud_h
        hud_base = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        draw = ImageDraw.Draw(hud_base)

        radius = max(10, int(round(16 * s)))
        draw.rounded_rectangle(
            (0, 0, w - 1, h - 1),
            radius=radius,
            fill=(9, 13, 18, 195),
            outline=(255, 255, 255, 32),
            width=max(1, int(round(s))),
        )

        pad_x = max(10, int(round(16 * s)))
        pad_y = max(8, int(round(12 * s)))
        draw.text(
            (pad_x, pad_y),
            "SPEED",
            font=self.font_hud_kicker,
            fill=(172, 182, 192, 230),
        )

        divider_y = int(round(h * 0.60))
        draw.line(
            (pad_x, divider_y, w - pad_x, divider_y),
            fill=(255, 255, 255, 22),
            width=max(1, int(round(s))),
        )

        inner_w = w - pad_x * 2
        col_w = inner_w / 3.0
        label_y = divider_y + max(4, int(round(6 * s)))
        labels = ["DISTANCE", "ELEVATION", "CLIMB"]
        for i, label in enumerate(labels):
            x = int(round(pad_x + i * col_w))
            if i:
                sep_x = int(round(pad_x + i * col_w - 6 * s))
                draw.line(
                    (sep_x, label_y, sep_x, h - pad_y),
                    fill=(255, 255, 255, 18),
                    width=max(1, int(round(s))),
                )
            draw.text((x, label_y), label, font=self.font_hud_label, fill=(134, 145, 156, 235))

        self.hud_pad_x = pad_x
        self.hud_pad_y = pad_y
        self.hud_divider_y = divider_y
        self.hud_col_w = col_w
        self.hud_static_base = hud_base

    def _build_hud(self, idx: int) -> Image.Image:
        d = self.d
        s = self.ui_scale
        hud = self.hud_static_base.copy()
        draw = ImageDraw.Draw(hud)
        pad_x = self.hud_pad_x
        pad_y = self.hud_pad_y

        speed_text = f"{d.speeds[idx]:.1f}"
        speed_y = pad_y + max(12, int(round(14 * s)))
        draw.text((pad_x, speed_y), speed_text, font=self.font_hud_speed, fill=(250, 252, 255, 255))
        sb = draw.textbbox((pad_x, speed_y), speed_text, font=self.font_hud_speed)
        unit_x = sb[2] + max(4, int(round(6 * s)))
        unit_y = sb[3] - max(12, int(round(16 * s)))
        draw.text((unit_x, unit_y), "km/h", font=self.font_hud_unit, fill=(170, 180, 190, 235))

        label_y = self.hud_divider_y + max(4, int(round(6 * s)))
        value_y = label_y + max(10, int(round(13 * s)))
        metrics = [
            (f"{d.distances[idx]:.1f}", "km"),
            (f"{d.eles[idx]:.0f}", "m"),
            (f"+{d.elevation_gain[idx]:.0f}", "m"),
        ]
        for i, (value, unit) in enumerate(metrics):
            x = int(round(pad_x + i * self.hud_col_w))
            draw.text((x, value_y), value, font=self.font_hud_metric, fill=(245, 247, 250, 255))
            vb = draw.textbbox((x, value_y), value, font=self.font_hud_metric)
            draw.text(
                (vb[2] + max(2, int(round(3 * s))), value_y + max(2, int(round(3 * s)))),
                unit,
                font=self.font_hud_metric_unit,
                fill=(150, 160, 170, 225),
            )
        return hud

    def _get_hud(self, frame_idx: int, idx: int) -> Image.Image:
        if (
            self.cached_hud is None
            or frame_idx % self.hud_update_every == 0
            or idx == self.d.total_points - 1
        ):
            self.cached_hud = self._build_hud(idx)
            self.cached_hud_idx = idx
        return self.cached_hud

    # ---------- minimap ----------
    def _init_minimap(self):
        d = self.d
        s = self.ui_scale

        self.mini_pad = max(10, int(round(14 * s)))
        label_h = max(14, int(round(18 * s)))

        avail_w = max(self.mini_w - 2 * self.mini_pad, 1)
        avail_h = max(self.mini_h - 2 * self.mini_pad - label_h, 1)

        min_x, max_x = float(d.xs.min()), float(d.xs.max())
        min_y, max_y = float(d.ys.min()), float(d.ys.max())
        center_x = (min_x + max_x) * 0.5
        center_y = (min_y + max_y) * 0.5

        route_w = max(max_x - min_x, 1.0)
        route_h = max(max_y - min_y, 1.0)

        scale_x = (avail_w * 0.88) / route_w
        scale_y = (avail_h * 0.88) / route_h
        scale = min(scale_x, scale_y)

        center_px_x = self.mini_pad + avail_w * 0.5
        center_px_y = self.mini_pad + label_h + avail_h * 0.5

        self.mini_px_x = center_px_x + (d.xs - center_x) * scale
        self.mini_px_y = center_px_y - (d.ys - center_y) * scale

        self.mini_layer = Image.new("RGBA", (self.mini_w, self.mini_h), (0, 0, 0, 0))
        draw = ImageDraw.Draw(self.mini_layer)
        radius = max(10, int(round(16 * self.ui_scale)))
        draw.rounded_rectangle(
            (0, 0, self.mini_w - 1, self.mini_h - 1),
            radius=radius,
            fill=(9, 13, 18, 195),
            outline=(255, 255, 255, 32),
            width=max(1, int(round(self.ui_scale))),
        )
        draw.text(
            (self.mini_pad, self.mini_pad - int(2 * self.ui_scale)),
            "ROUTE",
            font=self.font_panel_label,
            fill=(172, 182, 192, 235),
        )

        full_pts = [(int(round(x)), int(round(y))) for x, y in zip(self.mini_px_x, self.mini_px_y)]
        if len(full_pts) >= 2:
            draw.line(full_pts, fill=(255, 255, 255, 65), width=max(1, int(round(2 * self.ui_scale))))

        self.mini_progress_layer = self.mini_layer.copy()
        self.mini_draw = ImageDraw.Draw(self.mini_progress_layer)
        self.mini_last_idx = 0
        self.cached_mini_idx = -1
        self.cached_mini_img = None

    def _advance_minimap(self, idx: int):
        idx = min(max(int(idx), 0), self.d.total_points - 1)
        if idx <= self.mini_last_idx:
            return
        for seg_end in range(self.mini_last_idx + 1, idx + 1):
            p0 = (int(round(self.mini_px_x[seg_end - 1])), int(round(self.mini_px_y[seg_end - 1])))
            p1 = (int(round(self.mini_px_x[seg_end])), int(round(self.mini_px_y[seg_end])))
            self.mini_draw.line([p0, p1], fill=config.ORANGE + (255,), width=max(2, int(round(3 * self.ui_scale))))
        self.mini_last_idx = idx

    def _compose_minimap(self, idx: int) -> Image.Image:
        self._advance_minimap(idx)
        if idx == self.cached_mini_idx and self.cached_mini_img is not None:
            return self.cached_mini_img

        mini = self.mini_progress_layer.copy()
        draw = ImageDraw.Draw(mini)
        x = int(round(self.mini_px_x[idx]))
        y = int(round(self.mini_px_y[idx]))
        r = max(4, int(round(5 * self.ui_scale)))
        draw.ellipse((x - r - 2, y - r - 2, x + r + 2, y + r + 2), fill=(255, 255, 255, 235))
        draw.ellipse((x - r, y - r, x + r, y + r), fill=config.ORANGE + (255,))
        self.cached_mini_idx = idx
        self.cached_mini_img = mini
        return mini

    # ---------- elevation ----------
    def _init_elevation(self):
        d = self.d
        s = self.ui_scale
        pad = max(10, int(round(14 * s)))
        label_h = max(14, int(round(18 * s)))

        xmin = float(d.distances.min())
        xmax = max(float(d.distances.max()), xmin + 0.001)
        ymin = float(d.eles.min()) - 5.0
        ymax = float(d.eles.max()) + 5.0
        if ymax <= ymin:
            ymax = ymin + 10.0

        left, right = pad, self.elev_w - pad
        top, bottom = pad + label_h, self.elev_h - pad
        ex = left + (d.distances - xmin) / (xmax - xmin) * max(right - left, 1)
        ey = top + (ymax - d.eles) / (ymax - ymin) * max(bottom - top, 1)
        self.elev_px_x = ex
        self.elev_px_y = ey
        full_pts = [(int(round(x)), int(round(y))) for x, y in zip(ex, ey)]

        self.elev_base = Image.new("RGBA", (self.elev_w, self.elev_h), (0, 0, 0, 0))
        bdraw = ImageDraw.Draw(self.elev_base)
        radius = max(10, int(round(16 * s)))
        bdraw.rounded_rectangle(
            (0, 0, self.elev_w - 1, self.elev_h - 1),
            radius=radius,
            fill=(9, 13, 18, 195),
            outline=(255, 255, 255, 32),
            width=max(1, int(round(s))),
        )
        bdraw.text((pad, pad - int(2 * s)), "ELEVATION", font=self.font_panel_label, fill=(172, 182, 192, 235))
        if len(full_pts) >= 2:
            bdraw.line(full_pts, fill=(255, 255, 255, 52), width=max(1, int(round(2 * s))))

        self.elev_progress_full = Image.new("RGBA", (self.elev_w, self.elev_h), (0, 0, 0, 0))
        pdraw = ImageDraw.Draw(self.elev_progress_full)
        if len(full_pts) >= 2:
            poly = [(full_pts[0][0], bottom)] + full_pts + [(full_pts[-1][0], bottom)]
            pdraw.polygon(poly, fill=config.ORANGE + (48,))
            pdraw.line(full_pts, fill=config.ORANGE + (235,), width=max(2, int(round(2 * s))))

        self.elev_full_composite = self.elev_base.copy()
        if len(full_pts) >= 2:
            self.elev_full_composite.alpha_composite(self.elev_progress_full)
        self.cached_elev_reveal_x = -1
        self.cached_elev_img = None

    def _compose_elevation(self, idx: int) -> Image.Image:
        reveal_x = int(round(self.elev_px_x[idx]))
        reveal_x = min(max(reveal_x, 0), self.elev_w - 1)
        if reveal_x == self.cached_elev_reveal_x and self.cached_elev_img is not None:
            return self.cached_elev_img

        panel = self.elev_base.copy()
        if reveal_x > 0:
            crop = self.elev_full_composite.crop((0, 0, reveal_x + 1, self.elev_h))
            panel.paste(crop, (0, 0))
        self.cached_elev_reveal_x = reveal_x
        self.cached_elev_img = panel
        return panel

    # ---------- summary ----------
    def _init_summary(self):
        d = self.d
        if d.total_seconds and d.total_seconds > 0:
            avg_speed = d.distances[-1] / (d.total_seconds / 3600.0)
            hours = int(d.total_seconds // 3600)
            minutes = int((d.total_seconds % 3600) // 60)
            duration_value = f"{hours}h {minutes:02d}m"
        else:
            avg_speed = float(np.mean(d.speeds))
            duration_value = "N/A"

        self.summary_stats = [
            ("DISTANCE", f"{d.distances[-1]:.2f}", "km"),
            ("CLIMB", f"{d.elevation_gain[-1]:.0f}", "m"),
            ("AVG SPEED", f"{avg_speed:.1f}", "km/h"),
            ("DURATION", duration_value, ""),
        ]

    # ---------- drawing helpers ----------
    @staticmethod
    def _draw_marker(draw: ImageDraw.ImageDraw, x: int, y: int, fill, outline=None, r=8, outline_w=2):
        box = (x - r, y - r, x + r, y + r)
        draw.ellipse(box, fill=fill)
        if outline is not None and outline_w > 0:
            for k in range(outline_w):
                draw.ellipse((x - r - k, y - r - k, x + r + k, y + r + k), outline=outline)

    def _draw_summary(self, frame: Image.Image, alpha: float):
        if alpha <= 0.001:
            return

        alpha = max(0.0, min(1.0, float(alpha)))
        s = self.ui_scale
        x0 = int(config.FRAME_WIDTH * 0.065)
        x1 = int(config.FRAME_WIDTH * 0.935)
        y0 = int(config.FRAME_HEIGHT * config.SUMMARY_PANEL_TOP_FRAC)
        y1 = int(config.FRAME_HEIGHT * config.SUMMARY_PANEL_BOTTOM_FRAC)
        w, h = x1 - x0, y1 - y0
        radius = max(22, int(round(28 * s)))

        base = frame.convert("RGBA")
        crop = frame.crop((x0, y0, x1, y1)).filter(ImageFilter.GaussianBlur(radius=max(8, int(14*s)))).convert("RGBA")
        shade = Image.new("RGBA", crop.size, (7, 11, 16, int(172 * alpha)))
        crop.alpha_composite(shade)
        mask = Image.new("L", (w, h), 0)
        mdraw = ImageDraw.Draw(mask)
        mdraw.rounded_rectangle((0, 0, w-1, h-1), radius=radius, fill=int(255 * alpha))
        base.paste(crop, (x0, y0), mask)

        draw = ImageDraw.Draw(base)
        pad_x = int(round(28 * s))
        header_y = y0 + int(round(24 * s))
        draw.text(
            (x0 + pad_x, header_y),
            "RIDE STATS",
            font=self.font_summary_title,
            fill=(248, 250, 252, int(255*alpha)),
        )

        header_bottom = y0 + int(round(80 * s))
        draw.line(
            (x0+pad_x, header_bottom, x1-pad_x, header_bottom),
            fill=(255,255,255,int(28*alpha)),
            width=max(1, int(round(s))),
        )

        stat_top = header_bottom + int(round(18 * s))
        inner_w = w - pad_x*2
        col_w = inner_w / 4.0
        for i, (label, value, unit) in enumerate(self.summary_stats):
            col_x = int(round(x0 + pad_x + i * col_w))
            if i:
                sep_x = int(round(x0 + pad_x + i*col_w - 12*s))
                draw.line(
                    (sep_x, stat_top, sep_x, y1-int(24*s)),
                    fill=(255,255,255,int(22*alpha)),
                    width=max(1, int(round(s))),
                )
            draw.text(
                (col_x, stat_top), label, font=self.font_summary_label,
                fill=(154, 166, 178, int(240*alpha)),
            )
            value_y = stat_top + int(round(26 * s))
            draw.text(
                (col_x, value_y), value, font=self.font_summary_value,
                fill=(250, 252, 255, int(255*alpha)),
            )
            if unit:
                vb = draw.textbbox((col_x, value_y), value, font=self.font_summary_value)
                draw.text(
                    (vb[2] + int(7*s), value_y + int(12*s)), unit,
                    font=self.font_summary_unit,
                    fill=(160, 170, 180, int(230*alpha)),
                )

        frame.paste(base.convert("RGB"))

    def _get_hud_np(self, frame_idx: int, idx: int) -> np.ndarray:
        hud_img = self._get_hud(frame_idx, idx)
        if idx == getattr(self, "_cached_hud_np_idx", -1) and getattr(self, "_cached_hud_np_arr", None) is not None:
            return self._cached_hud_np_arr
        arr = np.asarray(hud_img.convert("RGBA"), dtype=np.uint8)
        self._cached_hud_np_idx = idx
        self._cached_hud_np_arr = arr
        return arr

    def _compose_minimap_np(self, idx: int) -> np.ndarray:
        img = self._compose_minimap(idx)
        if idx == getattr(self, "_cached_mini_np_idx", -1) and getattr(self, "_cached_mini_np_arr", None) is not None:
            return self._cached_mini_np_arr
        arr = np.asarray(img.convert("RGBA"), dtype=np.uint8)
        self._cached_mini_np_idx = idx
        self._cached_mini_np_arr = arr
        return arr

    def _compose_elevation_np(self, idx: int) -> np.ndarray:
        img = self._compose_elevation(idx)
        reveal_x = int(round(self.elev_px_x[idx]))
        if reveal_x == getattr(self, "_cached_elev_np_rx", -1) and getattr(self, "_cached_elev_np_arr", None) is not None:
            return self._cached_elev_np_arr
        arr = np.asarray(img.convert("RGBA"), dtype=np.uint8)
        self._cached_elev_np_rx = reveal_x
        self._cached_elev_np_arr = arr
        return arr

    def _draw_media_popups(self, frame: Image.Image | np.ndarray, frame_idx: int, view_x: float, view_y: float, margin: float):
        if not self.media_popups:
            return

        active_popups = [p for p in self.media_popups if p["start_frame"] <= frame_idx < p["end_frame"]]
        if not active_popups:
            return

        is_numpy = isinstance(frame, np.ndarray)
        pil_frame = Image.fromarray(frame) if is_numpy else frame

        for popup in active_popups:
            sf = popup["start_frame"]
            ef = popup["end_frame"]
            ff = popup["fade_frames"]
            if frame_idx - sf < ff:
                raw_a = (frame_idx - sf) / float(ff)
            elif ef - frame_idx < ff:
                raw_a = (ef - frame_idx) / float(ff)
            else:
                raw_a = 1.0

            alpha = ease_smoothstep(raw_a)
            if alpha <= 0.01:
                continue

            item = popup["item"]
            video_reader = popup.get("video_reader")
            if video_reader is not None:
                f_offset = max(0, frame_idx - sf)
                thumb = video_reader.get_frame(f_offset)
                if thumb is None:
                    thumb = item.thumbnail
            else:
                thumb = item.thumbnail

            if thumb is None:
                continue

            tw, th = thumb.size

            # 將媒體縮圖卡片固定置於動畫畫面正中央
            cx = (config.FRAME_WIDTH - tw) // 2
            cy = (config.FRAME_HEIGHT - th) // 2

            base = pil_frame.convert("RGBA")
            overlay = Image.new("RGBA", base.size, (0, 0, 0, 0))

            # 劇院級中央背景遮罩暗化 (Backdrop Overlay)
            shade_alpha = int(140 * alpha)
            shade = Image.new("RGBA", base.size, (7, 11, 16, shade_alpha))
            base.alpha_composite(shade)

            if alpha >= 0.99:
                overlay.paste(thumb, (cx, cy), thumb)
            else:
                thumb_alpha = thumb.copy()
                r, g, b, a = thumb_alpha.split()
                a = a.point(lambda p: int(p * alpha))
                thumb_alpha.putalpha(a)
                overlay.paste(thumb_alpha, (cx, cy), thumb_alpha)

            # 若照片設定有自訂說明文字，於相片下方繪製質感放大浮雕文字標籤列
            caption_text = str(getattr(item, "caption", "") or "").strip()
            if caption_text:
                odraw = ImageDraw.Draw(overlay)
                cap_sz = getattr(item, "caption_size", None)
                if cap_sz is not None and cap_sz > 0:
                    font_size = max(10, int(round(float(cap_sz) * self.ui_scale)))
                    font = load_font(font_size, bold=True)
                else:
                    font = self.font_caption

                tb = odraw.textbbox((0, 0), caption_text, font=font)
                text_w = tb[2] - tb[0]
                text_h = tb[3] - tb[1]

                s = self.ui_scale
                pad_x = max(16, int(round(26 * s)))
                pad_y = max(8, int(round(12 * s)))
                gap = max(10, int(round(16 * s)))

                cap_w = text_w + 2 * pad_x
                cap_h = text_h + 2 * pad_y
                cap_x = (config.FRAME_WIDTH - cap_w) // 2
                cap_y = cy + th + gap

                # 若文字標籤超出畫面底部，向上移至照片卡片內部下方
                if cap_y + cap_h > config.FRAME_HEIGHT - int(20 * s):
                    cap_y = cy + th - cap_h - int(12 * s)

                radius = max(10, int(round(16 * s)))
                odraw.rounded_rectangle(
                    (cap_x, cap_y, cap_x + cap_w - 1, cap_y + cap_h - 1),
                    radius=radius,
                    fill=(9, 13, 18, int(215 * alpha)),
                    outline=(255, 255, 255, int(60 * alpha)),
                    width=max(1, int(round(1.5 * s))),
                )
                tx = cap_x + pad_x - tb[0]
                ty = cap_y + pad_y - tb[1]
                odraw.text((tx, ty), caption_text, font=font, fill=(255, 255, 255, int(248 * alpha)))

            base.alpha_composite(overlay)
            pil_frame.paste(base.convert("RGB"))

        if is_numpy:
            np.copyto(frame, np.asarray(pil_frame, dtype=np.uint8))

    # ---------- frame render ----------
    def render_main_frame(self, frame_idx: int) -> np.ndarray | Image.Image:
        i = min(max(int(frame_idx), 0), self.main_frames - 1)
        idx = int(self.main_indices[i])
        d = self.d

        view_x = float(self.camera_x[i])
        view_y = float(self.camera_y[i])
        heading_rad = float(self.camera_h[i])
        pitch_deg = float(self.camera_p[i])
        current_margin = float(self.camera_m[i])

        local_rm = self.local_maps.get(view_x, view_y, idx)

        if getattr(config, "CAMERA_MODE", "North-Up") == "3D-Terrain":
            from gpx_renderer.core.terrain_3d import sample_dem_elevation
            rider_z = sample_dem_elevation(local_rm, float(d.xs[idx]), float(d.ys[idx]))
        else:
            rider_z = float(d.eles[idx])

        frame = self._crop_raster(local_rm, view_x, view_y, current_margin, heading_rad=heading_rad, pitch_deg=pitch_deg, rider_z=rider_z)
        px, py = self._world_to_frame_px(float(d.xs[idx]), float(d.ys[idx]), view_x, view_y, current_margin, heading_rad=heading_rad, z=rider_z, pitch_deg=pitch_deg)

        if isinstance(frame, np.ndarray):
            # 原生 OpenCV / NumPy 高速渲染途徑 (Zero-Copy)
            # 1. 繪製指示點 (白色外圈 + Strava 經典橘內圈)
            cv2.circle(frame, (px, py), 7 + 3, (255, 255, 255), -1, lineType=cv2.LINE_AA)
            cv2.circle(frame, (px, py), 7, config.ORANGE, -1, lineType=cv2.LINE_AA)

            # 2. 疊加資訊面板
            if getattr(config, "SHOW_SPEED_HUD", True):
                hud_np = self._get_hud_np(i, idx)
                _blend_rgba_overlay_np(frame, hud_np, self.hud_x, self.hud_y)

            if getattr(config, "SHOW_MINIMAP", True):
                mini_np = self._compose_minimap_np(idx)
                _blend_rgba_overlay_np(frame, mini_np, self.mini_x, self.mini_y)

            if getattr(config, "SHOW_ELEVATION", True):
                elev_np = self._compose_elevation_np(idx)
                _blend_rgba_overlay_np(frame, elev_np, self.elev_x, self.elev_y)

            # 3. 媒體相片卡片彈出
            if self.media_popups:
                self._draw_media_popups(frame, frame_idx, view_x, view_y, current_margin)

            return frame
        else:
            # Pillow Fallback 途徑
            draw = ImageDraw.Draw(frame)
            self._draw_marker(draw, px, py, config.WHITE, config.ORANGE, r=7, outline_w=3)

            if getattr(config, "SHOW_SPEED_HUD", True):
                hud = self._get_hud(i, idx)
                frame.paste(hud, (self.hud_x, self.hud_y), hud)

            if getattr(config, "SHOW_MINIMAP", True):
                mini = self._compose_minimap(idx)
                frame.paste(mini, (self.mini_x, self.mini_y), mini)

            if getattr(config, "SHOW_ELEVATION", True):
                elev = self._compose_elevation(idx)
                frame.paste(elev, (self.elev_x, self.elev_y), elev)

            # 媒體卡片與背景暗化遮罩放置於最頂層 (無法被 HUD / 小地圖 / 海拔圖遮擋)
            self._draw_media_popups(frame, frame_idx, view_x, view_y, current_margin)

            return frame

    def render_end_frame(self, end_frame_idx: int) -> Image.Image | np.ndarray:
        d = self.d

        if end_frame_idx >= self.zoom_frames and self.cached_hold_frame is not None:
            return self.cached_hold_frame.copy()

        if self.zoom_frames > 0:
            progress = min(max((end_frame_idx + 1) / self.zoom_frames, 0.0), 1.0)
        else:
            progress = 1.0

        eased = ease_smoothstep(progress)
        start_x = float(self.camera_x[-1])
        start_y = float(self.camera_y[-1])
        start_h = float(self.camera_h[-1])
        start_p = float(self.camera_p[-1])
        start_m = float(self.camera_m[-1])
        target_h = math.pi / 2.0  # 平滑旋轉回正北朝上
        current_pitch = start_p * (1.0 - eased)  # 平滑由 3D 俯角抬升回 2D 正俯瞰 (0°)

        ux = math.cos(start_h) * (1.0 - eased) + math.cos(target_h) * eased
        uy = math.sin(start_h) * (1.0 - eased) + math.sin(target_h) * eased
        heading_rad = math.atan2(uy, ux)

        end_x, end_y, end_margin = compute_end_route_view(d)
        view_x = start_x + (end_x - start_x) * eased
        view_y = start_y + (end_y - start_y) * eased
        margin = start_m + (end_margin - start_m) * eased

        if self.rm is None:
            raise RuntimeError("render_end_frame 需要 overview_map。")
        frame = self._crop_raster(self.rm, view_x, view_y, margin, heading_rad=heading_rad, pitch_deg=current_pitch, rider_z=float(d.eles[-1]))
        frame = self._draw_visible_track(frame, d.total_points - 1, view_x, view_y, margin, heading_rad=heading_rad, pitch_deg=current_pitch)

        sx, sy = self._world_to_frame_px(float(d.xs[0]), float(d.ys[0]), view_x, view_y, margin, heading_rad=heading_rad, z=float(d.eles[0]), pitch_deg=current_pitch)
        ex, ey = self._world_to_frame_px(float(d.xs[-1]), float(d.ys[-1]), view_x, view_y, margin, heading_rad=heading_rad, z=float(d.eles[-1]), pitch_deg=current_pitch)

        if isinstance(frame, np.ndarray):
            cv2.circle(frame, (sx, sy), 8 + 2, (255, 255, 255), -1, lineType=cv2.LINE_AA)
            cv2.circle(frame, (sx, sy), 8, config.GREEN, -1, lineType=cv2.LINE_AA)
            cv2.circle(frame, (ex, ey), 8 + 2, (255, 255, 255), -1, lineType=cv2.LINE_AA)
            cv2.circle(frame, (ex, ey), 8, config.ORANGE, -1, lineType=cv2.LINE_AA)
            pil_frame = Image.fromarray(frame)
            card_alpha = ease_smoothstep((progress - 0.60) / 0.40)
            self._draw_summary(pil_frame, card_alpha)
            frame = np.asarray(pil_frame, dtype=np.uint8).copy()
        else:
            draw = ImageDraw.Draw(frame)
            self._draw_marker(draw, sx, sy, config.GREEN, config.WHITE, r=8, outline_w=2)
            self._draw_marker(draw, ex, ey, config.ORANGE, config.WHITE, r=8, outline_w=2)
            card_alpha = ease_smoothstep((progress - 0.60) / 0.40)
            self._draw_summary(frame, card_alpha)

        if end_frame_idx >= self.zoom_frames:
            self.cached_hold_frame = frame.copy()
        return frame

    def render_frame_bytes(self, frame_idx: int) -> bytes | memoryview:
        if frame_idx < self.main_frames:
            frame = self.render_main_frame(frame_idx)
        else:
            frame = self.render_end_frame(frame_idx - self.main_frames)

        if isinstance(frame, np.ndarray):
            return memoryview(np.ascontiguousarray(frame)).cast("B")
        return frame.tobytes("raw", "RGB")
