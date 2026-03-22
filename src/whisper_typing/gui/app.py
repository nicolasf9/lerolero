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

        # Live bubble tracking: during recording we UPDATE one bubble, not create many
        self._live_bubble_text: ctk.CTkLabel | None = None
        self._live_bubble_meta: ctk.CTkLabel | None = None
        self._is_recording = False

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

    # ── Tab navigation ─────────────────────────────────────────────────

    def _show_tab(self, key: str) -> None:
        """Switch to a different tab — rebuild content."""
        self._current_tab = key
        for w in self._tab_frame.winfo_children():
            w.destroy()

        p = Theme.get()
        if key == "general":
            self._build_tab_general(p)
        elif key == "history":
            self._build_tab_history(p)
        elif key == "metrics":
            self._build_tab_metrics(p)
        elif key == "settings":
            self.open_configure()
            self.sidebar.set_active("general")
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
        self.chat_frame = ctk.CTkScrollableFrame(self._tab_frame, fg_color=p.bg, corner_radius=0)
        self.chat_frame.grid(row=1, column=0, sticky="nsew", padx=0, pady=0)
        self.chat_frame.grid_columnconfigure(0, weight=1)
        self._tab_frame.grid_rowconfigure(1, weight=1)
        self._chat_row = 0

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

            # Text
            ctk.CTkLabel(card, text=text[:250] + ("..." if len(text) > 250 else ""),
                         font=ctk.CTkFont(family=_F, size=13),
                         text_color=p.text, wraplength=500,
                         justify="left", anchor="nw").grid(
                row=0, column=0, padx=14, pady=(10, 2), sticky="ew")

            # Meta
            meta_text = f"{ts[:16].replace('T', ' ')}  \u00b7  {words} words"
            ctk.CTkLabel(card, text=meta_text,
                         font=ctk.CTkFont(family=_M, size=10),
                         text_color=p.muted_dim).grid(
                row=1, column=0, padx=14, pady=(0, 10), sticky="w")

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
        c = ctk.CTkFrame(parent, fg_color=p.surface, corner_radius=12,
                          border_width=1, border_color=p.border)
        c.grid(row=0, column=col, padx=4, pady=4, sticky="nsew")
        c.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(c, text=label, font=ctk.CTkFont(family=_F, size=9, weight="bold"),
                     text_color=p.muted).grid(row=0, column=0, padx=12, pady=(12, 0), sticky="w")
        ctk.CTkLabel(c, text=value, font=ctk.CTkFont(family=_F, size=20, weight="bold"),
                     text_color=color).grid(row=1, column=0, padx=12, pady=(2, 12), sticky="w")

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
        ctk.CTkLabel(
            self.chat_frame, text=f"  {text}",
            font=ctk.CTkFont(family=_F, size=13, slant="italic"),
            text_color=p.muted, anchor="w",
        ).grid(row=self._chat_row, column=0, padx=60, pady=(12, 4), sticky="ew")
        self._chat_row += 1

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

        if self._live_bubble_meta is not None:
            self._live_bubble_meta.configure(text="  \u00b7  ".join(parts))

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
            # Create a fresh bubble for this recording session
            self._create_bubble()
            self.status_pill.configure(text=f"  {display}  ",
                                        fg_color=p.pill_rec_bg, text_color=p.pill_rec_fg)
        elif any(k in status for k in ("Processing", "Loading", "Improving")):
            self.status_pill.configure(text=f"  {display}  ",
                                        fg_color=p.pill_proc_bg, text_color=p.pill_proc_fg)
        elif "Error" in status or "Failed" in status:
            self._is_recording = False
            self.status_pill.configure(text=f"  {display}  ",
                                        fg_color=p.pill_error_bg, text_color=p.pill_error_fg)
        else:
            # Ready / Text Ready — finalize the bubble
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
