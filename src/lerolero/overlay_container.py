"""Floating overlay — Siri-inspired animated orb with waveform ring."""

import collections
import math
import threading
import time
import tkinter as tk
from collections.abc import Callable

# Overlay dimensions
_ORB_RADIUS = 48
_RING_RADIUS = 60
_WIN_SIZE = 160
_PAD = 32

# Colors
_BG = "#0c0c10"
_REC_GLOW = "#ff4444"
_REC_ORB = "#cc2222"
_PROC_GLOW = "#fbbf24"
_PROC_ORB = "#d4951c"
_DONE_GLOW = "#34d399"
_DONE_ORB = "#1fa06a"
_IDLE_ORB = "#333340"
_TEXT = "#e8e8f0"

_BAR_COUNT = 32
_HISTORY_LEN = 32


class StatusOverlay:
    """Siri-style animated orb overlay with pulsating ring and waveform."""

    def __init__(
        self,
        audio_level_fn: Callable[[], float] | None = None,
        on_copy: Callable[[], None] | None = None,
        on_cancel: Callable[[], None] | None = None,
    ) -> None:
        self.root: tk.Tk | None = None
        self.canvas: tk.Canvas | None = None
        self.thread: threading.Thread | None = None
        self.visible: bool = False

        self._state: str = "idle"  # idle, recording, processing, success, error
        self._start_time: float | None = None
        self._hide_id: str | None = None
        self._tick: int = 0
        self._pulse_phase: float = 0.0

        self._audio_level_fn = audio_level_fn
        self._on_copy = on_copy
        self._on_cancel = on_cancel
        self._target_app: str = ""
        self._has_result: bool = False
        self._is_hovered: bool = False

        self._levels: collections.deque[float] = collections.deque(
            [0.0] * _HISTORY_LEN, maxlen=_HISTORY_LEN,
        )

    def start(self) -> None:
        if self.thread is not None and self.thread.is_alive():
            return
        self.thread = threading.Thread(target=self._run, daemon=True)
        self.thread.start()

    def _run(self) -> None:
        root = tk.Tk()
        self.root = root
        root.title("LeroLero Overlay")
        root.overrideredirect(True)
        root.attributes("-topmost", True)
        root.attributes("-alpha", 0.92)
        root.config(bg=_BG, highlightthickness=0)

        # Center the orb window in top-center of screen
        sw = root.winfo_screenwidth()
        x_pos = (sw - _WIN_SIZE) // 2
        root.geometry(f"{_WIN_SIZE}x{_WIN_SIZE}+{x_pos}+{_PAD}")
        root.resizable(False, False)

        # Make background transparent (platform-specific)
        import sys
        if sys.platform == "win32":
            root.wm_attributes("-transparentcolor", _BG)
        elif sys.platform == "darwin":
            try:
                root.wm_attributes("-transparent", True)
                root.config(bg="systemTransparent")
            except Exception:
                pass
        # Linux: no reliable transparency without compositing — skip gracefully

        self.canvas = tk.Canvas(
            root, width=_WIN_SIZE, height=_WIN_SIZE,
            bg=_BG, highlightthickness=0, bd=0,
        )
        self.canvas.pack(fill="both", expand=True)

        root.bind("<Enter>", self._on_hover_enter)
        root.bind("<Leave>", self._on_hover_leave)
        root.bind("<Button-1>", self._on_click)

        self._update_loop()
        root.mainloop()

    def _get_colors(self) -> tuple[str, str, str]:
        """Return (glow_color, orb_color, text_color) for current state."""
        if self._state == "recording":
            return _REC_GLOW, _REC_ORB, "#ff6b6b"
        if self._state == "processing":
            return _PROC_GLOW, _PROC_ORB, "#fbbf24"
        if self._state == "success":
            return _DONE_GLOW, _DONE_ORB, "#34d399"
        if self._state == "error":
            return "#ff4444", "#991b1b", "#ff6b6b"
        return "#444455", _IDLE_ORB, _TEXT

    def _lerp_color(self, c1: str, c2: str, t: float) -> str:
        """Linear interpolate between two hex colors."""
        r1, g1, b1 = int(c1[1:3], 16), int(c1[3:5], 16), int(c1[5:7], 16)
        r2, g2, b2 = int(c2[1:3], 16), int(c2[3:5], 16), int(c2[5:7], 16)
        r = int(r1 + (r2 - r1) * t)
        g = int(g1 + (g2 - g1) * t)
        b = int(b1 + (b2 - b1) * t)
        return f"#{r:02x}{g:02x}{b:02x}"

    def _draw(self) -> None:
        """Render the animated orb, glow rings, and waveform bars."""
        if self.canvas is None:
            return
        self.canvas.delete("all")

        cx, cy = _WIN_SIZE // 2, _WIN_SIZE // 2
        glow_col, orb_col, text_col = self._get_colors()

        # Pulse factor (breathing effect)
        self._pulse_phase += 0.08
        pulse = 0.5 + 0.5 * math.sin(self._pulse_phase)

        # Audio level for ring animation
        avg_level = sum(self._levels) / max(1, len(self._levels))

        # --- Outer glow (large soft) ---
        glow_r = _RING_RADIUS + 12 + pulse * 8 + avg_level * 20
        for i in range(5):
            r = glow_r - i * 3
            alpha_hex = max(8, min(40, int(15 + pulse * 25 - i * 5)))
            fade = self._lerp_color(_BG, glow_col, alpha_hex / 100)
            self.canvas.create_oval(
                cx - r, cy - r, cx + r, cy + r,
                fill="", outline=fade, width=3,
            )

        # --- Waveform ring (bars around the orb) ---
        if self._state == "recording" and any(l > 0.01 for l in self._levels):
            for i, level in enumerate(self._levels):
                angle = (2 * math.pi * i / _BAR_COUNT) - math.pi / 2
                inner_r = _ORB_RADIUS + 4
                bar_len = 4 + level * 25 + pulse * 2
                outer_r = inner_r + bar_len

                x1 = cx + math.cos(angle) * inner_r
                y1 = cy + math.sin(angle) * inner_r
                x2 = cx + math.cos(angle) * outer_r
                y2 = cy + math.sin(angle) * outer_r

                # Color intensity based on level
                t = min(1.0, level * 2)
                bar_col = self._lerp_color("#442222", _REC_GLOW, t)
                self.canvas.create_line(x1, y1, x2, y2, fill=bar_col, width=3, capstyle="round")

        elif self._state == "processing":
            # Spinning dots during processing
            for i in range(12):
                angle = (2 * math.pi * i / 12) + self._tick * 0.15
                r = _ORB_RADIUS + 10
                x = cx + math.cos(angle) * r
                y = cy + math.sin(angle) * r
                dot_alpha = (math.sin(angle - self._tick * 0.15) + 1) / 2
                dot_col = self._lerp_color(_BG, _PROC_GLOW, dot_alpha * 0.8)
                dot_size = 2 + dot_alpha * 2
                self.canvas.create_oval(
                    x - dot_size, y - dot_size, x + dot_size, y + dot_size,
                    fill=dot_col, outline="",
                )

        # --- Main orb (solid circle with gradient edge) ---
        orb_pulse_r = _ORB_RADIUS + pulse * 3
        # Edge ring
        self.canvas.create_oval(
            cx - orb_pulse_r - 2, cy - orb_pulse_r - 2,
            cx + orb_pulse_r + 2, cy + orb_pulse_r + 2,
            fill="", outline=glow_col, width=2,
        )
        # Solid orb
        self.canvas.create_oval(
            cx - orb_pulse_r, cy - orb_pulse_r,
            cx + orb_pulse_r, cy + orb_pulse_r,
            fill=orb_col, outline="",
        )

        # --- Center icon/text ---
        if self._state == "recording":
            elapsed = int(time.time() - self._start_time) if self._start_time else 0
            m, s = divmod(elapsed, 60)
            self.canvas.create_text(
                cx, cy - 6, text="\u25cf REC", fill="#ffffff",
                font=("Segoe UI", 10, "bold"),
            )
            self.canvas.create_text(
                cx, cy + 12, text=f"{m}:{s:02d}", fill="#ffcccc",
                font=("Segoe UI", 11),
            )
        elif self._state == "processing":
            dots = "\u2022" * ((self._tick // 6) % 4)
            self.canvas.create_text(
                cx, cy, text=f"\u231b{dots}", fill="#1a1400",
                font=("Segoe UI", 14),
            )
        elif self._state == "success":
            icon = "\u2713"
            self.canvas.create_text(
                cx, cy - 4, text=icon, fill="#001a0d",
                font=("Segoe UI", 18, "bold"),
            )
            if self._target_app:
                self.canvas.create_text(
                    cx, cy + 16, text=self._target_app[:15], fill="#003d1f",
                    font=("Segoe UI", 7),
                )
        elif self._state == "error":
            self.canvas.create_text(
                cx, cy, text="\u26a0", fill="#ffffff",
                font=("Segoe UI", 16),
            )

        # --- Hover actions ---
        if self._is_hovered and self._has_result:
            # Copy button
            self.canvas.create_oval(
                cx - 36, cy + _ORB_RADIUS + 10,
                cx - 12, cy + _ORB_RADIUS + 34,
                fill="#2a2a3a", outline="#555566", width=1,
                tags="copy_btn",
            )
            self.canvas.create_text(
                cx - 24, cy + _ORB_RADIUS + 22, text="\U0001f4cb",
                font=("Segoe UI", 9), fill=_TEXT, tags="copy_btn",
            )
            # Cancel button
            self.canvas.create_oval(
                cx + 12, cy + _ORB_RADIUS + 10,
                cx + 36, cy + _ORB_RADIUS + 34,
                fill="#2a2a3a", outline="#ff6b6b", width=1,
                tags="cancel_btn",
            )
            self.canvas.create_text(
                cx + 24, cy + _ORB_RADIUS + 22, text="\u2715",
                font=("Segoe UI", 9), fill="#ff6b6b", tags="cancel_btn",
            )

    def _update_loop(self) -> None:
        if self.root is None or self.canvas is None:
            return

        self._tick += 1

        # Sample audio level
        if self._state == "recording" and self._audio_level_fn is not None:
            try:
                level = self._audio_level_fn()
            except Exception:
                level = 0.0
            self._levels.append(level)

        # Draw
        if self.visible:
            self._draw()
            self.root.deiconify()
        else:
            self.root.withdraw()

        self.root.after(50, self._update_loop)

    def update_status(self, status: str) -> None:
        self.visible = True
        self._has_result = False

        if self.root is not None and self._hide_id is not None:
            self.root.after_cancel(str(self._hide_id))
            self._hide_id = None

        if status == "Recording":
            self._state = "recording"
            self._start_time = time.time()
            self._levels = collections.deque(
                [0.0] * _HISTORY_LEN, maxlen=_HISTORY_LEN,
            )
            self._pulse_phase = 0.0
        elif status == "Processing":
            self._state = "processing"
            self._start_time = None
        elif "Success" in status or "Ready" in status or "Text Ready" in status:
            self._state = "success"
            self._start_time = None
            self._has_result = True
            if self.root is not None:
                self._hide_id = str(self.root.after(2500, self.hide))
        elif "Error" in status:
            self._state = "error"
            self._start_time = None
        else:
            self._state = "idle"
            self._start_time = None

    def _on_hover_enter(self, _event: object = None) -> None:
        self._is_hovered = True

    def _on_hover_leave(self, _event: object = None) -> None:
        self._is_hovered = False

    def _on_click(self, event: tk.Event) -> None:
        """Handle click on hover buttons."""
        if not self._has_result:
            return
        cx, cy = _WIN_SIZE // 2, _WIN_SIZE // 2
        x, y = event.x, event.y

        # Copy button area
        if cx - 36 <= x <= cx - 12 and cy + _ORB_RADIUS + 10 <= y <= cy + _ORB_RADIUS + 34:
            self._do_copy()
        # Cancel button area
        elif cx + 12 <= x <= cx + 36 and cy + _ORB_RADIUS + 10 <= y <= cy + _ORB_RADIUS + 34:
            self._do_cancel()

    def _do_copy(self) -> None:
        if self._on_copy:
            self._on_copy()

    def _do_cancel(self) -> None:
        if self._on_cancel:
            self._on_cancel()
        self._has_result = False
        self._is_hovered = False
        self.hide()

    def set_target_app(self, app_name: str) -> None:
        short = app_name.split(" - ")[0].strip() if " - " in app_name else app_name
        self._target_app = short[:25]

    def hide(self) -> None:
        self.visible = False
        self._hide_id = None
        self._state = "idle"

    def stop(self) -> None:
        if self.root is not None:
            self.root.quit()
