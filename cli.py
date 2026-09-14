"""Command-line entry point for the browser launcher."""
from __future__ import annotations

import os
import sys

from .colors import *
from .help import *
from .paths import find_user_browser
from .version import VERSION
from .repl import dispatch, repl
from .window_registry import cmd_kill, kill_all
from .browser_choice import cmd_choose


def ensure_user_browser_installed():
    if find_user_browser() is None:
        note("ERR", "找不到已安裝的 Microsoft Edge 或 Google Chrome。")
        note("INFO", "請先安裝 Edge/Chrome，或設定 COOL_BROWSER=edge/chrome。")
        raise SystemExit(1)


def main():
    args = sys.argv[1:]
    if not args:
        ensure_user_browser_installed()
        repl()
        return

    if any(arg in ("-h", "--help", "/help") for arg in args):
        command = args[0].lstrip("-/").lower()
        aliases = {
            "l": "login",
            "login": "login",
            "u": "url",
            "url": "url",
            "visit": "url",
        }
        print(CMD_HELP.get(aliases.get(command, ""), HELP_TEXT))
        return
    if args[0] in ("-v", "--version"):
        print(VERSION)
        return
    if args[0].lower() in ("-c", "--choose"):
        cmd_choose(args[1:])
        return
    if args[0].lower() in ("-k", "--killall", "--kill-all", "--kill"):
        dispatch(args[0].lower(), args[1:])
        return

    ensure_user_browser_installed()
    dispatch(args[0].lower(), args[1:])


__all__ = ["main"]
