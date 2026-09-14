"""Minimal interactive command loop."""
from __future__ import annotations

import shlex

from .colors import *
from .help import *
from .version import *
from .commands.account import cmd_login
from .commands.urls import cmd_url
from .window_registry import cmd_kill, kill_all
from .browser_choice import cmd_choose


def repl():
    while True:
        try:
            line = input(f"{CYAN}cool>{RESET} ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            return
        if not line:
            continue
        if line.lower() in {"exit", "quit", "q", "/exit"}:
            return
        try:
            parts = shlex.split(line)
        except ValueError as exc:
            note("ERR", f"指令格式錯誤：{exc}")
            continue
        if parts and parts[0].lower() == "cool":
            parts = parts[1:]
        if not parts:
            print(HELP_TEXT)
            continue
        dispatch(parts[0].lower(), parts[1:])


def dispatch(command: str, args: list[str]):
    if command in ("-c", "--choose"):
        cmd_choose(args[1:] if command == "-c" and args[:1] == ["--choose"] else args)
    elif command in ("-h", "--help", "help"):
        print(HELP_TEXT)
    elif command in ("-v", "--version"):
        print(VERSION)
    elif command in ("-l", "--login"):
        cmd_login(args)
    elif command in ("-u", "--url", "--visit"):
        cmd_url(args)
    elif command in ("-K", "--killall", "--kill-all") or (
        command == "-k" and args and args[0].lower() in ("--killall", "--kill-all")
    ):
        kill_all()
    elif command in ("-k", "--kill"):
        cmd_kill(args)
    else:
        note("WARN", f"未知指令：{command}")
        print(HELP_TEXT)


__all__ = ["repl", "dispatch"]
