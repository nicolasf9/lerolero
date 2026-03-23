"""macOS platform implementation — osascript + subprocess."""

from __future__ import annotations

import json
import logging
import os
import plistlib
import subprocess
from pathlib import Path
from typing import Any

from lerolero.platform._base import WindowInfo

logger = logging.getLogger(__name__)


class MacOSPlatform:
    """macOS implementation using osascript (AppleScript) for window management."""

    def get_active_window(self) -> WindowInfo | None:
        try:
            script = '''
            tell application "System Events"
                set fp to first process whose frontmost is true
                set appName to name of fp
                set winTitle to ""
                try
                    set winTitle to name of first window of fp
                end try
                return appName & "|" & winTitle
            end tell
            '''
            result = subprocess.run(
                ["osascript", "-e", script],
                capture_output=True, text=True, timeout=5,
            )
            if result.returncode == 0:
                parts = result.stdout.strip().split("|", 1)
                app_name = parts[0] if parts else ""
                win_title = parts[1] if len(parts) > 1 else ""
                return WindowInfo(
                    handle=app_name,
                    title=win_title,
                    process_name=app_name.lower(),
                )
        except Exception:
            pass
        return None

    def focus_window(self, handle: Any) -> bool:
        app_name = handle
        if not app_name:
            return False
        try:
            script = f'''
            tell application "{app_name}" to activate
            '''
            result = subprocess.run(
                ["osascript", "-e", script],
                capture_output=True, timeout=5,
            )
            return result.returncode == 0
        except Exception:
            return False

    def hide_window(self, handle: Any) -> bool:
        app_name = handle
        if not app_name:
            return False
        try:
            script = f'''
            tell application "System Events"
                set visible of process "{app_name}" to false
            end tell
            '''
            subprocess.run(["osascript", "-e", script], capture_output=True, timeout=5)
            return True
        except Exception:
            return False

    def show_window(self, handle: Any) -> bool:
        return self.focus_window(handle)

    def get_process_name(self, handle: Any) -> str:
        return str(handle).lower() if handle else ""

    def play_beep(self, frequency: int = 440, duration_ms: int = 200) -> None:
        try:
            # Use sounddevice for cross-platform tone
            import numpy as np
            import sounddevice as sd
            t = np.linspace(0, duration_ms / 1000, int(16000 * duration_ms / 1000), endpoint=False)
            tone = (0.3 * np.sin(2 * np.pi * frequency * t)).astype(np.float32)
            sd.play(tone, 16000, blocking=False)
        except Exception:
            try:
                subprocess.run(
                    ["afplay", "/System/Library/Sounds/Tink.aiff"],
                    capture_output=True, timeout=3,
                )
            except Exception:
                pass

    def update_startup_shortcut(self, enable: bool, app_path: Path | None = None) -> None:
        plist_path = Path.home() / "Library" / "LaunchAgents" / "com.lerolero.app.plist"
        try:
            if not enable:
                plist_path.unlink(missing_ok=True)
                return

            target = app_path or Path(__file__).resolve()
            plist_data = {
                "Label": "com.lerolero.app",
                "ProgramArguments": ["python3", "-m", "lerolero"],
                "RunAtLoad": True,
                "KeepAlive": False,
            }
            plist_path.parent.mkdir(parents=True, exist_ok=True)
            with open(plist_path, "wb") as f:
                plistlib.dump(plist_data, f)
        except Exception as e:
            logger.error("Failed to update launch agent: %s", e)

    def detect_gpu(self) -> str:
        # macOS has no GPU acceleration for Whisper (no OpenVINO/CUDA/DirectML)
        return "cpu"

    def show_error_dialog(self, title: str, message: str) -> None:
        try:
            escaped = message.replace('"', '\\"').replace("\n", "\\n")
            script = f'display dialog "{escaped}" with title "{title}" buttons {{"OK"}} default button "OK" with icon caution'
            subprocess.run(["osascript", "-e", script], capture_output=True, timeout=30)
        except Exception:
            print(f"\nERROR: {title}\n{message}")

    def get_paste_modifier(self) -> str:
        return "cmd"

    def set_app_icon(self) -> None:
        # macOS handles app icons via Info.plist in .app bundle
        pass
