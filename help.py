"""Help text for the small browser launcher CLI."""
from __future__ import annotations

from .colors import *

HELP_TEXT = f"""{CYAN}cool.py — Cool English 瀏覽器啟動工具{RESET}

  {GREEN}cool -l{RESET}, {GREEN}--login{RESET}       在 Edge/Chrome 手動登入
  {GREEN}cool -u{RESET}, {GREEN}--url{RESET}         開啟課程網址
  {GREEN}cool -c --choose{RESET}             選擇 Edge 或 Chrome
  {GREEN}cool -k -kill ID{RESET}           關閉指定 CLI 視窗
  {GREEN}cool -K --KILLALL{RESET}          關閉全部 CLI 登記視窗
  {GREEN}cool -v{RESET}, {GREEN}--version{RESET}     顯示版本
  {GREEN}cool -h{RESET}, {GREEN}--help{RESET}        顯示說明

網址流程：
  執行 `cool -u` 後，CLI 會詢問頁面數量與每個視窗的開啟延遲。
  版面固定使用 Snap/FancyZones 風格，每個新視窗出現後立即重排。
  `cool -u -c` 會先選擇瀏覽器，再開始開啟頁面。

CLI 不讀取或保存密碼、Cookie、瀏覽器儲存資料，也不會關閉分頁。
"""

CMD_HELP = {
    "login": f"{CYAN}cool -l{RESET}\n在使用者的 Edge/Chrome 中手動登入；登入資料只留在瀏覽器。",
    "url": f"{CYAN}cool -u{RESET}\n詢問頁面數量與開啟延遲，固定使用 Snap 版面。",
    "help": f"{CYAN}cool -h{RESET}\n顯示可用指令。",
}

__all__ = [name for name in globals() if not name.startswith("__")]
