# -*- coding: utf-8 -*-
"""
手動發布 GPX Ride Renderer 至 GitHub Releases 之專用腳本。
"""

import argparse
import json
import os
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path


def detect_version(project_root: Path) -> str:
    """自動從 gpx_renderer/__init__.py 讀取 __version__ 版本號。"""
    init_file = project_root / "gpx_renderer" / "__init__.py"
    if init_file.exists():
        try:
            content = init_file.read_text(encoding="utf-8")
            match = re.search(r'__version__\s*=\s*["\']([^"\']+)["\']', content)
            if match:
                return match.group(1).strip()
        except Exception as e:
            print(f"[WARN] 讀取 __init__.py 版本失敗：{e}")
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


def load_release_notes(project_root: Path) -> tuple[str, str]:
    """
    優先讀取 release_notes/ 最新說明的 Markdown 檔案；
    若無則向下相容讀取根目錄下的 release_notes.md。
    回傳 (內容, 來源檔案路徑說明)。
    """
    notes_dir = project_root / "release_notes"
    if notes_dir.exists() and notes_dir.is_dir():
        note_files = sorted(notes_dir.glob("*.md"), key=lambda p: p.name, reverse=True)
        for note_file in note_files:
            try:
                content = note_file.read_text(encoding="utf-8-sig").strip()
                if content:
                    return content, f"release_notes/{note_file.name}"
            except Exception as e:
                print(f"[WARN] 讀取 {note_file.name} 失敗：{e}")

    notes_file = project_root / "release_notes.md"
    if notes_file.exists():
        try:
            content = notes_file.read_text(encoding="utf-8-sig").strip()
            if content:
                return content, "release_notes.md"
        except Exception as e:
            print(f"[WARN] 讀取 release_notes.md 失敗：{e}")
    return "", ""


def publish_to_github_release(zip_file: Path, version: str, repo: str, token: str, release_notes: str = "") -> bool:
    """透過 GitHub REST API 自動建立/更新 Release 並上傳 ZIP 檔案。"""
    tag = f"v{version}"
    release_title = f"GPX Ride Renderer v{version}"

    body_parts = [f"## GPX Ride Renderer v{version} (Windows 64-bit)\n"]
    body_parts.append(
        f"### 下載與使用說明\n"
        f"1. 下載下方 `{zip_file.name}` 壓縮檔。\n"
        f"2. 解壓縮至任意資料夾。\n"
        f"3. 雙擊執行 `GPX_Ride_Renderer.exe` 即可開始使用。\n\n"
        f"### 系統需求與特性\n"
        f"- 系統支援：Windows 10 / 11 64-bit\n"
        f"- 內建 FFmpeg 核心與完整地圖/3D地形模組\n"
        f"- 免安裝 Python 環境，開箱即用\n"
    )
    if release_notes:
        body_parts.append(f"### 更新內容\n{release_notes}\n")
    release_body = "\n".join(body_parts)

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
        with urllib.request.urlopen(req, timeout=30) as resp:
            if resp.status == 200:
                release_data = json.loads(resp.read().decode("utf-8"))
                print(f"[INFO] 偵測到既有 Release ({tag})，正在同步更新發布說明與附件...")
                # 同步更新說明內容
                patch_url = f"https://api.github.com/repos/{repo}/releases/{release_data['id']}"
                patch_payload = json.dumps({"name": release_title, "body": release_body}).encode("utf-8")
                patch_headers = dict(headers)
                patch_headers["Content-Type"] = "application/json"
                patch_req = urllib.request.Request(patch_url, data=patch_payload, headers=patch_headers, method="PATCH")
                try:
                    with urllib.request.urlopen(patch_req, timeout=30) as patch_resp:
                        release_data = json.loads(patch_resp.read().decode("utf-8"))
                        print("[OK] 已成功同步最新更新說明至 Release！")
                except Exception as patch_err:
                    print(f"[WARN] 更新 Release 說明異常：{patch_err}")
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
            with urllib.request.urlopen(create_req, timeout=30) as resp:
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
                    with urllib.request.urlopen(init_req, timeout=30):
                        pass
                    # 重試建立 Release
                    with urllib.request.urlopen(create_req, timeout=30) as retry_resp:
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
                with urllib.request.urlopen(del_req, timeout=30) as del_resp:
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
        with urllib.request.urlopen(upload_req, timeout=300) as resp:
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


def parse_args():
    parser = argparse.ArgumentParser(description="手動發布 GPX Ride Renderer 至 GitHub Releases")
    parser.add_argument("-y", "--yes", action="store_true", help="略過確認提示，直接執行發布")
    parser.add_argument("--repo", type=str, default="", help="指定目標 GitHub 倉庫 (例如 user/repo)")
    parser.add_argument("--version", type=str, default="", help="指定發布版本號 (例如 1.3.0)")
    return parser.parse_args()


def main():
    if hasattr(sys.stdout, "reconfigure"):
        try:
            sys.stdout.reconfigure(encoding="utf-8")
        except Exception:
            pass

    args = parse_args()
    project_root = Path(__file__).resolve().parent
    version = args.version or detect_version(project_root)
    env_vars = load_env_vars(project_root)

    github_token = os.environ.get("GITHUB_TOKEN") or env_vars.get("GITHUB_TOKEN", "")
    github_repo = args.repo or os.environ.get("GITHUB_REPO") or env_vars.get("GITHUB_REPO", "kw31304/gpx-ride-animation-releases")

    zip_filename = f"GPX_Ride_Renderer_v{version}_windows_x64.zip"
    dist_dir = project_root.parent / "gpx-ride-animation-releases"
    zip_path = dist_dir / zip_filename

    if not zip_path.exists():
        fallback_zip = project_root / "dist" / zip_filename
        if fallback_zip.exists():
            zip_path = fallback_zip

    release_notes, notes_source = load_release_notes(project_root)

    print("=" * 70)
    print(f"[INFO] GPX Ride Renderer 發布至 GitHub Releases")
    print(f"• 目標版本：v{version}")
    print(f"• 目標倉庫：{github_repo}")
    print(f"• 壓縮檔案：{zip_path}")
    if notes_source:
        print(f"• 更新說明：已載入 `{notes_source}` (將自動附加至 Release 說明)")
    else:
        print("• 更新說明：未偵測到 release notes (將使用預設說明樣板)")
    print("=" * 70)

    if not zip_path.exists():
        print(f"[ERROR] 找不到待發布的壓縮檔案：{zip_path}")
        print("請先執行 python build_exe.py 進行打包與壓縮後再發布。")
        sys.exit(1)

    if not github_token:
        print("[ERROR] 未找到 GITHUB_TOKEN，無法發布。")
        print("請確認專案目錄下的 .env 檔案中是否包含 GITHUB_TOKEN=ghp_xxx")
        sys.exit(1)

    if not args.yes:
        confirm = input(f"\n即將發布 {zip_filename} 至 GitHub ({github_repo})，確認發布？[Y/n]: ").strip().lower()
        if confirm and confirm != "y":
            print("[INFO] 已取消發布。")
            sys.exit(0)

    success = publish_to_github_release(
        zip_file=zip_path,
        version=version,
        repo=github_repo,
        token=github_token,
        release_notes=release_notes,
    )
    if not success:
        sys.exit(1)


if __name__ == "__main__":
    main()

