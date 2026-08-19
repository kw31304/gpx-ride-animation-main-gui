# -*- coding: utf-8 -*-
"""
核心業務邏輯與渲染引擎套件初始化。
"""

from gpx_renderer.core.data import (
    RideData,
    latlon_to_mercator,
    ease_smoothstep,
    haversine_steps_m,
    quick_gpx_distance_km,
    auto_duration_seconds,
    format_seconds_human,
    load_gpx,
    compute_end_route_view,
)

from gpx_renderer.core.map_utils import (
    RasterMap,
    choose_map_style,
    _fetch_raster,
    build_overview_raster_map,
    LocalChunkState,
    LocalBasemapCache,
)

from gpx_renderer.core.encoder import (
    find_ffmpeg,
    encoder_is_listed,
    encoder_works,
    choose_encoder,
    build_ffmpeg_command,
    encode_video,
    _concat_mp4_segments,
    _encode_end_segment,
)

from gpx_renderer.core.renderer import RideRenderer

from gpx_renderer.core.parallel import (
    SegmentTask,
    DynamicWorkerConfig,
    BenchmarkWorkerConfig,
    performance_benchmark_job,
    encode_video_parallel,
    render_job,
)

from gpx_renderer.core.media import (
    MediaItem,
    scan_media_files,
    match_media_to_ride,
    prepare_thumbnail,
)

from gpx_renderer.core.cache_manager import CacheManager

__all__ = [
    "RideData",
    "latlon_to_mercator",
    "ease_smoothstep",
    "haversine_steps_m",
    "quick_gpx_distance_km",
    "auto_duration_seconds",
    "format_seconds_human",
    "load_gpx",
    "compute_end_route_view",
    "RasterMap",
    "choose_map_style",
    "_fetch_raster",
    "build_overview_raster_map",
    "LocalChunkState",
    "LocalBasemapCache",
    "CacheManager",
    "find_ffmpeg",
    "encoder_is_listed",
    "encoder_works",
    "choose_encoder",
    "build_ffmpeg_command",
    "encode_video",
    "_concat_mp4_segments",
    "_encode_end_segment",
    "RideRenderer",
    "SegmentTask",
    "DynamicWorkerConfig",
    "BenchmarkWorkerConfig",
    "performance_benchmark_job",
    "encode_video_parallel",
    "render_job",
]
