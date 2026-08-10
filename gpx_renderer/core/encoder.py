# -*- coding: utf-8 -*-
"""
FFmpeg 搜尋、NVENC/CPU 編碼器檢測、轉碼指令建立、單程序渲染與 MP4 片段合併。
"""

from __future__ import annotations
import os
import sys
import math
import time
import shutil
import subprocess
from pathlib import Path

from gpx_renderer import config
from gpx_renderer.utils import application_dir, _background_subprocess_kwargs


def find_ffmpeg() -> str:
    local_name = "ffmpeg.exe" if os.name == "nt" else "ffmpeg"
    bundled_ffmpeg = application_dir() / local_name
    if bundled_ffmpeg.is_file():
        return str(bundled_ffmpeg)

    system_ffmpeg = shutil.which("ffmpeg")
    if system_ffmpeg:
        return system_ffmpeg

    try:
        import imageio_ffmpeg
        return imageio_ffmpeg.get_ffmpeg_exe()
    except Exception as exc:
        raise RuntimeError(
            "找不到 FFmpeg。EXE 版請把 ffmpeg.exe 放在主程式旁，"
            "或安裝 FFmpeg / imageio-ffmpeg。"
        ) from exc


def encoder_is_listed(ffmpeg: str, encoder: str) -> bool:
    try:
        result = subprocess.run(
            [ffmpeg, "-hide_banner", "-encoders"],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=10,
            check=False,
            **_background_subprocess_kwargs(),
        )
        return encoder in result.stdout
    except Exception:
        return False


def encoder_works(ffmpeg: str, encoder: str, fps: int) -> bool:
    if not encoder_is_listed(ffmpeg, encoder):
        return False

    cmd = [
        ffmpeg,
        "-hide_banner",
        "-loglevel", "error",
        "-f", "lavfi",
        "-i", f"color=c=black:s={config.FRAME_WIDTH}x{config.FRAME_HEIGHT}:r={fps}:d=0.1",
        "-frames:v", "1",
        "-an",
        "-c:v", encoder,
    ]

    if encoder == "h264_nvenc":
        cmd += ["-preset", config.NVENC_PRESET, "-pix_fmt", "yuv420p"]
    else:
        cmd += ["-preset", config.CPU_PRESET, "-pix_fmt", "yuv420p"]

    cmd += ["-f", "null", "-"]

    try:
        result = subprocess.run(
            cmd,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=15,
            check=False,
            **_background_subprocess_kwargs(),
        )
        if result.returncode == 0:
            return True

        print(f"[WARN] {encoder} 測試失敗：")
        if result.stderr.strip():
            print(result.stderr.strip())
        return False
    except Exception as exc:
        print(f"[WARN] {encoder} 測試例外：{exc}")
        return False


def choose_encoder(ffmpeg: str, fps: int):
    if config.USE_GPU_IF_AVAILABLE:
        print("[INFO] 偵測 NVIDIA NVENC...")
        if encoder_works(ffmpeg, "h264_nvenc", fps):
            print("[INFO] 已啟用 RTX / NVIDIA NVENC：h264_nvenc")
            return "h264_nvenc"
        print("[INFO] NVENC 未通過實際測試，回退 CPU。")

    if encoder_works(ffmpeg, "libx264", fps):
        print(f"[INFO] 使用 CPU 編碼：libx264 ({config.CPU_PRESET})")
        return "libx264"

    raise RuntimeError("找不到可用的 h264_nvenc 或 libx264。")


def build_ffmpeg_command(ffmpeg: str, encoder: str, output: str, fps: int):
    cmd = [
        ffmpeg,
        "-y",
        "-hide_banner",
        "-loglevel", config.FFMPEG_LOGLEVEL,
        "-f", "rawvideo",
        "-vcodec", "rawvideo",
        "-pix_fmt", "rgb24",
        "-s:v", f"{config.FRAME_WIDTH}x{config.FRAME_HEIGHT}",
        "-r", str(fps),
        "-i", "-",
        "-an",
    ]

    if encoder == "h264_nvenc":
        cmd += [
            "-c:v", "h264_nvenc",
            "-preset", config.NVENC_PRESET,
            "-tune", "hq",
            "-rc", "vbr",
            "-b:v", config.NVENC_BITRATE,
            "-maxrate", config.NVENC_BITRATE,
            "-bufsize", "24M",
        ]
    else:
        cmd += [
            "-c:v", "libx264",
            "-preset", config.CPU_PRESET,
            "-crf", str(config.CPU_CRF),
            "-threads", str(max(1, os.cpu_count() or 1)),
        ]

    cmd += [
        "-pix_fmt", "yuv420p",
        "-movflags", "+faststart",
        output,
    ]
    return cmd


