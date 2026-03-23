"""Abstract platform interface — all OS-specific code goes through this."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol, runtime_checkable


@dataclass
class WindowInfo:
    """Platform-agnostic window information."""
    handle: Any  # HWND on Windows, window ID on Linux, dict on macOS
    title: str
    process_name: str  # e.g. "code" (normalized, no .exe)


@runtime_checkable
class PlatformBase(Protocol):
    """Protocol that every platform implementation must fulfill."""

    def get_active_window(self) -> WindowInfo | None:
        """Return info about the currently focused window."""
        ...

    def focus_window(self, handle: Any) -> bool:
        """Bring a window to foreground. Returns True on success."""
        ...

    def hide_window(self, handle: Any) -> bool:
        """Hide a window. Returns True on success."""
        ...

    def show_window(self, handle: Any) -> bool:
        """Show a previously hidden window. Returns True on success."""
        ...

    def get_process_name(self, handle: Any) -> str:
        """Get the normalized process name (no .exe, lowercase)."""
        ...

    def play_beep(self, frequency: int = 440, duration_ms: int = 200) -> None:
        """Play a short audio beep for user feedback."""
        ...

    def update_startup_shortcut(self, enable: bool, app_path: Path | None = None) -> None:
        """Enable/disable auto-start with the OS."""
        ...

    def detect_gpu(self) -> str:
        """Detect GPU type. Returns 'openvino', 'cuda', 'directml', or 'cpu'."""
        ...

    def show_error_dialog(self, title: str, message: str) -> None:
        """Show a native error dialog."""
        ...

    def get_paste_modifier(self) -> str:
        """Return 'cmd' for macOS, 'ctrl' for others."""
        ...

    def set_app_icon(self) -> None:
        """Set the application icon in taskbar/dock."""
        ...
