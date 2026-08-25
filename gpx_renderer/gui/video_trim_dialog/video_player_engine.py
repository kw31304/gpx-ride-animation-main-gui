# -*- coding: utf-8 -*-
"""
video_player_engine.py
封裝 OpenCV 影片讀取、FPS/時長分析與影格解碼引擎。
"""

from __future__ import annotations
from typing import Optional, Tuple
from pathlib import Path
import numpy as np
import cv2
from PySide6.QtGui import QImage


def get_video_info(file_path: str) -> Tuple[float, float, int, int, int]:
    """
    透過 OpenCV 讀取影片時長、FPS、寬、高與總幀數。
    回傳: (total_duration_sec, video_fps, width, height, total_frames)
    """
    fps = 30.0
    frames = 300
    w = 640
    h = 480
    total_dur = 10.0

    try:
        cap = cv2.VideoCapture(file_path)
        if cap.isOpened():
            f_fps = cap.get(cv2.CAP_PROP_FPS)
            f_cnt = cap.get(cv2.CAP_PROP_FRAME_COUNT)
            f_w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            f_h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            if f_fps and np.isfinite(f_fps) and f_fps > 0:
                fps = float(f_fps)
            if f_cnt and f_cnt > 0:
                frames = int(f_cnt)
                total_dur = float(frames / fps)
            if f_w > 0 and f_h > 0:
                w = f_w
                h = f_h
            cap.release()
    except Exception:
        pass

    total_dur = max(0.1, round(total_dur, 2))
    return total_dur, fps, w, h, frames


def extract_frame_qimage(cap: Optional[cv2.VideoCapture], file_path: str, sec: float) -> Optional[QImage]:
    """
    從指定秒數抓取影格並轉換為 PySide6 QImage 格式。
    """
    try:
        if cap is None or not cap.isOpened():
            cap = cv2.VideoCapture(file_path)

        pos_ms = max(0.0, float(sec) * 1000.0)
        cap.set(cv2.CAP_PROP_POS_MSEC, pos_ms)
        ret, frame_bgr = cap.read()
        if ret and frame_bgr is not None:
            rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
            h, w, ch = rgb.shape
            return QImage(rgb.data, w, h, w * ch, QImage.Format_RGB888).copy()
    except Exception:
        pass
    return None


__all__ = [
    "get_video_info",
    "extract_frame_qimage",
]
