"""Linux platform implementation — xdotool + /proc."""

from __future__ import annotations

import logging
import os
import subprocess
from pathlib import Path
from typing import Any

from lerolero.platform._base import WindowInfo

logger = logging.getLogger(__name__)


def _run(cmd: list[str], timeout: int = 5) -> str:
    """Run a command and return stdout, or empty string on failure."""
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        return result.stdout.strip() if result.returncode == 0 else ""
    except Exception:
        return ""


def _has_xdotool() -> bool:
    return bool(_run(["which", "xdotool"]))


def _has_wmctrl() -> bool:
    return bool(_run(["which", "wmctrl"]))


class LinuxPlatform:
    """Linux implementation using xdotool/wmctrl + /proc."""

    def __init__(self) -> None:
        self._use_xdotool = _has_xdotool()
        self._use_wmctrl = _has_wmctrl()
        if not self._use_xdotool:
            logger.warning("xdotool not found. Install with: sudo apt install xdotool")

    def get_active_window(self) -> WindowInfo | None:
        if not self._use_xdotool:
            return None
        try:
            wid = _run(["xdotool", "getactivewindow"])
            if not wid:
                return None
            title = _run(["xdotool", "getactivewindow", "getwindowname"])
            pid = _run(["xdotool", "getactivewindow", "getwindowpid"])
            proc = ""
            if pid:
                comm_path = Path(f"/proc/{pid}/comm")
                if comm_path.exists():
                    proc = comm_path.read_text().strip()
            return WindowInfo(
                handle=int(wid),
                title=title,
                process_name=proc.lower(),
            )
        except Exception:
            return None

    def focus_window(self, handle: Any) -> bool:
        wid = str(handle)
        if self._use_xdotool:
            return bool(_run(["xdotool", "windowactivate", wid]))
        if self._use_wmctrl:
            return bool(_run(["wmctrl", "-i", "-a", wid]))
        return False

    def hide_window(self, handle: Any) -> bool:
        wid = str(handle)
        if self._use_xdotool:
            _run(["xdotool", "windowminimize", wid])
            return True
        return False

    def show_window(self, handle: Any) -> bool:
        return self.focus_window(handle)

    def get_process_name(self, handle: Any) -> str:
        if not self._use_xdotool:
            return ""
        try:
            pid = _run(["xdotool", "getwindowpid", str(handle)])
            if pid:
                comm_path = Path(f"/proc/{pid}/comm")
                if comm_path.exists():
                    return comm_path.read_text().strip().lower()
        except Exception:
            pass
        return ""

    def play_beep(self, frequency: int = 440, duration_ms: int = 200) -> None:
        try:
            import numpy as np
            import sounddevice as sd
            t = np.linspace(0, duration_ms / 1000, int(16000 * duration_ms / 1000), endpoint=False)
            tone = (0.3 * np.sin(2 * np.pi * frequency * t)).astype(np.float32)
            sd.play(tone, 16000, blocking=False)
        except Exception:
            try:
                # Fallback to paplay
                _run(["paplay", "/usr/share/sounds/freedesktop/stereo/bell.oga"])
            except Exception:
                pass

    def update_startup_shortcut(self, enable: bool, app_path: Path | None = None) -> None:
        autostart_dir = Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config")) / "autostart"
        desktop_file = autostart_dir / "lerolero.desktop"

        try:
            if not enable:
                desktop_file.unlink(missing_ok=True)
                return

            autostart_dir.mkdir(parents=True, exist_ok=True)
            desktop_file.write_text(
                "[Desktop Entry]\n"
                "Type=Application\n"
                "Name=LeroLero\n"
                "Comment=100% offline speech-to-text\n"
                "Exec=python3 -m lerolero\n"
                "Terminal=false\n"
                "StartupNotify=false\n"
                "X-GNOME-Autostart-enabled=true\n"
            )
        except Exception as e:
            logger.error("Failed to update autostart: %s", e)

    def detect_gpu(self) -> str:
        # Check NVIDIA
        nvidia_smi = _run(["nvidia-smi", "--query-gpu=name", "--format=csv,noheader"])
        if nvidia_smi:
            return "cuda"

        # Check via lspci
        lspci = _run(["lspci"]).lower()
        if "nvidia" in lspci:
            return "cuda"
        if "intel" in lspci and ("arc" in lspci or "iris" in lspci):
            return "openvino"
        # DirectML is Windows-only, AMD on Linux uses ROCm (not supported yet)

        return "cpu"

    def show_error_dialog(self, title: str, message: str) -> None:
        # Try zenity (GNOME), kdialog (KDE), then console
        for cmd in [
            ["zenity", "--error", f"--title={title}", f"--text={message}"],
            ["kdialog", "--error", message, "--title", title],
        ]:
            try:
                result = subprocess.run(cmd, capture_output=True, timeout=30)
                if result.returncode == 0:
                    return
            except Exception:
                continue
        print(f"\nERROR: {title}\n{message}")

    def get_paste_modifier(self) -> str:
        return "ctrl"

    def set_app_icon(self) -> None:
        # Linux handles app icons via .desktop files
        pass
