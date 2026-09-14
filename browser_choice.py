"""Interactive selection of the local browser used by cool."""
from __future__ import annotations

from .colors import *
from .paths import installed_browsers, save_browser_choice


def cmd_choose(args: list[str]):
    if args:
        note("WARN", "用法：cool -c --choose")
        return
    browsers = installed_browsers()
    if not browsers:
        note("ERR", "找不到可用的 Edge 或 Chrome")
        return
    print(f"\n{CYAN}選擇 cool 使用的瀏覽器：{RESET}")
    for index, (channel, executable) in enumerate(browsers, 1):
        print(f"  {YELLOW}{index}.{RESET} {channel} — {executable}")
    try:
        choice = input("請輸入編號（直接 Enter 取消）：").strip()
        if not choice:
            note("INFO", "已取消")
            return
        channel, executable = browsers[int(choice) - 1]
    except (ValueError, IndexError, EOFError, KeyboardInterrupt):
        print()
        note("ERR", "無效的瀏覽器選擇")
        return
    save_browser_choice(channel)
    status_line(f"瀏覽器偏好：{channel}", "DONE")
    note("INFO", f"已保存：{executable}")


__all__ = ["cmd_choose"]
