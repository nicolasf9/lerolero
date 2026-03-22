"""Main GUI — Resizable, ChatGPT-style chat, 4K-ready typography."""

import json
import tkinter as tk
import tkinter.font as tkfont
import threading
from datetime import UTC, datetime
from pathlib import Path

import customtkinter as ctk

from whisper_typing.app_controller import WhisperAppController
from whisper_typing.gui.personality import (
    fun_comparison, greeting, log_emoji, mascot,
    milestone_message, status_text, time_comparison,
)
from whisper_typing.gui.recording_orb import RecordingOrb
from whisper_typing.gui.screens import ConfigurationWindow
from whisper_typing.gui.sidebar import Sidebar
from whisper_typing.gui.theme import Theme
from whisper_typing.metrics import aggregate, backfill_from_transcripts, format_duration

_F = "Segoe UI"
_M = "Consolas"


class WhisperAppGUI(ctk.CTk):
    """Maximized resizable window with ChatGPT-style message feed."""

    def __init__(self, controller: WhisperAppController) -> None:
        super().__init__()
        self.controller = controller

        Theme.apply_from_config(controller.config.get("theme"))
        ctk.set_appearance_mode("dark" if Theme.is_dark() else "light")

        self.title("LeroLero")
        self.geometry("900x600")
        self.minsize(700, 500)
        # Center on screen
        self.update_idletasks()
        sw = self.winfo_screenwidth()
        sh = self.winfo_screenheight()
        x = (sw - 900) // 2
        y = (sh - 600) // 2
        self.geometry(f"900x600+{x}+{y}")

        # Load Modak font for branding
        self._modak_loaded = False
        try:
            font_path = Path(__file__).parent.parent / "assets" / "Modak-Regular.ttf"
            if font_path.exists():
                import ctypes
                ctypes.windll.gdi32.AddFontResourceExW(str(font_path), 0x10, 0)
                self._modak_loaded = True
        except Exception:  # noqa: BLE001
            pass

        # Set window icon (Windows taskbar + title bar)
        self._icon_path = Path(__file__).parent.parent / "assets" / "icon.ico"
        self._icon_png_path = Path(__file__).parent.parent / "assets" / "icon.png"
        try:
            if self._icon_path.exists():
                self.iconbitmap(str(self._icon_path))
            if self._icon_png_path.exists():
                self._icon_image = ctk.CTkImage(
                    light_image=__import__("PIL.Image", fromlist=["Image"]).open(self._icon_png_path),
                    dark_image=__import__("PIL.Image", fromlist=["Image"]).open(self._icon_png_path),
                    size=(28, 28),
                )
            else:
                self._icon_image = None
        except Exception:  # noqa: BLE001
            self._icon_image = None

        self.protocol("WM_DELETE_WINDOW", self.hide_window)

        self._chat_row = 0
        self._current_tab = "general"

        # Chat message storage — persists across tab switches
        self._chat_messages: list[dict] = []  # {type, text, meta, ts}

        # Live bubble tracking: during recording we UPDATE one bubble, not create many
        self._live_bubble_text: ctk.CTkLabel | None = None
        self._live_bubble_meta: ctk.CTkLabel | None = None
        self._is_recording = False
        self._recording_orb: RecordingOrb | None = None

        self._build_ui()

        # on_preview_update is called DURING recording (live) — update the current bubble
        self.controller.on_log = lambda msg: self.after(0, self.write_log, msg)
        self.controller.on_status_change = lambda s: self.after(0, self.update_status, s)
        self.controller.on_preview_update = lambda t, _: self.after(0, self._on_live_preview, t)

        self.config_window = None
        self.after(100, self.startup_controller)

    # ── Build ──────────────────────────────────────────────────────────

    def _build_ui(self) -> None:  # noqa: PLR0915
        p = Theme.get()
        self.configure(fg_color=p.bg)

        for w in self.winfo_children():
            w.destroy()

        # ── Root grid: sidebar (col 0) + content (col 1) ─────────────
        self.grid_columnconfigure(0, weight=0)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # ── Sidebar ──────────────────────────────────────────────────
        self.sidebar = Sidebar(self, on_tab_change=self._show_tab)
        self.sidebar.grid(row=0, column=0, sticky="nsew")

        # ── Content column ───────────────────────────────────────────
        content = ctk.CTkFrame(self, fg_color=p.bg, corner_radius=0)
        content.grid(row=0, column=1, sticky="nsew")
        content.grid_columnconfigure(0, weight=1)
        content.grid_rowconfigure(1, weight=1)  # tab content expands
        self._content_root = content

        # ── Top bar ──────────────────────────────────────────────────
        top = ctk.CTkFrame(content, fg_color=p.surface, corner_radius=0, height=46)
        top.grid(row=0, column=0, sticky="new")
        top.grid_columnconfigure(0, weight=1)
        top.grid_propagate(False)

        # Status + translate + controls in one row
        bar = ctk.CTkFrame(top, fg_color="transparent")
        bar.grid(row=0, column=0, padx=12, pady=8, sticky="ew")
        bar.grid_columnconfigure(1, weight=1)

        self.status_pill = ctk.CTkLabel(
            bar, text="  Starting  ",
            font=ctk.CTkFont(family=_F, size=12, weight="bold"),
            text_color=p.pill_start_fg, fg_color=p.pill_start_bg,
            corner_radius=12, height=28, width=130,
        )
        self.status_pill.grid(row=0, column=0, padx=(0, 8))

        self._is_translate = self.controller.config.get("whisper_task", "transcribe") == "translate"
        self.translate_btn = ctk.CTkButton(
            bar,
            text="\U0001f1e7\U0001f1f7 \u2192 \U0001f1ec\U0001f1e7" if self._is_translate else "\U0001f310 Transcribe",
            font=ctk.CTkFont(family=_F, size=11), height=28, width=100, corner_radius=12,
            fg_color=p.accent_dim if self._is_translate else "transparent",
            hover_color=p.surface2,
            text_color="#ffffff" if self._is_translate else p.muted,
            border_width=1, border_color=p.border,
            command=self._toggle_translate,
        )
        self.translate_btn.grid(row=0, column=1, padx=4, sticky="w")

        # Info label (model, backend, hotkey)
        self.lbl_info = ctk.CTkLabel(bar, text="", font=ctk.CTkFont(family=_M, size=10), text_color=p.muted)
        self.lbl_info.grid(row=0, column=2, padx=8, sticky="e")

        # Right controls
        _bs = dict(height=28, font=ctk.CTkFont(family=_F, size=12),
                   fg_color="transparent", hover_color=p.surface2,
                   text_color=p.muted, corner_radius=6)
        ctk.CTkButton(bar, text="\u263e" if Theme.is_dark() else "\u2600",
                       width=28, command=self._toggle_theme, **_bs).grid(row=0, column=3, padx=2)
        ctk.CTkButton(bar, text="\u2015", width=28,
                       command=self.hide_window, **_bs).grid(row=0, column=4, padx=2)
        ctk.CTkButton(bar, text="\u2715", width=28, height=28,
                       font=ctk.CTkFont(size=12), fg_color="transparent",
                       hover_color=p.close_hover, text_color=p.close_text,
                       corner_radius=6, command=self.quit_app).grid(row=0, column=5, padx=2)

        # ── Tab content area ─────────────────────────────────────────
        self._tab_frame = ctk.CTkFrame(content, fg_color=p.bg, corner_radius=0)
        self._tab_frame.grid(row=1, column=0, sticky="nsew")
        self._tab_frame.grid_columnconfigure(0, weight=1)
        self._tab_frame.grid_rowconfigure(0, weight=1)

        # ── Bottom log (collapsible) ─────────────────────────────────
        self._log_open = False
        self._log_container = ctk.CTkFrame(content, fg_color=p.surface, corner_radius=0)
        self._log_container.grid(row=2, column=0, sticky="sew")
        self._log_container.grid_columnconfigure(0, weight=1)

        log_toggle = ctk.CTkButton(
            self._log_container, text="\u25b6  System Logs",
            font=ctk.CTkFont(family=_F, size=11), height=24,
            fg_color="transparent", hover_color=p.surface2,
            text_color=p.muted, anchor="w", corner_radius=0,
            command=self._toggle_log,
        )
        log_toggle.grid(row=0, column=0, sticky="ew", padx=8, pady=2)
        self._log_toggle_btn = log_toggle

        self._log_box = ctk.CTkFrame(self._log_container, fg_color=p.surface, height=70)
        self._log_box.grid_columnconfigure(0, weight=1)
        self._log_box.grid_rowconfigure(0, weight=1)
        self._log_box.grid_propagate(False)

        self.log_text = ctk.CTkTextbox(
            self._log_box, font=ctk.CTkFont(family=_M, size=11),
            fg_color=p.surface, text_color=p.log_text,
            border_width=0, corner_radius=0,
        )
        self.log_text.grid(row=0, column=0, sticky="nsew", padx=10, pady=4)
        self._set_readonly(self.log_text)
        self._log_box.grid_remove()

        # ── Metrics labels (used by update_metrics, always exist) ────
        self.lbl_m_words = ctk.CTkLabel(self, text="")
        self.lbl_m_sessions = ctk.CTkLabel(self, text="")
        self.lbl_m_saved = ctk.CTkLabel(self, text="")
        self.lbl_m_streak = ctk.CTkLabel(self, text="")
        # Hide them — they're just data holders; actual display is in tabs
        for w in (self.lbl_m_words, self.lbl_m_sessions, self.lbl_m_saved, self.lbl_m_streak):
            w.place(x=-9999, y=-9999)

        # Build the default tab
        self._show_tab("general")

        # ── Preloader overlay (shown during model loading) ───────────
        self._preloader = ctk.CTkFrame(content, fg_color=p.bg, corner_radius=0)
        self._preloader.place(relx=0, rely=0, relwidth=1, relheight=1)
        self._preloader.lift()

        pre_inner = ctk.CTkFrame(self._preloader, fg_color="transparent")
        pre_inner.place(relx=0.5, rely=0.45, anchor="center")

        # Spinner canvas
        self._spinner_canvas = tk.Canvas(
            pre_inner, width=64, height=64, bg=p.bg, highlightthickness=0,
        )
        self._spinner_canvas.pack(pady=(0, 16))
        self._spinner_angle = 0
        self._spinner_running = True
        self._animate_spinner()

        ctk.CTkLabel(
            pre_inner, text="Carregando motores de IA...",
            font=ctk.CTkFont(family=_F, size=16, weight="bold"),
            text_color=p.text,
        ).pack(pady=(0, 6))

        model = self.controller.config.get("model", "whisper-base").split("/")[-1]
        ctk.CTkLabel(
            pre_inner, text=f"{model}  \u00b7  detecting GPU...",
            font=ctk.CTkFont(family=_M, size=11),
            text_color=p.muted,
        ).pack()

    def _animate_spinner(self) -> None:
        """Rotating arc spinner for the preloader."""
        if not self._spinner_running:
            return
        c = self._spinner_canvas
        p = Theme.get()
        c.delete("all")

        cx, cy, r = 32, 32, 24
        # Trail arcs (fading)
        for i, offset in enumerate([60, 30, 0]):
            alpha_hex = ["33", "66", "ff"][i]
            color = p.accent if i == 2 else p.accent_dim
            start = self._spinner_angle - offset
            c.create_arc(
                cx - r, cy - r, cx + r, cy + r,
                start=start, extent=80, style="arc",
                outline=color, width=3,
            )

        self._spinner_angle = (self._spinner_angle + 8) % 360
        c.after(33, self._animate_spinner)

    def _hide_preloader(self) -> None:
        """Remove the preloader overlay."""
        self._spinner_running = False
        if hasattr(self, "_preloader") and self._preloader.winfo_exists():
            self._preloader.destroy()

    # ── Dotted surface background ──────────────────────────────────────

    def _draw_dotted_bg(self, p: object) -> None:
        """Draw an animated dotted wave grid behind tab content (dotted-surface inspired)."""
        import math as _math

        bg_canvas = tk.Canvas(self._tab_frame, bg=p.bg, highlightthickness=0)
        bg_canvas.place(relx=0, rely=0, relwidth=1, relheight=1)
        tk.Widget.lower(bg_canvas)

        # Dot color: subtle blend between bg and border
        r1, g1, b1 = int(p.bg[1:3], 16), int(p.bg[3:5], 16), int(p.bg[5:7], 16)
        r2, g2, b2 = int(p.border[1:3], 16), int(p.border[3:5], 16), int(p.border[5:7], 16)
        t = 0.2
        dot_color = f"#{int(r1+(r2-r1)*t):02x}{int(g1+(g2-g1)*t):02x}{int(b1+(b2-b1)*t):02x}"
        dot_hi = f"#{int(r1+(r2-r1)*0.35):02x}{int(g1+(g2-g1)*0.35):02x}{int(b1+(b2-b1)*0.35):02x}"

        spacing = 22
        self._dot_tick = 0
        self._dot_items: list[int] = []

        def _init_dots() -> None:
            bg_canvas.delete("all")
            self._dot_items.clear()
            w = bg_canvas.winfo_width()
            h = bg_canvas.winfo_height()
            for col in range(0, w + spacing, spacing):
                for row_y in range(0, h + spacing, spacing):
                    item = bg_canvas.create_oval(col, row_y, col + 2, row_y + 2, fill=dot_color, outline="")
                    self._dot_items.append((item, col, row_y))

        def _animate_wave() -> None:
            if not bg_canvas.winfo_exists():
                return
            self._dot_tick += 1
            for item, bx, by in self._dot_items:
                # Sine wave displacement
                dy = _math.sin((bx / spacing + self._dot_tick * 0.08)) * 3
                dx = _math.cos((by / spacing + self._dot_tick * 0.06)) * 2
                # Brightness varies with wave
                wave_val = (_math.sin((bx + by) / 40 + self._dot_tick * 0.1) + 1) / 2
                color = dot_hi if wave_val > 0.7 else dot_color
                bg_canvas.coords(item, bx + dx, by + dy, bx + dx + 2, by + dy + 2)
                bg_canvas.itemconfig(item, fill=color)
            bg_canvas.after(80, _animate_wave)

        bg_canvas.bind("<Configure>", lambda _e: _init_dots())
        bg_canvas.after(200, lambda: (_init_dots(), _animate_wave()))
        self._dotted_canvas = bg_canvas

    # ── Tab navigation ─────────────────────────────────────────────────

    def _show_tab(self, key: str) -> None:
        """Switch to a different tab — rebuild content."""
        # Detach live bubble references (they belong to destroyed widgets)
        if key != "general" and key != self._current_tab:
            self._live_bubble_text = None
            self._live_bubble_meta = None

        self._current_tab = key
        for w in self._tab_frame.winfo_children():
            w.destroy()
        # Reset row weights
        for i in range(5):
            self._tab_frame.grid_rowconfigure(i, weight=0)

        p = Theme.get()

        # Dotted surface background
        self._draw_dotted_bg(p)

        if key == "general":
            self._build_tab_general(p)
        elif key == "history":
            self._build_tab_history(p)
        elif key == "metrics":
            self._build_tab_metrics(p)
        elif key == "settings":
            self._build_tab_settings(p)
        elif key == "about":
            self._build_tab_about(p)

    def _build_tab_general(self, p: object) -> None:
        """General tab — chat bubbles + metrics strip."""
        # Metrics strip at top
        ms = ctk.CTkFrame(self._tab_frame, fg_color=p.surface2, corner_radius=0, height=32)
        ms.grid(row=0, column=0, sticky="new")
        ms.grid_columnconfigure(3, weight=1)
        ms.grid_propagate(False)

        _mf = ctk.CTkFont(family=_F, size=11, weight="bold")
        agg = aggregate()
        self._gen_words = ctk.CTkLabel(ms, text=f"\U0001f4ac {agg.words_today:,} words", font=_mf, text_color=p.accent)
        self._gen_words.grid(row=0, column=0, padx=(12, 8), pady=5, sticky="w")
        self._gen_sessions = ctk.CTkLabel(ms, text=f"\U0001f3af {agg.sessions_today} sessions", font=_mf, text_color=p.muted)
        self._gen_sessions.grid(row=0, column=1, padx=8, pady=5, sticky="w")
        self._gen_saved = ctk.CTkLabel(ms, text=f"\u23f1 {format_duration(agg.time_saved_today_s)} saved", font=_mf, text_color=p.green)
        self._gen_saved.grid(row=0, column=2, padx=8, pady=5, sticky="w")
        streak_text = ""
        if agg.streak_days > 1:
            streak_text = f"\U0001f525 {agg.streak_days}-day streak!"
        elif agg.streak_days == 1:
            streak_text = "\U0001f31f Day 1!"
        self._gen_streak = ctk.CTkLabel(ms, text=streak_text, font=_mf, text_color=p.gold)
        self._gen_streak.grid(row=0, column=3, padx=8, pady=5, sticky="w")

        # Chat area
        self.chat_frame = ctk.CTkScrollableFrame(self._tab_frame, fg_color="transparent", corner_radius=0)
        self.chat_frame.grid(row=1, column=0, sticky="nsew", padx=0, pady=0)
        self.chat_frame.grid_columnconfigure(0, weight=1)
        self._tab_frame.grid_rowconfigure(1, weight=1)
        self._chat_row = 0

        # Restore saved messages
        if self._chat_messages:
            for msg in self._chat_messages:
                if msg["type"] == "system":
                    self._add_system_msg(msg["text"])
                elif msg["type"] == "bubble":
                    self._add_saved_bubble(msg["text"], msg.get("meta", ""), p)
            self._live_bubble_text = None
            self._live_bubble_meta = None
        else:
            self._empty_state = None
            self._build_empty_state(p)

    def _build_tab_history(self, p: object) -> None:
        """History tab — search + scrollable list."""
        self._tab_frame.grid_rowconfigure(1, weight=1)

        # Search bar
        search_frame = ctk.CTkFrame(self._tab_frame, fg_color="transparent")
        search_frame.grid(row=0, column=0, padx=16, pady=(12, 4), sticky="ew")
        search_frame.grid_columnconfigure(0, weight=1)

        self._hist_search = ctk.CTkEntry(
            search_frame, placeholder_text="\U0001f50d Search transcriptions...",
            font=ctk.CTkFont(family=_F, size=13), height=38,
            fg_color=p.surface, border_color=p.accent_dim, border_width=2,
            corner_radius=10,
        )
        self._hist_search.grid(row=0, column=0, sticky="ew")
        self._hist_search.bind("<KeyRelease>", lambda e: self._filter_history())

        # Animated glowing border for search bar
        self._search_glow_colors = [p.accent_dim, p.accent, p.accent_hover, p.accent]
        self._search_glow_idx = 0
        self._animate_search_glow()

        # Scrollable list
        self._hist_list = ctk.CTkScrollableFrame(self._tab_frame, fg_color=p.bg, corner_radius=0)
        self._hist_list.grid(row=1, column=0, sticky="nsew", padx=8, pady=4)
        self._hist_list.grid_columnconfigure(0, weight=1)
        self._load_history_entries(p)

    def _load_history_entries(self, p: object, query: str = "") -> None:
        """Load history entries into the history tab."""
        for w in self._hist_list.winfo_children():
            w.destroy()

        from whisper_typing.paths import get_history_dir
        hist_file = get_history_dir() / "transcripts.jsonl"
        if not hist_file.exists():
            ctk.CTkLabel(self._hist_list, text="No transcriptions yet.",
                         font=ctk.CTkFont(family=_F, size=14),
                         text_color=p.muted).grid(row=0, column=0, padx=20, pady=40)
            return

        entries = []
        try:
            with hist_file.open("r", encoding="utf-8") as f:
                for line in f:
                    try:
                        entries.append(json.loads(line))
                    except json.JSONDecodeError:
                        pass
        except OSError:
            pass

        q = query.lower().strip()
        for idx, data in enumerate(reversed(entries[-50:])):
            text = data.get("text", "")
            if q and q not in text.lower():
                continue
            ts = data.get("timestamp", "?")
            words = len(text.split()) if text.strip() else 0

            card = ctk.CTkFrame(self._hist_list, fg_color=p.surface, corner_radius=10,
                                 border_width=1, border_color=p.border)
            card.grid(row=idx, column=0, padx=4, pady=3, sticky="ew")
            card.grid_columnconfigure(0, weight=1)

            # Spotlight glow canvas
            spot = tk.Canvas(card, bg=p.surface, highlightthickness=0)
            spot.place(relx=0, rely=0, relwidth=1, relheight=1)
            spot.lower()

            def _spot_move(e: tk.Event, cv=spot) -> None:
                cv.delete("all")
                cv.create_oval(
                    e.x - 80, e.y - 80, e.x + 80, e.y + 80,
                    fill=p.accent_dim, outline="", stipple="gray12",
                )

            def _spot_leave(_e: tk.Event, cv=spot) -> None:
                cv.delete("all")

            card.bind("<Motion>", _spot_move)
            card.bind("<Leave>", _spot_leave)
            spot.bind("<Motion>", _spot_move)
            spot.bind("<Leave>", _spot_leave)

            # Text
            ctk.CTkLabel(card, text=text[:250] + ("..." if len(text) > 250 else ""),
                         font=ctk.CTkFont(family=_F, size=13),
                         text_color=p.text, wraplength=500,
                         justify="left", anchor="nw").grid(
                row=0, column=0, padx=14, pady=(10, 2), sticky="ew")

            # Meta + copy button
            meta_frame = ctk.CTkFrame(card, fg_color="transparent")
            meta_frame.grid(row=1, column=0, padx=14, pady=(0, 10), sticky="ew")
            meta_frame.grid_columnconfigure(0, weight=1)

            meta_text = f"{ts[:16].replace('T', ' ')}  \u00b7  {words} words"
            ctk.CTkLabel(meta_frame, text=meta_text,
                         font=ctk.CTkFont(family=_M, size=10),
                         text_color=p.muted_dim).grid(row=0, column=0, sticky="w")

            # Copy button (always subtle, more visible on hover)
            copy_btn = ctk.CTkButton(
                meta_frame, text="\U0001f4cb", width=24, height=20,
                font=ctk.CTkFont(size=11), fg_color="transparent",
                hover_color=p.surface2, text_color=p.muted, corner_radius=4,
                command=lambda t=text: self._copy_text(t),
            )
            copy_btn.grid(row=0, column=1, sticky="e")

    def _animate_search_glow(self) -> None:
        """Cycle the search bar border color for a glowing effect."""
        if not hasattr(self, "_hist_search") or not self._hist_search.winfo_exists():
            return
        color = self._search_glow_colors[self._search_glow_idx % len(self._search_glow_colors)]
        self._hist_search.configure(border_color=color)
        self._search_glow_idx += 1
        self._hist_search.after(800, self._animate_search_glow)

    def _filter_history(self) -> None:
        q = self._hist_search.get() if hasattr(self, "_hist_search") else ""
        self._load_history_entries(Theme.get(), q)

    def _build_tab_metrics(self, p: object) -> None:
        """Metrics tab — cards + bar chart."""
        self._tab_frame.grid_rowconfigure(2, weight=1)
        agg = aggregate()

        # Cards row
        cards = ctk.CTkFrame(self._tab_frame, fg_color="transparent")
        cards.grid(row=0, column=0, padx=16, pady=(16, 8), sticky="ew")
        cards.grid_columnconfigure((0, 1, 2, 3), weight=1)

        self._metric_card(cards, 0, "\u23f1 TIME SAVED", format_duration(agg.total_time_saved_s), p.green, p)
        self._metric_card(cards, 1, "\U0001f4ac TOTAL WORDS", f"{agg.total_words:,}", p.accent, p)
        self._metric_card(cards, 2, "\U0001f3af SESSIONS", str(agg.total_sessions), p.muted, p)
        self._metric_card(cards, 3, "\u26a1 AVG SPEED", f"{agg.avg_words_per_session:.0f} w/session", p.gold, p)

        # Bar chart - last 7 days
        ctk.CTkLabel(self._tab_frame, text="  LAST 7 DAYS",
                     font=ctk.CTkFont(family=_F, size=11, weight="bold"),
                     text_color=p.accent).grid(row=1, column=0, padx=20, pady=(12, 4), sticky="w")

        bar_frame = ctk.CTkFrame(self._tab_frame, fg_color=p.surface, corner_radius=10,
                                  border_width=1, border_color=p.border)
        bar_frame.grid(row=2, column=0, padx=16, pady=(0, 16), sticky="nsew")
        bar_frame.grid_columnconfigure(1, weight=1)

        max_w = max(agg.words_by_day.values()) if agg.words_by_day else 1
        for i, (day, words) in enumerate(sorted(agg.words_by_day.items())):
            ctk.CTkLabel(bar_frame, text=day[5:],
                         font=ctk.CTkFont(family=_M, size=11), text_color=p.muted).grid(
                row=i, column=0, padx=(14, 6), pady=4, sticky="w")
            bar = ctk.CTkProgressBar(bar_frame, height=12, corner_radius=6,
                                     fg_color=p.border, progress_color=p.accent_dim)
            bar.grid(row=i, column=1, padx=4, pady=4, sticky="ew")
            bar.set(words / max(max_w, 1))
            ctk.CTkLabel(bar_frame, text=str(words),
                         font=ctk.CTkFont(family=_M, size=11, weight="bold"),
                         text_color=p.text).grid(
                row=i, column=2, padx=(6, 14), pady=4, sticky="e")

    @staticmethod
    def _metric_card(parent: ctk.CTkFrame, col: int, label: str, value: str, color: str, p: object) -> None:
        """Holographic metric card with mouse-tracking glow effect."""
        c = ctk.CTkFrame(parent, fg_color=p.surface, corner_radius=12,
                          border_width=1, border_color=p.border)
        c.grid(row=0, column=col, padx=4, pady=4, sticky="nsew")
        c.grid_columnconfigure(0, weight=1)

        # Glow canvas (sits behind labels)
        glow = tk.Canvas(c, bg=p.surface, highlightthickness=0, width=1, height=1)
        glow.place(relx=0, rely=0, relwidth=1, relheight=1)
        glow.lower()

        def _on_motion(event: tk.Event) -> None:
            glow.delete("all")
            x, y = event.x, event.y
            # Radial glow following cursor
            r = 60
            # Create oval glow — color varies based on x position
            hue_shift = x / max(c.winfo_width(), 1)
            # Blend between accent_dim and green based on position
            glow.create_oval(
                x - r, y - r, x + r, y + r,
                fill=p.accent_dim, outline="", stipple="gray12",
            )
            # Subtle shine line
            glow.create_line(
                x - 30, y - 20, x + 30, y + 20,
                fill=color, width=1, stipple="gray25",
            )

        def _on_leave(_event: tk.Event) -> None:
            glow.delete("all")

        for widget in (c, glow):
            widget.bind("<Motion>", _on_motion)
            widget.bind("<Leave>", _on_leave)

        ctk.CTkLabel(c, text=label, font=ctk.CTkFont(family=_F, size=9, weight="bold"),
                     text_color=p.muted).grid(row=0, column=0, padx=12, pady=(12, 0), sticky="w")
        ctk.CTkLabel(c, text=value, font=ctk.CTkFont(family=_F, size=20, weight="bold"),
                     text_color=color).grid(row=1, column=0, padx=12, pady=(2, 12), sticky="w")

    def _build_tab_settings(self, p: object) -> None:
        """Settings tab — inline form (not a modal)."""
        import sounddevice as sd
        from whisper_typing.constants import WHISPER_MODELS
        from whisper_typing.paths import get_data_dir

        self._tab_frame.grid_rowconfigure(0, weight=1)

        form = ctk.CTkScrollableFrame(self._tab_frame, fg_color="transparent", corner_radius=0)
        form.grid(row=0, column=0, sticky="nsew", padx=16, pady=8)
        form.grid_columnconfigure(1, weight=1)

        cfg = self.controller.config
        _lbl = {"font": ctk.CTkFont(family=_F, size=12), "text_color": p.muted}
        _ent = {
            "font": ctk.CTkFont(family=_M, size=12),
            "fg_color": p.surface2, "text_color": p.text,
            "border_width": 1, "border_color": p.border, "corner_radius": 8,
        }
        _cmb = {
            **_ent,
            "button_color": p.border, "button_hover_color": p.accent_dim,
            "dropdown_fg_color": p.surface, "dropdown_text_color": p.text,
            "dropdown_hover_color": p.surface2,
        }
        _swi = {
            "font": ctk.CTkFont(family=_F, size=12), "text_color": p.muted,
            "progress_color": p.accent_dim, "button_color": p.text,
            "button_hover_color": p.accent_hover, "fg_color": p.border,
        }

        def _sec(title: str, r: int) -> int:
            ctk.CTkLabel(form, text=title, font=ctk.CTkFont(family=_F, size=10, weight="bold"),
                         text_color=p.accent).grid(row=r, column=0, columnspan=2, padx=12, pady=(16, 4), sticky="w")
            return r + 1

        row = 0
        row = _sec("\U0001f3a4 AUDIO", row)

        # Mic
        ctk.CTkLabel(form, text="Microphone", **_lbl).grid(row=row, column=0, padx=12, pady=6, sticky="w")
        mic_list = ["(System Default)"]
        for d in sd.query_devices():
            if d["max_input_channels"] > 0:
                mic_list.append(d["name"])
        self._s_mic = ctk.CTkComboBox(form, values=mic_list, **_cmb)
        self._s_mic.grid(row=row, column=1, padx=12, pady=6, sticky="ew")
        mic_name = cfg.get("microphone_name")
        self._s_mic.set(mic_name if mic_name and mic_name in mic_list else "(System Default)")
        row += 1

        ctk.CTkLabel(form, text="Recording Mode", **_lbl).grid(row=row, column=0, padx=12, pady=6, sticky="w")
        self._s_rec_mode = ctk.CTkComboBox(form, values=["toggle", "hold"], **_cmb)
        self._s_rec_mode.grid(row=row, column=1, padx=12, pady=6, sticky="ew")
        self._s_rec_mode.set(cfg.get("recording_mode", "toggle"))
        row += 1

        ctk.CTkLabel(form, text="Auto Stop", **_lbl).grid(row=row, column=0, padx=12, pady=6, sticky="w")
        self._s_auto_stop = ctk.CTkSwitch(form, text="Stop on silence", **_swi)
        self._s_auto_stop.grid(row=row, column=1, padx=12, pady=6, sticky="w")
        if cfg.get("auto_stop", True):
            self._s_auto_stop.select()
        row += 1

        # ── MODEL
        row = _sec("\U0001f9e0 MODEL", row)

        ctk.CTkLabel(form, text="Whisper Model", **_lbl).grid(row=row, column=0, padx=12, pady=6, sticky="w")
        self._s_model = ctk.CTkComboBox(form, values=[m[1] for m in WHISPER_MODELS], **_cmb)
        self._s_model.grid(row=row, column=1, padx=12, pady=6, sticky="ew")
        self._s_model.set(cfg.get("model", "openai/whisper-base"))
        row += 1

        ctk.CTkLabel(form, text="Language", **_lbl).grid(row=row, column=0, padx=12, pady=6, sticky="w")
        self._s_lang = ctk.CTkComboBox(form, values=["auto", "pt", "en", "es", "fr", "de", "it", "ja", "zh", "ko"], **_cmb)
        self._s_lang.grid(row=row, column=1, padx=12, pady=6, sticky="ew")
        lang = cfg.get("language")
        self._s_lang.set(lang if lang and lang.lower() != "auto" else "auto")
        row += 1

        ctk.CTkLabel(form, text="Device", **_lbl).grid(row=row, column=0, padx=12, pady=6, sticky="w")
        self._s_device = ctk.CTkComboBox(form, values=["auto", "cpu", "GPU", "cuda", "openvino", "directml"], **_cmb)
        self._s_device.grid(row=row, column=1, padx=12, pady=6, sticky="ew")
        self._s_device.set(cfg.get("device", "auto"))
        row += 1

        # ── HOTKEY
        row = _sec("\u2328 HOTKEYS", row)

        ctk.CTkLabel(form, text="Record Hotkey", **_lbl).grid(row=row, column=0, padx=12, pady=6, sticky="w")
        self._s_hotkey = ctk.CTkEntry(form, **_ent)
        self._s_hotkey.grid(row=row, column=1, padx=12, pady=6, sticky="ew")
        self._s_hotkey.insert(0, cfg.get("hotkey", "<f8>"))
        row += 1

        ctk.CTkLabel(form, text="Translate Hotkey", **_lbl).grid(row=row, column=0, padx=12, pady=6, sticky="w")
        self._s_translate_hk = ctk.CTkEntry(form, placeholder_text="e.g. <f10>", **_ent)
        self._s_translate_hk.grid(row=row, column=1, padx=12, pady=6, sticky="ew")
        self._s_translate_hk.insert(0, cfg.get("translate_hotkey", ""))
        row += 1

        # ── TYPING
        row = _sec("\u270d TYPING", row)

        self._s_live = ctk.CTkSwitch(form, text="Live Typing (type while recording)", **_swi)
        self._s_live.grid(row=row, column=0, columnspan=2, padx=12, pady=6, sticky="w")
        if cfg.get("live_typing", True):
            self._s_live.select()
        row += 1

        self._s_paste = ctk.CTkSwitch(form, text="Auto Paste (paste on finish)", **_swi)
        self._s_paste.grid(row=row, column=0, columnspan=2, padx=12, pady=6, sticky="w")
        if cfg.get("auto_paste", True):
            self._s_paste.select()
        row += 1

        # ── STORAGE
        row = _sec("\U0001f4be STORAGE", row)

        ctk.CTkLabel(form, text="Data Directory", **_lbl).grid(row=row, column=0, padx=12, pady=6, sticky="w")
        self._s_data_dir = ctk.CTkEntry(form, **_ent)
        self._s_data_dir.grid(row=row, column=1, padx=12, pady=6, sticky="ew")
        self._s_data_dir.insert(0, str(cfg.get("data_dir", get_data_dir())))
        row += 1

        self._s_save_audio = ctk.CTkSwitch(form, text="Save audio recordings (.wav)", **_swi)
        self._s_save_audio.grid(row=row, column=0, columnspan=2, padx=12, pady=6, sticky="w")
        if cfg.get("save_audio", False):
            self._s_save_audio.select()
        row += 1

        self._s_history = ctk.CTkSwitch(form, text="Save transcription history", **_swi)
        self._s_history.grid(row=row, column=0, columnspan=2, padx=12, pady=6, sticky="w")
        if cfg.get("save_history", True):
            self._s_history.select()
        row += 1

        # ── GENERAL
        row = _sec("\u2699 GENERAL", row)

        ctk.CTkLabel(form, text="Theme", **_lbl).grid(row=row, column=0, padx=12, pady=6, sticky="w")
        self._s_theme = ctk.CTkComboBox(form, values=["dark", "light"], **_cmb)
        self._s_theme.grid(row=row, column=1, padx=12, pady=6, sticky="ew")
        self._s_theme.set(cfg.get("theme", "dark"))
        row += 1

        for text_lbl, attr, cfg_key, desc, default in [
            ("Show Overlay", "_s_overlay", "show_overlay", "Floating status overlay", True),
            ("Refocus Window", "_s_refocus", "refocus_window", "Switch back after paste", True),
            ("Run at Startup", "_s_startup", "run_at_startup", "Windows auto-start", False),
        ]:
            sw = ctk.CTkSwitch(form, text=f"{text_lbl} — {desc}", **_swi)
            sw.grid(row=row, column=0, columnspan=2, padx=12, pady=6, sticky="w")
            if cfg.get(cfg_key, default):
                sw.select()
            setattr(self, attr, sw)
            row += 1

        # Save button
        ctk.CTkButton(
            form, text="\u2714  Save Settings", width=200, height=40,
            font=ctk.CTkFont(family=_F, size=14, weight="bold"),
            fg_color=p.accent_dim, hover_color=p.accent_hover,
            text_color="white", corner_radius=10, command=self._save_settings,
        ).grid(row=row, column=0, columnspan=2, padx=12, pady=(20, 12))

    def _save_settings(self) -> None:
        """Save inline settings."""
        mic = self._s_mic.get()
        new_cfg = {
            "hotkey": self._s_hotkey.get().strip() or "<f8>",
            "translate_hotkey": self._s_translate_hk.get().strip() or "",
            "model": self._s_model.get(),
            "language": self._s_lang.get() if self._s_lang.get() != "auto" else None,
            "device": self._s_device.get(),
            "microphone_name": mic if mic != "(System Default)" else None,
            "recording_mode": self._s_rec_mode.get(),
            "auto_stop": bool(self._s_auto_stop.get()),
            "live_typing": bool(self._s_live.get()),
            "auto_paste": bool(self._s_paste.get()),
            "theme": self._s_theme.get(),
            "show_overlay": bool(self._s_overlay.get()),
            "refocus_window": bool(self._s_refocus.get()),
            "run_at_startup": bool(self._s_startup.get()),
            "save_history": bool(self._s_history.get()),
            "save_audio": bool(self._s_save_audio.get()),
        }
        data_dir = self._s_data_dir.get().strip()
        if data_dir:
            new_cfg["data_dir"] = data_dir
        self.controller.update_config(new_cfg)
        self.write_log("Settings saved.")
        self.update_sidebar_info()

    def _build_tab_about(self, p: object) -> None:
        """About tab."""
        frame = ctk.CTkFrame(self._tab_frame, fg_color="transparent")
        frame.grid(row=0, column=0, padx=40, pady=40, sticky="nsew")
        frame.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(frame, text="LeroLero",
                     font=ctk.CTkFont(family="Modak" if self._modak_loaded else _F, size=36),
                     text_color=p.text).grid(row=0, column=0, pady=(20, 4))
        ctk.CTkLabel(frame, text="v1.0.0",
                     font=ctk.CTkFont(family=_M, size=12), text_color=p.muted).grid(row=1, column=0, pady=(0, 16))
        ctk.CTkLabel(frame, text="100% offline speech-to-text for Windows",
                     font=ctk.CTkFont(family=_F, size=14), text_color=p.muted).grid(row=2, column=0, pady=4)
        ctk.CTkLabel(frame, text="Powered by OpenVINO / CUDA / DirectML + Whisper",
                     font=ctk.CTkFont(family=_F, size=12), text_color=p.muted_dim).grid(row=3, column=0, pady=2)
        ctk.CTkLabel(frame, text="Your voice never leaves your computer.",
                     font=ctk.CTkFont(family=_F, size=12, slant="italic"),
                     text_color=p.accent).grid(row=4, column=0, pady=(16, 4))
        ctk.CTkLabel(frame, text="Based on whisper-typing by Roger Filomeno (MIT)",
                     font=ctk.CTkFont(family=_F, size=11), text_color=p.muted_dim).grid(row=5, column=0, pady=2)

    # ── Chat messages ──────────────────────────────────────────────────

    def _build_empty_state(self, p: object) -> None:
        """Show a friendly empty state when no transcriptions exist yet."""
        hotkey = self.controller.config.get("hotkey", "<f8>")
        frame = ctk.CTkFrame(self.chat_frame, fg_color="transparent")
        frame.grid(row=0, column=0, padx=40, pady=(120, 40), sticky="ew")
        frame.grid_columnconfigure(0, weight=1)

        # Large mic icon
        ctk.CTkLabel(
            frame, text="\U0001f399",
            font=ctk.CTkFont(size=56), text_color=p.accent,
        ).grid(row=0, column=0, pady=(0, 12))

        ctk.CTkLabel(
            frame, text="Tudo pronto.",
            font=ctk.CTkFont(family=_F, size=22, weight="bold"),
            text_color=p.text,
        ).grid(row=1, column=0, pady=(0, 6))

        ctk.CTkLabel(
            frame,
            text=f"Pressione  {hotkey.upper().strip('<>')}  e comece a ditar.",
            font=ctk.CTkFont(family=_F, size=15),
            text_color=p.muted,
        ).grid(row=2, column=0, pady=(0, 8))

        ctk.CTkLabel(
            frame,
            text="100% offline  \u00b7  sua voz nunca sai do seu computador",
            font=ctk.CTkFont(family=_F, size=11),
            text_color=p.muted,
        ).grid(row=3, column=0, pady=(4, 0))

        self._empty_state = frame
        self._chat_row = 1

    def _remove_empty_state(self) -> None:
        """Remove the empty state when first bubble is created."""
        if self._empty_state is not None:
            self._empty_state.destroy()
            self._empty_state = None

    def _add_system_msg(self, text: str) -> None:
        p = Theme.get()
        if not hasattr(self, "chat_frame") or not self.chat_frame.winfo_exists():
            return
        ctk.CTkLabel(
            self.chat_frame, text=f"  {text}",
            font=ctk.CTkFont(family=_F, size=13, slant="italic"),
            text_color=p.muted, anchor="w",
        ).grid(row=self._chat_row, column=0, padx=60, pady=(12, 4), sticky="ew")
        self._chat_row += 1
        # Save for tab switch restoration
        self._chat_messages.append({"type": "system", "text": text})

    def _create_bubble(self) -> None:
        """Create a new chat bubble for the current recording session."""
        self._remove_empty_state()
        p = Theme.get()

        # Card directly in chat — no avatar, cleaner layout
        card = ctk.CTkFrame(self.chat_frame, fg_color=p.surface, corner_radius=14,
                             border_width=1, border_color=p.border)
        card.grid(row=self._chat_row, column=0, padx=(30, 30), pady=(8, 4), sticky="ew")
        card.grid_columnconfigure(0, weight=1)
        self._chat_row += 1
        self._live_card = card

        # Text label — capped width for readability
        self._live_bubble_text = ctk.CTkLabel(
            card, text="...",
            font=ctk.CTkFont(family=_F, size=16),
            text_color=p.text,
            wraplength=min(800, max(400, self.winfo_width() - 120)),
            justify="left", anchor="nw",
        )
        self._live_bubble_text.grid(row=0, column=0, padx=18, pady=(14, 4), sticky="ew")

        # Bottom row: meta + action buttons
        bottom = ctk.CTkFrame(card, fg_color="transparent")
        bottom.grid(row=1, column=0, padx=18, pady=(0, 12), sticky="ew")
        bottom.grid_columnconfigure(0, weight=1)

        self._live_bubble_meta = ctk.CTkLabel(
            bottom, text="recording...",
            font=ctk.CTkFont(family=_F, size=11),
            text_color=p.muted_dim, anchor="w",
        )
        self._live_bubble_meta.grid(row=0, column=0, sticky="w")

        # Hover action buttons (hidden by default)
        actions = ctk.CTkFrame(bottom, fg_color="transparent")
        actions.grid(row=0, column=1, sticky="e")
        actions.grid_remove()

        _ab = dict(width=26, height=22, corner_radius=4, font=ctk.CTkFont(size=12),
                    fg_color="transparent", hover_color=p.surface2, text_color=p.muted)

        text_ref = self._live_bubble_text
        copy_btn = ctk.CTkButton(
            actions, text="\U0001f4cb",
            command=lambda: self._copy_bubble_text(text_ref, card),
            **_ab,
        )
        copy_btn.pack(side="left", padx=1)

        del_btn = ctk.CTkButton(
            actions, text="\U0001f5d1",
            command=lambda c=card: self._delete_bubble(c),
            **_ab,
        )
        del_btn.pack(side="left", padx=1)

        # Hover bindings
        def _show(_e: object) -> None:
            actions.grid()

        def _hide(_e: object) -> None:
            actions.grid_remove()

        card.bind("<Enter>", _show)
        card.bind("<Leave>", _hide)
        for child in (self._live_bubble_text, self._live_bubble_meta, bottom, actions, copy_btn, del_btn):
            child.bind("<Enter>", _show)
            child.bind("<Leave>", _hide)

    def _add_saved_bubble(self, text: str, meta: str, p: object) -> None:
        """Re-render a saved bubble (for tab switch restoration)."""
        card = ctk.CTkFrame(self.chat_frame, fg_color=p.surface, corner_radius=14,
                             border_width=1, border_color=p.border)
        card.grid(row=self._chat_row, column=0, padx=(30, 30), pady=(8, 4), sticky="ew")
        card.grid_columnconfigure(0, weight=1)
        self._chat_row += 1

        ctk.CTkLabel(
            card, text=text, font=ctk.CTkFont(family=_F, size=16),
            text_color=p.text, wraplength=min(800, max(400, self.winfo_width() - 300)),
            justify="left", anchor="nw",
        ).grid(row=0, column=0, padx=18, pady=(14, 4), sticky="ew")

        ctk.CTkLabel(
            card, text=meta, font=ctk.CTkFont(family=_F, size=11),
            text_color=p.muted_dim, anchor="w",
        ).grid(row=1, column=0, padx=18, pady=(0, 12), sticky="w")

    def _copy_text(self, text: str) -> None:
        """Copy text to clipboard."""
        import pyperclip
        pyperclip.copy(text)
        self.write_log("Copied to clipboard.")

    def _copy_bubble_text(self, text_label: ctk.CTkLabel, card: ctk.CTkFrame) -> None:
        """Copy bubble text to clipboard with visual feedback."""
        import pyperclip
        text = text_label.cget("text")
        if text and text != "...":
            pyperclip.copy(text)
            p = Theme.get()
            # Flash card border as feedback
            orig_border = card.cget("border_color")
            card.configure(border_color=p.green)
            self.after(600, lambda: card.configure(border_color=orig_border))

    def _delete_bubble(self, card: ctk.CTkFrame) -> None:
        """Remove a bubble card from the chat."""
        card.destroy()

    def _on_live_preview(self, text: str) -> None:
        """Called during recording — update the live bubble text, don't create new ones."""
        if not text or not text.strip():
            return

        # If we don't have a live bubble yet, create one
        if self._live_bubble_text is None:
            self._create_bubble()

        # Update text in-place
        self._live_bubble_text.configure(text=text)

        # Auto-scroll
        try:
            self.chat_frame._parent_canvas.yview_moveto(1.0)
        except Exception:  # noqa: BLE001
            pass

    def _finalize_bubble(self) -> None:
        """Called when recording finishes — stamp the metadata and detach."""
        if self._live_bubble_text is None:
            return

        p = Theme.get()
        ts = datetime.now(UTC).astimezone().strftime("%H:%M:%S")
        text = self._live_bubble_text.cget("text")
        words = len(text.split()) if text and text.strip() and text != "..." else 0
        dur = self.controller.last_recording_duration
        win = self.controller.last_target_window_title or "Desktop"

        parts = [ts]
        if dur > 0:
            parts.append(f"{dur:.1f}s")
        if words > 0:
            parts.append(f"{words} words")
        parts.append(f"\U0001f4bb {win}")

        meta_str = "  \u00b7  ".join(parts)
        if self._live_bubble_meta is not None:
            self._live_bubble_meta.configure(text=meta_str)

        # Save for persistence across tab switches
        self._chat_messages.append({"type": "bubble", "text": text, "meta": meta_str})

        # Detach — next recording will create a fresh bubble
        self._live_bubble_text = None
        self._live_bubble_meta = None

    # ── (Side panel replaced by sidebar tabs) ──────────────────────────

    def _toggle_translate(self) -> None:
        self._is_translate = not self._is_translate
        p = Theme.get()
        task = "translate" if self._is_translate else "transcribe"
        self.controller.config["whisper_task"] = task
        from whisper_typing.app_controller import save_config
        save_config(self.controller.config)

        if self._is_translate:
            self.translate_btn.configure(
                text="\U0001f1e7\U0001f1f7 \u2192 \U0001f1ec\U0001f1e7",
                fg_color=p.accent_dim, text_color="#ffffff",
            )
            self.write_log("Translation mode: speech will be translated to English.")
        else:
            self.translate_btn.configure(
                text="\U0001f310 Transcribe",
                fg_color="transparent", text_color=p.muted,
            )
            self.write_log("Transcription mode: speech kept in original language.")

    def _toggle_log(self) -> None:
        if self._log_open:
            self._log_box.grid_remove()
            self._log_toggle_btn.configure(text="\u25b6  System Logs")
            self._log_open = False
        else:
            self._log_box.grid(row=1, column=0, sticky="sew")
            self._log_toggle_btn.configure(text="\u25bc  System Logs")
            self._log_open = True

    # Side panel methods removed — replaced by tab-based layout

    # ── Theme ──────────────────────────────────────────────────────────

    def _toggle_theme(self) -> None:
        Theme.toggle()
        ctk.set_appearance_mode("dark" if Theme.is_dark() else "light")
        self.controller.config["theme"] = "dark" if Theme.is_dark() else "light"
        from whisper_typing.app_controller import save_config
        save_config(self.controller.config)
        self._live_bubble_text = None
        self._live_bubble_meta = None
        self._build_ui()
        self.update_sidebar_info()
        self.update_metrics()

    # ── Helpers ────────────────────────────────────────────────────────

    @staticmethod
    def _set_readonly(w: ctk.CTkTextbox, *, readonly: bool = True) -> None:
        w.configure(state="disabled" if readonly else "normal")

    def startup_controller(self) -> None:
        self.write_log("Loading models...")
        self.update_status("Loading")

        def _init() -> None:
            n = backfill_from_transcripts()
            if n > 0:
                self.after(0, self.write_log, f"Migrated {n} legacy transcripts.")
            success = self.controller.initialize_components()
            self.after(0, self._hide_preloader)
            self.after(0, self.update_sidebar_info)
            self.after(0, self.update_metrics)
            if success:
                self.controller.start_listener()
                self.controller.setup_tray(on_open=self.show_window)
                self.after(0, self.update_status, "Ready")
                self.after(0, self.write_log, greeting())
                hk = self.controller.config.get("hotkey", "<f8>")
                self.after(0, self.write_log, f"Press {hk} to start talking.")
                self.after(0, self._add_system_msg, greeting())
            else:
                self.after(0, self.update_status, "Error")
                self.after(0, self.write_log, "Failed to initialize.")

        threading.Thread(target=_init, daemon=True).start()

    def update_sidebar_info(self) -> None:
        cfg = self.controller.config
        # Show actual detected backend if transcriber is loaded
        backend = "detecting..."
        if self.controller.transcriber:
            backend = self.controller.transcriber.backend
        parts = [
            f"model: {cfg.get('model', '?').split('/')[-1]}",
            f"backend: {backend}",
            f"hotkey: {cfg.get('hotkey', '?')}",
        ]
        self.lbl_info.configure(text="  \u00b7  ".join(parts))

    def update_metrics(self) -> None:
        agg = aggregate()
        # Update general tab metrics strip if it exists
        if hasattr(self, "_gen_words") and self._gen_words.winfo_exists():
            self._gen_words.configure(text=f"\U0001f4ac {agg.words_today:,} words")
            self._gen_sessions.configure(text=f"\U0001f3af {agg.sessions_today} sessions")
            self._gen_saved.configure(text=f"\u23f1 {format_duration(agg.time_saved_today_s)} saved")
            streak = ""
            if agg.streak_days > 1:
                streak = f"\U0001f525 {agg.streak_days}-day streak!"
            elif agg.streak_days == 1:
                streak = "\U0001f31f Day 1!"
            self._gen_streak.configure(text=streak)

        msg = milestone_message(agg.total_words, agg.words_today, agg.sessions_today)
        if msg:
            self.write_log(msg)

    def write_log(self, message: str) -> None:
        ts = datetime.now(UTC).astimezone().strftime("%H:%M")
        line = f" {ts}  {log_emoji(message)}\n"
        self._set_readonly(self.log_text, readonly=False)
        self.log_text.insert("end", line)
        self.log_text.see("end")
        self._set_readonly(self.log_text)

    def update_status(self, status: str) -> None:
        p = Theme.get()
        display = status_text(status)

        if "Recording" in status:
            self._is_recording = True
            self._create_bubble()
            self.status_pill.configure(text=f"  {display}  ",
                                        fg_color=p.pill_rec_bg, text_color=p.pill_rec_fg)
            # Show recording orb in general tab
            if self._current_tab == "general" and hasattr(self, "chat_frame"):
                if self._recording_orb is None:
                    self._recording_orb = RecordingOrb(
                        self.chat_frame, audio_level_fn=self.controller._get_audio_level,
                    )
                self._recording_orb.show(self.chat_frame)
        elif any(k in status for k in ("Processing", "Loading", "Improving")):
            # Hide orb during processing
            if self._recording_orb:
                self._recording_orb.hide()
            self.status_pill.configure(text=f"  {display}  ",
                                        fg_color=p.pill_proc_bg, text_color=p.pill_proc_fg)
        elif "Error" in status or "Failed" in status:
            self._is_recording = False
            if self._recording_orb:
                self._recording_orb.hide()
            self.status_pill.configure(text=f"  {display}  ",
                                        fg_color=p.pill_error_bg, text_color=p.pill_error_fg)
        else:
            # Ready / Text Ready — finalize the bubble
            if self._recording_orb:
                self._recording_orb.hide()
            if self._is_recording or self._live_bubble_text is not None:
                self._is_recording = False
                self._finalize_bubble()
                self.after(500, self.update_metrics)
            self.status_pill.configure(text=f"  {display}  ",
                                        fg_color=p.pill_ready_bg, text_color=p.pill_ready_fg)

    # ── Dialogs ────────────────────────────────────────────────────────

    def open_configure(self) -> None:
        if self.config_window is None or not self.config_window.winfo_exists():
            self.config_window = ConfigurationWindow(self, self.controller)
            self.config_window.wait_window()
            self.update_sidebar_info()
        else:
            self.config_window.focus()

    # ── Window ─────────────────────────────────────────────────────────

    def show_window(self) -> None:
        self.after(0, self.deiconify)
        self.after(0, self.focus_force)

    def hide_window(self) -> None:
        self.withdraw()

    def quit_app(self) -> None:
        self.controller.shutdown()
        self.quit()
        self.destroy()
