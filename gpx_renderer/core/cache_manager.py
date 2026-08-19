# -*- coding: utf-8 -*-
"""
快取管理模組 (CacheManager)：
負責全域底圖切片 (Tiles) 與 DEM 高程圖資的磁碟快取管理。
支援：
1. Session 暫存模式（預設）：儲存於 .map_cache/session_xxx/，程式關閉時自動安全刪除。
2. Persistent 永久保留模式：儲存於 .map_cache/persistent/，跨次重開程式依然秒載入。
3. LRU 自動容量上限修剪 (預設 1GB / 1024MB)。
4. 一鍵全域快取清除與孤立暫存自動清理。
5. 執行緒與行程安全的原子 PNG 切片快取（避免 Windows 檔案鎖死與 PermissionError）。
"""

from __future__ import annotations
import os
import sys
import time
import shutil
import hashlib
from pathlib import Path
from typing import Optional
import numpy as np
from PIL import Image

from gpx_renderer import config
from gpx_renderer.utils.env import application_dir

_ORIGINAL_CT_RETRYER = None


def _safe_cached_tile_retryer(tile_url, wait, max_retries, headers: dict[str, str] | None = None, timeout=None):
    """自訂執行緒安全且行程安全的 PNG 切片快取攔截器，完全取代 contextily 不穩定的 joblib pickle 快取。"""
    if headers is None:
        headers = {}
    tiles_dir = CacheManager.get_tiles_dir()
    url_hash = hashlib.sha256(tile_url.encode("utf-8")).hexdigest()
    tile_file = tiles_dir / f"{url_hash}.png"

    # 1. 本機磁碟快取命中檢查
    if tile_file.exists():
        try:
            with Image.open(tile_file) as img:
                arr = np.asarray(img.convert("RGBA"))
            CacheManager.touch_file(tile_file)
            return arr
        except Exception:
            try:
                tile_file.unlink(missing_ok=True)
            except Exception:
                pass

    # 2. 未命中快取，向圖資伺服器請求
    global _ORIGINAL_CT_RETRYER
    if _ORIGINAL_CT_RETRYER is None:
        import contextily.tile as ct
        _ORIGINAL_CT_RETRYER = ct._retryer

    arr = _ORIGINAL_CT_RETRYER(tile_url, wait, max_retries, headers, timeout=timeout)

    # 3. 原子寫入本機 PNG 快取
    tmp_file = tiles_dir / f"{url_hash}.tmp_{os.getpid()}_{time.time_ns()}"
    try:
        img = Image.fromarray(arr)
        img.save(tmp_file, format="PNG", optimize=False)
        tmp_file.replace(tile_file)
        CacheManager.touch_file(tile_file)
    except Exception:
        try:
            if tmp_file.exists():
                tmp_file.unlink(missing_ok=True)
        except Exception:
            pass

    return arr


