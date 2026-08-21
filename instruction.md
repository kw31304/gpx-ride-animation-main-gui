**Workflow Rule:**
每次完成程式碼修改，在執行 `git add` 與 `git push` 之前，你必須嚴格遵守以下雙軌記錄與提交流程：

1. **內部開發日誌 (Internal Changelogs)**

   * 檢查專案根目錄是否存在 `changelogs/` 資料夾，若無請自動建立。
   * 建立以時間戳命名的日誌檔案（格式：`changelogs/update_YYYYMMDD_HHMM.md`）。
   * 請嚴格按照以下結構分類說明：
     * **邏輯變更 (Logic)**：摘要 Python 核心邏輯的修改。若涉及特定控制器或物件（例如 `TabPCD`），請務必確保大小寫與命名標示完全準確。
     * **介面與體驗 (UI/UX)**：詳細列出 PySide6 的變動。必須明確指出 `.ui` 檔案的修改、特定元件（如 `Edit_Btn_Format` 等按鈕或文字框）的屬性調整。
     * **樣式設定 (Styling)**：若有調整 QSS 樣式表，請具體列出變更細節，包含精確的色碼 (Hex codes)、對齊邏輯，或是自訂的 Tooltip 行為。

2. **公開發布說明 (Public Release Notes)**

   * 檢查專案根目錄是否存在 `release_notes/` 資料夾，若無請自動建立。
   * 在該資料夾內建立以當前日期與時間命名的 Markdown 檔案（例如 `release_notes/release_20260821_1619.md`），專門作為打包 EXE 執行檔後，發布至 GitHub Releases 給使用者看的更新項目。
   * 內容須以「使用者導向」撰寫（繁體中文），捨棄底層程式碼細節，簡明扼要地列出：新增功能、體驗優化項目與修復的已知問題。

3. **語法驗證、版本控制與推送**

   * 執行基礎語法檢查（確保 Python 腳本無 SyntaxError）。
   * 雙邊日誌寫入完成後，務必將這些 Markdown 檔加入追蹤。
   * 連同所有修改的程式碼一起執行：
     * `git add .`
     * `git commit -m "<feat/fix/refactor/style/perf>: <簡明摘要>"`
     * `git push`
