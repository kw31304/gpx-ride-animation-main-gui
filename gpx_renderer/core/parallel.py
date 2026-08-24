# -*- coding: utf-8 -*-
"""
多程序平行渲染引擎 (Multiprocessing Workers)、Auto Tune 效能測試與高階渲染任務執行入口。
"""

from __future__ import annotations
import os
import sys
import time
import math
import json
import shutil
import tempfile
import subprocess
import multiprocessing as mp
from dataclasses import dataclass
from pathlib import Path
import gc

import numpy as np

try:
    import cv2
    HAVE_CV2 = True
except Exception:
    cv2 = None
    HAVE_CV2 = False

from gpx_renderer import config
from gpx_renderer.utils import _background_subprocess_kwargs
from gpx_renderer.core.data import RideData, load_gpx, format_seconds_human
from gpx_renderer.core.map_utils import RasterMap, choose_map_style, build_overview_raster_map
from gpx_renderer.core.encoder import (
    find_ffmpeg,
    encoder_works,
    choose_encoder,
    build_ffmpeg_command,
    encode_video,
    _concat_mp4_segments,
    _encode_end_segment,
)
from gpx_renderer.core.renderer import RideRenderer
from gpx_renderer.core.cache_manager import CacheManager


@dataclass
class SegmentTask:
    segment_index: int
    start_frame: int
    end_frame: int
    output_path: str


@dataclass
class DynamicWorkerConfig:
    gpx_path: str
    map_style_key: str
    fps: int
    video_duration: float
    ffmpeg: str
    encoder: str
    settings: dict


@dataclass
class BenchmarkWorkerConfig:
    gpx_path: str
    map_style_key: str
    fps: int
    video_duration: float
    ffmpeg: str
    encoder: str
    settings: dict


def _build_benchmark_ffmpeg_command(ffmpeg: str, encoder: str, fps: int):
    """與正式輸出相同的 raw RGB -> encoder 路徑，但丟到 FFmpeg null muxer。"""
    cmd = [
        ffmpeg, "-hide_banner", "-loglevel", "error",
        "-f", "rawvideo", "-vcodec", "rawvideo",
        "-pix_fmt", "rgb24", "-s:v", f"{config.FRAME_WIDTH}x{config.FRAME_HEIGHT}",
        "-r", str(fps), "-i", "-", "-an",
    ]
    if encoder == "h264_nvenc":
        cmd += [
            "-c:v", "h264_nvenc", "-preset", config.NVENC_PRESET,
            "-tune", "hq", "-rc", "vbr",
            "-b:v", config.NVENC_BITRATE, "-maxrate", config.NVENC_BITRATE, "-bufsize", "24M",
        ]
    else:
        cmd += [
            "-c:v", "libx264", "-preset", config.CPU_PRESET,
            "-crf", str(config.CPU_CRF), "-threads", "1",
        ]
    cmd += ["-pix_fmt", "yuv420p", "-f", "null", "-"]
    return cmd


def _benchmark_worker_entry(
    worker_id: int,
    worker_cfg: BenchmarkWorkerConfig,
    start_frame: int,
    end_frame: int,
    start_event,
    ready_queue,
    result_queue,
):
    """Benchmark worker。先 warm-up renderer，再由 parent 同步開始計時。"""
    ffmpeg_proc = None
    ready_sent = False
    try:
        config.apply_render_config(worker_cfg.settings)
        if HAVE_CV2:
            try:
                cv2.setNumThreads(max(1, int(config.CV2_THREADS_PER_WORKER)))
            except Exception:
                pass

        data = load_gpx(worker_cfg.gpx_path)
        map_style = config.MAP_STYLE_OPTIONS[worker_cfg.map_style_key][1]
        renderer = RideRenderer(
            data=data, overview_map=None, map_style=map_style, fps=worker_cfg.fps,
            video_duration=worker_cfg.video_duration, zoom_out_duration=0.0, end_hold_duration=0.0,
            tile_cache_enabled=False,
        )

        warm_frame = max(0, min(int(start_frame), renderer.main_frames - 1))
        renderer.render_main_frame(warm_frame)

        cmd = _build_benchmark_ffmpeg_command(worker_cfg.ffmpeg, worker_cfg.encoder, worker_cfg.fps)
        ffmpeg_proc = subprocess.Popen(
            cmd, stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE,
            bufsize=16 * 1024 * 1024,
            **_background_subprocess_kwargs(),
        )
        if ffmpeg_proc.stdin is None:
            raise RuntimeError("Benchmark FFmpeg stdin 無法開啟。")

        ready_queue.put(("ready", worker_id, ""))
        ready_sent = True
        if not start_event.wait(timeout=120.0):
            raise TimeoutError("Benchmark 等待同步開始逾時。")

        t0 = time.perf_counter()
        frames = 0
        for frame_idx in range(start_frame + 1, end_frame):
            ffmpeg_proc.stdin.write(renderer.render_frame_bytes(frame_idx))
            frames += 1

        ffmpeg_proc.stdin.close()
        stderr = ffmpeg_proc.stderr.read().decode("utf-8", errors="replace") if ffmpeg_proc.stderr else ""
        rc = ffmpeg_proc.wait()
        elapsed = time.perf_counter() - t0
        if rc != 0:
            raise RuntimeError(f"Benchmark FFmpeg exit={rc}: {stderr.strip()}")
        result_queue.put(("done", worker_id, frames, elapsed, ""))
    except Exception as exc:
        target = result_queue if ready_sent else ready_queue
        try:
            target.put(("error", worker_id, 0, 0.0, repr(exc)) if ready_sent else ("error", worker_id, repr(exc)))
        except Exception:
            pass
    finally:
        if ffmpeg_proc is not None and ffmpeg_proc.poll() is None:
            try:
                if ffmpeg_proc.stdin:
                    ffmpeg_proc.stdin.close()
            except Exception:
                pass
            try:
                ffmpeg_proc.terminate(); ffmpeg_proc.wait(timeout=3)
            except Exception:
                pass