class CacheManager:
    _SESSION_ID: str = f"session_{os.getpid()}_{int(time.time())}"
    _INITIALIZED: bool = False

    @classmethod
    def get_base_dir(cls) -> Path:
        """主程式根目錄下的 .map_cache 資料夾"""
        base = application_dir() / ".map_cache"
        try:
            base.mkdir(parents=True, exist_ok=True)
        except Exception:
            pass
        return base

    @classmethod
    def get_session_id(cls) -> str:
        return cls._SESSION_ID

    @classmethod
    def set_session_id(cls, session_id: str):
        if session_id and session_id.strip():
            cls._SESSION_ID = session_id.strip()

    @classmethod
    def get_mode(cls) -> str:
        mode = getattr(config, "MAP_CACHE_MODE", "session")
        return "persistent" if str(mode).lower() == "persistent" else "session"

    @classmethod
    def get_active_dir(cls) -> Path:
        """依據當前快取模式取得作用中的快取目錄"""
        base = cls.get_base_dir()
        if cls.get_mode() == "persistent":
            target = base / "persistent"
        else:
            target = base / cls._SESSION_ID
        try:
            target.mkdir(parents=True, exist_ok=True)
        except Exception:
            pass
        return target

    @classmethod
    def get_tiles_dir(cls) -> Path:
        """地圖 XYZ 切片存放目錄"""
        d = cls.get_active_dir() / "tiles"
        try:
            d.mkdir(parents=True, exist_ok=True)
        except Exception:
            pass
        return d

    @classmethod
    def get_dem_dir(cls) -> Path:
        """DEM 高程圖資存放目錄"""
        d = cls.get_active_dir() / "dem_tiles"
        try:
            d.mkdir(parents=True, exist_ok=True)
        except Exception:
            pass
        return d

    @classmethod
    def init_cache_system(cls, session_id: Optional[str] = None):
        """初始化快取系統（註冊 contextily 切片快取攔截器，清理孤立 session）"""
        if session_id:
            cls.set_session_id(session_id)

        # 1. 確保基本目錄建立
        cls.get_tiles_dir()
        cls.get_dem_dir()

        # 2. 註冊自訂快取攔截器至 contextily.tile
        try:
            import contextily.tile as ct
            global _ORIGINAL_CT_RETRYER
            if _ORIGINAL_CT_RETRYER is None:
                _ORIGINAL_CT_RETRYER = ct._retryer
            ct._retryer = _safe_cached_tile_retryer
        except Exception:
            pass

        # 3. 清理上次異常中斷遺留的孤立 Session
        if not cls._INITIALIZED:
            cls.cleanup_orphan_sessions()
            cls._INITIALIZED = True

    @classmethod
    def touch_file(cls, file_path: str | Path):
        """更新檔案最後訪問時間 (Access Time)，供 LRU 淘汰演算法排序使用"""
        try:
            p = Path(file_path)
            if p.is_file():
                os.utime(str(p), None)
        except Exception:
            pass

    @classmethod
    def get_cache_size_bytes(cls) -> int:
        """計算 .map_cache 目錄下所有快取檔案的總位元組數"""
        base = cls.get_base_dir()
        if not base.exists():
            return 0
        total = 0
        try:
            for root, _, files in os.walk(base):
                for f in files:
                    try:
                        fp = os.path.join(root, f)
                        total += os.path.getsize(fp)
                    except Exception:
                        pass
        except Exception:
            pass
        return total

    @classmethod
    def get_cache_size_mb(cls) -> float:
        """計算目前快取容量 (MB)"""
        return cls.get_cache_size_bytes() / (1024.0 * 1024.0)

    @classmethod
    def prune_if_exceeds(cls, max_mb: Optional[float] = None, target_mb: Optional[float] = None):
        """
        LRU 容量上限保護機制：
        若目前快取超過 max_mb (預設 1024 MB)，依最後訪問時間 (Access Time) 由舊到新刪除，
        直至容量降至 target_mb (預設 800 MB)。
        """
        if max_mb is None:
            max_mb = float(getattr(config, "MAP_CACHE_MAX_MB", 1024.0))
        if target_mb is None:
            target_mb = max_mb * 0.8  # 退避水位 80%

        base = cls.get_base_dir()
        if not base.exists():
            return

        file_list = []
        total_bytes = 0

        for root, _, files in os.walk(base):
            for f in files:
                fp = os.path.join(root, f)
                try:
                    stat = os.stat(fp)
                    atime = getattr(stat, "st_atime", stat.st_mtime)
                    size = stat.st_size
                    file_list.append((atime, size, fp))
                    total_bytes += size
                except Exception:
                    pass

        current_mb = total_bytes / (1024.0 * 1024.0)
        if current_mb <= max_mb:
            return

        print(f"[CACHE] 目前快取容量 {current_mb:.1f} MB 超過上限 {max_mb:.0f} MB，啟動 LRU 自動修剪至 {target_mb:.0f} MB...")

        # 依最後訪問時間由舊到新排序 (最舊的排在最前面)
        file_list.sort(key=lambda x: x[0])

        target_bytes = target_mb * 1024.0 * 1024.0
        deleted_count = 0

        for _, size, fp in file_list:
            if total_bytes <= target_bytes:
                break
            try:
                os.remove(fp)
                total_bytes -= size
                deleted_count += 1
            except Exception:
                pass

        print(f"[CACHE] LRU 修剪完成：已清理 {deleted_count} 個舊切片檔案，剩餘快取容量 {total_bytes / (1024.0 * 1024.0):.1f} MB。")

    @classmethod
    def cleanup_current_session(cls):
        """清理當前執行的 Session 暫存目錄（關閉主程式時調用）"""
        try:
            base = cls.get_base_dir()
            session_dir = base / cls._SESSION_ID
            if session_dir.exists():
                shutil.rmtree(session_dir, ignore_errors=True)
        except Exception:
            pass

    @classmethod
    def cleanup_orphan_sessions(cls):
        """清理先前異常中斷殘留的所有孤立 Session 資料夾"""
        try:
            base = cls.get_base_dir()
            if not base.exists():
                return
            for item in base.iterdir():
                if item.is_dir() and item.name.startswith("session_") and item.name != cls._SESSION_ID:
                    shutil.rmtree(item, ignore_errors=True)
        except Exception:
            pass

    @classmethod
    def cleanup_all_cache(cls):
        """一鍵手動清除所有快取（由 GUI 按鈕觸發）"""
        try:
            base = cls.get_base_dir()
            if base.exists():
                for item in base.iterdir():
                    if item.is_dir():
                        shutil.rmtree(item, ignore_errors=True)
                    else:
                        try:
                            item.unlink(missing_ok=True)
                        except Exception:
                            pass
            # 重新建立目錄結構
            cls.get_tiles_dir()
            cls.get_dem_dir()
        except Exception as exc:
            print(f"[WARN] 清理快取時發生錯誤: {exc}")
