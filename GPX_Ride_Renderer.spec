# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['D:/gpx-ride-animation-main/GPX_Ride_Renderer.py'],
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=['gpx_renderer', 'gpx_renderer.config', 'gpx_renderer.utils', 'gpx_renderer.utils.env', 'gpx_renderer.utils.font', 'gpx_renderer.core', 'gpx_renderer.core.data', 'gpx_renderer.core.map_utils', 'gpx_renderer.core.encoder', 'gpx_renderer.core.renderer', 'gpx_renderer.core.parallel', 'gpx_renderer.core.media', 'gpx_renderer.gui', 'gpx_renderer.gui.app', 'gpx_renderer.gui.help', 'PIL', 'PIL.Image', 'PIL.ImageDraw', 'PIL.ImageFont', 'PIL.ImageFilter', 'cv2', 'numpy', 'matplotlib', 'gpxpy', 'requests', 'contextily', 'geopy', 'shapely', 'pyproj', 'exifread', 'imageio_ffmpeg'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='GPX_Ride_Renderer',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='GPX_Ride_Renderer',
)
