# -*- coding: utf-8 -*-
"""
Tkinter 設定說明字典 (SETTING_HELP) 與幫助說明對話框視窗。
"""

import tkinter as tk
from tkinter import ttk


SETTING_HELP = {
    "map_style": (
        "地圖風格",
        "用途：決定影片主畫面與結尾 overview 使用的底圖樣式。\n\n"
        "影響：主要影響視覺風格，不太影響渲染 FPS，但不同圖源的下載速度可能不同。\n\n"
        "建議：深色路線影片可使用 DarkMatter；想看道路與地名更清楚可用 Voyager；衛星圖資訊量最高，但畫面也比較雜。"
    ),
    "profile": (
        "模式",
        "用途：一次套用一組解析度、Local Zoom、bitrate、NVENC preset、Workers 與 Chunks / Worker。\n\n"
        "快速：偏向測試與預覽。\n平衡：兼顧速度與畫質。\n高畫質：目前預設，1440×1440、Local Zoom 17、30M、p5。\n\n"
        "注意：切換模式會覆蓋上述相關欄位的值，之後仍可逐項手動微調。"
    ),
    "camera_mode": (
        "視角模式",
        "用途：決定路線動畫的鏡頭視角朝向與 3D 地形透視。\n\n"
        "• 正北朝上 (North-Up)：傳統 2D 平面視角，地圖北方永遠保持朝上。\n"
        "• 跟隨行進方向 (Heading-Up)：鏡頭與地圖會隨著騎乘/行進方向動態旋轉，使路線總是朝向畫面上方延伸。\n"
        "• 3D 真地形 (3D-Terrain)：電影級動態視角！開場以 2D 平面全景停留 1.5 秒，路線開始移動時鏡頭滑順俯衝轉為 3D 鳥瞰並拉近跟飛，接近結尾時再平滑抬升回 2D 全景與總覽卡片。"
    ),
    "resolution": (
        "解析度選單",
        "用途：選擇輸出影片的解析度尺寸與畫面比例。\n\n"
        "預設選單包含：\n"
        "• 直式手機 9:16 (1080×1920, 720×1280) - 適用 IG Reels, TikTok, YouTube Shorts\n"
        "• 正方形 1:1 (1440×1440, 1080×1080) - 適用 IG 貼文/FB\n"
        "• 橫式螢幕 16:9 (2560×1440, 1920×1080, 1280×720) - 適用 YouTube / 電腦\n"
        "• ⚡ 超低解析度測試 (640×360, 480×480, 360×640) - 極速測試與預覽\n"
        "• 自訂解析度：手動輸入任意寬度與高度。"
    ),
    "fps": (
        "FPS",
        "用途：設定輸出影片每秒包含多少幀。\n\n"
        "調高：動態更順，但相同秒數下需要渲染更多幀，時間與檔案大小通常增加。\n"
        "調低：渲染更快，但運鏡與標記移動較不流暢。\n\n"
        "建議：30 FPS 已很順；60 FPS 適合追求流暢感；超過 60 FPS 通常收益較小。"
    ),
    "duration": (
        "主動畫秒數",
        "用途：控制摩托車沿 GPX 路徑播放的主動畫長度，不包含最後 zoom-out 與結尾停留。\n\n"
        "調高：每公里播放得更慢，觀眾比較容易看清細節，同時總幀數與渲染時間增加。\n"
        "調低：節奏更快、影片更短。\n\n"
        "若啟用『依 GPX 距離自動設定秒數』，此欄位會由距離公式自動計算。"
    ),
    "auto_duration": (
        "依 GPX 距離自動設定秒數",
        "用途：依 GPX 總距離自動計算主動畫長度，讓不同長度的騎乘路線保持相近節奏。\n\n"
        "開啟後：主動畫秒數會自動鎖定並由『每 100 km 幾秒』決定。\n"
        "關閉後：可直接手動輸入主動畫秒數。\n\n"
        "目前最低主動畫長度仍會受到程式的安全下限限制。"
    ),
    "seconds_per_100km": (
        "每 100 km 秒數",
        "用途：自動時長的節奏倍率。公式約為：距離 km ÷ 100 × 此數值。\n\n"
        "調高：同一段路線播放得更慢、更細。\n"
        "調低：播放更快、更精簡。\n\n"
        "建議：你目前實測最好看的預設是每 100 km = 60 秒。"
    ),
    "local_zoom": (
        "Local Zoom",
        "用途：決定主動畫局部底圖下載的地圖縮放層級。數字越大，地圖原始細節越多。\n\n"
        "調高：道路、文字與地圖細節更清楚，但 tile 數量、下載量、RAM 與處理成本增加。\n"
        "調低：下載與渲染較輕，但放大後可能變糊。\n\n"
        "建議：高畫質使用 17；18 通常成本明顯增加；auto 由 contextily 自行決定。"
    ),
    "view_margin": (
        "View Margin",
        "用途：控制主動畫鏡頭在摩托車位置周圍一次看多大的實際地理範圍，單位是 Web Mercator 的公尺尺度。\n\n"
        "調大：鏡頭更遠，能看到更多周邊道路與路徑，移動感較平穩。\n"
        "調小：鏡頭更近，路線與道路看起來更大，但相機移動更敏感。\n\n"
        "建議：你目前實測最好看的預設是 1600。"
    ),
    "workers": (
        "Workers",
        "用途：同時使用多少個獨立渲染程序處理不同 chunks。這是目前影響總渲染速度最大的設定之一。\n\n"
        "調高：可提高 CPU 與 GPU pipeline 利用率，但會增加 RAM、磁碟、tile I/O 與多程序排程成本。\n"
        "調太高：反而可能因資源競爭而變慢。\n\n"
        "建議：先使用 Auto Tune，以實測 FPS 決定，不要只看 CPU 核心數。"
    ),
    "bitrate": (
        "NVENC bitrate",
        "用途：設定 H.264 NVENC 輸出碼率，主要影響壓縮畫質與 MP4 檔案大小。\n\n"
        "調高：細節、道路文字與移動畫面較不容易出現壓縮色塊，但檔案更大。\n"
        "調低：檔案較小，但快速移動或細節密集的地圖可能變糊。\n\n"
        "建議：1440×1440 高畫質目前使用 30M；若仍看到壓縮痕跡可試 40M。"
    ),
    "nvenc_preset": (
        "NVENC preset",
        "用途：控制 NVIDIA NVENC 的速度與壓縮效率取捨。p1 偏快，p7 偏向更高壓縮品質。\n\n"
        "往 p7：通常同 bitrate 下壓縮品質更好，但編碼工作量增加。\n"
        "往 p1：編碼更輕，但壓縮效率較差。\n\n"
        "建議：目前高畫質預設 p5。你的 Video Encode 使用率不高，因此 p5 很合理。"
    ),
    "tile_connections": (
        "Tile connections",
        "用途：contextily 下載地圖 tile 時可同時使用的連線數。\n\n"
        "調高：網路與圖源允許時，首次下載底圖可能更快。\n"
        "調太高：可能造成伺服器限流、連線失敗或多 worker 同時搶網路。\n\n"
        "建議：多程序渲染時保守使用 2 到 4；單程序預抓圖時可以再提高。"
    ),
    "zoomout": (
        "Zoom-out 秒",
        "用途：主動畫跑完後，鏡頭從局部視角拉遠到完整路線 overview 所花的時間。\n\n"
        "調高：轉場更慢、更有電影感。\n"
        "調低：很快進入 RIDE STATS。\n\n"
        "只影響結尾轉場，不影響主動畫速度。"
    ),
    "end_hold": (
        "結尾停留秒",
        "用途：完整路徑與 RIDE STATS 出現後，畫面維持多久再結束影片。\n\n"
        "調高：觀眾有更多時間閱讀距離、爬升、平均速度與時長。\n"
        "調低：影片結尾更俐落。"
    ),
    "chunks": (
        "Chunks / Worker",
        "用途：決定主動畫切成多少小工作區塊，總 chunks 約等於 Workers × 此數值。\n\n"
        "調高：工作切得更細，動態負載平衡更好，較不容易發生某個 worker 已完成、另一個還剩最多的長尾。\n"
        "調太高：每個 chunk 的 FFmpeg、地圖與管理固定成本占比增加。\n\n"
        "建議：4 是目前預設甜蜜點；路線各區段負載差異很大時可試 6。"
    ),
    "parallel": (
        "多程序",
        "用途：允許同時啟動多個 worker 平行渲染主動畫。\n\n"
        "開啟：正式長片通常快很多。\n"
        "關閉：使用單 process，較適合除錯或確認單一 worker 問題。\n\n"
        "Workers 大於 1 時通常建議開啟。"
    ),
    "basemap": (
        "底圖",
        "用途：是否下載並顯示道路或衛星等地圖底圖。\n\n"
        "開啟：正常成片使用。\n"
        "關閉：只留下簡化背景與路線，可用來排查底圖下載問題或做極速測試。"
    ),
    "preview": (
        "Preview",
        "用途：只渲染一小段主動畫，快速檢查 HUD、路徑、地圖、畫質與設定是否正確。\n\n"
        "Preview 仍可使用多程序，但因測試片段很短，程序啟動成本占比會比較高，因此 Preview FPS 不一定能代表長片最終速度。"
    ),
    "contextily_cache": (
        "Contextily cache",
        "用途：讓 contextily/joblib 將下載與處理結果保存到磁碟 cache，之後遇到相同請求可重用。\n\n"
        "優點：單程序或重複跑同一區域時可減少重新下載。\n"
        "缺點：多程序同時寫 cache 曾造成 contention、joblib 警告與 worker 收尾問題。"
    ),
    "parallel_cache": (
        "並行時停用 joblib cache",
        "用途：在多程序 worker 裡關閉 contextily/joblib 的磁碟 cache。\n\n"
        "建議保持開啟這個選項，也就是多程序時停用 joblib cache。這可以避免多個 worker 同時 hash、寫入或鎖定同一份 cache。\n\n"
        "代價：不同 worker 可能各自下載部分相同 tile。"
    ),
    "autotune": (
        "效能測試 / Auto Tune",
        "用途：用短 benchmark 實測不同 Workers 數量的等效 FPS，再推薦接近峰值效能的最低 worker 數。\n\n"
        "測試會依你目前的解析度、FPS、NVENC 等設定執行，但刻意不下載網路底圖，避免結果被 CDN 或網速污染。\n\n"
        "建議：更改解析度或大型效能設定後，可以重新跑一次 Auto Tune。"
    ),
    "media_path": (
        "路線媒體相片/影片",
        "用途：選擇包含照片或影片的資料夾或檔案。程式會自動讀取 EXIF 拍攝時間與 GPS 座標，自動插入對應的時間軸與軌跡位置。\n\n"
        "支援格式：JPG, JPEG, PNG, WEBP, MP4, MOV 等。"
    ),
    "media_duration": (
        "媒體停留秒數",
        "用途：控制相片/影片懸浮預覽卡片在畫面上停留顯示的時間長度（秒）。\n\n"
        "動態效果：包含登場與退場滑順淡入淡出動畫。"
    ),
    "media_offset": (
        "時間偏移校正",
        "用途：當相機時間與 GPS 時間未對齊（例如相機時區未設定或快慢 N 秒/小時）時，輸入秒數進行校正（可為正數或負數）。"
    ),
    "enable_media": (
        "路線媒體",
        "用途：是否在路線動畫中顯示相片/影片懸浮卡片。"
    ),
    "use_real_speed": (
        "跟隨 GPX 實際速度",
        "用途：控制騎乘動畫在路線上的移動速度模式。\n\n"
        "• 未勾選（等速移動，預設）：動畫在路線上以均勻幾何速度前進，視覺推進最流暢。\n"
        "• 勾選（實際速度移動）：依照 GPX 實際記錄的時間點前進。真實還原騎乘時上坡變慢、下坡變快或停等紅燈的體感。"
    ),
}


