"""Saved-course URL management and browser command."""
from __future__ import annotations
from .._compat import *
from ..paths import *
from ..colors import *
import time
import math
from ..win_workspace import (
    arrange_windows,
    _browser_windows,
    current_virtual_desktop_id,
    move_window_to_virtual_desktop,
)
from ..window_registry import register_window
from ..browser_choice import cmd_choose

def load_urls() -> list[str]:
    """讀取儲存的課程網址清單。"""
    if not URLS_FILE.exists():
        return []
    try:
        lines = URLS_FILE.read_text(encoding="utf-8").splitlines()
        urls = []
        for l in lines:
            l = l.strip()
            if l and not l.startswith("#") and (l.startswith("http://") or l.startswith("https://")):
                if l not in urls:
                    urls.append(l)
        return urls
    except Exception:
        return []

def save_urls(urls: list[str]):
    """將網址清單排版並寫入 urls.txt。"""
    header = [
        "# Cool English 課程網址清單",
        f"# 最後更新時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        "# 每行一個網址，支援 cool -u 快速選取或依序瀏覽",
        "",
    ]
    data = "\n".join(header + urls) + "\n"
    _atomic_write(URLS_FILE, data, 0o600)

def cmd_write(args: list[str] = None):
    """批量寫入/貼上課程網址並自動排版儲存。"""
    print(f"{CYAN}=== 批量寫入課程網址 (-w) ==={RESET}")
    print(f"{DIM}請直接貼上包含網址的文字（可多行、可含雜訊）。{RESET}")
    print(f"{DIM}輸入完成後請按兩次 Enter，或輸入空白行送出：{RESET}\n")

    input_lines = []
    while True:
        try:
            line = input()
            if not line.strip():
                if input_lines:
                    break
                else:
                    continue
            input_lines.append(line)
        except (EOFError, KeyboardInterrupt):
            print()
            break

    raw_text = "\n".join(input_lines)
    found_urls = re.findall(r'https?://[^\s"\'<>]+', raw_text)
    if not found_urls:
        note("WARN", "未在輸入內容中找到任何有效網址 (http/https)")
        return []

    # 規範化與去重
    cleaned_urls = []
    for u in found_urls:
        u = u.rstrip(".,;)>]")
        if u not in cleaned_urls:
            cleaned_urls.append(u)

    existing = load_urls()
    total = list(existing)
    added_count = 0
    for u in cleaned_urls:
        if u not in total:
            total.append(u)
            added_count += 1

    save_urls(total)
    status_line("網址排版與儲存", "DONE")
    note("INFO", f"本次解析出 {len(cleaned_urls)} 個網址，新增 {added_count} 個，清單總計 {len(total)} 個。")
    print(f"\n{CYAN}目前已儲存的課程網址清單：{RESET}")
    for idx, u in enumerate(total, 1):
        print(f"  {YELLOW}{idx:2d}.{RESET} {u}")
    print()
    return total