def _run_worker_benchmark(
    gpx_path: str, map_style_key: str, fps: int, duration: float,
    ffmpeg: str, encoder: str, workers: int, benchmark_frames: int, start_frame: int, settings: dict,
):
    """回傳 (aggregate_fps, timed_frames, wall_seconds)。"""
    main_frames = max(1, int(round(duration * fps)))
    workers = max(1, min(int(workers), main_frames))
    window = min(main_frames - start_frame, max(workers * 4, int(benchmark_frames) + workers))
    if window < workers * 2:
        start_frame = 0
        window = min(main_frames, max(workers * 4, int(benchmark_frames) + workers))
    ranges0 = _split_frame_ranges(window, workers)
    ranges = [(start_frame + a, start_frame + b) for a, b in ranges0 if b - a >= 2]
    if not ranges:
        raise RuntimeError("影片太短，無法執行 worker benchmark。")
    workers = len(ranges)

    bench_settings = dict(settings)
    bench_settings.update({
        "ENABLE_BASEMAP": False,
        "MAP_USE_CACHE": False,
        "PARALLEL_DISABLE_TILE_CACHE": True,
        "LOCAL_CACHE_CHUNKS": min(3, max(1, int(bench_settings.get("LOCAL_CACHE_CHUNKS", 3)))),
        "PREVIEW_MODE": False,
    })
    worker_cfg = BenchmarkWorkerConfig(
        gpx_path=gpx_path, map_style_key=map_style_key, fps=fps, video_duration=duration,
        ffmpeg=ffmpeg, encoder=encoder, settings=bench_settings,
    )

    ctx = mp.get_context("spawn")
    start_event = ctx.Event()
    ready_queue = ctx.Queue()
    result_queue = ctx.Queue()
    processes = []
    try:
        for worker_id, (a, b) in enumerate(ranges):
            p = ctx.Process(
                target=_benchmark_worker_entry,
                args=(worker_id, worker_cfg, a, b, start_event, ready_queue, result_queue),
                name=f"benchmark_{workers}w_{worker_id}",
            )
            p.start(); processes.append(p)

        ready = 0
        ready_deadline = time.perf_counter() + 120.0
        while ready < workers:
            if time.perf_counter() > ready_deadline:
                raise TimeoutError(f"{workers} workers benchmark 初始化逾時。")
            try:
                msg = ready_queue.get(timeout=0.25)
            except Exception:
                msg = None
            if msg:
                if msg[0] == "ready":
                    ready += 1
                elif msg[0] == "error":
                    raise RuntimeError(f"Benchmark worker {msg[1] + 1} 初始化失敗：{msg[2]}")
            for i, proc in enumerate(processes):
                if proc.exitcode not in (None, 0):
                    raise RuntimeError(f"Benchmark worker {i + 1} 提前退出，exitcode={proc.exitcode}")

        wall_start = time.perf_counter()
        start_event.set()
        done = 0
        timed_frames = 0
        run_deadline = wall_start + 180.0
        while done < workers:
            if time.perf_counter() > run_deadline:
                raise TimeoutError(f"{workers} workers benchmark 執行逾時。")
            try:
                msg = result_queue.get(timeout=0.25)
            except Exception:
                msg = None
            if msg:
                kind, worker_id, frames, elapsed, payload = msg
                if kind == "done":
                    done += 1
                    timed_frames += int(frames)
                elif kind == "error":
                    raise RuntimeError(f"Benchmark worker {worker_id + 1} 失敗：{payload}")
            for i, proc in enumerate(processes):
                if proc.exitcode not in (None, 0):
                    raise RuntimeError(f"Benchmark worker {i + 1} 異常退出，exitcode={proc.exitcode}")

        wall = time.perf_counter() - wall_start
        aggregate_fps = timed_frames / wall if wall > 0 else 0.0
        return aggregate_fps, timed_frames, wall
    finally:
        try:
            start_event.set()
        except Exception:
            pass
        for proc in processes:
            try:
                proc.join(timeout=1.5)
                if proc.is_alive():
                    proc.terminate(); proc.join(timeout=3.0)
            except Exception:
                pass
        for q in (ready_queue, result_queue):
            try:
                q.close(); q.cancel_join_thread()
            except Exception:
                pass


def _default_benchmark_candidates(current_workers: int | None = None):
    logical = max(1, int(os.cpu_count() or 1))
    cap = min(logical, 16)
    if cap <= 1:
        return [1]
    candidates = [x for x in (2, 4, 6, 8, 10, 12, 14, 16) if x <= cap]
    if current_workers is not None:
        cw = max(1, min(int(current_workers), cap))
        candidates.append(cw)
    if cap not in candidates:
        candidates.append(cap)
    return sorted(set(candidates))


