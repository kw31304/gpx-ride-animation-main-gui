# -*- coding: utf-8 -*-
"""
手動發布 GPX Ride Renderer 至 GitHub Releases 之專用腳本。
"""

import json
import os
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path


def detect_version(project_root: Path) -> str:
    """自動從 qt_app.py 的 setWindowTitle 中解析版本號。"""
    qt_app_file = project_root / "gpx_renderer" / "gui" / "qt_app.py"
    if qt_app_file.exists():
        try:
            content = qt_app_file.read_text(encoding="utf-8")
            match = re.search(r'setWindowTitle\(\s*["\'].*?[vV]?(\d+\.\d+(?:\.\d+)?).*?["\']\s*\)', content)
            if match:
                return match.group(1)
        except Exception as e:
            print(f"[WARN] 讀取 qt_app.py 版本失敗：{e}")
    return "1.0.0"


def load_env_vars(project_root: Path) -> dict:
    """載入專案目錄下的 .env 環境設定檔。"""
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


def publish_to_github_release(zip_file: Path, version: str, repo: str, token: str) -> bool:
    """透過 GitHub REST API 自動建立 Release 並上傳 ZIP 檔案。"""
    tag = f"v{version}"
    release_title = f"GPX Ride Renderer v{version}"
    release_body = (
        f"## GPX Ride Renderer v{version} (Windows 64-bit)\n\n"
        f"### 📥 下載與使用說明\n"
        f"1. 下載下方 `{zip_file.name}` 壓縮檔。\n"
        f"2. 解壓縮至任意資料夾。\n"
        f"3. 雙擊執行 `GPX_Ride_Renderer.exe` 即可開始使用。\n\n"
        f"### ⚙️ 特性與需求\n"
        f"- 系統支援：Windows 10 / 11 64-bit\n"
        f"- 內建 FFmpeg 核心與完整地圖/3D地形模組\n"
        f"- 免安裝 Python 環境，開箱即用"
    )

    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": "GPX-Ride-Renderer-Builder",
    }

    print(f"\n[INFO] 正在連線至 GitHub 倉庫：{repo} (發布標籤: {tag})...")

    # 1. 檢查 Release 是否已存在
    release_data = None
    check_url = f"https://api.github.com/repos/{repo}/releases/tags/{tag}"
    req = urllib.request.Request(check_url, headers=headers, method="GET")
    try:
        with urllib.request.urlopen(req) as resp:
            if resp.status == 200:
                release_data = json.loads(resp.read().decode("utf-8"))
                print(f"[INFO] 偵測到既有 Release ({tag})，將直接更新該版本附件...")
    except urllib.error.HTTPError as e:
        if e.code != 404:
            print(f"[ERROR] 查詢 GitHub Release 失敗 (HTTP {e.code})：{e.read().decode('utf-8')}")
            return False

    # 2. 若不存在則建立 Release
    if not release_data:
        create_url = f"https://api.github.com/repos/{repo}/releases"
        payload = json.dumps({
            "tag_name": tag,
            "name": release_title,
            "body": release_body,
            "draft": False,
            "prerelease": False,
        }).encode("utf-8")
        create_headers = dict(headers)
        create_headers["Content-Type"] = "application/json"
        create_req = urllib.request.Request(create_url, data=payload, headers=create_headers, method="POST")
        try:
            with urllib.request.urlopen(create_req) as resp:
                release_data = json.loads(resp.read().decode("utf-8"))
                print(f"[OK] 成功建立 GitHub Release: {release_title}")
        except urllib.error.HTTPError as e:
            err_body = e.read().decode("utf-8")
            if e.code == 422 and "Repository is empty" in err_body:
                print("[INFO] 偵測到倉庫尚未初始化 (空倉庫)，正在自動建立初始 README.md 與 main 分支...")
                try:
                    import base64
                    init_content = base64.b64encode(b"# GPX Ride Renderer Releases\n\nOfficial releases and downloads for GPX Ride Renderer (Windows).\n").decode("utf-8")
                    init_payload = json.dumps({"message": "Initial commit: Initialize repository with README.md", "content": init_content}).encode("utf-8")
                    init_req = urllib.request.Request(f"https://api.github.com/repos/{repo}/contents/README.md", data=init_payload, headers=create_headers, method="PUT")
                    with urllib.request.urlopen(init_req):
                        pass
                    # 重試建立 Release
                    with urllib.request.urlopen(create_req) as retry_resp:
                        release_data = json.loads(retry_resp.read().decode("utf-8"))
                        print(f"[OK] 倉庫初始化完成，成功建立 GitHub Release: {release_title}")
                except Exception as init_err:
                    print(f"[ERROR] 嘗試自動初始化倉庫失敗：{init_err}")
                    return False
            else:
                print(f"[ERROR] 建立 GitHub Release 失敗 (HTTP {e.code})：{err_body}")
                return False

    # 3. 檢查並刪除同名舊 Asset
    upload_url_template = release_data.get("upload_url", "")
    base_upload_url = upload_url_template.split("{")[0]

    for asset in release_data.get("assets", []):
        if asset.get("name") == zip_file.name:
            asset_id = asset["id"]
            print(f"[INFO] 偵測到同名舊檔案 ({zip_file.name})，正在移除以覆蓋最新版...")
            del_url = f"https://api.github.com/repos/{repo}/releases/assets/{asset_id}"
            del_req = urllib.request.Request(del_url, headers=headers, method="DELETE")
            try:
                with urllib.request.urlopen(del_req) as del_resp:
                    pass
            except Exception as e:
                print(f"[WARN] 移除舊 Asset 異常：{e}")

    # 4. 上傳新的 ZIP Asset
    upload_url = f"{base_upload_url}?name={urllib.parse.quote(zip_file.name)}"
    upload_headers = dict(headers)
    upload_headers["Content-Type"] = "application/zip"
    upload_headers["Content-Length"] = str(zip_file.stat().st_size)

    print(f"[INFO] 正在上傳 {zip_file.name} 至 GitHub Releases (檔案大小: {zip_file.stat().st_size / (1024*1024):.2f} MB，請稍候)...")
    with open(zip_file, "rb") as f:
        data = f.read()

    upload_req = urllib.request.Request(upload_url, data=data, headers=upload_headers, method="POST")
    try:
        with urllib.request.urlopen(upload_req) as resp:
            result = json.loads(resp.read().decode("utf-8"))
            download_url = result.get("browser_download_url", "")
            print("=" * 70)
            print("[SUCCESS] 🎉 成功發布至 GitHub Releases！")
            print(f"• Release 頁面網址：{release_data.get('html_url')}")
            print(f"• 檔案公開下載連結：{download_url}")
            print("=" * 70)
            return True
    except urllib.error.HTTPError as e:
        print(f"[ERROR] 上傳檔案失敗 (HTTP {e.code})：{e.read().decode('utf-8')}")
        return False


