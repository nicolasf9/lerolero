"""Micro-interaction animations using only CTk after() loops."""

from __future__ import annotations

import random


def _hex_to_rgb(h: str) -> tuple[int, int, int]:
    h = h.lstrip("#")
    return int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)


def _rgb_to_hex(r: int, g: int, b: int) -> str:
    return f"#{r:02x}{g:02x}{b:02x}"


def lerp_color(a: str, b: str, t: float) -> str:
    """Linearly interpolate between two hex colors."""
    r1, g1, b1 = _hex_to_rgb(a)
    r2, g2, b2 = _hex_to_rgb(b)
    return _rgb_to_hex(
        int(r1 + (r2 - r1) * t),
        int(g1 + (g2 - g1) * t),
        int(b1 + (b2 - b1) * t),
    )


class PulseAnimation:
    """Oscillate a widget's fg_color between two colors."""

    def __init__(
        self, widget: object, color_a: str, color_b: str,
        period_ms: int = 1200, steps: int = 24,
    ) -> None:
        self.widget = widget
        self.color_a = color_a
        self.color_b = color_b
        self.period_ms = period_ms
        self.steps = steps
        self._step = 0
        self._direction = 1
        self._after_id: str | None = None
        self._running = False

    def start(self) -> None:
        if self._running:
            return
        self._running = True
        self._step = 0
        self._direction = 1
        self._tick()

    def stop(self, restore_color: str | None = None) -> None:
        self._running = False
        if self._after_id is not None:
            self.widget.after_cancel(self._after_id)
            self._after_id = None
        if restore_color:
            self.widget.configure(fg_color=restore_color)

    def _tick(self) -> None:
        if not self._running:
            return
        t = self._step / max(self.steps, 1)
        color = lerp_color(self.color_a, self.color_b, t)
        self.widget.configure(fg_color=color)
        self._step += self._direction
        if self._step >= self.steps or self._step <= 0:
            self._direction *= -1
        delay = self.period_ms // max(self.steps * 2, 1)
        self._after_id = self.widget.after(delay, self._tick)


class TypingDotsAnimation:
    """Animate '...' dots on a label."""

    def __init__(
        self, label: object, base_text: str = "Thinking", interval_ms: int = 400,
    ) -> None:
        self.label = label
        self.base_text = base_text
        self.interval_ms = interval_ms
        self._dot_count = 0
        self._after_id: str | None = None
        self._running = False

    def start(self) -> None:
        if self._running:
            return
        self._running = True
        self._dot_count = 0
        self._tick()

    def stop(self) -> None:
        self._running = False
        if self._after_id is not None:
            self.label.after_cancel(self._after_id)
            self._after_id = None

    def _tick(self) -> None:
        if not self._running:
            return
        dots = "." * self._dot_count
        self.label.configure(text=f"  {self.base_text}{dots}  ")
        self._dot_count = (self._dot_count + 1) % 4
        self._after_id = self.label.after(self.interval_ms, self._tick)


class CountUpAnimation:
    """Animate a number counting up from start to end."""

    def __init__(
        self, label: object, end_val: float,
        duration_ms: int = 800, fmt: str = "{:.0f}",
        start_val: float = 0,
    ) -> None:
        self.label = label
        self.start_val = start_val
        self.end_val = end_val
        self.duration_ms = duration_ms
        self.fmt = fmt
        self._step = 0
        self._steps = 20
        self._after_id: str | None = None

    def start(self) -> None:
        self._step = 0
        self._tick()

    def _tick(self) -> None:
        progress = self._step / max(self._steps, 1)
        # ease-out quad
        t = 1 - (1 - progress) ** 2
        val = self.start_val + (self.end_val - self.start_val) * t
        self.label.configure(text=self.fmt.format(val))
        self._step += 1
        if self._step <= self._steps:
            delay = self.duration_ms // self._steps
            self._after_id = self.label.after(delay, self._tick)


# ── Waveform bars (unicode block elements) ─────────────────────────────

_BARS = "\u2581\u2582\u2583\u2584\u2585\u2586\u2587\u2588"


class WaveformIndicator:
    """Show a simple unicode waveform that animates during recording."""

    def __init__(self, label: object, width: int = 12, interval_ms: int = 120) -> None:
        self.label = label
        self.width = width
        self.interval_ms = interval_ms
        self._after_id: str | None = None
        self._running = False

    def start(self) -> None:
        if self._running:
            return
        self._running = True
        self._tick()

    def stop(self) -> None:
        self._running = False
        if self._after_id is not None:
            self.label.after_cancel(self._after_id)
            self._after_id = None
        self.label.configure(text="")

    def _tick(self) -> None:
        if not self._running:
            return
        bars = "".join(random.choice(_BARS[:5]) for _ in range(self.width))  # noqa: S311
        self.label.configure(text=bars)
        self._after_id = self.label.after(self.interval_ms, self._tick)
