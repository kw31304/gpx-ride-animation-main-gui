# -*- coding: utf-8 -*-
"""
相片與影片 EXIF 座標/拍攝時間解析、GPX 時間軸對齊與縮圖快取處理器。
"""

from __future__ import annotations
import os
import sys
import json
import re
import subprocess
from datetime import datetime, timezone, timedelta
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional

import numpy as np
from PIL import Image, ImageOps, ImageDraw, ImageFilter, ExifTags

from gpx_renderer import config
from gpx_renderer.core.data import RideData, latlon_to_mercator, haversine_steps_m


@dataclass
class MediaItem:
    file_path: str
    filename: str
    media_type: str  # "image" or "video"
    timestamp: Optional[datetime] = None  # EXIF 拍攝時間
    has_exif_time: bool = False  # 是否具備真實 EXIF/Metadata 拍攝時間 (非檔案修改時間備援)
    lat: Optional[float] = None
    lon: Optional[float] = None
    mercator_x: Optional[float] = None
    mercator_y: Optional[float] = None
    matched_index: int = -1  # 匹配之 RideData xs/ys 陣列索引
    matched_frame: int = -1  # 匹配之動畫主畫格索引
    matched_km: float = 0.0  # 匹配之實際里程 (km)
    thumbnail: Optional[Image.Image] = None  # 快取縮圖
    caption: str = ""  # 照片下方自訂說明文字
    manual_distance_km: Optional[float] = None  # 手動指定之里程數 (km)

    @property
    def current_km(self) -> float:
        if self.manual_distance_km is not None and self.manual_distance_km >= 0:
            return float(self.manual_distance_km)
        return float(self.matched_km)


def _convert_dms_to_deg(dms, ref: str) -> float:
    def _to_float(x):
        if isinstance(x, (tuple, list)) and len(x) == 2:
            return float(x[0]) / max(float(x[1]), 1e-9)
        return float(x)

    deg = _to_float(dms[0])
    minute = _to_float(dms[1])
    sec = _to_float(dms[2])
    val = deg + (minute / 60.0) + (sec / 3600.0)
    if ref.upper() in ("S", "W"):
        val = -val
    return val


def parse_image_exif(file_path: str | Path) -> tuple[Optional[datetime], Optional[float], Optional[float]]:
    """從相片檔解析 (timestamp, lat, lon)。"""
    path = Path(file_path)
    dt_out = None
    lat_out = None
    lon_out = None

    try:
        with Image.open(path) as img:
            exif_raw = img._getexif()
            if not exif_raw:
                return None, None, None

            exif = {}
            for tag, val in exif_raw.items():
                tag_name = ExifTags.TAGS.get(tag, tag)
                exif[tag_name] = val

            # 解析拍攝時間
            for time_tag in ("DateTimeOriginal", "DateTimeDigitized", "DateTime"):
                if time_tag in exif and isinstance(exif[time_tag], str):
                    try:
                        raw_str = exif[time_tag].strip()
                        dt_out = datetime.strptime(raw_str, "%Y:%m:%d %H:%M:%S")
                        break
                    except Exception:
                        pass

            # 解析 GPSInfo
            gps_info_raw = exif.get("GPSInfo")
            if gps_info_raw and isinstance(gps_info_raw, dict):
                gps = {}
                for t, v in gps_info_raw.items():
                    sub_tag = ExifTags.GPSTAGS.get(t, t)
                    gps[sub_tag] = v

                lat_dms = gps.get("GPSLatitude")
                lat_ref = gps.get("GPSLatitudeRef", "N")
                lon_dms = gps.get("GPSLongitude")
                lon_ref = gps.get("GPSLongitudeRef", "E")

                if lat_dms and lon_dms:
                    lat_out = _convert_dms_to_deg(lat_dms, lat_ref)
                    lon_out = _convert_dms_to_deg(lon_dms, lon_ref)

    except Exception:
        pass

    return dt_out, lat_out, lon_out