def main():
    if hasattr(sys.stdout, "reconfigure"):
        try:
            sys.stdout.reconfigure(encoding="utf-8")
        except Exception:
            pass

    project_root = Path(__file__).resolve().parent
    version = detect_version(project_root)
    env_vars = load_env_vars(project_root)

    github_token = os.environ.get("GITHUB_TOKEN") or env_vars.get("GITHUB_TOKEN", "")
    github_repo = os.environ.get("GITHUB_REPO") or env_vars.get("GITHUB_REPO", "kw31304/gpx-ride-animation-releases")

    dist_dir = project_root.parent / "gpx-ride-animation-releases"
    zip_filename = f"GPX_Ride_Renderer_v{version}_windows_x64.zip"
    zip_path = dist_dir / zip_filename

    print("=" * 70)
    print(f"[INFO] GPX Ride Renderer 手動發布至 GitHub Releases")
    print(f"• 目標版本：v{version}")
    print(f"• 目標倉庫：{github_repo}")
    print(f"• 壓縮檔案：{zip_path}")
    print("=" * 70)

    if not zip_path.exists():
        print(f"[ERROR] 找不到待發布的壓縮檔案：{zip_path}")
        print("請先執行 python build_exe.py 進行打包與壓縮後再發布。")
        sys.exit(1)

    if not github_token:
        print("[ERROR] 未找到 GITHUB_TOKEN，無法發布。")
        print("請確認專案目錄下的 .env 檔案中是否包含 GITHUB_TOKEN=ghp_xxx")
        sys.exit(1)

    confirm = input(f"\n即將發布 {zip_filename} 至 GitHub ({github_repo})，確認發布？[Y/n]: ").strip().lower()
    if confirm and confirm != "y":
        print("[INFO] 已取消發布。")
        sys.exit(0)

    success = publish_to_github_release(
        zip_file=zip_path,
        version=version,
        repo=github_repo,
        token=github_token,
    )
    if not success:
        sys.exit(1)


if __name__ == "__main__":
    main()