def _choose_url_interactive(urls: list[str]) -> list[str] | str | None:
    """提供互動式清單選擇要訪問的網址。"""
    if not urls:
        return None
    if os.name == "nt":
        print(f"\n{CYAN}已儲存的課程網址清單：{RESET}")
        for i, u in enumerate(urls, 1):
            print(f"  {YELLOW}{i:2d}.{RESET} {u}")
        print(f"  {GREEN}A.{RESET} 同時開啟全部")
        try:
            choice = input("請選擇編號/A（直接 Enter 取消）: ").strip()
        except (EOFError, KeyboardInterrupt):
            return None
        if not choice:
            return None
        if choice.upper() == "A":
            return "ALL"
        try:
            index = int(choice) - 1
            return urls[index] if 0 <= index < len(urls) else None
        except ValueError:
            return None
    try:
        import curses
        selected_res = None
        action = "select"

        def _curses_url_menu(stdscr):
            nonlocal selected_res, action
            curses.curs_set(0)
            stdscr.keypad(True)
            stdscr.nodelay(False)
            cur = 0
            confirm_delete = False
            total_items = len(urls) + 1
            marked_set = set()

            while True:
                stdscr.clear()
                h, w = stdscr.getmaxyx()
                stdscr.addstr(0, 0, "課程網址選單 [1-9/Space 多選] [Del 刪除]"[:w-1])
                stdscr.addstr(1, 0, DIM + "─" * min(w - 1, 80) + RESET)

                for i, u in enumerate(urls):
                    y = 3 + i
                    if y >= h - 3:
                        break
                    mark = "[✓]" if i in marked_set else "[ ]"
                    label = f" {mark} [{i+1:2d}] {u} "
                    if i == cur:
                        stdscr.addstr(y, 2, label[:w-4], curses.A_REVERSE | curses.A_BOLD)
                    else:
                        stdscr.addstr(y, 2, label[:w-4])

                all_y = 3 + len(urls)
                if all_y < h - 3:
                    all_label = "     [ A] ★ 同時開啟全部已儲存網址 (全開模式) "
                    if cur == len(urls):
                        stdscr.addstr(all_y, 2, all_label[:w-4], curses.A_REVERSE | curses.A_BOLD)
                    else:
                        stdscr.addstr(all_y, 2, all_label[:w-4], curses.A_BOLD)

                hint_y = min(h - 2, 3 + total_items + 1)
                if confirm_delete and cur < len(urls):
                    warn_msg = f" ⚠️ 確定要從清單中刪除第 [{cur+1}] 個網址嗎？ 按 [y] 確認刪除，其他鍵取消 "
                    stdscr.addstr(hint_y, 0, warn_msg[:w-1], curses.A_REVERSE | curses.A_BOLD)
                else:
                    count_str = f"已勾選 {len(marked_set)} 個網址" if marked_set else "單網址模式"
                    stdscr.addstr(hint_y, 0, DIM + f"[{count_str}] 1-9/Space:多選 | Del:刪除 | Enter:開啟"[:w-1] + RESET)

                stdscr.refresh()
                key = stdscr.getch()

                if confirm_delete:
                    if key in (ord('y'), ord('Y')):
                        action = "delete"
                        selected_res = cur
                        break
                    else:
                        confirm_delete = False
                    continue

                if key == 27:
                    selected_res = None
                    break

                if key == curses.KEY_UP and cur > 0:
                    cur -= 1
                elif key == curses.KEY_DOWN and cur < total_items - 1:
                    cur += 1
                # 數字鍵 (1~9) 或空白鍵：勾選網址。
                elif ord('1') <= key <= ord('9'):
                    target = key - ord('1')
                    if target < len(urls):
                        cur = target
                        if target in marked_set:
                            marked_set.remove(target)
                        else:
                            marked_set.add(target)
                elif key == ord(' '):
                    if cur < len(urls):
                        if cur in marked_set:
                            marked_set.remove(cur)
                        else:
                            marked_set.add(cur)
                elif key in (ord('a'), ord('A')):
                    selected_res = "ALL"
                    action = "select"
                    break
                # Delete 鍵 (所有刪除操作均進入防呆確認)
                elif key in (curses.KEY_DC, ord('d'), ord('D'), 330, 127):
                    if cur < len(urls):
                        confirm_delete = True
                elif key in (10, 13, curses.KEY_ENTER):
                    if cur == len(urls):
                        selected_res = "ALL"
                    elif marked_set:
                        selected_res = [urls[i] for i in sorted(marked_set)]
                    else:
                        selected_res = urls[cur]
                    action = "select"
                    break
                elif key in (ord('q'), ord('Q')):
                    selected_res = None
                    break

        curses.wrapper(_curses_url_menu)
        if selected_res is None:
            note("INFO", "已取消選擇")
            return None

        if action == "delete":
            del_idx = selected_res
            deleted_url = urls.pop(del_idx)
            save_urls(urls)
            status_line("刪除網址", "DONE")
            note("INFO", f"已從 urls.txt 移除網址：{deleted_url}")
            return None

        return selected_res
    except Exception as e:
        note("WARN", f"curses 選單失敗 ({e})，改用數字選單")
        print(f"\n{CYAN}已儲存的課程網址清單：{RESET}")
        for i, u in enumerate(urls, 1):
            print(f"  {YELLOW}{i:2d}.{RESET} {u}")
        print(f"  {GREEN} A.{RESET} {BOLD}同時開啟全部 (多分頁並行模式){RESET}")
        try:
            choice = input("\n請選擇編號 (1~N / A 全部 / 直接 Enter 取消): ").strip()
            if not choice:
                return None
            if choice.upper() == "A":
                return "ALL"
            idx = int(choice) - 1
            if 0 <= idx < len(urls):
                return urls[idx]
        except (ValueError, EOFError, KeyboardInterrupt):
            pass
        note("INFO", "已取消選擇")
        return None