def parse_video_metadata(file_path: str | Path, ffmpeg_exe: str | None = None) -> tuple[Optional[datetime], Optional[float], Optional[float]]:
    """嘗試透過 ffprobe 解析影片 creation_time 與 location 標籤。"""
    path = Path(file_path)
    dt_out = None
    lat_out = None
    lon_out = None

    ffprobe = None
    if ffmpeg_exe:
        candidate = Path(ffmpeg_exe).parent / ("ffprobe.exe" if os.name == "nt" else "ffprobe")
        if candidate.is_file():
            ffprobe = str(candidate)

    if not ffprobe:
        import shutil
        ffprobe = shutil.which("ffprobe")

    if not ffprobe:
        return None, None, None

    cmd = [
        ffprobe, "-v", "quiet",
        "-print_format", "json",
        "-show_format", "-show_streams",
        str(path),
    ]

    try:
        kwargs = {}
        if os.name == "nt":
            kwargs["creationflags"] = getattr(subprocess, "CREATE_NO_WINDOW", 0)
        res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True, encoding="utf-8", **kwargs)
        if res.returncode == 0:
            data = json.loads(res.stdout)
            tags = data.get("format", {}).get("tags", {})

            for k, v in tags.items():
                k_lower = k.lower()
                if "creation_time" in k_lower and isinstance(v, str):
                    try:
                        clean = v.replace("Z", "+00:00")
                        dt_out = datetime.fromisoformat(clean).replace(tzinfo=None)
                    except Exception:
                        pass
                elif "location" in k_lower and isinstance(v, str):
                    # 例如 "+25.0330+121.5654/"
                    m = re.match(r"([+-]\d+\.\d+)([+-]\d+\.\d+)", v)
                    if m:
                        lat_out = float(m.group(1))
                        lon_out = float(m.group(2))
    except Exception:
        pass

    return dt_out, lat_out, lon_out


def scan_media_files(
    path: str | Path,
    time_offset_sec: float = 0.0,
    ffmpeg_exe: str | None = None,
) -> List[MediaItem]:
    """掃描指定的檔案或資料夾，解析 EXIF/Metadata。"""
    p = Path(path).expanduser().resolve()
    if not p.exists():
        return []

    files = []
    if p.is_file():
        files = [p]
    elif p.is_dir():
        image_exts = {".jpg", ".jpeg", ".png", ".webp", ".bmp"}
        video_exts = {".mp4", ".mov", ".avi", ".mkv", ".webm"}
        for root_dir, _, filenames in os.walk(p):
            for fn in filenames:
                ext = Path(fn).suffix.lower()
                if ext in image_exts or ext in video_exts:
                    files.append(Path(root_dir) / fn)

    overrides = {}
    if getattr(config, "MEDIA_OVERRIDES_JSON", None):
        try:
            overrides = json.loads(config.MEDIA_OVERRIDES_JSON)
        except Exception:
            overrides = {}

    items = []
    for f in sorted(files):
        ext = f.suffix.lower()
        is_video = ext in {".mp4", ".mov", ".avi", ".mkv", ".webm"}
        media_type = "video" if is_video else "image"

        has_exif_dt = False
        if is_video:
            dt, lat, lon = parse_video_metadata(f, ffmpeg_exe)
            if dt is not None:
                has_exif_dt = True
        else:
            dt, lat, lon = parse_image_exif(f)
            if dt is not None:
                has_exif_dt = True

        # 若無 EXIF 時間，採用檔案修改時間備援
        if dt is None:
            try:
                dt = datetime.fromtimestamp(f.stat().st_mtime)
            except Exception:
                dt = None

        if dt and time_offset_sec != 0.0:
            dt = dt + timedelta(seconds=time_offset_sec)

        mx, my = None, None
        if lat is not None and lon is not None:
            mx_arr, my_arr = latlon_to_mercator(np.array([lat]), np.array([lon]))
            mx = float(mx_arr[0])
            my = float(my_arr[0])

        item_ovr = overrides.get(f.name) or overrides.get(str(f)) or overrides.get(f.stem) or {}
        if item_ovr.get("excluded") or item_ovr.get("deleted"):
            continue

        caption = str(item_ovr.get("caption", "") or "")
        man_dist = item_ovr.get("manual_distance_km")
        if man_dist is not None:
            try:
                man_dist = float(man_dist)
            except Exception:
                man_dist = None

        items.append(MediaItem(
            file_path=str(f),
            filename=f.name,
            media_type=media_type,
            timestamp=dt,
            has_exif_time=has_exif_dt,
            lat=lat,
            lon=lon,
            mercator_x=mx,
            mercator_y=my,
            caption=caption,
            manual_distance_km=man_dist,
        ))

    return items


