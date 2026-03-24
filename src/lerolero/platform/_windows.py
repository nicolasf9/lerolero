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
                logger.info("Startup shortcut removed")
                return

            # Determine what to launch
            if getattr(sys, "frozen", False):
                # Running as .exe — point shortcut at the exe
                target = Path(sys.executable)
                work_dir = target.parent
                args = ""
            else:
                # Running via Python — create a .bat wrapper or use pythonw
                # Find the project's run.bat
                project_root = Path(__file__).resolve().parent.parent.parent.parent
                # Use run_silent.bat (no pause, minimized) for startup
                run_bat = project_root / "run_silent.bat"
                if not run_bat.exists():
                    run_bat.write_text(
                        '@echo off\n'
                        f'cd /d "{project_root}"\n'
                        'start /min "" uv run lerolero\n',
                        encoding="utf-8",
                    )
                target = run_bat
                work_dir = project_root
                args = ""

            sys_root = os.environ.get("SystemRoot", r"C:\WINDOWS")
            ps = Path(sys_root) / "System32" / "WindowsPowerShell" / "v1.0" / "powershell.exe"

            # Escape paths for PowerShell
            lnk = str(shortcut_path).replace("'", "''")
            tgt = str(target).replace("'", "''")
            wd = str(work_dir).replace("'", "''")

            script = (
                f"$s=(New-Object -COM WScript.Shell).CreateShortcut('{lnk}');"
                f"$s.TargetPath='{tgt}';"
                f"$s.WorkingDirectory='{wd}';"
                f"$s.WindowStyle=7;"  # Minimized
                f"$s.Save()"
            )
            result = subprocess.run(
                [str(ps), "-Command", script],
                capture_output=True, text=True, timeout=10,
                creationflags=subprocess.CREATE_NO_WINDOW,
            )
            if result.returncode == 0:
                logger.info("Startup shortcut created: %s -> %s", shortcut_path, target)
            else:
                logger.error("PowerShell error: %s", result.stderr)
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
