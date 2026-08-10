# GPX Ride Renderer

這是 [shao0927/gpx-ride-animation](https://github.com/shao0927/gpx-ride-animation) 的 Windows 強化版，可將 GPX 騎乘紀錄轉成動態地圖影片。此版本加入圖形介面、多程序渲染、Workers Auto Tune、NVIDIA NVENC、結尾路線總覽與 RIDE STATS，並提供可攜式 Windows EXE。

## 專案簡介與架構摘要

本專案採 **GUI 圖形介面與核心邏輯分離** 的模組化設計：

- **進入點 (`GPX_Ride_Renderer.py`)**：負責轉接 CLI、GUI 啟動與多程序 Task 派發。
- **核心套件 (`gpx_renderer/`)**：
  - **`config.py`**：全域設定、地圖風格 (`MAP_STYLE_OPTIONS`) 與動態快照。
  - **`core/`**：
    - `data.py`：GPX 解析、`RideData` 結構與地理數據計算。
    - `map_utils.py`：底圖下載 (contextily) 與區域地圖增量快取 (`LocalBasemapCache`)。
    - `encoder.py`：FFmpeg/NVENC 編碼器測試與影片合併。
    - `renderer.py`：`RideRenderer` 畫格繪製引擎（包含 HUD 速度錶、小地圖、海拔圖與結尾統計）。
    - `parallel.py`：多程序動態分塊渲染與 Auto Tune 效能測試。
  - **`gui/`**：
    - `app.py`：Tkinter GUI 主介面與進度監控。
    - `help.py` & `components.py`：設定說明對話框與 UI 複用元件。
  - **`utils/`**：`env.py` (UTF-8 stdio、字型載入) 與 `config_io.py` (JSON 設定讀寫)。

## 功能

- Windows 圖形介面，可直接選擇 GPX、輸出位置、解析度與地圖風格
- 依 GPX 距離自動計算影片長度
- 多程序動態分塊渲染，支援 Workers Auto Tune
- NVIDIA NVENC 硬體編碼，無法使用時回退至 libx264
- 局部高解析度底圖、即時軌跡、速度 HUD、小地圖與海拔圖
- 結尾 zoom-out、完整路線總覽與騎乘統計
- Windows 可攜式 ZIP，不必另外安裝 FFmpeg

## 畫面預覽

渲染設定與多 worker 進度：

![GPX Ride Renderer 渲染介面](https://hackmd.io/_uploads/Byo_aXrUze.png)

V1.0.0 完成畫面與 overview 底圖：

![GPX Ride Renderer 完成畫面](https://hackmd.io/_uploads/BkFSR4BUGg.png)

## 專案內容與目錄結構

```text
GPX_Ride_Renderer.py                 主程式進入點 (GUI/CLI/Subprocess)
GPX_Ride_Renderer.spec               PyInstaller 打包設定檔
build_exe.bat                        Windows 打包腳本
requirements-build.txt               執行與打包相依套件
run_source.bat                       從原始碼啟動腳本
gpx_renderer/                        核心模組套件資料夾
├── config.py                        全域參數與動態設定
├── core/                            核心渲染與平行處理引擎
│   ├── data.py                      GPX 數據解析與數學輔助
│   ├── encoder.py                   FFmpeg/NVENC 編碼與影片合併
│   ├── map_utils.py                 地圖下載與增量快取
│   ├── parallel.py                  多程序動態分塊與 Auto Tune
│   └── renderer.py                  RideRenderer 畫格繪製引擎
├── gui/                             Tkinter 圖形介面
│   ├── app.py                       主介面與進度監控
│   ├── components.py                UI 輔助元件
│   └── help.py                      設定說明對話框
└── utils/                           共用工具函式
    ├── config_io.py                 JSON 設定讀寫
    └── env.py                       環境、UTF-8 及字型處理
```

儲存庫只保留原始碼與建置腳本，不包含編譯產物。若只想使用程式，請前往 [GitHub Releases](https://github.com/ccccchhhheeenng/gpx-ride-animation/releases/latest) 下載 `GPX_Ride_Renderer_Windows_x64.zip`，解壓縮後執行 `GPX Ride Renderer.exe`。

## 從原始碼執行

需要 64 位元 Python 3.10 或更新版本。

```bat
run_source.bat
```

若尚未安裝相依套件：

```powershell
python -m pip install -r requirements-build.txt
```

## 重新打包

```bat
build_exe.bat
```

完成後，新版 ZIP 位於：

```text
release\GPX_Ride_Renderer_Windows_x64.zip
```

ZIP 不需複製到專案根目錄，也不要提交到 Git。建立新版時，將它上傳為 GitHub Release 的附件。

目前公開版本為 V1.0.0。先前的 V7.5.x 名稱屬於尚未公開的開發階段；公開版本從 V1.0.0 開始。

## 上游與授權

本 fork 已取得原作者同意建立。上游儲存庫目前沒有 `LICENSE`，此同意不等同於標準開源授權；原始程式的權利仍屬原作者所有。
