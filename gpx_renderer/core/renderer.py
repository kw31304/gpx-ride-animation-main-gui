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
            from gpx_renderer.core.media import prepare_thumbnail

            valid_items = [m for m in media_items if m.matched_index >= 0]
            valid_items.sort(key=lambda m: m.matched_index)

            # 群組 (Cluster) 判別：近距離點位或短時間內之相片
            clusters = []
            if valid_items:
                curr_cluster = [valid_items[0]]
                for idx_m in range(1, len(valid_items)):
                    prev_item = curr_cluster[-1]
                    curr_item = valid_items[idx_m]
                    close_gpx = abs(curr_item.matched_index - prev_item.matched_index) <= max(6, int(self.d.total_points * 0.04))
                    close_time = False
                    if curr_item.timestamp and prev_item.timestamp:
                        close_time = abs((curr_item.timestamp.replace(tzinfo=None) - prev_item.timestamp.replace(tzinfo=None)).total_seconds()) <= 15.0

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
            cluster_by_spot = {clus[0].matched_index: clus for clus in clusters}
            cluster_spot_processed = set()

            for k_idx in range(len(spots) - 1):
                s0, s1 = spots[k_idx], spots[k_idx + 1]
                seg_frames = max(1, int(round(base_ride_frames * (span_weights[k_idx] / total_weight))))
                endpoint_flag = (k_idx == len(spots) - 2)

                if use_real:
                    try:
                        times_sub = self.d.gpx_times[s0:s1 + 1]
                        tb = times_sub[0].replace(tzinfo=None)
                        elapsed_sub = np.array([(t.replace(tzinfo=None) - tb).total_seconds() for t in times_sub], dtype=np.float64)
                        tot_t = elapsed_sub[-1]
                        if tot_t > 0:
                            t_targets = np.linspace(0, tot_t, seg_frames, endpoint=endpoint_flag)
                            pts_sub = np.arange(s0, s1 + 1)
                            seg_indices = np.interp(t_targets, elapsed_sub, pts_sub).astype(np.int32)
                        else:
                            d0, d1 = float(self.d.distances[s0]), float(self.d.distances[s1])
                            target_dists = np.linspace(d0, d1, seg_frames, endpoint=endpoint_flag)
                            seg_indices = np.interp(target_dists, self.d.distances[s0:s1 + 1], np.arange(s0, s1 + 1)).astype(np.int32)
                    except Exception:
                        d0, d1 = float(self.d.distances[s0]), float(self.d.distances[s1])
                        target_dists = np.linspace(d0, d1, seg_frames, endpoint=endpoint_flag)
                        seg_indices = np.interp(target_dists, self.d.distances[s0:s1 + 1], np.arange(s0, s1 + 1)).astype(np.int32)
                else:
                    d0, d1 = float(self.d.distances[s0]), float(self.d.distances[s1])
                    target_dists = np.linspace(d0, d1, seg_frames, endpoint=endpoint_flag)
                    seg_indices = np.interp(target_dists, self.d.distances[s0:s1 + 1], np.arange(s0, s1 + 1)).astype(np.int32)

                if main_idx_list and len(seg_indices) > 0 and seg_indices[0] == main_idx_list[-1]:
                    seg_indices = seg_indices[1:]

                for pt_idx in seg_indices:
                    pt_val = int(pt_idx)
                    main_idx_list.append(pt_val)

                    if pt_val in cluster_by_spot and pt_val not in cluster_spot_processed:
                        cluster_spot_processed.add(pt_val)
                        clus = cluster_by_spot[pt_val]

                        k_count = len(clus)
                        item_duration_sec = float(config.MEDIA_POPUP_DURATION) + max(0.0, (k_count - 1) * 1.5)
                        item_dur_frames = max(1, int(round(item_duration_sec * self.fps)))

                        for item in clus:
                            start_f = len(main_idx_list) - 1
                            end_f = start_f + item_dur_frames

                            if item.thumbnail is None:
                                item.thumbnail = prepare_thumbnail(item.file_path, max_w=max_thumb_w, max_h=max_thumb_h)

                            if item.thumbnail is not None:
                                self.media_popups.append({
                                    "item": item,
                                    "start_frame": start_f,
                                    "end_frame": end_f,
                                    "fade_frames": fade_frames,
                                })

                            main_idx_list.extend([pt_val] * item_dur_frames)

            self.main_indices = np.array(main_idx_list, dtype=np.int32)
            self.main_frames = len(self.main_indices)
        else:
            self.main_frames = max(1, int(round(self.video_duration * self.fps)))
            use_real = bool(config.USE_REAL_SPEED and self.d.gpx_times and len(self.d.gpx_times) == self.d.total_points and self.d.gpx_times[0] is not None)
            if use_real:
                try:
                    tb = self.d.gpx_times[0].replace(tzinfo=None)
                    elapsed = np.array([(t.replace(tzinfo=None) - tb).total_seconds() for t in self.d.gpx_times], dtype=np.float64)
                    tot_t = elapsed[-1]
                    if tot_t > 0:
                        t_targets = np.linspace(0, tot_t, self.main_frames)
                        self.main_indices = np.interp(t_targets, elapsed, np.arange(self.d.total_points)).astype(np.int32)
                    else:
                        d0, d1 = float(self.d.distances[0]), float(self.d.distances[-1])
                        target_dists = np.linspace(d0, d1, self.main_frames)
                        self.main_indices = np.interp(target_dists, self.d.distances, np.arange(self.d.total_points)).astype(np.int32)
                except Exception:
                    d0, d1 = float(self.d.distances[0]), float(self.d.distances[-1])
                    target_dists = np.linspace(d0, d1, self.main_frames)
                    self.main_indices = np.interp(target_dists, self.d.distances, np.arange(self.d.total_points)).astype(np.int32)
            else:
                d0, d1 = float(self.d.distances[0]), float(self.d.distances[-1])
                target_dists = np.linspace(d0, d1, self.main_frames)
                self.main_indices = np.interp(target_dists, self.d.distances, np.arange(self.d.total_points)).astype(np.int32)

        self.zoom_frames = max(0, int(round(self.zoom_out_duration * self.fps)))
        self.hold_frames = max(0, int(round(self.end_hold_duration * self.fps)))
        self.total_frames = self.main_frames + self.zoom_frames + self.hold_frames
        self.camera_x, self.camera_y, self.camera_h = self._precompute_camera()

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
        self.font_hud_kicker = load_font(max(10, int(round(11 * ui_scale))), bold=True)
        self.font_hud_speed = load_font(max(28, int(round(43 * ui_scale))), bold=True)
        self.font_hud_unit = load_font(max(11, int(round(14 * ui_scale))), bold=True)
        self.font_hud_label = load_font(max(9, int(round(10 * ui_scale))), bold=True)
        self.font_hud_metric = load_font(max(13, int(round(18 * ui_scale))), bold=True)
        self.font_panel_label = load_font(max(9, int(round(10 * ui_scale))), bold=True)

        self.font_summary_title = load_font(max(22, int(round(30 * ui_scale))), bold=True)
        self.font_summary_label = load_font(max(9, int(round(11 * ui_scale))), bold=True)
        self.font_summary_value = load_font(max(20, int(round(29 * ui_scale))), bold=True)
        self.font_summary_unit = load_font(max(10, int(round(12 * ui_scale))), bold=True)
        self.font_caption = load_font(max(18, int(round(25 * ui_scale))), bold=True)

        self.hud_update_every = max(1, int(round(self.fps / max(1, config.HUD_UPDATE_HZ))))
        self.cached_hud: Image.Image | None = None
        self.cached_hud_idx = -1

        self._init_minimap()
        self._init_elevation()
        self._init_summary()
        self._terrain_out_buffer = np.full((config.FRAME_HEIGHT, config.FRAME_WIDTH, 3), 17, dtype=np.uint8)

    # ---------- geometry ----------
    def _precompute_camera(self):
        tx = self.d.xs[self.main_indices]
        ty = self.d.ys[self.main_indices]
        cx_arr = np.empty(self.main_frames, dtype=np.float64)
        cy_arr = np.empty(self.main_frames, dtype=np.float64)
        ch_arr = np.empty(self.main_frames, dtype=np.float64)

        cx_arr[0] = tx[0]
        cy_arr[0] = ty[0]
        a = self.camera_alpha

        for i in range(1, self.main_frames):
            cx_arr[i] = cx_arr[i - 1] + (tx[i] - cx_arr[i - 1]) * a
            cy_arr[i] = cy_arr[i - 1] + (ty[i] - cy_arr[i - 1]) * a

        if getattr(config, "CAMERA_MODE", "North-Up") in ("Heading-Up", "3D-Terrain") and self.d.headings is not None and len(self.d.headings) > 0:
            target_h = self.d.headings[self.main_indices]

            rot_base_alpha = min(max(getattr(config, "CAMERA_ROTATION_SMOOTH", 0.025), 1e-6), 1.0)
            rot_alpha = 1.0 - (1.0 - rot_base_alpha) ** (60.0 / self.fps)

            max_speed_deg = float(getattr(config, "CAMERA_MAX_ROTATION_SPEED_DEG", 25.0))
            max_step_rad = math.radians(max_speed_deg) / float(self.fps)
            deadband_rad = math.radians(1.5)

            ch_arr[0] = float(target_h[0])

            for i in range(1, self.main_frames):
                prev_angle = float(ch_arr[i - 1])
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

        return cx_arr, cy_arr, ch_arr

    def _world_to_frame_px(self, x: float, y: float, view_x: float, view_y: float, margin: float, heading_rad: float = math.pi / 2.0, z: float = 0.0):
        if getattr(config, "CAMERA_MODE", "North-Up") == "3D-Terrain":
            from gpx_renderer.core.terrain_3d import Camera3D, project_3d_points
            pitch_deg = float(getattr(config, "CAMERA_PITCH_DEG", 50.0))
            exaggeration = float(getattr(config, "ELEVATION_EXAGGERATION", 1.5))
            margin_3d = margin * 1.8
            cam_alt = margin_3d * 0.8
            cam = Camera3D(
                x=view_x, y=view_y, z=(z * exaggeration) + cam_alt,
                heading_rad=heading_rad, pitch_deg=pitch_deg, exaggeration=exaggeration
            )
            px_arr, py_arr, _ = project_3d_points(np.array([x]), np.array([y]), np.array([z]), cam, margin_3d)
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
        cmap = matplotlib.colormaps[config.TRACK_CMAP]
        normalized = self.d.speed_norm(self.d.speeds[1:])
        rgba = cmap(normalized, bytes=True)
        return [tuple(map(int, c[:3])) for c in rgba]

    def _crop_raster(self, rm: RasterMap, view_x: float, view_y: float, margin: float, heading_rad: float = math.pi / 2.0) -> Image.Image:
        if getattr(config, "CAMERA_MODE", "North-Up") == "3D-Terrain":
            from gpx_renderer.core.terrain_3d import render_3d_terrain_frame
            pitch_deg = float(getattr(config, "CAMERA_PITCH_DEG", 50.0))
            exaggeration = float(getattr(config, "ELEVATION_EXAGGERATION", 1.5))
            margin_3d = margin * 1.8
            return render_3d_terrain_frame(
                rm, view_x, view_y, margin_3d, heading_rad,
                pitch_deg=pitch_deg, exaggeration=exaggeration,
                out_buffer=self._terrain_out_buffer,
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
                borderValue=(17, 17, 17),
            )
            return Image.fromarray(out)

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
            fillcolor=(17, 17, 17),
        )

    def _draw_visible_track(self, frame: Image.Image, idx: int, view_x: float, view_y: float, margin: float, heading_rad: float = math.pi / 2.0) -> Image.Image:
        if getattr(config, "CAMERA_MODE", "North-Up") == "3D-Terrain":
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
            arr = np.asarray(frame, dtype=np.uint8).copy()
            for j, seg_id in enumerate(ids):
                cv2.line(
                    arr,
                    (int(px0[j]), int(py0[j])),
                    (int(px1[j]), int(py1[j])),
                    self.track_colors[int(seg_id)],
                    thickness=5,
                    lineType=cv2.LINE_AA,
                )
            return Image.fromarray(arr)

        draw = ImageDraw.Draw(frame)
        for j, seg_id in enumerate(ids):
            i = int(seg_id)
            draw.line([(int(px0[j]), int(py0[j])), (int(px1[j]), int(py1[j]))], fill=self.track_colors[i], width=5)
        return frame

    # ---------- HUD ----------
    def _build_hud(self, idx: int) -> Image.Image:
        d = self.d
        s = self.ui_scale
        w = max(300, int(round(config.FRAME_WIDTH * 0.355)))
        h = max(142, int(round(config.FRAME_HEIGHT * 0.175)))
        hud = Image.new("RGBA", (w + int(10 * s), h + int(12 * s)), (0, 0, 0, 0))
        draw = ImageDraw.Draw(hud)

        radius = max(16, int(round(22 * s)))
        draw.rounded_rectangle(
            (0, 0, w - 1, h - 1),
            radius=radius,
            fill=(9, 13, 18, 205),
            outline=(255, 255, 255, 36),
            width=max(1, int(round(s))),
        )

        pad = int(round(18 * s))
        draw.text(
            (pad, int(16*s)),
            "SPEED",
            font=self.font_hud_kicker,
            fill=(205, 212, 220, 230),
        )

        speed_text = f"{d.speeds[idx]:.1f}"
        speed_y = int(39 * s)
        draw.text((pad, speed_y), speed_text, font=self.font_hud_speed, fill=(250, 252, 255, 255))
        sb = draw.textbbox((pad, speed_y), speed_text, font=self.font_hud_speed)
        unit_x = sb[2] + int(8 * s)
        unit_y = sb[3] - int(20 * s)
        draw.text((unit_x, unit_y), "km/h", font=self.font_hud_unit, fill=(170, 180, 190, 235))

        divider_y = int(round(h * 0.66))
        draw.line(
            (pad, divider_y, w - pad, divider_y),
            fill=(255, 255, 255, 25),
            width=max(1, int(round(s))),
        )
        metrics = [
            ("DISTANCE", f"{d.distances[idx]:.1f}", "km"),
            ("ELEVATION", f"{d.eles[idx]:.0f}", "m"),
            ("CLIMB", f"+{d.elevation_gain[idx]:.0f}", "m"),
        ]
        inner_w = w - pad * 2
        col_w = inner_w / 3.0
        label_y = divider_y + int(10 * s)
        value_y = label_y + int(15 * s)
        for i, (label, value, unit) in enumerate(metrics):
            x = int(round(pad + i * col_w))
            if i:
                sep_x = int(round(pad + i * col_w - 8 * s))
                draw.line(
                    (sep_x, label_y, sep_x, h - int(12*s)),
                    fill=(255, 255, 255, 20),
                    width=max(1, int(round(s))),
                )
            draw.text((x, label_y), label, font=self.font_hud_label, fill=(134, 145, 156, 235))
            draw.text((x, value_y), value, font=self.font_hud_metric, fill=(245, 247, 250, 255))
            vb = draw.textbbox((x, value_y), value, font=self.font_hud_metric)
            draw.text(
                (vb[2] + int(4*s), value_y + int(4*s)),
                unit,
                font=self.font_hud_label,
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

        self.mini_w = max(220, int(round(280 * s)))
        self.mini_h = max(150, int(round(180 * s)))
        margin_right = max(16, int(round(20 * s)))
        margin_top = max(16, int(round(20 * s)))
        self.mini_x = config.FRAME_WIDTH - self.mini_w - margin_right
        self.mini_y = margin_top + self.mini_h

        self.mini_pad = max(10, int(round(14 * s)))
        label_h = max(16, int(round(20 * s)))

        avail_w = max(self.mini_w - 2 * self.mini_pad, 1)
        avail_h = max(self.mini_h - 2 * self.mini_pad - label_h, 1)

        min_x, max_x = float(d.xs.min()), float(d.xs.max())
        min_y, max_y = float(d.ys.min()), float(d.ys.max())
        center_x = (min_x + max_x) * 0.5
        center_y = (min_y + max_y) * 0.5

        route_w = max(max_x - min_x, 1.0)
        route_h = max(max_y - min_y, 1.0)

        scale_x = (avail_w * 0.85) / route_w
        scale_y = (avail_h * 0.85) / route_h
        scale = min(scale_x, scale_y)

        center_px_x = self.mini_pad + avail_w * 0.5
        center_px_y = self.mini_pad + label_h + avail_h * 0.5

        self.mini_px_x = center_px_x + (d.xs - center_x) * scale
        self.mini_px_y = center_px_y - (d.ys - center_y) * scale

        self.mini_layer = Image.new("RGBA", (self.mini_w, self.mini_h), (0, 0, 0, 0))
        draw = ImageDraw.Draw(self.mini_layer)
        radius = max(14, int(round(20 * self.ui_scale)))
        draw.rounded_rectangle(
            (0, 0, self.mini_w - 1, self.mini_h - 1),
            radius=radius,
            fill=(9, 13, 18, 172),
            outline=(255, 255, 255, 30),
            width=max(1, int(round(self.ui_scale))),
        )
        draw.text(
            (self.mini_pad, self.mini_pad - int(2*self.ui_scale)),
            "ROUTE",
            font=self.font_panel_label,
            fill=(172, 182, 192, 235),
        )

        full_pts = [(int(round(x)), int(round(y))) for x, y in zip(self.mini_px_x, self.mini_px_y)]
        if len(full_pts) >= 2:
            draw.line(full_pts, fill=(255, 255, 255, 72), width=max(1, int(round(2*self.ui_scale))))

        self.mini_progress_layer = self.mini_layer.copy()
        self.mini_draw = ImageDraw.Draw(self.mini_progress_layer)
        self.mini_last_idx = 0

    def _advance_minimap(self, idx: int):
        idx = min(max(int(idx), 0), self.d.total_points - 1)
        if idx <= self.mini_last_idx:
            return
        for seg_end in range(self.mini_last_idx + 1, idx + 1):
            p0 = (int(round(self.mini_px_x[seg_end - 1])), int(round(self.mini_px_y[seg_end - 1])))
            p1 = (int(round(self.mini_px_x[seg_end])), int(round(self.mini_px_y[seg_end])))
            self.mini_draw.line([p0, p1], fill=config.ORANGE + (255,), width=max(2, int(round(3*self.ui_scale))))
        self.mini_last_idx = idx

    def _compose_minimap(self, idx: int) -> Image.Image:
        self._advance_minimap(idx)
        mini = self.mini_progress_layer.copy()
        draw = ImageDraw.Draw(mini)
        x = int(round(self.mini_px_x[idx]))
        y = int(round(self.mini_px_y[idx]))
        r = max(4, int(round(5 * self.ui_scale)))
        draw.ellipse((x-r-2, y-r-2, x+r+2, y+r+2), fill=(255, 255, 255, 235))
        draw.ellipse((x-r, y-r, x+r, y+r), fill=config.ORANGE + (255,))
        return mini

    # ---------- elevation ----------
    def _init_elevation(self):
        d = self.d
        self.elev_x = int(round(config.FRAME_WIDTH * 0.045))
        self.elev_w = int(round(config.FRAME_WIDTH * 0.91))
        self.elev_h = int(round(config.FRAME_HEIGHT * 0.155))
        self.elev_y = int(round(config.FRAME_HEIGHT * 0.80))
        pad = max(12, int(round(15 * self.ui_scale)))
        label_h = max(18, int(round(22 * self.ui_scale)))

        xmin = float(d.distances.min())
        xmax = max(float(d.distances.max()), xmin + 0.001)
        ymin = float(d.eles.min()) - 5.0
        ymax = float(d.eles.max()) + 5.0
        if ymax <= ymin:
            ymax = ymin + 10.0

        left, right = pad, self.elev_w - pad
        top, bottom = pad + label_h, self.elev_h - pad
        ex = left + (d.distances - xmin) / (xmax - xmin) * max(right-left, 1)
        ey = top + (ymax - d.eles) / (ymax - ymin) * max(bottom-top, 1)
        self.elev_px_x = ex
        self.elev_px_y = ey
        full_pts = [(int(round(x)), int(round(y))) for x, y in zip(ex, ey)]

        self.elev_base = Image.new("RGBA", (self.elev_w, self.elev_h), (0, 0, 0, 0))
        bdraw = ImageDraw.Draw(self.elev_base)
        radius = max(14, int(round(20 * self.ui_scale)))
        bdraw.rounded_rectangle(
            (0, 0, self.elev_w - 1, self.elev_h - 1),
            radius=radius,
            fill=(9, 13, 18, 172),
            outline=(255, 255, 255, 30),
            width=max(1, int(round(self.ui_scale))),
        )
        bdraw.text((pad, pad-int(2*self.ui_scale)), "ELEVATION", font=self.font_panel_label, fill=(172, 182, 192, 235))
        if len(full_pts) >= 2:
            bdraw.line(full_pts, fill=(255, 255, 255, 52), width=max(1, int(round(2*self.ui_scale))))

        self.elev_progress_full = Image.new("RGBA", (self.elev_w, self.elev_h), (0, 0, 0, 0))
        pdraw = ImageDraw.Draw(self.elev_progress_full)
        if len(full_pts) >= 2:
            poly = [(full_pts[0][0], bottom)] + full_pts + [(full_pts[-1][0], bottom)]
            pdraw.polygon(poly, fill=config.ORANGE + (48,))
            pdraw.line(full_pts, fill=config.ORANGE + (235,), width=max(2, int(round(2*self.ui_scale))))

    def _compose_elevation(self, idx: int) -> Image.Image:
        panel = self.elev_base.copy()
        reveal_x = int(round(self.elev_px_x[idx]))
        reveal_x = min(max(reveal_x, 0), self.elev_w - 1)
        if reveal_x > 0:
            crop = self.elev_progress_full.crop((0, 0, reveal_x + 1, self.elev_h))
            panel.alpha_composite(crop, (0, 0))
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

    def _draw_media_popups(self, frame: Image.Image, frame_idx: int, view_x: float, view_y: float, margin: float):
        if not self.media_popups:
            return

        for popup in self.media_popups:
            sf = popup["start_frame"]
            ef = popup["end_frame"]
            if not (sf <= frame_idx <= ef):
                continue

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
            thumb = item.thumbnail
            if thumb is None:
                continue

            tw, th = thumb.size

            # 將媒體縮圖卡片固定置於動畫畫面正中央
            cx = (config.FRAME_WIDTH - tw) // 2
            cy = (config.FRAME_HEIGHT - th) // 2

            base = frame.convert("RGBA")
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
                font = self.font_caption
                tb = odraw.textbbox((0, 0), caption_text, font=font)
                text_w = tb[2] - tb[0]
                text_h = tb[3] - tb[1]

                s = self.ui_scale
                pad_x = max(20, int(round(26 * s)))
                pad_y = max(10, int(round(12 * s)))
                gap = max(12, int(round(16 * s)))

                cap_w = text_w + 2 * pad_x
                cap_h = text_h + 2 * pad_y
                cap_x = (config.FRAME_WIDTH - cap_w) // 2
                cap_y = cy + th + gap

                # 若文字標籤超出畫面底部，向上移至照片卡片內部下方
                if cap_y + cap_h > config.FRAME_HEIGHT - int(20 * s):
                    cap_y = cy + th - cap_h - int(12 * s)

                radius = max(12, int(round(16 * s)))
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
            frame.paste(base.convert("RGB"))

    # ---------- frame render ----------
    def render_main_frame(self, frame_idx: int) -> Image.Image:
        i = min(max(int(frame_idx), 0), self.main_frames - 1)
        idx = int(self.main_indices[i])
        d = self.d

        view_x = float(self.camera_x[i])
        view_y = float(self.camera_y[i])
        heading_rad = float(self.camera_h[i])

        local_rm = self.local_maps.get(view_x, view_y, idx)
        frame = self._crop_raster(local_rm, view_x, view_y, config.VIEW_MARGIN, heading_rad=heading_rad)

        draw = ImageDraw.Draw(frame)
        px, py = self._world_to_frame_px(float(d.xs[idx]), float(d.ys[idx]), view_x, view_y, config.VIEW_MARGIN, heading_rad=heading_rad, z=float(d.eles[idx]))
        self._draw_marker(draw, px, py, config.WHITE, config.ORANGE, r=7, outline_w=3)

        hud = self._get_hud(i, idx)
        frame.paste(hud, (int(config.FRAME_WIDTH * 0.05), int(config.FRAME_HEIGHT * 0.08)), hud)

        mini = self._compose_minimap(idx)
        frame.paste(mini, (self.mini_x, self.mini_y - self.mini_h), mini)

        elev = self._compose_elevation(idx)
        frame.paste(elev, (self.elev_x, self.elev_y), elev)

        # 媒體卡片與背景暗化遮罩放置於最頂層 (無法被 HUD / 小地圖 / 海拔圖遮擋)
        self._draw_media_popups(frame, frame_idx, view_x, view_y, config.VIEW_MARGIN)

        return frame

    def render_end_frame(self, end_frame_idx: int) -> Image.Image:
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
        target_h = math.pi / 2.0  # 平滑旋轉回正北朝上

        ux = math.cos(start_h) * (1.0 - eased) + math.cos(target_h) * eased
        uy = math.sin(start_h) * (1.0 - eased) + math.sin(target_h) * eased
        heading_rad = math.atan2(uy, ux)

        end_x, end_y, end_margin = compute_end_route_view(d)
        view_x = start_x + (end_x - start_x) * eased
        view_y = start_y + (end_y - start_y) * eased
        margin = config.VIEW_MARGIN + (end_margin - config.VIEW_MARGIN) * eased

        if self.rm is None:
            raise RuntimeError("render_end_frame 需要 overview_map。")
        frame = self._crop_raster(self.rm, view_x, view_y, margin, heading_rad=heading_rad)
        frame = self._draw_visible_track(frame, d.total_points - 1, view_x, view_y, margin, heading_rad=heading_rad)
        draw = ImageDraw.Draw(frame)

        sx, sy = self._world_to_frame_px(float(d.xs[0]), float(d.ys[0]), view_x, view_y, margin, heading_rad=heading_rad)
        ex, ey = self._world_to_frame_px(float(d.xs[-1]), float(d.ys[-1]), view_x, view_y, margin, heading_rad=heading_rad)
        self._draw_marker(draw, sx, sy, config.GREEN, config.WHITE, r=8, outline_w=2)
        self._draw_marker(draw, ex, ey, config.ORANGE, config.WHITE, r=8, outline_w=2)

        card_alpha = ease_smoothstep((progress - 0.60) / 0.40)
        self._draw_summary(frame, card_alpha)

        if end_frame_idx >= self.zoom_frames:
            self.cached_hold_frame = frame.copy()
        return frame

    def render_frame_bytes(self, frame_idx: int) -> bytes:
        if frame_idx < self.main_frames:
            frame = self.render_main_frame(frame_idx)
        else:
            frame = self.render_end_frame(frame_idx - self.main_frames)

        return frame.tobytes("raw", "RGB")
