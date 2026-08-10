# -*- coding: utf-8 -*-
"""
核心資料結構 (RideData)、GPX 軌跡解析與地理座標數學計算。
"""

from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path

import gpxpy
import numpy as np
from matplotlib.colors import Normalize

from gpx_renderer import config


@dataclass
class RideData:
    xs: np.ndarray
    ys: np.ndarray
    eles: np.ndarray
    distances: np.ndarray
    speeds: np.ndarray
    elevation_gain: np.ndarray
    total_seconds: float | None
    route_center_x: float
    route_center_y: float
    fit_margin: float
    speed_norm: Normalize
    gpx_times: list | None = None

    @property
    def total_points(self) -> int:
        return len(self.xs)


def latlon_to_mercator(lat: np.ndarray, lon: np.ndarray):
    """WGS84 -> Web Mercator EPSG:3857。"""
    r = 6378137.0
    lon_rad = np.radians(lon)
    lat_rad = np.radians(np.clip(lat, -85.05112878, 85.05112878))
    x = r * lon_rad
    y = r * np.log(np.tan(np.pi / 4.0 + lat_rad / 2.0))
    return x, y


def ease_smoothstep(p: float) -> float:
    p = min(max(float(p), 0.0), 1.0)
    return p * p * (3.0 - 2.0 * p)


def haversine_steps_m(lats: np.ndarray, lons: np.ndarray) -> np.ndarray:
    """
    向量化 Haversine，相較 geopy 逐點呼叫快很多。
    對騎乘 GPX 的總距離估算足夠精確，且只在初始化執行一次。
    """
    lat1 = np.radians(lats[:-1])
    lat2 = np.radians(lats[1:])
    dlat = lat2 - lat1
    dlon = np.radians(lons[1:] - lons[:-1])

    a = np.sin(dlat / 2.0) ** 2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlon / 2.0) ** 2
    c = 2.0 * np.arctan2(np.sqrt(a), np.sqrt(np.maximum(1.0 - a, 0.0)))

    out = np.zeros(len(lats), dtype=np.float64)
    out[1:] = 6371008.8 * c
    return out


def quick_gpx_distance_km(path: str | Path) -> float:
    """只讀取 GPX 經緯度並快速估算總距離，供 GUI 自動計算主動畫秒數。"""
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"找不到 GPX：{path.resolve()}")

    with path.open("r", encoding="utf-8") as f:
        gpx = gpxpy.parse(f)

    lats = []
    lons = []
    for track in gpx.tracks:
        for segment in track.segments:
            for pt in segment.points:
                lats.append(float(pt.latitude))
                lons.append(float(pt.longitude))

    if len(lats) < 2:
        raise ValueError("GPX 軌跡點數量不足，至少需要 2 點。")

    lats_arr = np.asarray(lats, dtype=np.float64)
    lons_arr = np.asarray(lons, dtype=np.float64)
    return float(np.sum(haversine_steps_m(lats_arr, lons_arr)) / 1000.0)


def auto_duration_seconds(distance_km: float, seconds_per_100km: float) -> float:
    rate = max(float(seconds_per_100km), 0.01)
    return max(float(config.AUTO_DURATION_MIN_SECONDS), float(distance_km) * rate / 100.0)


def format_seconds_human(seconds: float) -> str:
    total = max(0, int(round(seconds)))
    minutes, sec = divmod(total, 60)
    hours, minutes = divmod(minutes, 60)
    if hours:
        return f"{hours}h {minutes:02d}m {sec:02d}s"
    return f"{minutes}m {sec:02d}s"