def show_setting_help(root, key: str):
    info = SETTING_HELP.get(key)
    if not info:
        return
    title, body = info
    win = tk.Toplevel(root)
    win.title(f"設定說明 - {title}")
    win.transient(root)
    win.resizable(False, False)
    frame = ttk.Frame(win, padding=18)
    frame.pack(fill="both", expand=True)
    ttk.Label(frame, text=title, font=("Segoe UI", 13, "bold")).pack(anchor="w", pady=(0, 10))
    ttk.Label(frame, text=body, justify="left", wraplength=520).pack(anchor="w")
    ttk.Button(frame, text="關閉", command=win.destroy).pack(anchor="e", pady=(16, 0))
    win.update_idletasks()
    try:
        x = root.winfo_rootx() + max(20, (root.winfo_width() - win.winfo_width()) // 2)
        y = root.winfo_rooty() + max(20, (root.winfo_height() - win.winfo_height()) // 2)
        win.geometry(f"+{x}+{y}")
    except Exception:
        pass
    win.grab_set()
    win.focus_set()


def help_button(parent, root, key: str):
    return ttk.Button(parent, text="?", width=2, command=lambda k=key: show_setting_help(root, k))


def field_with_help(parent, root, widget, key: str, *, fill=False):
    box = ttk.Frame(parent)
    widget.pack(in_=box, side="left", fill="x" if fill else None, expand=fill)
    help_button(box, root, key).pack(side="left", padx=(5, 0))
    return box