def encode_video(renderer, ffmpeg: str, encoder: str, output: str):
    cmd = build_ffmpeg_command(ffmpeg, encoder, output, renderer.fps)

    process = subprocess.Popen(
        cmd,
        stdin=subprocess.PIPE,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.PIPE,
        bufsize=16 * 1024 * 1024,
        **_background_subprocess_kwargs(),
    )

    if process.stdin is None:
        raise RuntimeError("無法開啟 FFmpeg stdin pipe。")

    start = time.perf_counter()
    last_report = start

    try:
        for frame_idx in range(renderer.total_frames):
            process.stdin.write(renderer.render_frame_bytes(frame_idx))

            now = time.perf_counter()
            if now - last_report >= 1.0 or frame_idx == renderer.total_frames - 1:
                done = frame_idx + 1
                elapsed = now - start
                render_fps = done / elapsed if elapsed > 0 else 0.0
                pct = done / renderer.total_frames * 100.0
                eta = (renderer.total_frames - done) / render_fps if render_fps > 0 else math.inf
                eta_text = f"{eta:.0f}s" if math.isfinite(eta) else "--"

                realtime = render_fps / renderer.fps if renderer.fps > 0 else 0.0
                print(
                    f"\r[PROGRESS] {done:>6}/{renderer.total_frames}  "
                    f"{pct:6.2f}%  {render_fps:6.1f} frame/s  "
                    f"{realtime:4.2f}x realtime  ETA {eta_text}",
                    end="",
                    flush=True,
                )
                last_report = now

        process.stdin.close()
        stderr = process.stderr.read().decode("utf-8", errors="replace") if process.stderr else ""
        return_code = process.wait()
        print()
        if return_code != 0:
            raise RuntimeError(f"FFmpeg 結束碼：{return_code}\n{stderr.strip()}")

    except (BrokenPipeError, OSError) as exc:
        try:
            process.stdin.close()
        except Exception:
            pass
        try:
            return_code = process.wait(timeout=3)
        except subprocess.TimeoutExpired:
            process.terminate()
            return_code = process.wait(timeout=5)
        stderr = process.stderr.read().decode("utf-8", errors="replace") if process.stderr else ""
        detail = stderr.strip() or "FFmpeg 沒有回傳錯誤文字。"
        raise RuntimeError(
            f"FFmpeg pipe 提前關閉（exit={return_code}）：{type(exc).__name__}: {exc}\n{detail}"
        ) from exc
    except Exception:
        try:
            process.stdin.close()
        except Exception:
            pass
        process.terminate()
        process.wait()
        raise


def _concat_mp4_segments(ffmpeg: str, segment_paths, output: str, temp_dir: Path):
    if not segment_paths:
        raise RuntimeError("沒有可合併的影片 segment。")
    if len(segment_paths) == 1:
        shutil.copy2(segment_paths[0], output)
        return

    concat_file = temp_dir / "concat.txt"
    lines = []
    for p in segment_paths:
        path_text = Path(p).resolve().as_posix().replace("'", "'\\''")
        lines.append(f"file '{path_text}'")
    concat_file.write_text("\n".join(lines) + "\n", encoding="utf-8")

    cmd = [
        ffmpeg, "-y", "-hide_banner", "-loglevel", config.FFMPEG_LOGLEVEL,
        "-f", "concat", "-safe", "0", "-i", str(concat_file),
        "-c", "copy", "-movflags", "+faststart", output,
    ]
    result = subprocess.run(
        cmd, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, check=False,
        **_background_subprocess_kwargs(),
    )
    if result.returncode != 0:
        err = result.stderr.decode("utf-8", errors="replace")
        raise RuntimeError(f"FFmpeg concat 失敗：\n{err.strip()}")


def _encode_end_segment(renderer, ffmpeg: str, encoder: str, output: str):
    end_count = renderer.zoom_frames + renderer.hold_frames
    if end_count <= 0:
        return False

    cmd = build_ffmpeg_command(ffmpeg, encoder, output, renderer.fps)
    process = subprocess.Popen(
        cmd,
        stdin=subprocess.PIPE,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.PIPE,
        bufsize=16 * 1024 * 1024,
        **_background_subprocess_kwargs(),
    )
    if process.stdin is None:
        raise RuntimeError("無法開啟結尾 FFmpeg stdin。")

    try:
        for i in range(end_count):
            frame = renderer.render_end_frame(i)
            process.stdin.write(frame.tobytes("raw", "RGB"))
        process.stdin.close()
        stderr = process.stderr.read().decode("utf-8", errors="replace") if process.stderr else ""
        rc = process.wait()
        if rc != 0:
            raise RuntimeError(f"結尾 FFmpeg exit={rc}\n{stderr.strip()}")
        return True
    except Exception:
        try:
            process.stdin.close()
        except Exception:
            pass
        process.terminate()
        process.wait()
        raise