def load_gpx(path: str | Path) -> RideData:
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"找不到 GPX：{path.resolve()}")

    with path.open("r", encoding="utf-8") as f:
        gpx = gpxpy.parse(f)

    points = []
    for track in gpx.tracks:
        for segment in track.segments:
            for pt in segment.points:
                points.append((
                    float(pt.latitude),
                    float(pt.longitude),
                    float(pt.elevation) if pt.elevation is not None else 0.0,
                    pt.time,
                ))

    if len(points) < 2:
        raise ValueError("GPX 軌跡點數量不足，至少需要 2 點。")

    lats = np.asarray([p[0] for p in points], dtype=np.float64)
    lons = np.asarray([p[1] for p in points], dtype=np.float64)
    eles = np.asarray([p[2] for p in points], dtype=np.float64)
    times = [p[3] for p in points]

    xs, ys = latlon_to_mercator(lats, lons)

    step_m = haversine_steps_m(lats, lons)
    distances = np.cumsum(step_m) / 1000.0

    speeds = np.zeros(len(points), dtype=np.float64)
    for i in range(1, len(points)):
        t0 = times[i - 1]
        t1 = times[i]
        if t0 is not None and t1 is not None:
            dt = (t1 - t0).total_seconds()
            if dt > 0:
                speeds[i] = (step_m[i] / dt) * 3.6

    if len(speeds) >= 5:
        speeds = np.convolve(speeds, np.ones(5) / 5.0, mode="same")

    ele_diff = np.diff(eles, prepend=eles[0])
    elevation_gain = np.cumsum(np.maximum(ele_diff, 0.0))

    if times[0] is not None and times[-1] is not None:
        total_seconds = (times[-1] - times[0]).total_seconds()
    else:
        total_seconds = None

    route_center_x = float((xs.max() + xs.min()) / 2.0)
    route_center_y = float((ys.max() + ys.min()) / 2.0)
    route_half_w = float((xs.max() - xs.min()) / 2.0)
    route_half_h = float((ys.max() - ys.min()) / 2.0)
    fit_margin = max(
        config.VIEW_MARGIN,
        max(route_half_w, route_half_h) * (1.0 + config.END_PADDING_FRAC),
        1.0,
    )

    vmin = float(np.percentile(speeds, 5))
    vmax = float(np.percentile(speeds, 95))
    if not np.isfinite(vmin):
        vmin = 0.0
    if not np.isfinite(vmax) or vmax <= vmin:
        vmax = vmin + 1.0

    return RideData(
        xs=xs,
        ys=ys,
        eles=eles,
        distances=distances,
        speeds=speeds,
        elevation_gain=elevation_gain,
        total_seconds=total_seconds,
        route_center_x=route_center_x,
        route_center_y=route_center_y,
        fit_margin=fit_margin,
        speed_norm=Normalize(vmin=vmin, vmax=vmax, clip=True),
        gpx_times=times,
    )


def compute_end_route_view(data: RideData):
    """計算結尾 framing，讓完整路線落在下方 Dashboard 之外的安全區域。"""
    route_min_x = float(np.min(data.xs))
    route_max_x = float(np.max(data.xs))
    route_min_y = float(np.min(data.ys))
    route_max_y = float(np.max(data.ys))
    half_w = max((route_max_x - route_min_x) * 0.5, 1.0)
    half_h = max((route_max_y - route_min_y) * 0.5, 1.0)

    safe_w = max(config.END_ROUTE_SAFE_RIGHT_FRAC - config.END_ROUTE_SAFE_LEFT_FRAC, 0.10)
    safe_h = max(config.END_ROUTE_SAFE_BOTTOM_FRAC - config.END_ROUTE_SAFE_TOP_FRAC, 0.10)

    margin = max(
        config.VIEW_MARGIN,
        half_w / safe_w,
        half_h / safe_h,
        1.0,
    ) * config.END_ROUTE_EXTRA_PADDING

    target_px_center_x = (config.END_ROUTE_SAFE_LEFT_FRAC + config.END_ROUTE_SAFE_RIGHT_FRAC) * 0.5
    target_px_center_y = (config.END_ROUTE_SAFE_TOP_FRAC + config.END_ROUTE_SAFE_BOTTOM_FRAC) * 0.5

    view_x = data.route_center_x - 2.0 * margin * (target_px_center_x - 0.5)
    view_y = data.route_center_y + 2.0 * margin * (target_px_center_y - 0.5)
    return float(view_x), float(view_y), float(margin)