def match_media_to_ride(
    media_items: List[MediaItem],
    ride_data: RideData,
    gpx_times: Optional[List[datetime]] = None,
    time_offset_sec: float = 0.0,
) -> List[MediaItem]:
    """將 MediaItem 配對至 GPX 騎乘時間軸 (RideData.xs/ys 點位與 distances 里程)。"""
    if not media_items or ride_data.total_points < 1:
        return media_items

    has_gpx_times = gpx_times is not None and len(gpx_times) == ride_data.total_points and gpx_times[0] is not None

    for item in media_items:
        item.matched_index = 0
        item.matched_frame = -1
        item.matched_km = float(ride_data.distances[0]) if len(ride_data.distances) > 0 else 0.0

        # 0. 手動覆寫里程點 (最高優先權)
        if item.manual_distance_km is not None and item.manual_distance_km >= 0:
            target_km = float(item.manual_distance_km)
            dists = np.abs(ride_data.distances - target_km)
            best_i = int(np.argmin(dists))
            item.matched_index = best_i
            item.matched_km = target_km
            continue

        # 1. 嘗試時間配對 (僅在具備真實 EXIF 拍攝時間且時間與 GPX 吻合時生效)
        if has_gpx_times and item.has_exif_time and item.timestamp is not None:
            raw_ts = item.timestamp
            if time_offset_sec != 0.0:
                raw_ts = raw_ts + timedelta(seconds=time_offset_sec)
            item_ts = raw_ts.replace(tzinfo=None)
            g_start = gpx_times[0].replace(tzinfo=None)
            g_end = gpx_times[-1].replace(tzinfo=None)

            if g_start <= item_ts <= g_end:
                deltas = [abs((t.replace(tzinfo=None) - item_ts).total_seconds()) for t in gpx_times]
                best_i = int(np.argmin(deltas))
                item.matched_index = best_i
                item.matched_km = float(ride_data.distances[best_i])
                continue

        # 2. 時間不在區間內或缺乏時間戳記，改由 GPS 距離配對最近軌跡點
        if item.mercator_x is not None and item.mercator_y is not None:
            dists = (ride_data.xs - item.mercator_x) ** 2 + (ride_data.ys - item.mercator_y) ** 2
            best_i = int(np.argmin(dists))
            item.matched_index = best_i
            item.matched_km = float(ride_data.distances[best_i])
            continue

        # 3. 預設配對首點
        if len(ride_data.distances) > 0:
            item.matched_index = 0
            item.matched_km = float(ride_data.distances[0])

    return media_items


def load_media_thumbnail(file_path: str | Path, max_w: int = 600, max_h: int = 450) -> Optional[Image.Image]:
    """讀取相片或影片截圖並回傳經 EXIF 旋轉校正之 PIL Image 縮圖。"""
    p = Path(file_path)
    if not p.is_file():
        return None
    ext = p.suffix.lower()
    is_video = ext in {".mp4", ".mov", ".avi", ".mkv", ".webm"}
    if not is_video:
        try:
            with Image.open(p) as img:
                img = ImageOps.exif_transpose(img)
                img = img.convert("RGB")
                img.thumbnail((max_w, max_h), Image.Resampling.LANCZOS)
                return img
        except Exception:
            return None
    else:
        # Video: 嘗試以 OpenCV 讀取第一畫格
        try:
            import cv2
            cap = cv2.VideoCapture(str(p))
            ret, frame = cap.read()
            cap.release()
            if ret and frame is not None:
                rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                img = Image.fromarray(rgb)
                img.thumbnail((max_w, max_h), Image.Resampling.LANCZOS)
                return img
        except Exception:
            pass
        return None


def prepare_thumbnail(file_path: str, max_w: int = 800, max_h: int = 800) -> Optional[Image.Image]:
    """生成帶圓角與邊框的精美媒體縮圖卡片（自適應影片解析度與劇院級邊框）。"""
    path = Path(file_path)
    if not path.is_file():
        return None

    try:
        with Image.open(path) as img:
            img = ImageOps.exif_transpose(img)
            img = img.convert("RGB")
            img.thumbnail((max_w, max_h), Image.Resampling.LANCZOS)
            w, h = img.size

            radius = max(14, int(min(w, h) * 0.05))
            card = Image.new("RGBA", (w, h), (0, 0, 0, 0))
            mask = Image.new("L", (w, h), 0)
            mdraw = ImageDraw.Draw(mask)
            mdraw.rounded_rectangle((0, 0, w - 1, h - 1), radius=radius, fill=255)

            card.paste(img, (0, 0), mask)
            cdraw = ImageDraw.Draw(card)
            border_w = max(3, int(min(w, h) * 0.008))
            cdraw.rounded_rectangle((0, 0, w - 1, h - 1), radius=radius, outline=(255, 255, 255, 245), width=border_w)
            return card
    except Exception:
        return None
