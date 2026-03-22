"""Pulsating recording orb — Siri-inspired voice visualization."""

from __future__ import annotations

import math
import tkinter as tk

from whisper_typing.gui.theme import Theme


class RecordingOrb:
    """Canvas-based pulsating orb shown during recording."""

    def __init__(self, parent: tk.Widget, audio_level_fn=None) -> None:
        self._parent = parent
        self._audio_level_fn = audio_level_fn
        self._canvas: tk.Canvas | None = None
        self._running = False
        self._tick = 0
        self._ring1_r = 0.0
        self._ring1_alpha = 0.0
        self._ring2_r = 0.0
        self._ring2_alpha = 0.0

    def show(self, parent: tk.Widget | None = None) -> None:
        """Create and show the orb in the given parent."""
        if parent:
            self._parent = parent
        p = Theme.get()

        self._canvas = tk.Canvas(
            self._parent, width=180, height=180,
            bg=p.bg, highlightthickness=0,
        )
        self._canvas.pack(pady=(20, 10))
        self._running = True
        self._tick = 0
        self._ring1_r = 40.0
        self._ring1_alpha = 0.6
        self._ring2_r = 40.0
        self._ring2_alpha = 0.4
        self._animate()

    def hide(self) -> None:
        """Stop and destroy the orb."""
        self._running = False
        if self._canvas:
            self._canvas.destroy()
            self._canvas = None

    def _animate(self) -> None:
        if not self._running or not self._canvas:
            return

        self._tick += 1
        c = self._canvas
        c.delete("all")
        p = Theme.get()

        cx, cy = 90, 90

        # Get audio level
        level = 0.3
        if self._audio_level_fn:
            try:
                level = max(0.1, self._audio_level_fn())
            except Exception:  # noqa: BLE001
                pass

        # ── Pulse rings (expand outward, fade) ──────────────────────
        self._ring1_r += 1.2
        self._ring1_alpha -= 0.012
        if self._ring1_r > 80:
            self._ring1_r = 40.0
            self._ring1_alpha = 0.6

        self._ring2_r += 1.2
        self._ring2_alpha -= 0.012
        if self._ring2_r > 90:
            self._ring2_r = 40.0
            self._ring2_alpha = 0.4

        # Draw pulse rings as circles with decreasing intensity
        for ring_r, ring_a in [(self._ring1_r, self._ring1_alpha), (self._ring2_r, self._ring2_alpha)]:
            if ring_a > 0:
                intensity = int(max(0, min(255, ring_a * 255)))
                ring_color = f"#{intensity:02x}{int(intensity*0.3):02x}{int(intensity*0.3):02x}"
                c.create_oval(
                    cx - ring_r, cy - ring_r, cx + ring_r, cy + ring_r,
                    outline=ring_color, width=2,
                )

        # ── Outer glow (breathes with audio) ─────────────────────────
        glow_r = 42 + level * 15 + math.sin(self._tick * 0.1) * 3
        glow_color = p.pulse_rec_b
        c.create_oval(
            cx - glow_r, cy - glow_r, cx + glow_r, cy + glow_r,
            fill=glow_color, outline="",
        )

        # ── Middle layer ──────────────────────────────────────────────
        mid_r = 36 + level * 8 + math.sin(self._tick * 0.15) * 2
        c.create_oval(
            cx - mid_r, cy - mid_r, cx + mid_r, cy + mid_r,
            fill=p.pulse_rec_a, outline="",
        )

        # ── Core orb ─────────────────────────────────────────────────
        core_r = 28 + level * 5
        c.create_oval(
            cx - core_r, cy - core_r, cx + core_r, cy + core_r,
            fill="#ff8888", outline="",
        )

        # ── Mic icon ─────────────────────────────────────────────────
        c.create_text(cx, cy, text="\U0001f399", font=("Segoe UI", 24), fill="#ffffff")

        # ── Timer text below ─────────────────────────────────────────
        elapsed = self._tick // 30  # approx seconds at 30fps
        m, s = divmod(elapsed, 60)
        c.create_text(
            cx, cy + 60, text=f"{m}:{s:02d}",
            font=("Consolas", 12), fill=p.muted,
        )

        c.after(33, self._animate)  # ~30 FPS
