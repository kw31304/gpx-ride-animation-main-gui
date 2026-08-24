# -*- coding: utf-8 -*-
"""
相片與影片 EXIF 座標/拍攝時間解析、GPX 時間軸對齊與縮圖快取處理器。
"""

from __future__ import annotations
import os
import sys
import io
import math
import shutil
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
    duration_sec: Optional[float] = None  # 影片時長 (秒)
    popup_duration: Optional[float] = None  # 個別自訂之停留展示秒數 (秒)
    clip_start_sec: float = 0.0  # 影片截取播放起始秒數 (秒)
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
    caption_size: Optional[int] = None  # 說明文字自訂字級大小 (pt)
    manual_distance_km: Optional[float] = None  # 手動指定之里程數 (km)

    @property
    def effective_caption_size(self) -> int:
        """取得該媒體說明文字字級大小 (pt)：優先採用個別自訂值，預設為 MEDIA_CAPTION_FONT_SIZE (22)。"""
        if self.caption_size is not None and self.caption_size > 0:
            return int(self.caption_size)
        return int(getattr(config, "MEDIA_CAPTION_FONT_SIZE", 22))

    @property
    def current_km(self) -> float:
        if self.manual_distance_km is not None and self.manual_distance_km >= 0:
            return float(self.manual_distance_km)
        return float(self.matched_km)

    @property
    def effective_duration(self) -> float:
        """取得該媒體實際停留秒數：優先採用個別自訂值，影片預設原始長度，相片預設 3.0 秒。"""
        if self.popup_duration is not None and self.popup_duration > 0:
            return float(round(self.popup_duration, 2))
        if self.media_type == "video" and self.duration_sec is not None and self.duration_sec > 0:
            return float(round(self.duration_sec, 2))
        return float(getattr(config, "MEDIA_POPUP_DURATION", 3.0))

    @property
    def trim_summary_str(self) -> str:
        """格式化停留與裁剪摘要，如 4.5s (02.0~06.5s) 或 3.0s。"""
        eff = self.effective_duration
        if self.media_type == "video":
            st = float(self.clip_start_sec or 0.0)
            et = st + eff
            if self.duration_sec is not None and abs(eff - self.duration_sec) < 0.1 and st < 0.1:
                return f"{eff:.1f}s (全片)"
            return f"{eff:.1f}s ({st:.1f}~{et:.1f}s)"
        return f"{eff:.1f}s"

    @property
    def duration_str(self) -> str:
        """格式化影片時長字串 (如 12.5s 或 01:23)。"""
        if self.media_type != "video" or self.duration_sec is None or self.duration_sec <= 0:
            return "--"
        dur = float(self.duration_sec)
        m = int(dur // 60)
        s = dur % 60
        if m > 0:
            return f"{m:02d}:{int(s):02d} ({dur:.1f}s)"
        return f"{dur:.1f}s"


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


def parse_video_metadata(file_path: str | Path, ffmpeg_exe: str | None = None) -> tuple[Optional[datetime], Optional[float], Optional[float], Optional[float]]:
    """嘗試透過 ffprobe、ffmpeg 或 OpenCV 解析影片 creation_time、location 與 duration_sec。"""
    path = Path(file_path)
    dt_out = None
    lat_out = None
    lon_out = None
    dur_out = None

    # 1. 嘗試以 OpenCV VideoCapture 取得影片時長 (極速)
    try:
        import cv2
        cap = cv2.VideoCapture(str(path))
        if cap.isOpened():
            fps = cap.get(cv2.CAP_PROP_FPS)
            frames = cap.get(cv2.CAP_PROP_FRAME_COUNT)
            if fps and fps > 0 and frames and frames > 0:
                calc_dur = frames / float(fps)
                if calc_dur > 0 and np.isfinite(calc_dur):
                    dur_out = float(calc_dur)
            cap.release()
    except Exception:
        pass

    ffprobe = None
    if ffmpeg_exe:
        candidate = Path(ffmpeg_exe).parent / ("ffprobe.exe" if os.name == "nt" else "ffprobe")
        if candidate.is_file():
            ffprobe = str(candidate)

    if not ffprobe:
        ffprobe = shutil.which("ffprobe")

    if ffprobe:
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
                fmt = data.get("format", {})
                tags = fmt.get("tags", {})

                if dur_out is None and "duration" in fmt:
                    try:
                        dur_out = float(fmt["duration"])
                    except Exception:
                        pass

                for k, v in tags.items():
                    k_lower = k.lower()
                    if "creation_time" in k_lower and isinstance(v, str):
                        try:
                            clean = v.replace("Z", "+00:00")
                            dt_out = datetime.fromisoformat(clean).replace(tzinfo=None)
                        except Exception:
                            pass
                    elif "location" in k_lower and isinstance(v, str):
                        m = re.match(r"([+-]\d+\.\d+)([+-]\d+\.\d+)", v)
                        if m:
                            lat_out = float(m.group(1))
                            lon_out = float(m.group(2))
        except Exception:
            pass

    # 若 ffprobe 不存在或未解析出時間/座標，嘗試使用 ffmpeg -hide_banner -i 備援
    if dt_out is None or lat_out is None or dur_out is None:
        ff_candidate = ffmpeg_exe
        if not ff_candidate:
            try:
                from gpx_renderer.core.encoder import find_ffmpeg
                ff_candidate = find_ffmpeg()
            except Exception:
                ff_candidate = shutil.which("ffmpeg")

        if ff_candidate and Path(ff_candidate).is_file():
            try:
                kwargs = {}
                if os.name == "nt":
                    kwargs["creationflags"] = getattr(subprocess, "CREATE_NO_WINDOW", 0)
                cmd_ff = [str(ff_candidate), "-hide_banner", "-i", str(path)]
                res = subprocess.run(cmd_ff, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, text=True, encoding="utf-8", errors="replace", **kwargs)
                out_text = res.stderr or ""
                if dt_out is None:
                    m_time = re.search(r"creation_time\s*:\s*([0-9T:\-\.Z]+)", out_text, re.IGNORECASE)
                    if m_time:
                        try:
                            clean = m_time.group(1).replace("Z", "+00:00")
                            dt_out = datetime.fromisoformat(clean).replace(tzinfo=None)
                        except Exception:
                            pass
                if lat_out is None or lon_out is None:
                    m_loc = re.search(r"location\s*:\s*([+-]\d+\.\d+)([+-]\d+\.\d+)", out_text, re.IGNORECASE)
                    if m_loc:
                        try:
                            lat_out = float(m_loc.group(1))
                            lon_out = float(m_loc.group(2))
                        except Exception:
                            pass
                if dur_out is None:
                    m_dur = re.search(r"Duration:\s*(\d+):(\d+):(\d+(?:\.\d+)?)", out_text)
                    if m_dur:
                        try:
                            dh = float(m_dur.group(1))
                            dm = float(m_dur.group(2))
                            ds = float(m_dur.group(3))
                            dur_out = dh * 3600.0 + dm * 60.0 + ds
                        except Exception:
                            pass
            except Exception:
                pass

    return dt_out, lat_out, lon_out, dur_out


def scan_media_files(
    path: str | Path | list[str | Path],
    time_offset_sec: float = 0.0,
    ffmpeg_exe: str | None = None,
) -> List[MediaItem]:
    """掃描指定的檔案、資料夾或混合清單，解析 EXIF/Metadata。"""
    if not path:
        return []

    input_paths = []
    if isinstance(path, (list, tuple, set)):
        input_paths = list(path)
    elif isinstance(path, (str, Path)):
        p_str = str(path).strip()
        if ";" in p_str:
            input_paths = [p.strip() for p in p_str.split(";") if p.strip()]
        elif "\n" in p_str:
            input_paths = [p.strip() for p in p_str.split("\n") if p.strip()]
        else:
            input_paths = [p_str] if p_str else []

    files = []
    seen_paths = set()
    image_exts = {".jpg", ".jpeg", ".png", ".webp", ".bmp"}
    video_exts = {".mp4", ".mov", ".avi", ".mkv", ".webm", ".m4v", ".flv", ".wmv"}

    for p_item in input_paths:
        p = Path(p_item).expanduser().resolve()
        if not p.exists():
            continue
        if p.is_file():
            ext = p.suffix.lower()
            if ext in image_exts or ext in video_exts:
                canon = str(p).lower()
                if canon not in seen_paths:
                    seen_paths.add(canon)
                    files.append(p)
        elif p.is_dir():
            for root_dir, _, filenames in os.walk(p):
                for fn in filenames:
                    ext = Path(fn).suffix.lower()
                    if ext in image_exts or ext in video_exts:
                        full_f = Path(root_dir) / fn
                        canon = str(full_f).lower()
                        if canon not in seen_paths:
                            seen_paths.add(canon)
                            files.append(full_f)

    overrides = {}
    if getattr(config, "MEDIA_OVERRIDES_JSON", None):
        try:
            overrides = json.loads(config.MEDIA_OVERRIDES_JSON)
        except Exception:
            overrides = {}

    items = []
    for f in sorted(files):
        ext = f.suffix.lower()
        is_video = ext in {".mp4", ".mov", ".avi", ".mkv", ".webm", ".m4v", ".flv", ".wmv"}
        media_type = "video" if is_video else "image"

        has_exif_dt = False
        duration_sec = None
        if is_video:
            dt, lat, lon, duration_sec = parse_video_metadata(f, ffmpeg_exe)
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
        cap_sz = item_ovr.get("caption_size") or item_ovr.get("caption_font_size")
        if cap_sz is not None:
            try:
                cap_sz = int(cap_sz)
            except Exception:
                cap_sz = None
        else:
            cap_sz = None

        man_dist = item_ovr.get("manual_distance_km")
        if man_dist is not None:
            try:
                man_dist = float(man_dist)
            except Exception:
                man_dist = None

        popup_dur = item_ovr.get("popup_duration")
        if popup_dur is not None:
            try:
                popup_dur = float(popup_dur)
            except Exception:
                popup_dur = None
        else:
            if is_video and duration_sec is not None and duration_sec > 0:
                popup_dur = round(float(duration_sec), 2)
            elif not is_video:
                popup_dur = float(getattr(config, "MEDIA_POPUP_DURATION", 3.0))

        clip_start = item_ovr.get("clip_start_sec")
        if clip_start is not None:
            try:
                clip_start = float(clip_start)
            except Exception:
                clip_start = 0.0
        else:
            clip_start = 0.0

        items.append(MediaItem(
            file_path=str(f),
            filename=f.name,
            media_type=media_type,
            duration_sec=duration_sec,
            popup_duration=popup_dur,
            clip_start_sec=clip_start,
            timestamp=dt,
            has_exif_time=has_exif_dt,
            lat=lat,
            lon=lon,
            mercator_x=mx,
            mercator_y=my,
            caption=caption,
            caption_size=cap_sz,
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


def extract_video_frame(
    file_path: str | Path,
    time_sec: float = 0.0,
    ffmpeg_exe: str | None = None,
) -> Optional[Image.Image]:
    """從影片檔案中擷取單一畫面 (RGB PIL Image)，具備 OpenCV 與 FFmpeg 雙重容錯。"""
    p = Path(file_path).resolve()
    if not p.is_file():
        return None

    # 1. 優先嘗試 OpenCV VideoCapture
    try:
        import cv2
        cap = cv2.VideoCapture(str(p))
        if cap.isOpened():
            if time_sec > 0.0:
                cap.set(cv2.CAP_PROP_POS_MSEC, time_sec * 1000.0)
            ret, frame = cap.read()
            if not ret or frame is None:
                # 若時間超出或首幀失敗，重設至第 0 畫格重試
                cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                ret, frame = cap.read()
            cap.release()
            if ret and frame is not None:
                rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                return Image.fromarray(rgb)
    except Exception:
        pass

    # 2. OpenCV 失敗時，以 FFmpeg 作為可靠備援
    ff = ffmpeg_exe
    if not ff:
        try:
            from gpx_renderer.core.encoder import find_ffmpeg
            ff = find_ffmpeg()
        except Exception:
            ff = shutil.which("ffmpeg")

    if ff and Path(ff).is_file():
        try:
            kwargs = {}
            if os.name == "nt":
                kwargs["creationflags"] = getattr(subprocess, "CREATE_NO_WINDOW", 0)
            cmd = [
                str(ff), "-y", "-hide_banner", "-loglevel", "error",
                "-ss", f"{max(0.0, time_sec):.3f}",
                "-i", str(p),
                "-frames:v", "1",
                "-f", "image2pipe",
                "-vcodec", "png",
                "-",
            ]
            res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, **kwargs)
            if res.returncode == 0 and res.stdout:
                with Image.open(io.BytesIO(res.stdout)) as img:
                    return img.convert("RGB")
        except Exception:
            pass

    return None


class VideoPopupReader:
    """輕量化動態影片畫格讀取器，以串流按需解碼取代全量載入記憶體，將 RAM 佔用由數十 GB 降至數 MB。"""

    def __init__(
        self,
        file_path: str | Path,
        start_time_sec: float = 0.0,
        anim_fps: int = 60,
        max_w: int = 800,
        max_h: int = 800,
        ffmpeg_exe: str | None = None,
    ):
        self.file_path = str(Path(file_path).resolve())
        self.start_time_sec = max(0.0, float(start_time_sec))
        self.anim_fps = max(1, int(anim_fps))
        self.max_w = max_w
        self.max_h = max_h
        self.ffmpeg_exe = ffmpeg_exe
        self._cap = None
        self._video_fps: float = float(self.anim_fps)
        self._mask: Optional[Image.Image] = None
        self._border_img: Optional[Image.Image] = None
        self._cached_frame_offset: int = -1
        self._cached_card: Optional[Image.Image] = None
        self._init_metadata()

    def _init_metadata(self):
        try:
            import cv2
            cap = cv2.VideoCapture(self.file_path)
            if cap.isOpened():
                v_fps = cap.get(cv2.CAP_PROP_FPS)
                if v_fps and np.isfinite(v_fps) and v_fps > 0:
                    self._video_fps = float(v_fps)
                cap.release()
        except Exception:
            pass

    def get_frame(self, anim_frame_offset: int) -> Optional[Image.Image]:
        """依動畫彈出畫格偏移量 (0..N) 即時解碼並產出圓角白邊卡片 (單格快取)。"""
        if self._cached_frame_offset == anim_frame_offset and self._cached_card is not None:
            return self._cached_card

        import cv2
        if self._cap is None or not self._cap.isOpened():
            self._cap = cv2.VideoCapture(self.file_path)
            if not self._cap.isOpened():
                return None

        # 計算影片時間點
        t_sec = self.start_time_sec + (anim_frame_offset / float(self.anim_fps))
        target_msec = t_sec * 1000.0
        self._cap.set(cv2.CAP_PROP_POS_MSEC, target_msec)
        ret, frame = self._cap.read()
        if not ret or frame is None:
            self._cap.set(cv2.CAP_PROP_POS_MSEC, self.start_time_sec * 1000.0)
            ret, frame = self._cap.read()
            if not ret or frame is None:
                return None

        # 縮放與格式轉換
        h, w = frame.shape[:2]
        scale = min(self.max_w / float(w), self.max_h / float(h), 1.0)
        tw, th = max(1, int(round(w * scale))), max(1, int(round(h * scale)))
        resized = cv2.resize(frame, (tw, th), interpolation=cv2.INTER_AREA) if scale < 0.99 else frame
        rgb = cv2.cvtColor(resized, cv2.COLOR_BGR2RGB)
        pil_img = Image.fromarray(rgb)

        # 建立圓角遮罩與白邊框 (同尺寸快取重複使用)
        if self._mask is None or self._mask.size != (tw, th):
            radius = max(14, int(min(tw, th) * 0.05))
            self._mask = Image.new("L", (tw, th), 0)
            mdraw = ImageDraw.Draw(self._mask)
            mdraw.rounded_rectangle((0, 0, tw - 1, th - 1), radius=radius, fill=255)

            border_w = max(3, int(min(tw, th) * 0.008))
            self._border_img = Image.new("RGBA", (tw, th), (0, 0, 0, 0))
            bdraw = ImageDraw.Draw(self._border_img)
            bdraw.rounded_rectangle((0, 0, tw - 1, th - 1), radius=radius, outline=(255, 255, 255, 245), width=border_w)

        card = Image.new("RGBA", (tw, th), (0, 0, 0, 0))
        card.paste(pil_img, (0, 0), self._mask)
        card.alpha_composite(self._border_img)

        self._cached_frame_offset = anim_frame_offset
        self._cached_card = card
        return card

    def close(self):
        if self._cap is not None:
            try:
                self._cap.release()
            except Exception:
                pass
            self._cap = None

    def __del__(self):
        self.close()


def extract_video_frames_for_popup(
    file_path: str | Path,
    anim_frames_count: int,
    anim_fps: int = 60,
    max_w: int = 800,
    max_h: int = 800,
    start_time_sec: float = 0.0,
    ffmpeg_exe: str | None = None,
) -> list[Image.Image]:
    """為路線動畫彈出卡片提取動態影片畫格序列 (限制最大畫格數以防記憶體溢出)。"""
    reader = VideoPopupReader(
        file_path=file_path,
        start_time_sec=start_time_sec,
        anim_fps=anim_fps,
        max_w=max_w,
        max_h=max_h,
        ffmpeg_exe=ffmpeg_exe,
    )
    # 若請求畫格量過大，取關鍵畫格避免 MemoryError
    safe_count = min(anim_frames_count, 120)
    card_frames = []
    for af in range(safe_count):
        f = reader.get_frame(af)
        if f is not None:
            card_frames.append(f)
    reader.close()
    return card_frames


def load_media_thumbnail(
    file_path: str | Path,
    max_w: int = 600,
    max_h: int = 450,
    ffmpeg_exe: str | None = None,
) -> Optional[Image.Image]:
    """讀取相片或影片截圖並回傳經 EXIF 旋轉校正之 PIL Image 縮圖。"""
    p = Path(file_path)
    if not p.is_file():
        return None
    ext = p.suffix.lower()
    is_video = ext in {".mp4", ".mov", ".avi", ".mkv", ".webm", ".m4v", ".flv", ".wmv"}
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
        # Video: 透過 extract_video_frame 讀取首畫格截圖 (OpenCV + FFmpeg 備援)
        img = extract_video_frame(p, time_sec=0.0, ffmpeg_exe=ffmpeg_exe)
        if img is not None:
            try:
                img.thumbnail((max_w, max_h), Image.Resampling.LANCZOS)
                return img
            except Exception:
                pass
        return None


def prepare_thumbnail(
    file_or_image: str | Path | Image.Image,
    max_w: int = 800,
    max_h: int = 800,
    is_video: bool = False,
    ffmpeg_exe: str | None = None,
) -> Optional[Image.Image]:
    """生成帶圓角與邊框的精美媒體縮圖卡片（自適應影片解析度與劇院級邊框）。"""
    img = None
    if isinstance(file_or_image, Image.Image):
        img = file_or_image.copy()
    else:
        path = Path(file_or_image)
        if not path.is_file():
            return None
        ext = path.suffix.lower()
        is_vid = is_video or (ext in {".mp4", ".mov", ".avi", ".mkv", ".webm", ".m4v", ".flv", ".wmv"})
        if is_vid:
            img = extract_video_frame(path, time_sec=0.0, ffmpeg_exe=ffmpeg_exe)
        else:
            try:
                with Image.open(path) as raw_img:
                    img = ImageOps.exif_transpose(raw_img)
                    img = img.convert("RGB")
            except Exception:
                img = None

    if img is None:
        return None

    try:
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
