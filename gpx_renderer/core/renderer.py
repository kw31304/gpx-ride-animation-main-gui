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

        self.main_indices = np.linspace(
            0,
            self.d.total_points - 1,
            self.main_frames,
        ).astype(np.int32)
        self.camera_x, self.camera_y = self._precompute_camera()

        self.use_cv2 = bool(config.USE_OPENCV_FAST_PATH and HAVE_CV2)
        if not self.tile_cache_enabled:
            print("[INFO] Worker tile cache：OFF（避開 contextily/joblib 多程序 cache contention）")
        if self.use_cv2:
            print("[INFO] Renderer fast path：OpenCV warpAffine + local high-res tile chunks")
        elif config.USE_OPENCV_FAST_PATH:
            print("[INFO] 未安裝 OpenCV，鏡頭裁切改用 Pillow fallback。可執行：pip install opencv-python")

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

        ui_scale = max(0.78, min(1.8, min(config.FRAME_WIDTH, config.FRAME_HEIGHT) / 1000.0))
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

        self.hud_update_every = max(1, int(round(self.fps / max(1, config.HUD_UPDATE_HZ))))
        self.cached_hud: Image.Image | None = None
        self.cached_hud_idx = -1

        self._init_minimap()
        self._init_elevation()
        self._init_summary()

    # ---------- geometry ----------
    def _precompute_camera(self):
        tx = self.d.xs[self.main_indices]
        ty = self.d.ys[self.main_indices]
        cx_arr = np.empty(self.main_frames, dtype=np.float64)
        cy_arr = np.empty(self.main_frames, dtype=np.float64)
        cx_arr[0] = tx[0]
        cy_arr[0] = ty[0]
        a = self.camera_alpha

        for i in range(1, self.main_frames):
            cx_arr[i] = cx_arr[i - 1] + (tx[i] - cx_arr[i - 1]) * a
            cy_arr[i] = cy_arr[i - 1] + (ty[i] - cy_arr[i - 1]) * a
        return cx_arr, cy_arr

    def _world_to_frame_px(self, x: float, y: float, view_x: float, view_y: float, margin: float):
        left = view_x - margin
        top = view_y + margin
        px = (x - left) / (2.0 * margin) * config.FRAME_WIDTH
        py = (top - y) / (2.0 * margin) * config.FRAME_HEIGHT
        return int(round(px)), int(round(py))

    def _build_track_colors(self):
        cmap = matplotlib.colormaps[config.TRACK_CMAP]
        normalized = self.d.speed_norm(self.d.speeds[1:])
        rgba = cmap(normalized, bytes=True)
        return [tuple(map(int, c[:3])) for c in rgba]

    def _crop_raster(self, rm: RasterMap, view_x: float, view_y: float, margin: float) -> Image.Image:
        left_world = view_x - margin
        right_world = view_x + margin
        top_world = view_y + margin
        bottom_world = view_y - margin

        left_px = (left_world - rm.west) / (rm.east - rm.west) * (rm.width - 1)
        right_px = (right_world - rm.west) / (rm.east - rm.west) * (rm.width - 1)
        top_px = (rm.north - top_world) / (rm.north - rm.south) * (rm.height - 1)
        bottom_px = (rm.north - bottom_world) / (rm.north - rm.south) * (rm.height - 1)

        if self.use_cv2:
            src_w = max(float(right_px - left_px), 1e-6)
            src_h = max(float(bottom_px - top_px), 1e-6)
            sx = config.FRAME_WIDTH / src_w
            sy = config.FRAME_HEIGHT / src_h
            matrix = np.array(
                [[sx, 0.0, -left_px * sx], [0.0, sy, -top_px * sy]],
                dtype=np.float32,
            )
            out = cv2.warpAffine(
                rm.np_image,
                matrix,
                (config.FRAME_WIDTH, config.FRAME_HEIGHT),
                flags=cv2.INTER_LINEAR,
                borderMode=cv2.BORDER_CONSTANT,
                borderValue=(17, 17, 17),
            )
            return Image.fromarray(out)

        return rm.image.transform(
            (config.FRAME_WIDTH, config.FRAME_HEIGHT),
            Image.Transform.EXTENT,
            (left_px, top_px, right_px, bottom_px),
            resample=config.MAP_RESAMPLE,
            fillcolor=(17, 17, 17),
        )

    def _draw_visible_track(self, frame: Image.Image, idx: int, view_x: float, view_y: float, margin: float) -> Image.Image:
        seg_count = min(max(int(idx), 0), len(self.seg_x0))
        if seg_count <= 0:
            return frame

        left, right = view_x - margin, view_x + margin
        bottom, top = view_y - margin, view_y + margin
        mask = (
            (self.seg_max_x[:seg_count] >= left)
            & (self.seg_min_x[:seg_count] <= right)
            & (self.seg_max_y[:seg_count] >= bottom)
            & (self.seg_min_y[:seg_count] <= top)
        )
        ids = np.flatnonzero(mask)
        if ids.size == 0:
            return frame

        sx = config.FRAME_WIDTH / (2.0 * margin)
        sy = config.FRAME_HEIGHT / (2.0 * margin)

        if self.use_cv2:
            arr = np.asarray(frame, dtype=np.uint8).copy()
            x0 = np.rint((self.seg_x0[ids] - left) * sx).astype(np.int32)
            x1 = np.rint((self.seg_x1[ids] - left) * sx).astype(np.int32)
            y0 = np.rint((top - self.seg_y0[ids]) * sy).astype(np.int32)
            y1 = np.rint((top - self.seg_y1[ids]) * sy).astype(np.int32)
            for j, seg_id in enumerate(ids):
                cv2.line(
                    arr,
                    (int(x0[j]), int(y0[j])),
                    (int(x1[j]), int(y1[j])),
                    self.track_colors[int(seg_id)],
                    thickness=5,
                    lineType=cv2.LINE_AA,
                )
            return Image.fromarray(arr)

        draw = ImageDraw.Draw(frame)
        for seg_id in ids:
            i = int(seg_id)
            p0 = self._world_to_frame_px(float(self.seg_x0[i]), float(self.seg_y0[i]), view_x, view_y, margin)
            p1 = self._world_to_frame_px(float(self.seg_x1[i]), float(self.seg_y1[i]), view_x, view_y, margin)
            draw.line([p0, p1], fill=self.track_colors[i], width=5)
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
        self.mini_w = int(round(config.FRAME_WIDTH * 0.245))
        self.mini_h = int(round(config.FRAME_HEIGHT * 0.245))
        self.mini_x = int(round(config.FRAME_WIDTH * 0.715))
        self.mini_y = int(round(config.FRAME_HEIGHT * 0.055)) + self.mini_h
        self.mini_pad = max(12, int(round(15 * self.ui_scale)))
        label_h = max(18, int(round(22 * self.ui_scale)))

        span_x = max(float(np.ptp(d.xs)), 1.0)
        span_y = max(float(np.ptp(d.ys)), 1.0)
        pad_x = span_x * 0.10
        pad_y = span_y * 0.10
        self.mini_west = float(d.xs.min() - pad_x)
        self.mini_east = float(d.xs.max() + pad_x)
        self.mini_south = float(d.ys.min() - pad_y)
        self.mini_north = float(d.ys.max() + pad_y)

        left = self.mini_pad
        right = self.mini_w - self.mini_pad
        top = self.mini_pad + label_h
        bottom = self.mini_h - self.mini_pad
        self.mini_px_x = left + (d.xs - self.mini_west) / (self.mini_east - self.mini_west) * max(right - left, 1)
        self.mini_px_y = top + (self.mini_north - d.ys) / (self.mini_north - self.mini_south) * max(bottom - top, 1)

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
        self.elev_w = int(round(config.FRAME_WIDTH * 0.56))
        self.elev_h = int(round(config.FRAME_HEIGHT * 0.155))
        self.elev_x = int(round(config.FRAME_WIDTH * 0.045))
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

    # ---------- frame render ----------
    def render_main_frame(self, frame_idx: int) -> Image.Image:
        i = min(max(int(frame_idx), 0), self.main_frames - 1)
        idx = int(self.main_indices[i])
        d = self.d

        view_x = float(self.camera_x[i])
        view_y = float(self.camera_y[i])

        local_rm = self.local_maps.get(view_x, view_y, idx)
        frame = self._crop_raster(local_rm, view_x, view_y, config.VIEW_MARGIN)

        draw = ImageDraw.Draw(frame)
        px, py = self._world_to_frame_px(float(d.xs[idx]), float(d.ys[idx]), view_x, view_y, config.VIEW_MARGIN)
        self._draw_marker(draw, px, py, config.WHITE, config.ORANGE, r=7, outline_w=3)

        hud = self._get_hud(i, idx)
        frame.paste(hud, (int(config.FRAME_WIDTH * 0.05), int(config.FRAME_HEIGHT * 0.08)), hud)

        mini = self._compose_minimap(idx)
        frame.paste(mini, (self.mini_x, self.mini_y - self.mini_h), mini)

        elev = self._compose_elevation(idx)
        frame.paste(elev, (self.elev_x, self.elev_y), elev)
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
        end_x, end_y, end_margin = compute_end_route_view(d)
        view_x = start_x + (end_x - start_x) * eased
        view_y = start_y + (end_y - start_y) * eased
        margin = config.VIEW_MARGIN + (end_margin - config.VIEW_MARGIN) * eased

        if self.rm is None:
            raise RuntimeError("render_end_frame 需要 overview_map。")
        frame = self._crop_raster(self.rm, view_x, view_y, margin)
        frame = self._draw_visible_track(frame, d.total_points - 1, view_x, view_y, margin)
        draw = ImageDraw.Draw(frame)

        sx, sy = self._world_to_frame_px(float(d.xs[0]), float(d.ys[0]), view_x, view_y, margin)
        ex, ey = self._world_to_frame_px(float(d.xs[-1]), float(d.ys[-1]), view_x, view_y, margin)
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
