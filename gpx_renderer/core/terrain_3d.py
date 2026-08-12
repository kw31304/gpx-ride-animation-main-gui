# -*- coding: utf-8 -*-
"""
3D 地形網格與 3D 攝影機透視投影繪製引擎 (3D Terrain Projection & Mesh Renderer)。
使用 3D Pitch/Yaw 透視投影矩陣與 OpenCV 極速 3D 貼圖映射。
"""

from __future__ import annotations
import math
from dataclasses import dataclass
import numpy as np
from PIL import Image

try:
    import cv2
    HAVE_CV2 = True
except Exception:
    cv2 = None
    HAVE_CV2 = False

from gpx_renderer import config
from gpx_renderer.core.map_utils import RasterMap
from gpx_renderer.core.dem_utils import get_elevation_grid


@dataclass
class Camera3D:
    x: float
    y: float
    z: float
    heading_rad: float = math.pi / 2.0
    pitch_deg: float = 50.0
    exaggeration: float = 1.5


def project_3d_points(
    xs: np.ndarray,
    ys: np.ndarray,
    zs: np.ndarray,
    camera: Camera3D,
    view_margin: float,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """將 3D 世界座標 (X, Y, Z) 投影至 2D 螢幕畫格像素點 (px, py)，以及深度 dist。"""
    alpha = camera.heading_rad - math.pi / 2.0
    cos_a = math.cos(alpha)
    sin_a = math.sin(alpha)

    pitch_rad = math.radians(max(0.0, min(80.0, camera.pitch_deg)))
    cos_p = math.cos(pitch_rad)
    sin_p = math.sin(pitch_rad)

    dx = xs - camera.x
    dy = ys - camera.y
    dz = (zs * camera.exaggeration) - camera.z

    # 1. 旋轉 Yaw (heading)
    rx = dx * cos_a + dy * sin_a
    ry = -dx * sin_a + dy * cos_a
    rz = dz

    # 2. 旋轉 Pitch (俯角)
    ry_p = ry * cos_p - rz * sin_p
    rz_p = ry * sin_p + rz * cos_p

    # 3. 視距與 Perspective 遠小近大縮放
    d_cam = float(view_margin) * 1.8
    dist = d_cam + rz_p
    dist_safe = np.maximum(dist, 10.0)

    aspect = config.FRAME_WIDTH / float(config.FRAME_HEIGHT)
    margin_x = view_margin * aspect if aspect >= 1.0 else view_margin
    margin_y = view_margin if aspect >= 1.0 else view_margin / aspect

    kx = (config.FRAME_WIDTH / (2.0 * margin_x)) * d_cam
    ky = (config.FRAME_HEIGHT / (2.0 * margin_y)) * d_cam

    px = (config.FRAME_WIDTH * 0.5) + (rx / dist_safe) * kx
    py = (config.FRAME_HEIGHT * 0.5) - (ry_p / dist_safe) * ky

    return px, py, dist_safe


def render_3d_terrain_frame(
    local_rm: RasterMap,
    view_x: float,
    view_y: float,
    margin: float,
    heading_rad: float,
    pitch_deg: float = 50.0,
    exaggeration: float = 1.5,
    grid_res: int = 24,
    out_buffer: np.ndarray | None = None,
) -> Image.Image:
    """渲染帶有 3D 山脈地形起伏與透視投影的地圖畫格。"""
    W = config.FRAME_WIDTH
    H = config.FRAME_HEIGHT

    if out_buffer is not None and out_buffer.shape == (H, W, 3):
        out_arr = out_buffer
        out_arr.fill(17)
    else:
        out_arr = np.full((H, W, 3), 17, dtype=np.uint8)

    # 1. 取得該區域的高程 DEM 網格 (優先使用已預先計算好的塊陣列)
    if local_rm.dem_grid is not None:
        dem_grid = local_rm.dem_grid
    else:
        dem_grid = get_elevation_grid(local_rm.west, local_rm.south, local_rm.east, local_rm.north, rows=grid_res, cols=grid_res)
    avg_z = float(np.mean(dem_grid))

    camera = Camera3D(
        x=view_x,
        y=view_y,
        z=avg_z * exaggeration,
        heading_rad=heading_rad,
        pitch_deg=pitch_deg,
        exaggeration=exaggeration,
    )

    grid_x = np.linspace(local_rm.west, local_rm.east, grid_res, dtype=np.float64)
    grid_y = np.linspace(local_rm.north, local_rm.south, grid_res, dtype=np.float64)
    mesh_x, mesh_y = np.meshgrid(grid_x, grid_y)

    px_grid, py_grid, _ = project_3d_points(mesh_x.ravel(), mesh_y.ravel(), dem_grid.ravel(), camera, margin)
    px_grid = px_grid.reshape((grid_res, grid_res))
    py_grid = py_grid.reshape((grid_res, grid_res))

    # 源地圖影像像素
    src_img = local_rm.np_image if (HAVE_CV2 and local_rm.np_image is not None) else np.asarray(local_rm.image)
    src_h, src_w = src_img.shape[:2]

    src_x_grid = np.linspace(0, src_w - 1, grid_res, dtype=np.float32)
    src_y_grid = np.linspace(0, src_h - 1, grid_res, dtype=np.float32)
    src_mesh_x, src_mesh_y = np.meshgrid(src_x_grid, src_y_grid)

    out_arr = np.full((H, W, 3), 17, dtype=np.uint8)

    if HAVE_CV2 and cv2 is not None:
        # 分塊 3D 透視三角面片極速無縫貼圖 (Triangle Masked Affine Blending)
        for r in range(grid_res - 1):
            for c in range(grid_res - 1):
                dst_pts1 = np.float32([
                    [px_grid[r, c], py_grid[r, c]],
                    [px_grid[r, c + 1], py_grid[r, c + 1]],
                    [px_grid[r + 1, c], py_grid[r + 1, c]],
                ])
                src_pts1 = np.float32([
                    [src_mesh_x[r, c], src_mesh_y[r, c]],
                    [src_mesh_x[r, c + 1], src_mesh_y[r, c + 1]],
                    [src_mesh_x[r + 1, c], src_mesh_y[r + 1, c]],
                ])

                bx0 = max(0, int(math.floor(float(np.min(dst_pts1[:, 0])))))
                bx1 = min(W, int(math.ceil(float(np.max(dst_pts1[:, 0])))))
                by0 = max(0, int(math.floor(float(np.min(dst_pts1[:, 1])))))
                by1 = min(H, int(math.ceil(float(np.max(dst_pts1[:, 1])))))

                if bx1 > bx0 and by1 > by0:
                    pw, ph = bx1 - bx0, by1 - by0
                    dst1_loc = dst_pts1 - np.float32([bx0, by0])
                    try:
                        M1 = cv2.getAffineTransform(src_pts1, dst1_loc)
                        warped1 = cv2.warpAffine(src_img, M1, (pw, ph), flags=cv2.INTER_LINEAR)
                        mask1 = np.zeros((ph, pw), dtype=np.uint8)
                        cv2.fillConvexPoly(mask1, np.int32(np.round(dst1_loc)), 255)
                        patch1 = out_arr[by0:by1, bx0:bx1]
                        cv2.copyTo(warped1, mask1, patch1)
                    except Exception:
                        pass

                dst_pts2 = np.float32([
                    [px_grid[r, c + 1], py_grid[r, c + 1]],
                    [px_grid[r + 1, c + 1], py_grid[r + 1, c + 1]],
                    [px_grid[r + 1, c], py_grid[r + 1, c]],
                ])
                src_pts2 = np.float32([
                    [src_mesh_x[r, c + 1], src_mesh_y[r, c + 1]],
                    [src_mesh_x[r + 1, c + 1], src_mesh_y[r + 1, c + 1]],
                    [src_mesh_x[r + 1, c], src_mesh_y[r + 1, c]],
                ])

                bx0 = max(0, int(math.floor(float(np.min(dst_pts2[:, 0])))))
                bx1 = min(W, int(math.ceil(float(np.max(dst_pts2[:, 0])))))
                by0 = max(0, int(math.floor(float(np.min(dst_pts2[:, 1])))))
                by1 = min(H, int(math.ceil(float(np.max(dst_pts2[:, 1])))))

                if bx1 > bx0 and by1 > by0:
                    pw, ph = bx1 - bx0, by1 - by0
                    dst2_loc = dst_pts2 - np.float32([bx0, by0])
                    try:
                        M2 = cv2.getAffineTransform(src_pts2, dst2_loc)
                        warped2 = cv2.warpAffine(src_img, M2, (pw, ph), flags=cv2.INTER_LINEAR)
                        mask2 = np.zeros((ph, pw), dtype=np.uint8)
                        cv2.fillConvexPoly(mask2, np.int32(np.round(dst2_loc)), 255)
                        patch2 = out_arr[by0:by1, bx0:bx1]
                        cv2.copyTo(warped2, mask2, patch2)
                    except Exception:
                        pass

    return Image.fromarray(out_arr)