def cmd_url(args: list[str]):
    """用使用者已登入的 Edge/Chrome 開啟指定 URL。"""
    choose_browser = "-c" in args or "--choose" in args
    args = [arg for arg in args if arg not in ("-c", "--choose")]
    if choose_browser:
        cmd_choose([])

    if args:
        note("WARN", "現在只需要執行 cool -u，不需要附加參數")
        return
    saved_urls = load_urls()
    if not saved_urls:
        note("ERR", "尚未儲存課程網址，請先在 urls.txt 放入網址")
        return
    try:
        raw_count = input(f"要開啟幾個頁面？（1-{len(saved_urls)}，預設 {len(saved_urls)}）：").strip()
        count = len(saved_urls) if not raw_count else int(raw_count)
        raw_delay = input("每個頁面開啟間隔幾秒？（預設 2）：").strip()
        delay = 2.0 if not raw_delay else float(raw_delay)
    except (ValueError, EOFError, KeyboardInterrupt):
        print()
        note("INFO", "輸入無效或已取消")
        return
    if not 1 <= count <= len(saved_urls):
        note("ERR", f"頁面數量必須介於 1 和 {len(saved_urls)} 之間")
        return
    if not math.isfinite(delay) or delay < 0:
        note("ERR", "延遲秒數必須是有限且不小於 0 的數字")
        return
    urls_queue = saved_urls[:count]
    layout = "snap"
    gap = 0
    found = find_user_browser()
    if found is None:
        status_line("檢查使用者瀏覽器", "FAILED")
        note("ERR", "找不到已安裝的 Microsoft Edge 或 Google Chrome")
        return
    channel, executable = found
    existing_handles = set(_browser_windows())
    target_desktop = current_virtual_desktop_id()
    if target_desktop is None:
        note(
            "WARN",
            "目前 Windows 未提供可用的虛擬桌面 COM 元件；"
            "將繼續開啟，但無法強制指定虛擬桌面",
        )
    existing_windows = len(existing_handles)
    note("INFO", f"目前偵測到 {existing_windows} 個 Edge/Chrome 視窗")
    status_line(f"開啟使用者瀏覽器 ({channel})", "WORK")
    try:
        new_handles = []
        for index, current_url in enumerate(urls_queue, 1):
            before_launch = set(_browser_windows())
            subprocess.Popen(
                [str(executable), "--new-window", current_url],
                stdin=subprocess.DEVNULL,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            status_line(f"分頁 [{index}] 已交給 {channel}", "OK")
            deadline = time.monotonic() + 5.0
            current_handle = None
            while time.monotonic() < deadline:
                candidates = [
                    handle for handle in _browser_windows()
                    if handle not in existing_handles
                    and handle not in new_handles
                    and handle not in before_launch
                ]
                if candidates:
                    current_handle = candidates[-1]
                    break
                time.sleep(0.1)
            if current_handle is not None:
                if target_desktop is not None:
                    if move_window_to_virtual_desktop(current_handle, target_desktop):
                        time.sleep(0.1)
                    else:
                        note("WARN", f"第 {index} 個視窗無法移到執行時的虛擬桌面")
                new_handles.append(current_handle)
                window_id = register_window(current_handle, current_url)
                arranged = arrange_windows(new_handles, layout=layout, gap=gap)
                note(
                    "INFO",
                    f"新增第 {index} 個視窗，已重新排列 "
                    f"{arranged}/{len(new_handles)} 個新視窗；ID：{window_id}",
                )
            else:
                note("WARN", f"第 {index} 個新視窗尚未被 Windows 列舉到")
            if delay and index < len(urls_queue):
                time.sleep(delay)
        status_line(f"開啟使用者瀏覽器 ({channel})", "DONE")
        note("INFO", f"已交給你目前的 {channel} profile 開啟 {len(urls_queue)} 個網址")
        note("INFO", f"每個網址間隔 {delay:g} 秒")
        note("INFO", "固定使用 Snap 版面")
        note("INFO", "CLI 不會關閉分頁；請直接在瀏覽器中管理它們")
        note("INFO", "只排列本次新增視窗，原有視窗未移動")
    except Exception as e:
        status_line(f"開啟使用者瀏覽器 ({channel})", "FAILED")
        note("ERR", f"無法開啟使用者瀏覽器：{e}")

__all__ = [name for name in globals() if not name.startswith("__")]
