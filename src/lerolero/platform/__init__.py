"""Platform abstraction — auto-selects the right implementation for the current OS."""

from __future__ import annotations

import sys

from lerolero.platform._base import PlatformBase, WindowInfo

if sys.platform == "win32":
    from lerolero.platform._windows import WindowsPlatform as _PlatformImpl
elif sys.platform == "darwin":
    from lerolero.platform._macos import MacOSPlatform as _PlatformImpl
else:
    from lerolero.platform._linux import LinuxPlatform as _PlatformImpl

# Singleton instance
_platform: PlatformBase | None = None


def get_platform() -> PlatformBase:
    """Get the platform-specific implementation (singleton)."""
    global _platform
    if _platform is None:
        _platform = _PlatformImpl()
    return _platform


__all__ = ["PlatformBase", "WindowInfo", "get_platform"]
