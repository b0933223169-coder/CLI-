"""Project and persistent-data paths."""
from __future__ import annotations
from ._compat import *

BASE_URL = "https://www.coolenglish.edu.tw"
LOGIN_URL = f"{BASE_URL}/login/index.php"
DEFAULT_TARGET = f"{BASE_URL}/time/time_view_detail_by_people.php?id=2055519"

PACKAGE_DIR = Path(__file__).resolve().parent
PROJECT_DIR = (
    PACKAGE_DIR.parent
    if (PACKAGE_DIR / "cool_app").is_dir() and not (PACKAGE_DIR / "cli.py").is_file()
    else PACKAGE_DIR
)

def _base_dir() -> Path:
    try:
        base = PROJECT_DIR
        test = base / ".cool_write_test"
        try:
            test.touch(exist_ok=True)
            test.unlink(missing_ok=True)
            return base
        except Exception:
            pass
    except Exception:
        pass
    fallback = Path.home() / ".config" / "cool"
    fallback.mkdir(parents=True, exist_ok=True)
    return fallback

_BASE = _base_dir()
COLORS_FILE = _BASE / "colors.json"
URLS_FILE = _BASE / "urls.txt"
WINDOWS_FILE = _BASE / "windows.json"
BROWSER_FILE = _BASE / "browser.json"

def _browser_path_candidates() -> list[tuple[str, Path]]:
    """Collect browser executables from PATH, standard folders, and registry."""
    roots = {
        key: Path(value)
        for key, value in os.environ.items()
        if key in {"PROGRAMFILES", "PROGRAMFILES(X86)", "LOCALAPPDATA"}
        and value
    }
    candidates = [
        ("msedge", roots["PROGRAMFILES(X86)"] / "Microsoft/Edge/Application/msedge.exe")
        if "PROGRAMFILES(X86)" in roots else None,
        ("msedge", roots["PROGRAMFILES"] / "Microsoft/Edge/Application/msedge.exe")
        if "PROGRAMFILES" in roots else None,
        ("msedge", roots["LOCALAPPDATA"] / "Microsoft/Edge/Application/msedge.exe")
        if "LOCALAPPDATA" in roots else None,
        ("chrome", roots["PROGRAMFILES(X86)"] / "Google/Chrome/Application/chrome.exe")
        if "PROGRAMFILES(X86)" in roots else None,
        ("chrome", roots["PROGRAMFILES"] / "Google/Chrome/Application/chrome.exe")
        if "PROGRAMFILES" in roots else None,
        ("chrome", roots["LOCALAPPDATA"] / "Google/Chrome/Application/chrome.exe")
        if "LOCALAPPDATA" in roots else None,
    ]
    result = [item for item in candidates if item is not None]
    for channel, command in (("msedge", "msedge.exe"), ("chrome", "chrome.exe")):
        found = shutil.which(command)
        if found:
            result.append((channel, Path(found)))

    if os.name == "nt":
        try:
            import winreg
            registry_locations = (
                (winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\App Paths\msedge.exe", "msedge"),
                (winreg.HKEY_LOCAL_MACHINE, r"Software\Microsoft\Windows\CurrentVersion\App Paths\msedge.exe", "msedge"),
                (winreg.HKEY_LOCAL_MACHINE, r"Software\WOW6432Node\Microsoft\Windows\CurrentVersion\App Paths\msedge.exe", "msedge"),
                (winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\App Paths\chrome.exe", "chrome"),
                (winreg.HKEY_LOCAL_MACHINE, r"Software\Microsoft\Windows\CurrentVersion\App Paths\chrome.exe", "chrome"),
                (winreg.HKEY_LOCAL_MACHINE, r"Software\WOW6432Node\Microsoft\Windows\CurrentVersion\App Paths\chrome.exe", "chrome"),
            )
            for hive, key, channel in registry_locations:
                try:
                    with winreg.OpenKey(hive, key) as handle:
                        value, _ = winreg.QueryValueEx(handle, None)
                    executable = Path(str(value).strip('"'))
                    result.append((channel, executable))
                except (FileNotFoundError, OSError, TypeError, ValueError):
                    continue
        except ImportError:
            pass
    return result


def find_user_browser() -> tuple[str, Path] | None:
    """Find a real installed Microsoft Edge or Google Chrome executable."""
    preferred = os.environ.get("COOL_BROWSER", "").strip().lower()
    if not preferred and BROWSER_FILE.exists():
        try:
            preferred = json.loads(BROWSER_FILE.read_text(encoding="utf-8")).get("channel", "")
        except (OSError, ValueError, TypeError, AttributeError):
            preferred = ""
    candidates = _browser_path_candidates()
    if preferred in {"edge", "msedge"}:
        candidates = [item for item in candidates if item[0] == "msedge"]
    elif preferred in {"chrome", "google-chrome"}:
        candidates = [item for item in candidates if item[0] == "chrome"]

    seen = set()
    for channel, executable in candidates:
        resolved = str(executable.resolve()) if executable.exists() else str(executable)
        if resolved in seen:
            continue
        seen.add(resolved)
        if executable.is_file() and os.access(executable, os.X_OK):
            return channel, executable
    return None


def installed_browsers() -> list[tuple[str, Path]]:
    """Return unique installed supported browsers."""
    result = []
    seen = set()
    for channel, executable in _browser_path_candidates():
        if not executable.is_file() or not os.access(executable, os.X_OK):
            continue
        key = str(executable.resolve()).lower()
        if key not in seen:
            seen.add(key)
            result.append((channel, executable))
    return result


def save_browser_choice(channel: str):
    _atomic_write(
        BROWSER_FILE,
        json.dumps({"channel": channel}, ensure_ascii=False, indent=2) + "\n",
    )


for _old, _new in [
    (PROJECT_DIR / "colors.json", COLORS_FILE),
]:
    try:
        if _old.exists() and not _new.exists():
            _new.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(_old, _new)
            try:
                _new.chmod(0o600)
            except Exception:
                pass
    except Exception:
        pass

def _atomic_write(path: Path, data: str, mode: int = 0o600):
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=str(path.parent), prefix="." + path.name + ".tmp.")
    try:
        with open(fd, "w", encoding="utf-8") as f:
            f.write(data)
        Path(tmp).chmod(mode)
        Path(tmp).replace(path)
        try:
            path.chmod(mode)
        except Exception:
            pass
    finally:
        try:
            if Path(tmp).exists():
                Path(tmp).unlink()
        except Exception:
            pass

def _sanitize_filename(name: str, max_len: int = 80) -> str:
    name = name.strip()
    h = hashlib.sha256(name.encode("utf-8")).hexdigest()[:8]
    safe = re.sub(r"[^a-zA-Z0-9._-]", "_", name)
    safe = re.sub(r"_+", "_", safe).strip("._-") or "default"
    if len(safe) > max_len:
        safe = safe[: max_len - 9] + "_" + h
    if safe in ("", ".", ".."):
        safe = f"default_{h}"
    if safe.startswith("-"):
        safe = "_" + safe
    return safe

__all__ = [name for name in globals() if not name.startswith("__")]
