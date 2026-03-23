"""Floating overlay with centered waveform visualization — polished typography."""

import collections
import threading
import time
import tkinter as tk
import tkinter.font as tkfont
from collections.abc import Callable

_WIDTH = 420
_HEIGHT = 68
_PAD = 24

_BG = "#0c0c10"
_SURFACE = "#141420"
_GREEN = "#34d399"
_RED_BG = "#1c0a0a"
_GOLD = "#fbbf24"
_TEXT = "#e0e0e6"

# Waveform config
_BAR_COUNT = 40
_BAR_GAP = 2
_WAVE_H = 34
_HISTORY_LEN = 40

# Typography
_FONT_FAMILY = "Segoe UI Variable"
_FONT_FALLBACK = "Segoe UI"
_FONT_SIZE = 11


def _pick_font() -> str:
    """Pick the best available sans-serif font."""
    try:
        root = tk._default_root  # noqa: SLF001
        if root:
            families = tk.font.families(root)
        else:
            families = ()
        for f in (_FONT_FAMILY, "Inter", _FONT_FALLBACK):
            if f in families:
                return f
    except Exception:  # noqa: BLE001
        pass
    return _FONT_FALLBACK


class StatusOverlay:
    """Fixed-size overlay with centered audio waveform bars."""

    def __init__(
        self,
        audio_level_fn: Callable[[], float] | None = None,
        on_copy: Callable[[], None] | None = None,
        on_cancel: Callable[[], None] | None = None,
    ) -> None:
        self.root: tk.Tk | None = None
        self.label: tk.Label | None = None
        self.canvas: tk.Canvas | None = None
        self.thread: threading.Thread | None = None
        self.visible: bool = False
        self._target_text: str = ""
        self._target_fg: str = _TEXT
        self._target_bg: str = _BG
        self._start_time: float | None = None
        self._hide_id: str | None = None
        self._tick: int = 0
        self._is_recording: bool = False
        self._is_processing: bool = False

        self._audio_level_fn = audio_level_fn
        self._on_copy = on_copy
        self._on_cancel = on_cancel
        self._hover_buttons: list[tk.Button] = []
        self._is_hovered: bool = False
        self._has_result: bool = False
        self._target_app: str = ""
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
        root.overrideredirect(True)  # noqa: FBT003
        root.attributes("-topmost", True)  # noqa: FBT003
        root.attributes("-alpha", 0.95)
        root.config(bg=_BG, highlightthickness=2, highlightbackground="#222228")
        root.geometry(f"{_WIDTH}x{_HEIGHT}+{_PAD}+{_PAD}")
        root.resizable(False, False)  # noqa: FBT003

        font_family = _pick_font()

        # Status text (top) — improved typography
        self.label = tk.Label(
            root, text="", fg=_TEXT, bg=_BG,
            font=(font_family, _FONT_SIZE), anchor="w",
            wraplength=_WIDTH - 30,
        )
        self.label.place(x=12, y=3, width=_WIDTH - 24, height=22)

        # Waveform canvas (bottom) — centered bars
        self.canvas = tk.Canvas(
            root, width=_WIDTH - 16, height=_WAVE_H,
            bg=_SURFACE, highlightthickness=0, bd=0,
        )
        self.canvas.place(x=8, y=28, width=_WIDTH - 16, height=_WAVE_H)

        # Hover action buttons (hidden by default)
        btn_frame = tk.Frame(root, bg=_BG)
        btn_frame.place(x=_WIDTH - 70, y=3, width=60, height=22)
        btn_frame.place_forget()
        self._btn_frame = btn_frame

        _btn_kw = dict(
            font=("Segoe UI", 9), bd=0, padx=2, pady=0, cursor="hand2",
            bg=_BG, activebackground=_SURFACE,
        )
        copy_btn = tk.Button(btn_frame, text="\U0001f4cb", fg=_TEXT, command=self._do_copy, **_btn_kw)
        copy_btn.pack(side="left")
        cancel_btn = tk.Button(btn_frame, text="\u2715", fg="#ff6b6b", command=self._do_cancel, **_btn_kw)
        cancel_btn.pack(side="left")
        self._hover_buttons = [copy_btn, cancel_btn]

        root.bind("<Enter>", self._on_hover_enter)
        root.bind("<Leave>", self._on_hover_leave)

        self._update_loop()
        root.mainloop()

    def _draw_centered_waveform(self) -> None:
        """Draw centered vertical bars — grow from middle up and down."""
        if self.canvas is None:
            return
        self.canvas.delete("all")

        cw = _WIDTH - 16
        cy = _WAVE_H // 2
        bar_w = max(2, (cw - (_BAR_COUNT - 1) * _BAR_GAP) // _BAR_COUNT)

        for i, level in enumerate(self._levels):
            x = i * (bar_w + _BAR_GAP)
            half_h = max(1, int(level * (cy - 1)))

            if level > 0.5:
                color = "#ff6b6b"
            elif level > 0.2:
                color = "#e05555"
            elif level > 0.05:
                color = "#993333"
            else:
                color = "#442222"

            self.canvas.create_rectangle(
                x, cy - half_h, x + bar_w, cy + half_h,
                fill=color, outline="",
            )

        self.canvas.create_line(0, cy, cw, cy, fill="#333340", width=1)

    def _draw_idle_waveform(self) -> None:
        """Draw a flat center line when processing/idle."""
        if self.canvas is None:
            return
        self.canvas.delete("all")
        cw = _WIDTH - 16
        cy = _WAVE_H // 2

        bar_w = max(2, (cw - (_BAR_COUNT - 1) * _BAR_GAP) // _BAR_COUNT)
        for i in range(_BAR_COUNT):
            x = i * (bar_w + _BAR_GAP)
            h = 1 + int(abs((i + self._tick) % 10 - 5) * 0.4)
            self.canvas.create_rectangle(
                x, cy - h, x + bar_w, cy + h,
                fill="#333340", outline="",
            )

    def _update_loop(self) -> None:
        if self.label is None or self.root is None:
            return

        self._tick += 1

        display = self._target_text

        if self._start_time is not None:
            elapsed = int(time.time() - self._start_time)
            m, s = divmod(elapsed, 60)
            display = f"\u25cf REC   {m}:{s:02d}"

        if self._is_processing:
            dots = "." * ((self._tick // 5) % 4)
            display = f"\u231b thinking{dots: <3}"

        self.label.config(text=display, fg=self._target_fg, bg=self._target_bg)
        self.root.config(bg=self._target_bg)

        if self._is_recording:
            level = 0.0
            if self._audio_level_fn is not None:
                try:
                    level = self._audio_level_fn()
                except Exception:  # noqa: BLE001
                    pass
            self._levels.append(level)
            self._draw_centered_waveform()

            intensity = int(60 + 195 * min(1.0, level * 1.5))
            self.root.config(highlightbackground=f"#{intensity:02x}2525")
        elif self._is_processing:
            self._draw_idle_waveform()
            self.root.config(highlightbackground="#444420")
        else:
            if self.canvas is not None:
                self.canvas.delete("all")
            self.root.config(highlightbackground="#222228")

        if self.visible:
            self.root.deiconify()
        else:
            self.root.withdraw()

        self.root.after(70, self._update_loop)

    def update_status(self, status: str) -> None:
        self.visible = True
        self._is_processing = False
        self._is_recording = False

        if self.root is not None and self._hide_id is not None:
            self.root.after_cancel(str(self._hide_id))
            self._hide_id = None

        self._has_result = False

        if status == "Recording":
            self._target_text = "\u25cf REC   0:00"
            self._target_fg = "#ff6b6b"
            self._target_bg = _RED_BG
            self._start_time = time.time()
            self._is_recording = True
            self._levels = collections.deque(
                [0.0] * _HISTORY_LEN, maxlen=_HISTORY_LEN,
            )
        elif status == "Processing":
            self._target_text = "\u231b thinking"
            self._target_fg = "#1a1400"
            self._target_bg = _GOLD
            self._start_time = None
            self._is_processing = True
        elif "Success" in status or "Ready" in status or "Text Ready" in status:
            ready_label = "\u2728 ready"
            if self._target_app:
                ready_label = f"\u2728 \u2192 {self._target_app}"
            self._target_text = ready_label
            self._target_fg = "#001a0d"
            self._target_bg = _GREEN
            self._start_time = None
            self._has_result = True
            if self.root is not None:
                self._hide_id = str(self.root.after(2500, self.hide))
        elif "Error" in status:
            self._target_text = "\u26a0 error"
            self._target_fg = "#ffffff"
            self._target_bg = "#991b1b"
            self._start_time = None
        else:
            self._target_text = status.lower()[:30]
            self._target_fg = _TEXT
            self._target_bg = _BG
            self._start_time = None

    def _on_hover_enter(self, _event: object = None) -> None:
        self._is_hovered = True
        if self._has_result and hasattr(self, "_btn_frame"):
            self._btn_frame.place(x=_WIDTH - 70, y=3, width=60, height=22)

    def _on_hover_leave(self, _event: object = None) -> None:
        self._is_hovered = False
        if hasattr(self, "_btn_frame"):
            self._btn_frame.place_forget()

    def _do_copy(self) -> None:
        if self._on_copy:
            self._on_copy()
        # Flash green briefly
        if self.label:
            self.label.config(fg=_GREEN)
            self.root.after(400, lambda: self.label.config(fg=self._target_fg) if self.label else None)

    def _do_cancel(self) -> None:
        if self._on_cancel:
            self._on_cancel()
        self._has_result = False
        self._on_hover_leave()
        self.hide()

    def set_target_app(self, app_name: str) -> None:
        """Set the name of the target application for the 'Ready' state display."""
        # Shorten long names (e.g. "Google Chrome - My Page" → "Chrome")
        short = app_name.split(" - ")[0].strip() if " - " in app_name else app_name
        self._target_app = short[:25]

    def hide(self) -> None:
        self.visible = False
        self._hide_id = None

    def stop(self) -> None:
        if self.root is not None:
            self.root.quit()
