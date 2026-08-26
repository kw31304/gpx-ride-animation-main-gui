# -*- coding: utf-8 -*-
"""
GPX Ride Renderer - 打包與發布視覺化管理中心 (Release Manager GUI)
支援 PySide6 原生介面，具備以下功能：
1. 專案版本與環境依賴檢測 (Python, PyInstaller, FFmpeg, GitHub Token)
2. 一鍵執行 EXE 打包與 ZIP 壓縮 (背景非同步執行、即時控制台串流輸出)
3. 測試執行打包產出之 EXE 與開啟 dist 資料夾
4. 發布說明 (Release Notes) 視覺化清單檢視、編輯、儲存與新增
5. GitHub Releases 一鍵自動建立 Tag、發布說明與上傳 ZIP 檔案
"""

from __future__ import annotations
import os
import sys
import re
import json
import shutil
import subprocess
from pathlib import Path
from datetime import datetime

from PySide6.QtCore import Qt, QThread, Signal, QProcess, QTimer, QSize
from PySide6.QtGui import QFont, QColor, QTextCursor, QIcon, QAction
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QGridLayout, QLabel, QPushButton, QLineEdit, QPlainTextEdit,
    QComboBox, QCheckBox, QGroupBox, QSplitter, QFrame, QMessageBox,
    QFileDialog, QTabWidget, QProgressBar, QStatusBar
)


def get_project_root() -> Path:
    """取得專案根目錄路徑"""
    cur = Path(__file__).resolve().parent
    if (cur / "gpx_renderer").exists():
        return cur
    return cur.parent


def detect_version(project_root: Path) -> str:
    """自動從 gpx_renderer/__init__.py 讀取 __version__ 版本號"""
    init_file = project_root / "gpx_renderer" / "__init__.py"
    if init_file.exists():
        try:
            content = init_file.read_text(encoding="utf-8")
            match = re.search(r'__version__\s*=\s*["\']([^"\']+)["\']', content)
            if match:
                return match.group(1).strip()
        except Exception:
            pass
    return "1.0.0"


def load_env_vars(project_root: Path) -> dict:
    """載入 .env 檔案中的環境變數"""
    env_vars = {}
    env_file = project_root / ".env"
    if env_file.exists():
        try:
            for line in env_file.read_text(encoding="utf-8-sig").splitlines():
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    env_vars[k.strip().lstrip("\ufeff")] = v.strip().strip('"').strip("'")
        except Exception:
            pass
    return env_vars


class WorkerThread(QThread):
    """執行打包或發布任務的背景執行緒，即時發送命令列輸出"""
    line_received = Signal(str)
    finished_signal = Signal(int)

    def __init__(self, cmd: list[str], cwd: Path, env: dict | None = None, parent=None):
        super().__init__(parent)
        self.cmd = cmd
        self.cwd = cwd
        self.env = env

    def run(self):
        try:
            full_env = os.environ.copy()
            full_env["PYTHONUNBUFFERED"] = "1"
            full_env["PYTHONIOENCODING"] = "utf-8"
            if self.env:
                full_env.update(self.env)

            # 確保環境變數 PATH 包含完整 Conda / Python DLL 與執行檔路徑 (避免 GUI 啟動時遺漏 Library/bin)
            python_dir = Path(sys.executable).parent
            paths_to_add = [
                str(python_dir),
                str(python_dir / "Scripts"),
                str(python_dir / "DLLs"),
                str(python_dir / "Library" / "bin"),
                str(python_dir / "Library" / "usr" / "bin"),
                str(python_dir / "Library" / "mingw-w64" / "bin"),
            ]
            current_path = full_env.get("PATH", "")
            current_paths = current_path.split(os.pathsep)
            new_paths = [p for p in paths_to_add if Path(p).exists() and p not in current_paths]
            if new_paths:
                full_env["PATH"] = os.pathsep.join(new_paths + [current_path])

            proc = subprocess.Popen(
                self.cmd,
                cwd=str(self.cwd),
                env=full_env,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                encoding="utf-8",
                errors="replace",
                bufsize=1,
            )

            assert proc.stdout is not None
            for line in iter(proc.stdout.readline, ""):
                if line:
                    self.line_received.emit(line.rstrip())

            proc.stdout.close()
            rc = proc.wait()
            self.finished_signal.emit(rc)
        except Exception as exc:
            self.line_received.emit(f"[ERROR] 執行失敗：{exc}")
            self.finished_signal.emit(-1)


class ReleaseManagerWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.project_root = get_project_root()
        self.tools_dir = Path(__file__).resolve().parent
        self.notes_dir = self.tools_dir / "release_notes"
        self.notes_dir.mkdir(parents=True, exist_ok=True)
        self.env_vars = load_env_vars(self.project_root)

        self.worker: WorkerThread | None = None
        self._init_ui()
        self._refresh_environment_status()
        self._load_release_notes_list()

    def _init_ui(self):
        self.setWindowTitle("GPX Ride Renderer - 打包與發布管理中心")
        self.resize(1100, 780)
        self.setMinimumSize(950, 680)

        # 全域深色現代主題樣式表
        self.setStyleSheet("""
            QMainWindow, QWidget {
                background-color: #0d1117;
                color: #c9d1d9;
                font-family: "Segoe UI", "Microsoft JhengHei", sans-serif;
                font-size: 13px;
            }
            QGroupBox {
                border: 1px solid #30363d;
                border-radius: 8px;
                margin-top: 12px;
                padding-top: 14px;
                background-color: #161b22;
                font-weight: bold;
                color: #58a6ff;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top left;
                padding: 0 6px;
                left: 10px;
            }
            QLineEdit, QComboBox, QPlainTextEdit {
                background-color: #0d1117;
                border: 1px solid #30363d;
                border-radius: 6px;
                padding: 6px 10px;
                color: #f0f6fc;
                selection-background-color: #1f6feb;
            }
            QLineEdit:focus, QComboBox:focus, QPlainTextEdit:focus {
                border: 1px solid #58a6ff;
            }
            QPushButton {
                background-color: #21262d;
                border: 1px solid #30363d;
                border-radius: 6px;
                padding: 7px 14px;
                color: #c9d1d9;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: #30363d;
                border-color: #8b949e;
                color: #f0f6fc;
            }
            QPushButton:pressed {
                background-color: #161b22;
            }
            QPushButton#btn_primary {
                background-color: #238636;
                border-color: #2ea043;
                color: #ffffff;
                font-weight: bold;
            }
            QPushButton#btn_primary:hover {
                background-color: #2ea043;
            }
            QPushButton#btn_accent {
                background-color: #1f6feb;
                border-color: #388bfd;
                color: #ffffff;
                font-weight: bold;
            }
            QPushButton#btn_accent:hover {
                background-color: #388bfd;
            }
            QTabWidget::pane {
                border: 1px solid #30363d;
                border-radius: 8px;
                background-color: #161b22;
                top: -1px;
            }
            QTabBar::tab {
                background: #0d1117;
                border: 1px solid #30363d;
                border-bottom: none;
                padding: 8px 16px;
                border-top-left-radius: 6px;
                border-top-right-radius: 6px;
                color: #8b949e;
                margin-right: 4px;
                font-weight: bold;
            }
            QTabBar::tab:selected {
                background: #161b22;
                border-color: #30363d;
                color: #58a6ff;
            }
            QProgressBar {
                border: 1px solid #30363d;
                border-radius: 6px;
                background-color: #0d1117;
                text-align: center;
                color: #f0f6fc;
            }
            QProgressBar::chunk {
                background-color: #238636;
                border-radius: 5px;
            }
        """)

        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(14, 12, 14, 12)
        main_layout.setSpacing(10)

        # 1. 頂部環境與版本狀態卡片
        status_group = QGroupBox("📌 專案環境與授權狀態", self)
        status_layout = QGridLayout(status_group)
        status_layout.setContentsMargins(12, 10, 12, 10)
        status_layout.setHorizontalSpacing(16)
        status_layout.setVerticalSpacing(8)

        self.lbl_version = QLabel("偵測中...", self)
        self.lbl_version.setStyleSheet("font-weight: bold; color: #7ee787; font-size: 14px;")
        self.lbl_venv = QLabel("偵測中...", self)
        self.lbl_pyinstaller = QLabel("偵測中...", self)
        self.lbl_ffmpeg = QLabel("偵測中...", self)
        self.lbl_token = QLabel("偵測中...", self)
        self.lbl_repo = QLabel("偵測中...", self)

        status_layout.addWidget(QLabel("目前專案版本："), 0, 0)
        status_layout.addWidget(self.lbl_version, 0, 1)
        status_layout.addWidget(QLabel("目標發布倉庫："), 0, 2)
        status_layout.addWidget(self.lbl_repo, 0, 3)

        status_layout.addWidget(QLabel("Python 執行環境："), 1, 0)
        status_layout.addWidget(self.lbl_venv, 1, 1)
        status_layout.addWidget(QLabel("PyInstaller 套件："), 1, 2)
        status_layout.addWidget(self.lbl_pyinstaller, 1, 3)

        status_layout.addWidget(QLabel("FFmpeg 核心模組："), 2, 0)
        status_layout.addWidget(self.lbl_ffmpeg, 2, 1)
        status_layout.addWidget(QLabel("GitHub Token 授權："), 2, 2)
        status_layout.addWidget(self.lbl_token, 2, 3)

        main_layout.addWidget(status_group)

        # 2. 中間 Splitter (左側操作頁籤 + 右側即時終端控制台)
        splitter = QSplitter(Qt.Horizontal, self)

        # 左側功能分頁
        self.tabs = QTabWidget(self)

        # Tab 1: 打包管理
        tab_build = QWidget(self)
        layout_build = QVBoxLayout(tab_build)
        layout_build.setContentsMargins(12, 14, 12, 14)
        layout_build.setSpacing(12)

        desc_build = QLabel(
            "透過 PyInstaller 自動將專案封裝為獨立的 Windows 64-bit EXE 執行檔，\n"
            "並自動將產出的檔案夾打包壓縮為 ZIP 發行壓縮檔。", self
        )
        desc_build.setStyleSheet("color: #8b949e;")
        layout_build.addWidget(desc_build)

        build_options_group = QGroupBox("打包設定選項", tab_build)
        b_opt_layout = QVBoxLayout(build_options_group)
        self.chk_clean_build = QCheckBox("打包前自動清理舊的 build / dist 快取目錄 (--clean)", self)
        self.chk_clean_build.setChecked(True)
        self.chk_auto_zip = QCheckBox("打包完成後自動壓縮為標準發行 ZIP 壓縮包", self)
        self.chk_auto_zip.setChecked(True)
        self.chk_open_dist = QCheckBox("打包完成後自動開啟產出資料夾", self)
        self.chk_open_dist.setChecked(True)

        b_opt_layout.addWidget(self.chk_clean_build)
        b_opt_layout.addWidget(self.chk_auto_zip)
        b_opt_layout.addWidget(self.chk_open_dist)
        layout_build.addWidget(build_options_group)

        self.btn_run_build = QPushButton("🔨 開始一鍵打包 EXE & ZIP 壓縮包", self)
        self.btn_run_build.setObjectName("btn_primary")
        self.btn_run_build.setFixedHeight(40)
        self.btn_run_build.clicked.connect(self._run_build_process)
        layout_build.addWidget(self.btn_run_build)

        h_tools = QHBoxLayout()
        self.btn_open_dist_folder = QPushButton("📂 開啟 dist 輸出資料夾", self)
        self.btn_open_dist_folder.clicked.connect(self._open_dist_folder)
        self.btn_test_exe = QPushButton("▶️ 測試啟動打包好的 EXE", self)
        self.btn_test_exe.clicked.connect(self._test_run_exe)
        h_tools.addWidget(self.btn_open_dist_folder)
        h_tools.addWidget(self.btn_test_exe)
        layout_build.addLayout(h_tools)

        layout_build.addStretch()
        self.tabs.addTab(tab_build, "📦 EXE 打包管理")

        # Tab 2: 發布說明 (Release Notes)
        tab_notes = QWidget(self)
        layout_notes = QVBoxLayout(tab_notes)
        layout_notes.setContentsMargins(12, 14, 12, 14)
        layout_notes.setSpacing(8)

        h_notes_top = QHBoxLayout()
        h_notes_top.addWidget(QLabel("選擇發布說明歷程：", self))
        self.combo_notes = QComboBox(self)
        self.combo_notes.currentIndexChanged.connect(self._on_note_selected)
        h_notes_top.addWidget(self.combo_notes, 1)

        self.btn_new_note = QPushButton("➕ 新增新版說明", self)
        self.btn_new_note.clicked.connect(self._create_new_release_note)
        self.btn_save_note = QPushButton("💾 儲存修改", self)
        self.btn_save_note.clicked.connect(self._save_current_release_note)
        h_notes_top.addWidget(self.btn_new_note)
        h_notes_top.addWidget(self.btn_save_note)
        layout_notes.addLayout(h_notes_top)

        self.txt_notes_editor = QPlainTextEdit(self)
        self.txt_notes_editor.setFont(QFont("Consolas", 11))
        self.txt_notes_editor.setPlaceholderText("請輸入發布說明 Markdown 內容...")
        layout_notes.addWidget(self.txt_notes_editor, 1)

        self.tabs.addTab(tab_notes, "📝 發布說明管理")

        # Tab 3: GitHub Releases 發布
        tab_publish = QWidget(self)
        layout_publish = QVBoxLayout(tab_publish)
        layout_publish.setContentsMargins(12, 14, 12, 14)
        layout_publish.setSpacing(12)

        desc_pub = QLabel(
            "將打包好的 ZIP 壓縮檔與發布說明一鍵上傳發布至 GitHub Releases。\n"
            "需在 .env 檔案中設定 GITHUB_TOKEN。", self
        )
        desc_pub.setStyleSheet("color: #8b949e;")
        layout_publish.addWidget(desc_pub)

        pub_form = QGroupBox("GitHub Releases 發布設定", tab_publish)
        pub_form_layout = QGridLayout(pub_form)
        pub_form_layout.setVerticalSpacing(10)

        self.edit_pub_tag = QLineEdit(self)
        self.edit_pub_title = QLineEdit(self)
        self.edit_pub_zip = QLineEdit(self)
        self.btn_browse_zip = QPushButton("瀏覽...", self)
        self.btn_browse_zip.clicked.connect(self._browse_publish_zip)

        pub_form_layout.addWidget(QLabel("Release Tag 標籤："), 0, 0)
        pub_form_layout.addWidget(self.edit_pub_tag, 0, 1, 1, 2)

        pub_form_layout.addWidget(QLabel("Release 顯示標題："), 1, 0)
        pub_form_layout.addWidget(self.edit_pub_title, 1, 1, 1, 2)

        pub_form_layout.addWidget(QLabel("要上傳的 ZIP 檔案："), 2, 0)
        pub_form_layout.addWidget(self.edit_pub_zip, 2, 1)
        pub_form_layout.addWidget(self.btn_browse_zip, 2, 2)

        layout_publish.addWidget(pub_form)

        self.btn_run_publish = QPushButton("🚀 一鍵發布至 GitHub Releases", self)
        self.btn_run_publish.setObjectName("btn_accent")
        self.btn_run_publish.setFixedHeight(40)
        self.btn_run_publish.clicked.connect(self._run_publish_process)
        layout_publish.addWidget(self.btn_run_publish)

        layout_publish.addStretch()
        self.tabs.addTab(tab_publish, "🚀 GitHub Releases 發布")

        splitter.addWidget(self.tabs)

        # 右側終端控制台 (Log Console)
        console_widget = QWidget(self)
        console_layout = QVBoxLayout(console_widget)
        console_layout.setContentsMargins(0, 0, 0, 0)
        console_layout.setSpacing(6)

        h_console_top = QHBoxLayout()
        lbl_console_title = QLabel("💻 即時輸出控制台 (Terminal Output)", self)
        lbl_console_title.setStyleSheet("font-weight: bold; color: #58a6ff;")
        h_console_top.addWidget(lbl_console_title)
        h_console_top.addStretch()

        self.btn_clear_log = QPushButton("🧹 清空日誌", self)
        self.btn_clear_log.clicked.connect(lambda: self.txt_console.clear())
        self.btn_copy_log = QPushButton("📋 複製日誌", self)
        self.btn_copy_log.clicked.connect(self._copy_console_log)
        h_console_top.addWidget(self.btn_clear_log)
        h_console_top.addWidget(self.btn_copy_log)
        console_layout.addLayout(h_console_top)

        self.txt_console = QPlainTextEdit(self)
        self.txt_console.setReadOnly(True)
        self.txt_console.setFont(QFont("Consolas", 10))
        self.txt_console.setStyleSheet("""
            QPlainTextEdit {
                background-color: #06090e;
                color: #e6edf3;
                border: 1px solid #30363d;
                border-radius: 6px;
            }
        """)
        console_layout.addWidget(self.txt_console, 1)

        self.progress_bar = QProgressBar(self)
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setFixedHeight(14)
        console_layout.addWidget(self.progress_bar)

        splitter.addWidget(console_widget)
        splitter.setStretchFactor(0, 5)
        splitter.setStretchFactor(1, 6)

        main_layout.addWidget(splitter, 1)

    def _log(self, text: str):
        """向控制台輸出文字並自動滾動"""
        self.txt_console.appendPlainText(text)
        self.txt_console.moveCursor(QTextCursor.End)

    def _refresh_environment_status(self):
        """更新環境與依賴狀態"""
        version = detect_version(self.project_root)
        self.lbl_version.setText(f"v{version}")

        # Python / venv
        venv_python = self.project_root / ".venv" / "Scripts" / "python.exe"
        if venv_python.exists():
            self.lbl_venv.setText(f"虛擬環境 (.venv)")
            self.lbl_venv.setStyleSheet("color: #7ee787;")
        else:
            self.lbl_venv.setText(f"系統 Python ({sys.version.split()[0]})")
            self.lbl_venv.setStyleSheet("color: #d29922;")

        # PyInstaller
        try:
            import PyInstaller
            self.lbl_pyinstaller.setText(f"已就緒 (v{PyInstaller.__version__})")
            self.lbl_pyinstaller.setStyleSheet("color: #7ee787;")
        except ImportError:
            self.lbl_pyinstaller.setText("未安裝 (執行打包時將自動安裝)")
            self.lbl_pyinstaller.setStyleSheet("color: #f85149;")

        # FFmpeg
        ffmpeg_found = False
        try:
            import imageio_ffmpeg
            ff_p = Path(imageio_ffmpeg.get_ffmpeg_exe())
            if ff_p.exists():
                self.lbl_ffmpeg.setText("已就緒 (imageio_ffmpeg)")
                self.lbl_ffmpeg.setStyleSheet("color: #7ee787;")
                ffmpeg_found = True
        except Exception:
            pass

        if not ffmpeg_found:
            if (self.project_root.parent / "ffmpeg.exe").exists() or shutil.which("ffmpeg"):
                self.lbl_ffmpeg.setText("已就緒 (系統/根目錄)")
                self.lbl_ffmpeg.setStyleSheet("color: #7ee787;")
            else:
                self.lbl_ffmpeg.setText("未偵測到 FFmpeg")
                self.lbl_ffmpeg.setStyleSheet("color: #f85149;")

        # GitHub Token & Repo
        token = os.environ.get("GITHUB_TOKEN") or self.env_vars.get("GITHUB_TOKEN", "")
        if token:
            masked = token[:4] + "*" * max(4, len(token) - 8) + token[-4:] if len(token) > 8 else "****"
            self.lbl_token.setText(f"已授權 ({masked})")
            self.lbl_token.setStyleSheet("color: #7ee787;")
        else:
            self.lbl_token.setText("未設定 (請於 .env 填入 GITHUB_TOKEN)")
            self.lbl_token.setStyleSheet("color: #f85149;")

        repo = os.environ.get("GITHUB_REPO") or self.env_vars.get("GITHUB_REPO", "kw31304/gpx-ride-animation-releases")
        self.lbl_repo.setText(repo)

        # 同步更新發布分頁欄位
        self.edit_pub_tag.setText(f"v{version}")
        self.edit_pub_title.setText(f"GPX Ride Renderer v{version}")
        zip_filename = f"GPX_Ride_Renderer_v{version}_windows_x64.zip"
        expected_zip = self._get_dist_dir() / zip_filename
        if not expected_zip.exists():
            fallback_zip = self.project_root / "dist" / zip_filename
            if fallback_zip.exists():
                expected_zip = fallback_zip
        self.edit_pub_zip.setText(str(expected_zip))

    def _load_release_notes_list(self):
        """讀取 release_notes 資料夾內所有歷史說明檔案"""
        self.combo_notes.blockSignals(True)
        self.combo_notes.clear()

        note_files = sorted(self.notes_dir.glob("*.md"), key=lambda p: p.name, reverse=True)
        for f in note_files:
            self.combo_notes.addItem(f.name, str(f))

        self.combo_notes.blockSignals(False)

        if self.combo_notes.count() > 0:
            self._on_note_selected(0)
        else:
            self.txt_notes_editor.setPlainText("")

    def _on_note_selected(self, index: int):
        if index < 0 or index >= self.combo_notes.count():
            return
        file_path_str = self.combo_notes.currentData()
        if file_path_str:
            p = Path(file_path_str)
            if p.exists():
                try:
                    content = p.read_text(encoding="utf-8-sig")
                    self.txt_notes_editor.setPlainText(content)
                except Exception as e:
                    self._log(f"[WARN] 讀取檔案失敗：{e}")

    def _create_new_release_note(self):
        """建立全新以時間戳命名之發布說明檔案草稿"""
        ts = datetime.now().strftime("%Y%m%d_%H%M")
        filename = f"release_{ts}.md"
        target_path = self.notes_dir / filename

        version = detect_version(self.project_root)
        template = f"""## GPX Ride Renderer v{version} 更新內容

### 新增功能與亮點
- 

### 體驗與視覺優化
- 

### 錯誤修復與效能改善
- 
"""
        target_path.write_text(template, encoding="utf-8")
        self._load_release_notes_list()

        # 切換選取至新建立的檔案
        idx = self.combo_notes.findText(filename)
        if idx >= 0:
            self.combo_notes.setCurrentIndex(idx)
        self._log(f"[INFO] 已建立新發布說明草稿：{filename}")

    def _save_current_release_note(self):
        """儲存當前編輯的發布說明"""
        if self.combo_notes.count() == 0:
            return
        file_path_str = self.combo_notes.currentData()
        if not file_path_str:
            return
        p = Path(file_path_str)
        content = self.txt_notes_editor.toPlainText()
        try:
            p.write_text(content, encoding="utf-8")
            self._log(f"[OK] 已成功儲存發布說明：{p.name}")
            QMessageBox.information(self, "儲存成功", f"發布說明 {p.name} 儲存完成！")
        except Exception as e:
            self._log(f"[ERROR] 儲存失敗：{e}")
            QMessageBox.critical(self, "儲存失敗", f"儲存檔案失敗：{e}")

    def _run_build_process(self):
        """啟動 PyInstaller 打包腳本"""
        if self.worker and self.worker.isRunning():
            QMessageBox.warning(self, "警告", "目前已有打包或發布工作正在執行中！")
            return

        build_script = self.tools_dir / "build_exe.py"
        if not build_script.exists():
            QMessageBox.critical(self, "錯誤", f"找不到打包腳本：{build_script}")
            return

        venv_python = self.project_root / ".venv" / "Scripts" / "python.exe"
        if not venv_python.exists():
            venv_python = Path(sys.executable)

        cmd = [str(venv_python), str(build_script)]
        self._log("\n" + "=" * 65)
        self._log(f"[START] 啟動打包作業：{' '.join(cmd)}")
        self._log("=" * 65)

        self.progress_bar.setRange(0, 0)
        self.btn_run_build.setEnabled(False)
        self.btn_run_publish.setEnabled(False)

        self.worker = WorkerThread(cmd, cwd=self.project_root)
        self.worker.line_received.connect(self._log)
        self.worker.finished_signal.connect(self._on_build_finished)
        self.worker.start()

    def _on_build_finished(self, returncode: int):
        self.progress_bar.setRange(0, 100)
        self.btn_run_build.setEnabled(True)
        self.btn_run_publish.setEnabled(True)

        if returncode == 0:
            self.progress_bar.setValue(100)
            self._log("[SUCCESS] 🎉 EXE 打包與 ZIP 壓縮作業成功完成！\n")
            if self.chk_open_dist.isChecked():
                self._open_dist_folder()
            self._refresh_environment_status()
            QMessageBox.information(self, "完成", "打包作業已成功完成！")
        else:
            self.progress_bar.setValue(0)
            self._log(f"[ERROR] ❌ 打包失敗 (退出代碼 {returncode})\n")
            QMessageBox.critical(self, "失敗", f"打包失敗，退出代碼：{returncode}")

    def _get_dist_dir(self) -> Path:
        """取得發行輸出目錄 (預設 D:\\gpx-ride-animation-releases)"""
        d = Path("D:/gpx-ride-animation-releases")
        if d.parent.exists():
            return d
        return self.project_root.parent / "gpx-ride-animation-releases"

    def _open_dist_folder(self):
        """開啟發行輸出資料夾"""
        dist_dir = self._get_dist_dir()
        if not dist_dir.exists():
            dist_dir.mkdir(parents=True, exist_ok=True)
        if sys.platform == "win32":
            os.startfile(str(dist_dir))
        else:
            subprocess.Popen(["xdg-open", str(dist_dir)])

    def _test_run_exe(self):
        """測試啟動打包好的 EXE"""
        dist_dir = self._get_dist_dir()
        exe_path = dist_dir / "GPX_Ride_Renderer" / "GPX_Ride_Renderer.exe"
        if not exe_path.exists():
            QMessageBox.warning(self, "找不到檔案", f"找不到打包產物：\n{exe_path}\n請先執行打包作業。")
            return
        self._log(f"[INFO] 正在啟動測試執行檔：{exe_path}")
        subprocess.Popen([str(exe_path)], cwd=str(exe_path.parent))

    def _browse_publish_zip(self):
        """選擇發布 ZIP 檔案"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "選擇要發布的 ZIP 檔案", str(self._get_dist_dir()), "ZIP Files (*.zip)"
        )
        if file_path:
            self.edit_pub_zip.setText(file_path)

    def _run_publish_process(self):
        """啟動 GitHub Releases 發布腳本"""
        if self.worker and self.worker.isRunning():
            QMessageBox.warning(self, "警告", "目前已有工作正在執行中！")
            return

        zip_path = Path(self.edit_pub_zip.text().strip())
        if not zip_path.exists():
            QMessageBox.warning(self, "檔案不存在", f"找不到欲上傳之發布檔案：\n{zip_path}\n請先執行打包或手動選擇 ZIP 檔案。")
            return

        tag = self.edit_pub_tag.text().strip()
        version = tag.lstrip("v")
        publish_script = self.tools_dir / "publish_release.py"

        token = os.environ.get("GITHUB_TOKEN") or self.env_vars.get("GITHUB_TOKEN", "")
        if not token:
            QMessageBox.critical(
                self, "缺少 Token",
                "未偵測到 GITHUB_TOKEN！\n請於專案根目錄的 .env 檔案中設定 GITHUB_TOKEN=ghp_xxxx 後重試。"
            )
            return

        confirm = QMessageBox.question(
            self, "確認發布",
            f"即將發布至 GitHub Releases：\n• 版本標籤：{tag}\n• 壓縮檔案：{zip_path.name}\n\n確定要繼續嗎？",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.Yes
        )
        if confirm != QMessageBox.Yes:
            return

        venv_python = self.project_root / ".venv" / "Scripts" / "python.exe"
        if not venv_python.exists():
            venv_python = Path(sys.executable)

        cmd = [str(venv_python), str(publish_script), "--version", version, "-y"]
        self._log("\n" + "=" * 65)
        self._log(f"[START] 啟動 GitHub Releases 發布：{' '.join(cmd)}")
        self._log("=" * 65)

        self.progress_bar.setRange(0, 0)
        self.btn_run_build.setEnabled(False)
        self.btn_run_publish.setEnabled(False)

        self.worker = WorkerThread(cmd, cwd=self.project_root)
        self.worker.line_received.connect(self._log)
        self.worker.finished_signal.connect(self._on_publish_finished)
        self.worker.start()

    def _on_publish_finished(self, returncode: int):
        self.progress_bar.setRange(0, 100)
        self.btn_run_build.setEnabled(True)
        self.btn_run_publish.setEnabled(True)

        if returncode == 0:
            self.progress_bar.setValue(100)
            self._log("[SUCCESS] 🎉 GitHub Releases 發布作業成功完成！\n")
            QMessageBox.information(self, "發布成功", "Release 已成功建立並上傳至 GitHub！")
        else:
            self.progress_bar.setValue(0)
            self._log(f"[ERROR] ❌ 發布失敗 (退出代碼 {returncode})\n")
            QMessageBox.critical(self, "發布失敗", f"發布作業失敗，退出代碼：{returncode}")

    def _copy_console_log(self):
        """複製控制台全部日誌到剪貼簿"""
        clipboard = QApplication.clipboard()
        if clipboard:
            clipboard.setText(self.txt_console.toPlainText())
            self._log("[INFO] 已複製控制台日誌至剪貼簿。")


def main():
    app = QApplication(sys.argv)
    window = ReleaseManagerWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
