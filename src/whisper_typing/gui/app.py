"""Main GUI — Resizable, ChatGPT-style chat, 4K-ready typography."""

import json
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
        self.geometry("1100x750")
        self.minsize(700, 500)
        self.after(10, lambda: self.state("zoomed"))

        self.protocol("WM_DELETE_WINDOW", self.hide_window)

        self._side_open = False
        self._chat_row = 0

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

        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=0)
        self.grid_rowconfigure(0, weight=1)

        # ── Main column ────────────────────────────────────────────────
        main = ctk.CTkFrame(self, fg_color=p.bg, corner_radius=0)
        main.grid(row=0, column=0, sticky="nsew")
        main.grid_columnconfigure(0, weight=1)
        main.grid_rowconfigure(2, weight=1)

        # ── Top bar ────────────────────────────────────────────────────
        top = ctk.CTkFrame(main, fg_color=p.surface, corner_radius=0, height=50)
        top.grid(row=0, column=0, sticky="new")
        top.grid_columnconfigure(1, weight=1)
        top.grid_propagate(False)

        self.lbl_mascot = ctk.CTkLabel(top, text="\U0001f399",
                                        font=ctk.CTkFont(size=22), text_color=p.text)
        self.lbl_mascot.grid(row=0, column=0, padx=(16, 6), pady=10)

        ctk.CTkLabel(top, text="LeroLero",
                     font=ctk.CTkFont(family=_F, size=16, weight="bold"),
                     text_color=p.text).grid(row=0, column=0, padx=(46, 0), pady=10, sticky="w")

        self.status_pill = ctk.CTkLabel(
            top, text="  Starting  ",
            font=ctk.CTkFont(family=_F, size=12, weight="bold"),
            text_color=p.pill_start_fg, fg_color=p.pill_start_bg,
            corner_radius=12, height=28, width=140,
        )
        self.status_pill.grid(row=0, column=1, padx=10, pady=10)

        bf = ctk.CTkFrame(top, fg_color="transparent")
        bf.grid(row=0, column=2, padx=(0, 12), pady=10, sticky="e")

        _bs = dict(height=30, font=ctk.CTkFont(family=_F, size=12),
                   fg_color="transparent", hover_color=p.surface2,
                   text_color=p.muted, corner_radius=6)

        ctk.CTkButton(bf, text="\u263e" if Theme.is_dark() else "\u2600",
                       width=30, command=self._toggle_theme, **_bs).grid(row=0, column=0, padx=2)
        ctk.CTkButton(bf, text="\U0001f4ca Metrics", width=90,
                       command=self._toggle_side, **_bs).grid(row=0, column=1, padx=2)
        ctk.CTkButton(bf, text="\u2699 Settings", width=90,
                       command=self.open_configure, **_bs).grid(row=0, column=2, padx=2)
        ctk.CTkButton(bf, text="\u2015", width=30,
                       command=self.hide_window, **_bs).grid(row=0, column=3, padx=2)
        ctk.CTkButton(bf, text="\u2715", width=30, height=30,
                       font=ctk.CTkFont(size=12), fg_color="transparent",
                       hover_color=p.close_hover, text_color=p.close_text,
                       corner_radius=6, command=self.quit_app).grid(row=0, column=4, padx=2)

        # ── Metrics strip ──────────────────────────────────────────────
        ms = ctk.CTkFrame(main, fg_color=p.surface2, corner_radius=0, height=34)
        ms.grid(row=1, column=0, sticky="new")
        ms.grid_columnconfigure(4, weight=1)
        ms.grid_propagate(False)

        _mf = ctk.CTkFont(family=_F, size=12, weight="bold")
        self.lbl_m_words = ctk.CTkLabel(ms, text="\U0001f4ac 0 words", font=_mf, text_color=p.accent)
        self.lbl_m_words.grid(row=0, column=0, padx=(16, 12), pady=5, sticky="w")
        self.lbl_m_sessions = ctk.CTkLabel(ms, text="\U0001f3af 0 sessions", font=_mf, text_color=p.muted)
        self.lbl_m_sessions.grid(row=0, column=1, padx=12, pady=5, sticky="w")
        self.lbl_m_saved = ctk.CTkLabel(ms, text="\u23f1 0s saved", font=_mf, text_color=p.green)
        self.lbl_m_saved.grid(row=0, column=2, padx=12, pady=5, sticky="w")
        self.lbl_m_streak = ctk.CTkLabel(ms, text="", font=_mf, text_color=p.gold)
        self.lbl_m_streak.grid(row=0, column=3, padx=12, pady=5, sticky="w")

        self.lbl_info = ctk.CTkLabel(ms, text="", font=ctk.CTkFont(family=_M, size=10), text_color=p.muted)
        self.lbl_info.grid(row=0, column=4, padx=(0, 16), pady=5, sticky="e")

        # ── Chat area ──────────────────────────────────────────────────
        self.chat_frame = ctk.CTkScrollableFrame(main, fg_color=p.bg, corner_radius=0)
        self.chat_frame.grid(row=2, column=0, sticky="nsew", padx=0, pady=0)
        self.chat_frame.grid_columnconfigure(0, weight=1)
        self._chat_row = 0

        self._add_system_msg("Welcome to LeroLero! Press your hotkey to start speaking.")

        # ── Bottom log ─────────────────────────────────────────────────
        log_box = ctk.CTkFrame(main, fg_color=p.surface, corner_radius=0, height=70)
        log_box.grid(row=3, column=0, sticky="sew")
        log_box.grid_columnconfigure(0, weight=1)
        log_box.grid_rowconfigure(0, weight=1)
        log_box.grid_propagate(False)

        self.log_text = ctk.CTkTextbox(
            log_box, font=ctk.CTkFont(family=_M, size=11),
            fg_color=p.surface, text_color=p.log_text,
            border_width=0, corner_radius=0,
        )
        self.log_text.grid(row=0, column=0, sticky="nsew", padx=10, pady=4)
        self._set_readonly(self.log_text)

        # ── Side panel ─────────────────────────────────────────────────
        self.side_panel = ctk.CTkFrame(self, fg_color=p.surface, corner_radius=0, width=380)
        self._build_side(p)

    # ── Chat messages ──────────────────────────────────────────────────

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
        p = Theme.get()

        row = ctk.CTkFrame(self.chat_frame, fg_color="transparent")
        row.grid(row=self._chat_row, column=0, padx=(30, 80), pady=(8, 4), sticky="ew")
        row.grid_columnconfigure(1, weight=1)
        self._chat_row += 1

        # Avatar
        ctk.CTkLabel(
            row, text="\U0001f399", font=ctk.CTkFont(size=24),
            text_color=p.accent, width=40, height=40,
        ).grid(row=0, column=0, padx=(0, 12), pady=(6, 0), sticky="n")

        # Card
        card = ctk.CTkFrame(row, fg_color=p.surface, corner_radius=14,
                             border_width=1, border_color=p.border)
        card.grid(row=0, column=1, sticky="ew")
        card.grid_columnconfigure(0, weight=1)

        # Text label (will be updated live)
        self._live_bubble_text = ctk.CTkLabel(
            card, text="...",
            font=ctk.CTkFont(family=_F, size=16),
            text_color=p.text, wraplength=800,
            justify="left", anchor="nw",
        )
        self._live_bubble_text.grid(row=0, column=0, padx=18, pady=(14, 4), sticky="ew")

        # Meta label (updated when finalized)
        self._live_bubble_meta = ctk.CTkLabel(
            card, text="recording...",
            font=ctk.CTkFont(family=_F, size=11),
            text_color=p.muted, anchor="w",
        )
        self._live_bubble_meta.grid(row=1, column=0, padx=18, pady=(0, 12), sticky="w")

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

    # ── Side panel ─────────────────────────────────────────────────────

    def _build_side(self, p: object) -> None:
        for w in self.side_panel.winfo_children():
            w.destroy()

        self.side_panel.grid_columnconfigure(0, weight=1)
        self.side_panel.grid_rowconfigure(4, weight=1)

        hdr = ctk.CTkFrame(self.side_panel, fg_color="transparent")
        hdr.grid(row=0, column=0, padx=14, pady=(12, 4), sticky="ew")
        hdr.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(hdr, text="\U0001f4ca Metrics & History",
                     font=ctk.CTkFont(family=_F, size=15, weight="bold"),
                     text_color=p.text).grid(row=0, column=0, sticky="w")
        ctk.CTkButton(hdr, text="\u2715", width=28, height=28,
                       font=ctk.CTkFont(size=12), fg_color="transparent",
                       hover_color=p.surface2, text_color=p.muted,
                       corner_radius=6, command=self._toggle_side).grid(row=0, column=1)

        # Cards
        cards = ctk.CTkFrame(self.side_panel, fg_color="transparent")
        cards.grid(row=1, column=0, padx=12, pady=4, sticky="ew")
        cards.grid_columnconfigure((0, 1), weight=1)

        self._sp_time = self._sp_card(cards, 0, 0, "TIME SAVED", "0s", p.green, p)
        self._sp_words = self._sp_card(cards, 0, 1, "TOTAL WORDS", "0", p.accent, p)
        self._sp_avg = self._sp_card(cards, 1, 0, "AVG / SESSION", "0", p.muted, p)
        self._sp_proc = self._sp_card(cards, 1, 1, "AVG PROC", "0s", p.muted, p)

        # Bars
        ctk.CTkLabel(self.side_panel, text="  LAST 7 DAYS",
                     font=ctk.CTkFont(family=_F, size=10, weight="bold"),
                     text_color=p.accent).grid(row=2, column=0, padx=14, pady=(10, 2), sticky="w")

        self.sp_bars = ctk.CTkFrame(self.side_panel, fg_color=p.bg, corner_radius=8,
                                     border_width=1, border_color=p.border)
        self.sp_bars.grid(row=3, column=0, padx=12, pady=(0, 4), sticky="ew")
        self.sp_bars.grid_columnconfigure(1, weight=1)
        self._sp_bar_w: list = []

        # History
        ctk.CTkLabel(self.side_panel, text="  HISTORY",
                     font=ctk.CTkFont(family=_F, size=10, weight="bold"),
                     text_color=p.accent).grid(row=4, column=0, padx=14, pady=(8, 2), sticky="nw")

        self.sp_hist = ctk.CTkScrollableFrame(self.side_panel, fg_color=p.bg)
        self.sp_hist.grid(row=4, column=0, padx=10, pady=(24, 10), sticky="nsew")
        self.sp_hist.grid_columnconfigure(0, weight=1)

    @staticmethod
    def _sp_card(parent: ctk.CTkFrame, row: int, col: int,
                 label: str, value: str, color: str, p: object) -> ctk.CTkLabel:
        c = ctk.CTkFrame(parent, fg_color=p.surface2, corner_radius=10)
        c.grid(row=row, column=col, padx=3, pady=3, sticky="nsew")
        c.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(c, text=label, font=ctk.CTkFont(family=_F, size=9, weight="bold"),
                     text_color=p.muted).grid(row=0, column=0, padx=10, pady=(8, 0), sticky="w")
        v = ctk.CTkLabel(c, text=value, font=ctk.CTkFont(family=_F, size=17, weight="bold"),
                         text_color=color)
        v.grid(row=1, column=0, padx=10, pady=(0, 8), sticky="w")
        return v

    def _toggle_side(self) -> None:
        if self._side_open:
            self.side_panel.grid_forget()
            self._side_open = False
        else:
            self.side_panel.grid(row=0, column=1, sticky="nsew")
            self._side_open = True
            self._refresh_side()

    def _refresh_side(self) -> None:
        p = Theme.get()
        agg = aggregate()

        self._sp_time.configure(text=format_duration(agg.total_time_saved_s))
        self._sp_words.configure(text=f"{agg.total_words:,}")
        self._sp_avg.configure(text=f"{agg.avg_words_per_session:.0f}w")
        self._sp_proc.configure(text=format_duration(agg.avg_processing_s))

        # Bars
        for w in self._sp_bar_w:
            for item in w:
                item.destroy()
        self._sp_bar_w.clear()

        max_w = max(agg.words_by_day.values()) if agg.words_by_day else 1
        for i, (day, words) in enumerate(sorted(agg.words_by_day.items())):
            lbl = ctk.CTkLabel(self.sp_bars, text=day[5:],
                               font=ctk.CTkFont(family=_M, size=10), text_color=p.muted)
            lbl.grid(row=i, column=0, padx=(10, 4), pady=2, sticky="w")
            bar = ctk.CTkProgressBar(self.sp_bars, height=10, corner_radius=4,
                                     fg_color=p.border, progress_color=p.accent_dim)
            bar.grid(row=i, column=1, padx=2, pady=2, sticky="ew")
            bar.set(words / max(max_w, 1))
            n = ctk.CTkLabel(self.sp_bars, text=str(words),
                             font=ctk.CTkFont(family=_M, size=10), text_color=p.text)
            n.grid(row=i, column=2, padx=(4, 10), pady=2, sticky="e")
            self._sp_bar_w.append((lbl, bar, n))

        # History
        for w in self.sp_hist.winfo_children():
            w.destroy()

        hist_file = Path.cwd() / "history" / "transcripts.jsonl"
        if hist_file.exists():
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

            for idx, data in enumerate(reversed(entries[-25:])):
                ts = data.get("timestamp", "?")
                text = data.get("text", "")
                words = len(text.split()) if text.strip() else 0

                card = ctk.CTkFrame(self.sp_hist, fg_color=p.surface2, corner_radius=8)
                card.grid(row=idx, column=0, padx=2, pady=2, sticky="ew")
                card.grid_columnconfigure(0, weight=1)

                meta = ctk.CTkFrame(card, fg_color="transparent")
                meta.grid(row=0, column=0, padx=10, pady=(6, 0), sticky="ew")
                meta.grid_columnconfigure(0, weight=1)

                ctk.CTkLabel(meta, text=ts[:16].replace("T", " "),
                             font=ctk.CTkFont(family=_M, size=10),
                             text_color=p.muted).grid(row=0, column=0, sticky="w")
                ctk.CTkLabel(meta, text=f"{words}w",
                             font=ctk.CTkFont(family=_F, size=10),
                             text_color=p.accent).grid(row=0, column=1, sticky="e")

                ctk.CTkLabel(card, text=text[:180] + ("..." if len(text) > 180 else ""),
                             font=ctk.CTkFont(family=_F, size=12),
                             text_color=p.text, wraplength=320,
                             justify="left", anchor="w").grid(
                    row=1, column=0, padx=10, pady=(0, 6), sticky="w")

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
        self.lbl_m_words.configure(text=f"\U0001f4ac {agg.words_today:,} words")
        self.lbl_m_sessions.configure(text=f"\U0001f3af {agg.sessions_today} sessions")
        self.lbl_m_saved.configure(text=f"\u23f1 {format_duration(agg.time_saved_today_s)} saved")
        if agg.streak_days > 1:
            self.lbl_m_streak.configure(text=f"\U0001f525 {agg.streak_days}-day streak!")
        elif agg.streak_days == 1:
            self.lbl_m_streak.configure(text="\U0001f31f Day 1!")
        else:
            self.lbl_m_streak.configure(text="")

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
        self.lbl_mascot.configure(text=mascot(status))

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