def performance_benchmark_job(config_dict: dict | None = None):
    """GUI Auto Tune 子程序入口。只做短 benchmark，不輸出影片。"""
    config_dict = dict(config_dict or {})
    config.apply_render_config(config_dict)
    gpx_path = str(Path(config_dict.get("gpx_filename", config.gpx_filename)).expanduser().resolve())
    map_style_key = str(config_dict.get("map_style_key", "1"))
    if map_style_key not in config.MAP_STYLE_OPTIONS:
        map_style_key = "1"
    if not Path(gpx_path).is_file():
        raise FileNotFoundError(f"找不到 GPX：{gpx_path}")

    fps = max(1, int(config.FPS))
    duration = max(1.0, float(config.VIDEO_DURATION))
    logical = max(1, int(os.cpu_count() or 1))
    candidates = config_dict.get("BENCHMARK_CANDIDATES")
    if not candidates:
        candidates = _default_benchmark_candidates(config_dict.get("RENDER_WORKERS", config.RENDER_WORKERS))
    candidates = sorted(set(max(1, min(int(x), logical, 16)) for x in candidates))

    default_frames = max(240, min(360, int(round(fps * 5.0))))
    benchmark_frames = max(120, int(config_dict.get("BENCHMARK_FRAMES", default_frames)))
    main_frames = max(1, int(round(duration * fps)))
    max_workers = max(candidates) if candidates else 1
    usable = min(main_frames, benchmark_frames + max_workers)
    benchmark_frames = max(1, usable - max_workers)
    start_frame = max(0, int((main_frames - usable) * 0.20))

    print("=" * 72)
    print("[TEST] Workers Auto Tune")
    print(f"   CPU logical processors：{logical}")
    print(f"   測試解析度：{config.FRAME_WIDTH}x{config.FRAME_HEIGHT} | FPS={fps} | 約 {benchmark_frames} timed frames / 組")
    print("   Benchmark 不下載底圖，避免 CDN / 網速污染結果。")
    print("   會測 GPX camera + route + HUD/minimap/elevation + RGB pipe + FFmpeg/NVENC。")

    ffmpeg = find_ffmpeg()
    encoder = choose_encoder(ffmpeg, fps)
    if encoder != "h264_nvenc":
        result = {
            "recommended_workers": 1, "peak_fps": 0.0, "threshold_ratio": 0.97,
            "results": [], "note": "NVENC 不可用；正式 renderer 會回退單 process，因此建議 Workers=1。",
        }
        print("[WARN] NVENC 不可用，Auto Tune 不進行多程序測試。")
        print("AUTO_TUNE_RESULT:" + json.dumps(result, ensure_ascii=False))
        return result

    settings = config.snapshot_render_config()
    results = []
    prev_fps = None
    for idx, workers in enumerate(candidates, start=1):
        print(f"[TEST] 效能測試 [{idx}/{len(candidates)}] Workers={workers} ...", flush=True)
        try:
            agg_fps, frames_done, wall = _run_worker_benchmark(
                gpx_path=gpx_path, map_style_key=map_style_key, fps=fps, duration=duration,
                ffmpeg=ffmpeg, encoder=encoder, workers=workers, benchmark_frames=benchmark_frames,
                start_frame=start_frame, settings=settings,
            )
        except Exception as exc:
            print(f"[WARN] Workers={workers} 測試失敗：{exc}")
            print("   將以目前已成功的測試結果決定建議值，並停止測更高 Workers。")
            break
        gain = None if prev_fps is None or prev_fps <= 0 else (agg_fps / prev_fps - 1.0) * 100.0
        gain_text = "baseline" if gain is None else f"{gain:+.1f}% vs previous"
        print(f"[RESULT] Workers={workers}: {agg_fps:.1f} frame/s | {frames_done} frames / {wall:.2f}s | {gain_text}")
        results.append({"workers": workers, "fps": round(agg_fps, 3), "wall_seconds": round(wall, 3)})
        prev_fps = agg_fps

    if not results:
        raise RuntimeError("所有 Workers benchmark 都失敗，無法產生 Auto Tune 建議。")

    peak = max(r["fps"] for r in results) if results else 0.0
    threshold_ratio = 0.97
    threshold = peak * threshold_ratio
    eligible = [r for r in results if r["fps"] >= threshold]
    recommended = min(eligible, key=lambda r: r["workers"])["workers"] if eligible else (results[-1]["workers"] if results else 1)
    rec_row = next((r for r in results if r["workers"] == recommended), None)
    rec_fps = rec_row["fps"] if rec_row else 0.0

    note = (
        f"選擇達到峰值 {threshold_ratio*100:.0f}% 以上的最少 workers，"
        f"避免只為幾個百分點增加 RAM / 排程競爭。"
    )
    result = {
        "recommended_workers": int(recommended),
        "recommended_fps": round(float(rec_fps), 3),
        "peak_fps": round(float(peak), 3),
        "threshold_ratio": threshold_ratio,
        "results": results,
        "note": note,
    }
    print(f"[RESULT] 建議 Workers={recommended} | 約 {rec_fps:.1f} fps | 峰值 {peak:.1f} fps")
    print("   " + note)
    print("AUTO_TUNE_RESULT:" + json.dumps(result, ensure_ascii=False), flush=True)
    return result


def _split_frame_ranges(total_frames: int, segments: int):
    segments = max(1, min(int(segments), int(total_frames)))
    edges = np.linspace(0, total_frames, segments + 1, dtype=np.int64)
    out = []
    for i in range(segments):
        a, b = int(edges[i]), int(edges[i + 1])
        if b > a:
            out.append((a, b))
    return out


