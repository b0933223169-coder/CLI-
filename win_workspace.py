"""Small native Windows workspace manager for browser windows."""
from __future__ import annotations

import ctypes
import math
import os
import time
from ctypes import wintypes
from pathlib import Path


if os.name == "nt":
    user32 = ctypes.windll.user32
    kernel32 = ctypes.windll.kernel32
    PROCESS_QUERY_LIMITED_INFORMATION = 0x1000
    SWP_NOACTIVATE = 0x0010
    SWP_SHOWWINDOW = 0x0040

    class RECT(ctypes.Structure):
        _fields_ = [
            ("left", ctypes.c_long),
            ("top", ctypes.c_long),
            ("right", ctypes.c_long),
            ("bottom", ctypes.c_long),
        ]

    WNDENUMPROC = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)

    class GUID(ctypes.Structure):
        _fields_ = [
            ("Data1", ctypes.c_ulong),
            ("Data2", ctypes.c_ushort),
            ("Data3", ctypes.c_ushort),
            ("Data4", ctypes.c_ubyte * 8),
        ]

    CLSID_VIRTUAL_DESKTOP_MANAGER = GUID(
        0xAA509086, 0x5CA4, 0x4C25,
        (ctypes.c_ubyte * 8)(0x8F, 0x95, 0x58, 0x9D, 0x3C, 0x07, 0xB4, 0x8A),
    )
    IID_VIRTUAL_DESKTOP_MANAGER = GUID(
        0xA5CD92FF, 0x29BE, 0x454C,
        (ctypes.c_ubyte * 8)(0x8D, 0x04, 0xD8, 0x28, 0x79, 0xFB, 0x3F, 0x1B),
    )

    ole32 = ctypes.windll.ole32
    COINIT_APARTMENTTHREADED = 0x2
    ole32.CoInitializeEx.argtypes = [ctypes.c_void_p, wintypes.DWORD]
    ole32.CoInitializeEx.restype = ctypes.HRESULT
    ole32.CoCreateInstance.argtypes = [
        ctypes.POINTER(GUID), ctypes.c_void_p, wintypes.DWORD,
        ctypes.POINTER(GUID), ctypes.POINTER(ctypes.c_void_p),
    ]
    ole32.CoCreateInstance.restype = ctypes.HRESULT


def _browser_executables() -> set[str]:
    return {"msedge.exe", "chrome.exe"}


def _process_name(pid: int) -> str:
    if os.name != "nt":
        return ""
    handle = kernel32.OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION, False, pid)
    if not handle:
        return ""
    try:
        size = wintypes.DWORD(32768)
        buffer = ctypes.create_unicode_buffer(size.value)
        if not kernel32.QueryFullProcessImageNameW(handle, 0, buffer, ctypes.byref(size)):
            return ""
        return Path(buffer.value).name.lower()
    finally:
        kernel32.CloseHandle(handle)


def _browser_windows() -> list[wintypes.HWND]:
    if os.name != "nt":
        return []
    handles: list[wintypes.HWND] = []

    @WNDENUMPROC
    def callback(hwnd, _):
        if not user32.IsWindowVisible(hwnd) or user32.GetWindow(hwnd, 4):
            return True
        pid = wintypes.DWORD()
        user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
        if _process_name(pid.value) in _browser_executables():
            handles.append(hwnd)
        return True

    user32.EnumWindows(callback, 0)
    return handles


def _desktop_manager():
    if os.name != "nt":
        return None
    pointer = ctypes.c_void_p()
    init_result = ole32.CoInitializeEx(None, COINIT_APARTMENTTHREADED)
    if init_result not in (0, 1, 0x80010106):
        return None
    for context in (1, 4):
        pointer = ctypes.c_void_p()
        try:
            result = ole32.CoCreateInstance(
                ctypes.byref(CLSID_VIRTUAL_DESKTOP_MANAGER),
                None,
                context,
                ctypes.byref(IID_VIRTUAL_DESKTOP_MANAGER),
                ctypes.byref(pointer),
            )
        except OSError:
            continue
        if result >= 0 and pointer.value:
            return pointer
    return None


def _context_window():
    """Return the window belonging to the CLI's current desktop context."""
    console = kernel32.GetConsoleWindow()
    if console and user32.IsWindow(console):
        return console
    return user32.GetForegroundWindow()


def current_virtual_desktop_id():
    """Return the desktop GUID for the CLI context, when Windows exposes it."""
    if os.name != "nt":
        return None
    try:
        hwnd = _context_window()
        manager = _desktop_manager()
        if not hwnd or manager is None:
            return None
        desktop_id = GUID()
        vtable = ctypes.cast(
            ctypes.cast(manager, ctypes.POINTER(ctypes.c_void_p)).contents,
            ctypes.POINTER(ctypes.c_void_p),
        )
        get_id = ctypes.WINFUNCTYPE(
            ctypes.HRESULT, ctypes.c_void_p, wintypes.HWND, ctypes.POINTER(GUID)
        )(vtable[4])
        if get_id(manager, hwnd, ctypes.byref(desktop_id)) < 0:
            return None
        return desktop_id
    except (AttributeError, OSError, TypeError, ValueError):
        return None


def move_window_to_virtual_desktop(hwnd, desktop_id) -> bool:
    """Move one window to a captured desktop using IVirtualDesktopManager."""
    if os.name != "nt" or not hwnd or desktop_id is None:
        return False
    try:
        manager = _desktop_manager()
        if manager is None:
            return False
        vtable = ctypes.cast(
            ctypes.cast(manager, ctypes.POINTER(ctypes.c_void_p)).contents,
            ctypes.POINTER(ctypes.c_void_p),
        )
        move = ctypes.WINFUNCTYPE(
            ctypes.HRESULT, ctypes.c_void_p, wintypes.HWND, ctypes.POINTER(GUID)
        )(vtable[5])
        return move(manager, hwnd, ctypes.byref(desktop_id)) >= 0
    except (AttributeError, OSError, TypeError, ValueError):
        return False


