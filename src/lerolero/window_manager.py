"""Window management — delegates to platform-specific implementation."""

from __future__ import annotations

from typing import Any

from lerolero.platform import WindowInfo, get_platform


class WindowManager:
    """Cross-platform window manager. Delegates to platform layer."""

    def __init__(self) -> None:
        self._platform = get_platform()

    def get_active_window(self) -> WindowInfo | None:
        """Get the currently active window."""
        return self._platform.get_active_window()

    def focus_window(self, window: WindowInfo | Any) -> bool:
        """Bring the specified window to foreground."""
        handle = window.handle if isinstance(window, WindowInfo) else window
        return self._platform.focus_window(handle)

    def hide_window(self, window: WindowInfo | Any) -> bool:
        """Hide the specified window."""
        handle = window.handle if isinstance(window, WindowInfo) else window
        return self._platform.hide_window(handle)

    def show_window(self, window: WindowInfo | Any) -> bool:
        """Show the specified window."""
        handle = window.handle if isinstance(window, WindowInfo) else window
        return self._platform.show_window(handle)

    @staticmethod
    def get_process_name(window: WindowInfo | Any) -> str | None:
        """Get the normalized process name."""
        if isinstance(window, WindowInfo):
            return window.process_name
        platform = get_platform()
        return platform.get_process_name(window) or None