def _choose_dynamic_chunk_count(total_frames: int, fps: int, workers: int) -> int:
    desired = max(workers, workers * max(1, int(config.CHUNKS_PER_WORKER)))
    min_frames = max(1, int(round(max(0.25, float(config.MIN_CHUNK_SECONDS)) * max(1, int(fps)))))
    max_by_size = max(1, total_frames // min_frames)
    lower = min(workers, total_frames)
    return max(lower, min(desired, max_by_size, total_frames))


def _encode_chunk_with_renderer(renderer: RideRenderer, task: SegmentTask, ffmpeg: str, encoder: str, worker_id: int, result_queue):
    cmd = build_ffmpeg_command(ffmpeg, encoder, task.output_path, renderer.fps)
    process = subprocess.Popen(
        cmd, stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE,
        bufsize=16 * 1024 * 1024,
        **_background_subprocess_kwargs(),
    )
    if process.stdin is None:
        raise RuntimeError(f"Chunk {task.segment_index}: 無法開啟 FFmpeg stdin。")

    start_t = time.perf_counter()
    last_progress_t = start_t
    total = task.end_frame - task.start_frame
    result_queue.put(("start", worker_id, task.segment_index, 0, total, ""))
    try:
        for frame_idx in range(task.start_frame, task.end_frame):
            process.stdin.write(renderer.render_frame_bytes(frame_idx))
            now = time.perf_counter()
            if now - last_progress_t >= 0.45:
                done_local = frame_idx - task.start_frame + 1
                result_queue.put(("progress", worker_id, task.segment_index, done_local, total, ""))
                last_progress_t = now
        process.stdin.close()
        stderr = process.stderr.read().decode("utf-8", errors="replace") if process.stderr else ""
        rc = process.wait()
        if rc != 0:
            raise RuntimeError(f"Chunk {task.segment_index} FFmpeg exit={rc}\n{stderr.strip()}")
    except Exception:
        try:
            process.stdin.close()
        except Exception:
            pass
        try:
            process.terminate(); process.wait(timeout=5)
        except Exception:
            pass
        raise

    elapsed = time.perf_counter() - start_t
    result_queue.put(("done", worker_id, task.segment_index, total, total, f"{elapsed:.9f}"))


def _dynamic_worker_loop(worker_id: int, worker_cfg: DynamicWorkerConfig, task_queue, result_queue):
    try:
        config.apply_render_config(worker_cfg.settings)
        session_id = str(worker_cfg.settings.get("MAP_CACHE_SESSION_ID") or "")
        if session_id:
            CacheManager.set_session_id(session_id)
        CacheManager.init_cache_system()
        if HAVE_CV2:
            try:
                cv2.setNumThreads(max(1, int(config.CV2_THREADS_PER_WORKER)))
            except Exception:
                pass
        data = load_gpx(worker_cfg.gpx_path)
        map_style = config.MAP_STYLE_OPTIONS[worker_cfg.map_style_key][1]
        media_items = None
        if config.ENABLE_MEDIA and config.MEDIA_PATH:
            from gpx_renderer.core.media import scan_media_files, match_media_to_ride
            raw_media = scan_media_files(config.MEDIA_PATH, time_offset_sec=config.MEDIA_TIME_OFFSET_SEC, ffmpeg_exe=worker_cfg.ffmpeg)
            media_items = match_media_to_ride(raw_media, data, data.gpx_times)

        renderer = RideRenderer(
            data=data, overview_map=None, map_style=map_style, fps=worker_cfg.fps,
            video_duration=worker_cfg.video_duration, zoom_out_duration=0.0, end_hold_duration=0.0,
            tile_cache_enabled=not config.PARALLEL_DISABLE_TILE_CACHE,
            media_items=media_items,
        )
        result_queue.put(("ready", worker_id, -1, 0, 0, ""))
        while True:
            task = task_queue.get()
            if task is None:
                break
            try:
                _encode_chunk_with_renderer(renderer, task, worker_cfg.ffmpeg, worker_cfg.encoder, worker_id, result_queue)
                gc.collect()
            except Exception as exc:
                result_queue.put(("error", worker_id, task.segment_index, 0, 0, repr(exc)))
                return
        result_queue.put(("exit", worker_id, -1, 0, 0, ""))
    except Exception as exc:
        result_queue.put(("error", worker_id, -1, 0, 0, repr(exc)))


def encode_video_parallel(
    data: RideData,
    gpx_path: str,
    map_style_key: str,
    map_style,
    fps: int,
    duration: float,
    ffmpeg: str,
    encoder: str,
    output: str,
    media_items: list | None = None,
):
    temp_renderer = RideRenderer(
        data=data,
        overview_map=None,
        map_style=map_style,
        fps=fps,
        video_duration=duration,
        zoom_out_duration=0.0,
        end_hold_duration=0.0,
        tile_cache_enabled=True,
        media_items=media_items,
    )
    main_frames = temp_renderer.main_frames
    workers = max(1, min(int(config.RENDER_WORKERS), main_frames))
    chunk_count = _choose_dynamic_chunk_count(main_frames, fps, workers)
    ranges = _split_frame_ranges(main_frames, chunk_count)

    temp_dir = Path(tempfile.mkdtemp(prefix="gpx_render_v7_2_"))
    print(f"[INFO] 動態排程：{workers} persistent workers / {len(ranges)} chunks / {main_frames} frames")
    print(f"   平均 chunk：約 {main_frames / max(len(ranges), 1) / max(fps, 1):.1f}s；誰先做完就立即拿下一塊。")
    print(f"   暫存 segments：{temp_dir}")
    if config.PARALLEL_DISABLE_TILE_CACHE:
        print("   並行 worker 已停用 contextily/joblib 磁碟 cache，避免多程序 contention。")

    tasks = [
        SegmentTask(i, a, b, str(temp_dir / f"main_{i:04d}.mp4"))
        for i, (a, b) in enumerate(ranges)
    ]
    worker_cfg = DynamicWorkerConfig(
        gpx_path=gpx_path, map_style_key=map_style_key, fps=fps, video_duration=duration,
        ffmpeg=ffmpeg, encoder=encoder, settings=config.snapshot_render_config(),
    )

    wall_start = time.perf_counter()
    processes = []
    task_queue = None
    result_queue = None
    chunk_progress = {t.segment_index: 0 for t in tasks}
    chunk_totals = {t.segment_index: t.end_frame - t.start_frame for t in tasks}
    completed_paths = {}
    worker_status = {i: "啟動中" for i in range(workers)}
    worker_pct = {i: 0.0 for i in range(workers)}
    finished_chunks = 0

    try:
        ctx = mp.get_context("spawn")
        task_queue = ctx.Queue()
        result_queue = ctx.Queue()
        for task in tasks:
            task_queue.put(task)
        for _ in range(workers):
            task_queue.put(None)

        for worker_id in range(workers):
            p = ctx.Process(
                target=_dynamic_worker_loop, args=(worker_id, worker_cfg, task_queue, result_queue),
                name=f"dynamic_render_{worker_id}",
            )
            p.start(); processes.append(p)

        last_progress_print = 0.0
        while finished_chunks < len(tasks):
            try:
                kind, worker_id, chunk_idx, done_local, total, payload = result_queue.get(timeout=0.25)
            except Exception:
                kind = None

            if kind == "ready":
                worker_status[worker_id] = "待命"
                worker_pct[worker_id] = 0.0
            elif kind == "start":
                worker_status[worker_id] = f"C{chunk_idx + 1}/{len(tasks)} 0%"
                worker_pct[worker_id] = 0.0
            elif kind == "progress":
                chunk_progress[chunk_idx] = max(chunk_progress.get(chunk_idx, 0), int(done_local))
                local_pct = 100.0 * done_local / max(total, 1)
                worker_status[worker_id] = f"C{chunk_idx + 1}/{len(tasks)} {local_pct:.0f}%"
                worker_pct[worker_id] = local_pct
            elif kind == "done":
                chunk_progress[chunk_idx] = int(total)
                completed_paths[chunk_idx] = tasks[chunk_idx].output_path
                finished_chunks = len(completed_paths)
                elapsed = float(payload) if payload else 0.0
                fps_done = total / elapsed if elapsed > 0 else 0.0
                worker_status[worker_id] = "拿下一塊…" if finished_chunks < len(tasks) else "完成"
                worker_pct[worker_id] = 100.0
                print(f"\n[OK] Chunk {chunk_idx + 1}/{len(tasks)} 完成：{total} frames | {fps_done:.1f} frame/s | Worker {worker_id + 1}")
            elif kind == "exit":
                worker_status[worker_id] = "完成"
                worker_pct[worker_id] = 100.0
            elif kind == "error":
                raise RuntimeError(f"Worker {worker_id + 1} / chunk {chunk_idx + 1 if chunk_idx >= 0 else '?'} 失敗：\n{payload}")

            now = time.perf_counter()
            if now - last_progress_print >= 0.45 or finished_chunks == len(tasks):
                rendered = sum(min(chunk_progress[i], chunk_totals[i]) for i in chunk_progress)
                wall_elapsed = now - wall_start
                live_fps = rendered / wall_elapsed if wall_elapsed > 0 else 0.0
                pct = rendered * 100.0 / max(main_frames, 1)
                eta = (main_frames - rendered) / live_fps if live_fps > 0 else math.inf
                eta_text = f"{eta:.0f}s" if math.isfinite(eta) else "--"
                parts = [f"W{i+1}:{worker_status[i]}" for i in range(workers)]
                print(
                    f"\r[PROGRESS] 主動畫 {pct:6.2f}% | {rendered:>6}/{main_frames} frames | "
                    f"等效 {live_fps:6.1f} frame/s | ETA {eta_text} | " + " ".join(parts),
                    end="", flush=True,
                )
                progress_payload = {
                    "pct": round(pct, 2),
                    "rendered": rendered,
                    "total": main_frames,
                    "fps": round(live_fps, 1),
                    "eta_seconds": round(eta, 1) if math.isfinite(eta) else None,
                    "workers": [
                        {
                            "id": i + 1,
                            "status": worker_status[i],
                            "pct": round(worker_pct[i], 1),
                        }
                        for i in range(workers)
                    ],
                }
                print("\n[PROGRESS_JSON]" + json.dumps(progress_payload, ensure_ascii=False), flush=True)
                last_progress_print = now

            for idx, proc in enumerate(processes):
                if proc.exitcode not in (None, 0):
                    raise RuntimeError(f"Worker {idx + 1} 異常退出，exitcode={proc.exitcode}")

        print()
        for idx, proc in enumerate(processes):
            proc.join(timeout=3.0)
            if proc.is_alive():
                print(f"[WARN] Worker {idx + 1} 收尾逾時，強制結束（所有 chunk 已完成）。")
                proc.terminate(); proc.join(timeout=5.0)

        main_paths = [completed_paths[i] for i in range(len(tasks))]
        print("[MAP] 準備結尾 overview...")
        overview_map = build_overview_raster_map(data, map_style)
        end_renderer = RideRenderer(
            data=data, overview_map=overview_map, map_style=map_style, fps=fps,
            video_duration=duration, zoom_out_duration=config.ZOOM_OUT_DURATION, end_hold_duration=config.END_HOLD_DURATION,
            tile_cache_enabled=True,
        )
        end_path = temp_dir / "end.mp4"
        if _encode_end_segment(end_renderer, ffmpeg, encoder, str(end_path)):
            main_paths.append(str(end_path))

        print("[INFO] 合併 chunks（stream copy，不重新編碼）...")
        _concat_mp4_segments(ffmpeg, main_paths, output, temp_dir)
        wall = time.perf_counter() - wall_start
        total_frames = main_frames + end_renderer.zoom_frames + end_renderer.hold_frames
        print(f"[RESULT] V1.0.0 wall-clock：{wall:.1f}s | 等效 {total_frames / wall if wall > 0 else 0.0:.1f} frame/s")
    finally:
        for proc in processes:
            try:
                if proc.is_alive(): proc.terminate()
                proc.join(timeout=1.0)
            except Exception:
                pass
        for q in (task_queue, result_queue):
            if q is not None:
                try: q.close()
                except Exception: pass
                try: q.cancel_join_thread()
                except Exception: pass
        if config.KEEP_TEMP_SEGMENTS:
            print(f"[INFO] 保留暫存 chunks：{temp_dir}")
        else:
            shutil.rmtree(temp_dir, ignore_errors=True)


def _print_render_job_summary(
    data: RideData,
    config_dict: dict,
    map_label: str,
    map_style_key: str,
    fps: int,
    duration: float,
    total_frames: int,
    encoder: str,
    output_path: str,
    parallel_ok: bool,
    prefetch_stats: dict | None,
    render_elapsed: float,
    job_elapsed: float,
    matched_media: list,
):
    out_file = Path(output_path)
    out_size_mb = out_file.stat().st_size / (1024 * 1024) if out_file.is_file() else 0.0
    prefetch_stats = prefetch_stats or {}
    prefetch_elapsed = prefetch_stats.get("elapsed", 0.0)
    prefetch_chunks = prefetch_stats.get("total_chunks", 0)
    new_tiles = prefetch_stats.get("new_tiles", 0)
    new_dem = prefetch_stats.get("new_dem", 0)
    new_mb = prefetch_stats.get("new_bytes", 0) / (1024 * 1024)
    total_cache_mb = CacheManager.get_cache_size_mb()
    total_tiles = prefetch_stats.get("total_tiles", 0)

    encoder_quality = ""
    if "nvenc" in encoder:
        encoder_quality = f"NVENC 位元率: {config.NVENC_BITRATE} (preset: {config.NVENC_PRESET})"
    else:
        encoder_quality = f"CPU x264 (CRF: {config.CPU_CRF}, preset: {config.CPU_PRESET})"

    print("\n" + "=" * 78)
    print("                      GPX RIDE RENDERER 渲染完成報告                      ")
    print("=" * 78)
    print("\n[1] 路線與騎乘統計數據 (Ride Statistics)")
    print(f"  - GPX 檔案路徑       : {config.gpx_filename}")
    print(f"  - 路線總長度         : {data.distances[-1]:.2f} km")
    print(f"  - 累積總爬升         : +{data.elevation_gain[-1]:.0f} m")
    print(f"  - GPS 軌跡點數       : {data.total_points} 點")

    total_reqs = prefetch_stats.get("total_requests", 0)
    total_hits = prefetch_stats.get("total_hits", 0)
    total_misses = prefetch_stats.get("total_misses", 0)
    hit_rate = prefetch_stats.get("hit_rate_pct", 0.0)

    print("\n[2] 底圖預熱與快取統計 (Basemap & Cache Statistics)")
    print(f"  - 底圖預熱狀態       : {'啟用' if config.ENABLE_BASEMAP else '停用'} (風格: {map_label})")
    print(f"  - 下載預熱耗時       : {prefetch_elapsed:.2f} 秒 ({format_seconds_human(prefetch_elapsed)})")
    print(f"  - 路線涵蓋區塊       : {prefetch_chunks} 個局部網格區塊 (Zoom {config.LOCAL_MAP_ZOOM})")
    print(f"  - 切片請求總數       : {total_reqs} 次 (底圖切片: {prefetch_stats.get('tile_hits', 0) + prefetch_stats.get('tile_misses', 0)}, DEM: {prefetch_stats.get('dem_hits', 0) + prefetch_stats.get('dem_misses', 0)})")
    print(f"  - 本機快取再利用率   : {hit_rate:.1f}% (命中再利用: {total_hits} 次, 遠端新下載: {total_misses} 次)")
    print(f"  - 本次新增圖資       : +{new_tiles} 個 PNG 切片, +{new_dem} 個 DEM 區塊 (+{new_mb:.2f} MB)")
    print(f"  - 本機快取總容量     : {total_cache_mb:.2f} MB (共 {total_tiles} 個切片檔案)")
    print(f"  - 快取儲存模式       : {'Session 暫存 (關閉自動清理)' if CacheManager.get_mode() == 'session' else 'Persistent 永久保留'} (上限: {config.MAP_CACHE_MAX_MB} MB)")

    print("\n[3] 渲染效能與輸出結果 (Render & Output Performance)")
    print(f"  - 輸出影片檔案       : {output_path} ({out_size_mb:.2f} MB)")
    print(f"  - 畫面解析度與規格   : {config.FRAME_WIDTH}x{config.FRAME_HEIGHT} @ {fps} FPS (總畫格數: {total_frames} 幀)")
    print(f"  - 影片時長構成       : 主動畫 {duration:.1f}s + 結尾縮放 {config.ZOOM_OUT_DURATION:.1f}s + 結尾停留 {config.END_HOLD_DURATION:.1f}s (總時長: {total_frames / fps:.1f}s)")
    print(f"  - 編碼器與品質       : {encoder} | {encoder_quality}")
    print(f"  - 渲染並行模式       : {f'多程序並行 ({config.RENDER_WORKERS} Workers × {config.CHUNKS_PER_WORKER} chunks)' if parallel_ok else '單程序 (Single-process)'}")
    print(f"  - 底圖預載耗時       : {prefetch_elapsed:.2f} 秒 ({format_seconds_human(prefetch_elapsed)})")
    print(f"  - 主渲染運算耗時     : {render_elapsed:.2f} 秒 ({format_seconds_human(render_elapsed)})")
    print(f"  - 總流程執行耗時     : {job_elapsed:.2f} 秒 ({format_seconds_human(job_elapsed)})")
    render_fps = total_frames / max(render_elapsed, 0.001)
    overall_fps = total_frames / max(job_elapsed, 0.001)
    print(f"  - 平均渲染速率       : {render_fps:.1f} frame/s (主渲染) | {overall_fps:.1f} frame/s (全流程等效)")

    print("\n[4] 完整設定參數清單 (Configuration Parameters)")
    params = [
        ("gpx_filename", str(config.gpx_filename)),
        ("output_filename", str(config.output_filename)),
        ("FRAME_WIDTH", config.FRAME_WIDTH),
        ("FRAME_HEIGHT", config.FRAME_HEIGHT),
        ("FPS", config.FPS),
        ("VIDEO_DURATION", f"{config.VIDEO_DURATION:.1f}s"),
        ("AUTO_DURATION_ENABLED", config_dict.get("AUTO_DURATION_ENABLED", config.AUTO_DURATION_DEFAULT)),
        ("AUTO_SECONDS_PER_100KM", config_dict.get("AUTO_SECONDS_PER_100KM", config.AUTO_SECONDS_PER_100KM)),
        ("ZOOM_OUT_DURATION", f"{config.ZOOM_OUT_DURATION:.1f}s"),
        ("END_HOLD_DURATION", f"{config.END_HOLD_DURATION:.1f}s"),
        ("VIEW_MARGIN", f"{config.VIEW_MARGIN}m"),
        ("CAMERA_MODE", config.CAMERA_MODE),
        ("CAMERA_SMOOTH", config.CAMERA_SMOOTH),
        ("CAMERA_ROTATION_SMOOTH", config.CAMERA_ROTATION_SMOOTH),
        ("CAMERA_MAX_ROTATION_SPEED_DEG", f"{config.CAMERA_MAX_ROTATION_SPEED_DEG} deg/s"),
        ("CAMERA_PITCH_DEG", f"{config.CAMERA_PITCH_DEG} deg"),
        ("ELEVATION_EXAGGERATION", f"{config.ELEVATION_EXAGGERATION}x"),
        ("MAP_STYLE", f"{map_label} (Key: {map_style_key})"),
        ("ENABLE_BASEMAP", config.ENABLE_BASEMAP),
        ("LOCAL_MAP_ZOOM", config.LOCAL_MAP_ZOOM),
        ("OVERVIEW_MAP_ZOOM", config.OVERVIEW_MAP_ZOOM),
        ("LOCAL_CHUNK_STEP_M", f"{config.LOCAL_CHUNK_STEP_M}m"),
        ("LOCAL_CHUNK_BUFFER_M", f"{config.LOCAL_CHUNK_BUFFER_M}m"),
        ("TRACK_COLOR_SCHEME", config.TRACK_COLOR_SCHEME),
        ("TRACK_LINE_WIDTH", f"{config.TRACK_LINE_WIDTH}px"),
        ("SHOW_SPEED_HUD", config.SHOW_SPEED_HUD),
        ("SHOW_MINIMAP", config.SHOW_MINIMAP),
        ("SHOW_ELEVATION", config.SHOW_ELEVATION),
        ("ENABLE_DYNAMIC_SPEED_ZOOM", getattr(config, "ENABLE_DYNAMIC_SPEED_ZOOM", False)),
        ("USE_REAL_SPEED", getattr(config, "USE_REAL_SPEED", True)),
        ("HIDE_START_DISTANCE_KM", f"{config_dict.get('HIDE_START_DISTANCE_KM', 0.0)} km"),
        ("HIDE_END_DISTANCE_KM", f"{config_dict.get('HIDE_END_DISTANCE_KM', 0.0)} km"),
        ("PARALLEL_RENDER", config.PARALLEL_RENDER),
        ("RENDER_WORKERS", config.RENDER_WORKERS),
        ("CHUNKS_PER_WORKER", config.CHUNKS_PER_WORKER),
        ("CV2_THREADS_PER_WORKER", config.CV2_THREADS_PER_WORKER),
        ("MAP_CACHE_MODE", config.MAP_CACHE_MODE),
        ("MAP_CACHE_MAX_MB", f"{config.MAP_CACHE_MAX_MB} MB"),
        ("MAP_CACHE_SESSION_ID", config.MAP_CACHE_SESSION_ID or "(None)"),
        ("ENABLE_MEDIA", config.ENABLE_MEDIA),
        ("MEDIA_PATH", config.MEDIA_PATH or "(None)"),
        ("MEDIA_POPUP_DURATION", f"{config.MEDIA_POPUP_DURATION}s"),
        ("MEDIA_CAPTION_FONT_SIZE", f"{config.MEDIA_CAPTION_FONT_SIZE}pt"),
        ("MEDIA_TIME_OFFSET_SEC", f"{config.MEDIA_TIME_OFFSET_SEC}s"),
        ("MATCHED_MEDIA_COUNT", len(matched_media)),
    ]
    for k, v in params:
        print(f"  - {k:<30}: {v}")
    print("=" * 78 + "\n")


def render_job(config_dict: dict | None = None):
    """實際渲染入口。可由 CLI 或 Tkinter 啟動的子程序呼叫。"""
    job_start_wall = time.perf_counter()
    config_dict = dict(config_dict or {})
    config.apply_render_config(config_dict)

    session_id = str(config_dict.get("MAP_CACHE_SESSION_ID") or config.MAP_CACHE_SESSION_ID or "")
    if session_id:
        CacheManager.set_session_id(session_id)
    CacheManager.init_cache_system()

    if config_dict.get("gpx_filename"):
        config.gpx_filename = str(config_dict["gpx_filename"])
    if config_dict.get("output_filename"):
        config.output_filename = str(config_dict["output_filename"])

    map_style_key = str(config_dict.get("map_style_key", "1"))
    if map_style_key not in config.MAP_STYLE_OPTIONS:
        map_style_key = "1"
    map_label, map_style = config.MAP_STYLE_OPTIONS[map_style_key]
    print(f"[INFO] 地圖風格：{map_label}")

    fps = config.PREVIEW_FPS if config.PREVIEW_MODE else config.FPS
    duration = min(config.VIDEO_DURATION, config.PREVIEW_DURATION) if config.PREVIEW_MODE else config.VIDEO_DURATION
    gpx_path = str(Path(config.gpx_filename).expanduser().resolve())
    output_path = str(Path(config.output_filename).expanduser().resolve())

    if not Path(gpx_path).is_file():
        raise FileNotFoundError(f"找不到 GPX：{gpx_path}")
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)

    print(f"[INFO] 讀取 GPX：{gpx_path}")
    data = load_gpx(gpx_path)
    print(
        f"[OK] {data.total_points} points | "
        f"{data.distances[-1]:.2f} km | "
        f"+{data.elevation_gain[-1]:.0f} m"
    )
    if config_dict.get("AUTO_DURATION_ENABLED"):
        rate = float(config_dict.get("AUTO_SECONDS_PER_100KM", config.AUTO_SECONDS_PER_100KM))
        print(
            f"[INFO] 自動主動畫時長：{data.distances[-1]:.2f} km × {rate:g}s/100km "
            f"→ {config.VIDEO_DURATION:.1f}s ({format_seconds_human(config.VIDEO_DURATION)})"
        )

    ffmpeg = find_ffmpeg()
    print(f"[INFO] FFmpeg：{ffmpeg}")
    encoder = choose_encoder(ffmpeg, fps)

    matched_media = []
    if config.ENABLE_MEDIA and config.MEDIA_PATH:
        from gpx_renderer.core.media import scan_media_files, match_media_to_ride
        print(f"[INFO] 掃描路線媒體：{config.MEDIA_PATH}")
        raw_media = scan_media_files(config.MEDIA_PATH, time_offset_sec=config.MEDIA_TIME_OFFSET_SEC, ffmpeg_exe=ffmpeg)
        matched_media = match_media_to_ride(raw_media, data, data.gpx_times)
        print(f"[OK] 掃描到 {len(raw_media)} 個媒體檔案，成功與路線對齊 {len(matched_media)} 個時間點/座標")

    # 1. 預熱全路線底圖切片，確保所有 Worker 均可 100% 離線讀取快取避免伺服器限流
    prefetch_stats = None
    if config.ENABLE_BASEMAP:
        from gpx_renderer.core.map_utils import prefetch_route_basemap_chunks
        prefetch_stats = prefetch_route_basemap_chunks(data, config.MAP_STYLE_OPTIONS[map_style_key][1], config.LOCAL_MAP_ZOOM)

    temp_info_renderer = RideRenderer(
        data=data,
        overview_map=None,
        map_style=config.MAP_STYLE_OPTIONS[map_style_key][1],
        fps=fps,
        video_duration=duration,
        zoom_out_duration=config.ZOOM_OUT_DURATION,
        end_hold_duration=config.END_HOLD_DURATION,
        tile_cache_enabled=True,
        media_items=matched_media,
    )
    main_frames = temp_info_renderer.main_frames
    total_frames = temp_info_renderer.total_frames
    print(
        f"[INFO] V1.0.0 renderer：{config.FRAME_WIDTH}x{config.FRAME_HEIGHT} @ {fps} FPS | "
        f"{total_frames} frames | {total_frames / fps:.1f}s"
    )
    print("   Local chunk 會增量記住已畫軌跡；主動畫不再每幀重畫全部歷史 segments。")
    if config.PREVIEW_MODE:
        print(f"[INFO] Preview：{config.PREVIEW_DURATION:.1f}s 主動畫，但仍允許 {config.RENDER_WORKERS} workers 多程序渲染。")

    use_parallel = bool(
        config.PARALLEL_RENDER
        and config.RENDER_WORKERS > 1
        and encoder == "h264_nvenc"
    )

    parallel_ok = False
    render_start_wall = time.perf_counter()
    if use_parallel:
        print(
            f"[INFO] Parallel render ON：{config.RENDER_WORKERS} process(es), "
            f"OpenCV {config.CV2_THREADS_PER_WORKER} thread(s)/process"
        )
        try:
            encode_video_parallel(
                data=data,
                gpx_path=gpx_path,
                map_style_key=map_style_key,
                map_style=map_style,
                fps=fps,
                duration=duration,
                ffmpeg=ffmpeg,
                encoder=encoder,
                output=output_path,
                media_items=matched_media,
            )
            parallel_ok = True
        except Exception as exc:
            print(f"[WARN] Parallel render 失敗，將自動回退單 process：{exc}")

    if not parallel_ok:
        reasons = []
        if not config.PARALLEL_RENDER:
            reasons.append("多程序未啟用")
        if config.RENDER_WORKERS <= 1:
            reasons.append(f"Workers={config.RENDER_WORKERS}")
        if encoder != "h264_nvenc":
            reasons.append(f"encoder={encoder}")
        if reasons:
            print("[INFO] 單 process 原因：" + "；".join(reasons))
        if HAVE_CV2:
            try:
                cv2.setNumThreads(max(1, min(os.cpu_count() or 1, 6)))
            except Exception:
                pass
        overview_map = build_overview_raster_map(data, map_style)
        renderer = RideRenderer(
            data=data,
            overview_map=overview_map,
            map_style=map_style,
            fps=fps,
            video_duration=duration,
            zoom_out_duration=config.ZOOM_OUT_DURATION,
            end_hold_duration=config.END_HOLD_DURATION,
            media_items=matched_media,
        )
        print("[INFO] 使用單 process fallback。")
        encode_video(renderer, ffmpeg, encoder, output_path)

    render_elapsed = time.perf_counter() - render_start_wall
    job_elapsed = time.perf_counter() - job_start_wall

    _print_render_job_summary(
        data=data,
        config_dict=config_dict,
        map_label=map_label,
        map_style_key=map_style_key,
        fps=fps,
        duration=duration,
        total_frames=total_frames,
        encoder=encoder,
        output_path=output_path,
        parallel_ok=parallel_ok,
        prefetch_stats=prefetch_stats,
        render_elapsed=render_elapsed,
        job_elapsed=job_elapsed,
        matched_media=matched_media,
    )

    print(f"[DONE] 完成：{output_path}")
