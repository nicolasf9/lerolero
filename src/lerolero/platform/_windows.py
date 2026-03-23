"""Windows platform implementation — Win32 API calls."""

from __future__ import annotations

import ctypes
import logging
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

from lerolero.platform._base import WindowInfo

logger = logging.getLogger(__name__)

# Windows constants
SW_RESTORE = 9
SW_HIDE = 0
SW_SHOW = 5


class WindowsPlatform:
    """Windows implementation using Win32 API + pygetwindow."""

    def __init__(self) -> None:
        self.user32 = ctypes.windll.user32
        try:
            import pygetwindow as gw
            self._gw = gw
        except ImportError:
            self._gw = None
            logger.warning("pygetwindow not available")

    def get_active_window(self) -> WindowInfo | None:
        if not self._gw:
            return None
        try:
            window = self._gw.getActiveWindow()
            if window:
                proc = self._get_process_name_from_hwnd(window._hWnd) or ""
                return WindowInfo(
                    handle=window,
                    title=window.title or "",
                    process_name=_normalize_process(proc),
                )
        except Exception:
            pass
        return None

    def focus_window(self, handle: Any) -> bool:
        window = handle
        if not window or not hasattr(window, "_hWnd"):
            return False
        hwnd = window._hWnd
        try:
            if window.isMinimized:
                self.user32.ShowWindow(hwnd, SW_RESTORE)
            self.user32.SetForegroundWindow(hwnd)
            self.user32.SetActiveWindow(hwnd)
            return True
        except Exception:
            return False

    def hide_window(self, handle: Any) -> bool:
        window = handle
        if not window or not hasattr(window, "_hWnd"):
            return False
        try:
            self.user32.ShowWindow(window._hWnd, SW_HIDE)
            return True
        except Exception:
            return False

    def show_window(self, handle: Any) -> bool:
        window = handle
        if not window or not hasattr(window, "_hWnd"):
            return False
        try:
            self.user32.ShowWindow(window._hWnd, SW_SHOW)
            self.focus_window(window)
            return True
        except Exception:
            return False

    def get_process_name(self, handle: Any) -> str:
        window = handle
        if not window or not hasattr(window, "_hWnd"):
            return ""
        name = self._get_process_name_from_hwnd(window._hWnd) or ""
        return _normalize_process(name)

    def _get_process_name_from_hwnd(self, hwnd: int) -> str | None:
        try:
            pid = ctypes.c_ulong()
            ctypes.windll.user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
            handle = ctypes.windll.kernel32.OpenProcess(0x0400 | 0x0010, False, pid.value)
            if handle:
                try:
                    buf = ctypes.create_unicode_buffer(260)
                    size = ctypes.c_ulong(260)
                    if ctypes.windll.kernel32.QueryFullProcessImageNameW(handle, 0, buf, ctypes.byref(size)):
                        return os.path.basename(buf.value)
                finally:
                    ctypes.windll.kernel32.CloseHandle(handle)
        except Exception:
            pass
        return None

    def play_beep(self, frequency: int = 440, duration_ms: int = 200) -> None:
        try:
            import winsound
            winsound.Beep(frequency, duration_ms)
        except Exception:
            pass

    def update_startup_shortcut(self, enable: bool, app_path: Path | None = None) -> None:
        try:
            appdata = os.environ["APPDATA"]
            startup_dir = Path(appdata) / "Microsoft" / "Windows" / "Start Menu" / "Programs" / "Startup"
            shortcut_path = startup_dir / "LeroLero.lnk"

            if not enable:
                shortcut_path.unlink(missing_ok=True)
                return

            target = app_path or Path(sys.executable)
            sys_root = os.environ.get("SystemRoot", r"C:\WINDOWS")
            ps = Path(sys_root) / "System32" / "WindowsPowerShell" / "v1.0" / "powershell.exe"

            script = (
                f'$s=(New-Object -COM WScript.Shell).CreateShortcut("{shortcut_path}");'
                f'$s.TargetPath="{target}";'
                f'$s.WorkingDirectory="{target.parent}";'
                f"$s.Save()"
            )
            subprocess.run(
                [str(ps), "-Command", script],
                capture_output=True, timeout=10,
                creationflags=subprocess.CREATE_NO_WINDOW,
            )
        except Exception as e:
            logger.error("Failed to update startup shortcut: %s", e)

    def detect_gpu(self) -> str:
        try:
            result = subprocess.run(
                ["wmic", "path", "win32_videocontroller", "get", "name"],
                capture_output=True, text=True, timeout=10,
                creationflags=subprocess.CREATE_NO_WINDOW,
            )
            output = result.stdout.lower()
            if "nvidia" in output and any(x in output for x in ("geforce", "rtx", "gtx", "quadro")):
                return "cuda"
            if "intel" in output and any(x in output for x in ("arc", "iris", "uhd")):
                return "openvino"
            if "amd" in output and any(x in output for x in ("radeon", "rx ")):
                return "directml"
        except Exception:
            pass
        return "cpu"

    def show_error_dialog(self, title: str, message: str) -> None:
        try:
            ctypes.windll.user32.MessageBoxW(0, message, title, 0x10)
        except Exception:
            print(f"\nERROR: {title}\n{message}")
            input("Pressione Enter para fechar...")

    def get_paste_modifier(self) -> str:
        return "ctrl"

    def set_app_icon(self) -> None:
        try:
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("com.lerolero.app")
        except Exception:
            pass


def _normalize_process(name: str) -> str:
    """Normalize process name: remove .exe, lowercase."""
    if name.lower().endswith(".exe"):
        name = name[:-4]
    return name.lower()