def browser_window_count() -> int:
    """Return the number of visible top-level Edge/Chrome windows."""
    return len(_browser_windows()) if os.name == "nt" else 0


def _work_area() -> tuple[int, int, int, int]:
    rect = RECT()
    SPI_GETWORKAREA = 0x0030
    if not user32.SystemParametersInfoW(SPI_GETWORKAREA, 0, ctypes.byref(rect), 0):
        return 0, 0, user32.GetSystemMetrics(0), user32.GetSystemMetrics(1)
    return rect.left, rect.top, rect.right, rect.bottom


def _snap_rectangles(
    count: int,
    width: int,
    height: int,
    *,
    layout: str = "snap",
) -> list[tuple[int, int, int, int]]:
    """Return FancyZones-style zone rectangles for the supplied window count."""
    if count <= 0:
        return []
    if layout == "columns":
        return [
            (index * width // count, 0, (index + 1) * width // count - index * width // count, height)
            for index in range(count)
        ]
    if layout == "rows":
        return [
            (0, index * height // count, width, (index + 1) * height // count - index * height // count)
            for index in range(count)
        ]
    if layout == "grid":
        columns = math.ceil(math.sqrt(count))
        rows = math.ceil(count / columns)
        return [
            (
                column * width // columns,
                row * height // rows,
                (column + 1) * width // columns - column * width // columns,
                (row + 1) * height // rows - row * height // rows,
            )
            for index in range(count)
            for row, column in [divmod(index, columns)]
        ]
    if count == 1:
        return [(0, 0, width, height)]
    if count == 2:
        split = width // 2
        return [(0, 0, split, height), (split, 0, width - split, height)]
    if count == 3:
        split = width * 2 // 3
        half = height // 2
        return [
            (0, 0, split, height),
            (split, 0, width - split, half),
            (split, half, width - split, height - half),
        ]
    if count == 4:
        split_x = width // 2
        split_y = height // 2
        return [
            (0, 0, split_x, split_y),
            (split_x, 0, width - split_x, split_y),
            (0, split_y, split_x, height - split_y),
            (split_x, split_y, width - split_x, height - split_y),
        ]

    columns = math.ceil(math.sqrt(count))
    rows = math.ceil(count / columns)
    rectangles = []
    for index in range(count):
        row, column = divmod(index, columns)
        x1 = column * width // columns
        x2 = (column + 1) * width // columns
        y1 = row * height // rows
        y2 = (row + 1) * height // rows
        rectangles.append((x1, y1, x2 - x1, y2 - y1))
    return rectangles


def arrange_windows(
    handles: list[wintypes.HWND],
    *,
    topmost: bool = False,
    layout: str = "snap",
    gap: int = 0,
) -> int:
    """Arrange only supplied browser windows into independent FancyZones zones."""
    if os.name != "nt" or not handles:
        return 0
    handles = [hwnd for hwnd in handles if user32.IsWindow(hwnd)]
    if not handles:
        return 0

    left, top, right, bottom = _work_area()
    width = max(1, right - left)
    height = max(1, bottom - top)
    layout = layout.lower()
    if layout not in {"snap", "grid", "rows", "columns"}:
        layout = "snap"
    gap = max(0, min(int(gap), min(width, height) // 4))
    rectangles = _snap_rectangles(
        len(handles),
        width - gap * 2,
        height - gap * 2,
        layout=layout,
    )
    for hwnd, (offset_x, offset_y, w, h) in zip(handles, rectangles):
        x = left + gap + offset_x + (gap if offset_x else 0)
        y = top + gap + offset_y + (gap if offset_y else 0)
        w = max(1, w - (gap if offset_x + w < width - gap else 0) - (gap if offset_x else 0))
        h = max(1, h - (gap if offset_y + h < height - gap else 0) - (gap if offset_y else 0))
        # Snap Layouts changes geometry; it does not make every window
        # permanently topmost or manufacture simultaneous foreground focus.
        insert_after = wintypes.HWND(0)
        user32.SetWindowPos(
            hwnd,
            insert_after,
            x,
            y,
            max(1, w),
            max(1, h),
            SWP_NOACTIVATE | SWP_SHOWWINDOW,
        )
    return len(handles)


def arrange_browser_workspace(
    expected: int,
    *,
    wait_seconds: float = 1.5,
    topmost: bool = False,
    layout: str = "snap",
    gap: int = 0,
) -> int:
    """Compatibility helper that arranges the first visible browser windows.

    Returns the number of windows arranged. This is intentionally a local
    window operation; it does not inspect browser storage or network traffic.
    """
    if os.name != "nt" or expected <= 0:
        return 0
    deadline = time.monotonic() + max(0.0, wait_seconds)
    handles: list[wintypes.HWND] = []
    while time.monotonic() < deadline:
        handles = _browser_windows()
        if len(handles) >= expected:
            break
        time.sleep(0.1)
    handles = handles[:expected]
    if not handles:
        return 0

    return arrange_windows(handles, topmost=topmost, layout=layout, gap=gap)


__all__ = [
    "arrange_browser_workspace",
    "arrange_windows",
    "browser_window_count",
    "current_virtual_desktop_id",
    "move_window_to_virtual_desktop",
]
