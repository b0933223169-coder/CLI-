"""Manual browser login command."""
from __future__ import annotations

from ..paths import *
from ..colors import *
import subprocess


def cmd_login(args: list[str] | None = None):
    if args:
        note("WARN", "cool -l 不接受參數")
        return
    found = find_user_browser()
    if found is None:
        status_line("開啟登入頁", "FAILED")
        note("ERR", "找不到已安裝的 Microsoft Edge 或 Google Chrome")
        return
    channel, executable = found
    try:
        subprocess.Popen(
            [str(executable), LOGIN_URL],
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    except OSError as exc:
        status_line("開啟登入頁", "FAILED")
        note("ERR", f"無法開啟瀏覽器：{exc}")
        return
    status_line(f"開啟登入頁 ({channel})", "DONE")
    note("INFO", "請在瀏覽器中手動登入；CLI 不讀取或保存密碼、Cookie。")


__all__ = [name for name in globals() if not name.startswith("__")]
