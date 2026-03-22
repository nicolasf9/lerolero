"""Window management utilities for whisper-typing."""

import ctypes
import os

import pygetwindow as gw

# Windows constants
SW_RESTORE = 9
SW_HIDE = 0
SW_SHOW = 5


class WindowManager:
    """Manages window focus and retrieval operations."""

    def __init__(self) -> None:
        """Initialize the WindowManager."""
        self.user32 = ctypes.windll.user32

    def get_active_window(self) -> gw.Window | None:
        """Get the currently active window object."""
        try:
            # Returns the active window object
            window = gw.getActiveWindow()
            if window:
                return window
        except Exception:  # noqa: BLE001, S110
            pass
        return None

    def focus_window(self, window: gw.Window) -> bool:
        """Bring the specified window object to the foreground using Windows API."""
        if not window or not hasattr(window, "_hWnd"):
            return False

        hwnd = window._hWnd  # noqa: SLF001
        try:
            # 1. If minimized, restore it
            if window.isMinimized:
                self.user32.ShowWindow(hwnd, SW_RESTORE)

            # 2. Try to set as foreground window
            # We use the native SetForegroundWindow which is more robust
            self.user32.SetForegroundWindow(hwnd)

            # 3. Double check and force if needed (some apps are stubborn)
            self.user32.SetActiveWindow(hwnd)
        except Exception:  # noqa: BLE001
            return False
        else:
            return True

    def hide_window(self, window: gw.Window) -> bool:
        """Hide the specified window from the taskbar and screen."""
        if not window or not hasattr(window, "_hWnd"):
            return False
        try:
            hwnd = window._hWnd  # noqa: SLF001
            self.user32.ShowWindow(hwnd, SW_HIDE)
        except Exception:  # noqa: BLE001
            return False
        return True

    def show_window(self, window: gw.Window) -> bool:
        """Show the specified window and restore it."""
        if not window or not hasattr(window, "_hWnd"):
            return False
        try:
            hwnd = window._hWnd  # noqa: SLF001
            self.user32.ShowWindow(hwnd, SW_SHOW)
            self.focus_window(window)
        except Exception:  # noqa: BLE001
            return False
        return True

    @staticmethod
    def get_process_name(window: gw.Window) -> str | None:
        """Get the executable name of the process owning a window."""
        if not window or not hasattr(window, "_hWnd"):
            return None
        try:
            hwnd = window._hWnd  # noqa: SLF001
            pid = ctypes.c_ulong()
            ctypes.windll.user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
            PROCESS_QUERY_INFORMATION = 0x0400  # noqa: N806
            PROCESS_VM_READ = 0x0010  # noqa: N806
            handle = ctypes.windll.kernel32.OpenProcess(
                PROCESS_QUERY_INFORMATION | PROCESS_VM_READ, False, pid.value,  # noqa: FBT003
            )
            if handle:
                try:
                    buf = ctypes.create_unicode_buffer(260)
                    size = ctypes.c_ulong(260)
                    if ctypes.windll.kernel32.QueryFullProcessImageNameW(handle, 0, buf, ctypes.byref(size)):
                        return os.path.basename(buf.value)
                finally:
                    ctypes.windll.kernel32.CloseHandle(handle)
        except Exception:  # noqa: BLE001
            pass
        return None
