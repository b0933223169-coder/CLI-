# CLI for windows
一款用於 Windows 終端的課程網址管理工具，將工作交給使用者已安裝的
Microsoft Edge 或 Google Chrome。

`cool -l` 與 `cool -u` 都會使用本機已安裝、目前使用者 profile 的
Microsoft Edge 或 Google Chrome，不使用 Playwright、不注入或保存 Cookie，
也不會由 CLI 關閉分頁。登入由使用者在瀏覽器中手動完成。可用
`COOL_BROWSER=edge` 或 `COOL_BROWSER=chrome` 指定偏好；未指定時會優先使用
Edge，再使用 Chrome。

使用 `cool -c --choose` 可選擇本機已安裝的 Edge 或 Chrome；選擇會保存為
本機偏好，之後登入與課程指令都使用該瀏覽器。偏好不會傳送到網站。
也可以使用 `cool -u -c`，在本次開啟課程前先選擇瀏覽器。

保留的指令：

```text
cool -l
cool -c --choose
cool -u
cool -k -kill CW-XXXXXXXX
cool -K --KILLALL
cool -h
cool -v
```

執行 `cool -u` 後，程式會詢問要開啟幾個頁面，以及每個頁面之間的延遲秒數；
版面固定使用 Snap，並在每個新視窗出現後立即重新排列。CLI 不會修改課程
請求、偽造學習資料、讀取瀏覽器密碼或管理登入狀態。

每個由 `cool -u` 建立的視窗會取得一個只存在本機的 ID，例如
`CW-A1B2C3D4`。`cool -k -kill <id>` 只會關閉該 ID 對應的視窗；
`cool -K --KILLALL` 只會關閉 CLI 登記過的視窗。ID 不會傳送到網站。

版面引擎參考 PowerToys FancyZones 的 Zone 概念，但由本專案以 Win32 API
重新實作，使用左右、左大右上下、四格等 Snap 模板。
