"""Local registry for browser windows created by this CLI."""
from __future__ import annotations

import json
import secrets
import string
from datetime import datetime

from ._compat import *
from .paths import WINDOWS_FILE, _atomic_write
from .colors import note, status_line


def _load() -> list[dict]:
    try:
        raw = json.loads(WINDOWS_FILE.read_text(encoding="utf-8"))
        return [item for item in raw if isinstance(item, dict)] if isinstance(raw, list) else []
    except (OSError, ValueError, TypeError, json.JSONDecodeError):
        return []


def _save(items: list[dict]):
    _atomic_write(WINDOWS_FILE, json.dumps(items, ensure_ascii=False, indent=2) + "\n")


def _new_id(items: list[dict]) -> str:
    alphabet = string.ascii_uppercase + string.digits
    existing = {item.get("id") for item in items}
    while True:
        value = "CW-" + "".join(secrets.choice(alphabet) for _ in range(8))
        if value not in existing:
            return value


def register_window(hwnd: int, url: str) -> str:
    items = _load()
    window_id = _new_id(items)
    items.append({
        "id": window_id,
        "hwnd": int(hwnd),
        "url": url,
        "created_at": datetime.now().isoformat(timespec="seconds"),
    })
    _save(items)
    return window_id


def _alive_items() -> list[dict]:
    if os.name != "nt":
        return []
    import ctypes
    user32 = ctypes.windll.user32
    alive = []
    for item in _load():
        try:
            if user32.IsWindow(int(item["hwnd"])):
                alive.append(item)
        except (KeyError, TypeError, ValueError):
            continue
    if len(alive) != len(_load()):
        _save(alive)
    return alive


def kill_window(window_id: str) -> bool:
    if os.name != "nt":
        note("ERR", "視窗 ID 管理只支援 Windows")
        return False
    import ctypes
    user32 = ctypes.windll.user32
    items = _alive_items()
    match = next((item for item in items if item.get("id") == window_id), None)
    if match is None:
        note("ERR", f"找不到本機視窗 ID：{window_id}")
        return False
    user32.PostMessageW(int(match["hwnd"]), 0x0010, 0, 0)  # WM_CLOSE
    _save([item for item in items if item is not match])
    status_line(f"關閉視窗 {window_id}", "DONE")
    return True


def kill_all() -> int:
    if os.name != "nt":
        note("ERR", "視窗 ID 管理只支援 Windows")
        return 0
    import ctypes
    user32 = ctypes.windll.user32
    items = _alive_items()
    for item in items:
        user32.PostMessageW(int(item["hwnd"]), 0x0010, 0, 0)
    _save([])
    status_line("關閉 CLI 登記視窗", "DONE")
    note("INFO", f"已送出關閉要求：{len(items)} 個視窗")
    return len(items)


def cmd_kill(args: list[str]):
    if len(args) == 2 and args[0].lower() == "-kill":
        kill_window(args[1])
    elif len(args) == 1 and args[0].lower() == "--kill":
        note("ERR", "請提供視窗 ID：cool -k -kill CW-XXXXXXXX")
    elif len(args) == 1:
        kill_window(args[0])
    else:
        note("ERR", "用法：cool -k -kill <id>")


__all__ = ["register_window", "kill_window", "kill_all", "cmd_kill"]
