"""PyInstaller runtime hook — configure pythonnet before any import.

This runs at the very start of a frozen exe, before user code.
It tells pythonnet where to find the Python DLL and forces .NET Framework
(always present on Windows 10/11) so we don't need to bundle .NET Core.
"""

import os
import sys

if sys.platform == "win32":
    # 1. Tell pythonnet which Python DLL to use.
    #    In onedir builds, python3XX.dll lives in _internal/ (sys._MEIPASS).
    _meipass = getattr(sys, "_MEIPASS", None)
    if _meipass:
        _ver = f"python{sys.version_info.major}{sys.version_info.minor}.dll"
        for _candidate in (
            os.path.join(_meipass, _ver),                          # _internal/
            os.path.join(os.path.dirname(sys.executable), _ver),   # exe dir
        ):
            if os.path.exists(_candidate):
                os.environ["PYTHONNET_PYDLL"] = _candidate
                break

    # 2. Force .NET Framework runtime (netfx) — always available on Windows 10/11.
    #    This avoids needing to bundle or locate .NET Core / .NET 5+.
    os.environ.setdefault("PYTHONNET_RUNTIME", "netfx")
