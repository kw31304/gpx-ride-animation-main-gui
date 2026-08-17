
**Workflow Rule:**
每次完成程式碼修改，在執行 `git add` 與 `git push` 之前，你必須嚴格遵守以下流程：

1. 檢查專案根目錄是否存在 `changelogs/` 資料夾，若無請自動建立。
2. 在該資料夾內建立一個以當前日期命名的 Markdown 檔案（例如 `update_20260817.md`）。
3. 在檔案內詳細記錄你剛才修改了哪些邏輯或 UI 設定...等等。
4. 寫入完成後，再將這個日誌檔連同你修改的程式碼一起執行 `git add .`、`git commit` 並 `git push`。
