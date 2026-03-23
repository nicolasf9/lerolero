"""Settings dialog — no Gemini, offline only."""

import customtkinter as ctk
import sounddevice as sd

from lerolero.app_controller import WhisperAppController
from lerolero.constants import WHISPER_MODELS
from lerolero.gui.theme import Theme

_F = "Segoe UI"
_M = "Consolas"


def _input_devices() -> list[str]:
    devices = sd.query_devices()
    result = ["(System Default)"]
    for d in devices:
        if d["max_input_channels"] > 0:
            result.append(d["name"])
    return result


class ConfigurationWindow(ctk.CTkToplevel):
    """Settings dialog — fully offline."""

    def __init__(self, master: ctk.CTk, controller: WhisperAppController) -> None:  # noqa: PLR0915
        super().__init__(master)
        self.controller = controller
        p = Theme.get()

        self.title("Settings")
        self.geometry("520x580")
        self.minsize(440, 440)
        self.configure(fg_color=p.bg)
        self.transient(master)
        self.grab_set()

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        ctk.CTkLabel(
            self, text="\u2699 Settings",
            font=ctk.CTkFont(family=_F, size=20, weight="bold"), text_color=p.text,
        ).grid(row=0, column=0, padx=24, pady=(20, 8), sticky="w")

        form = ctk.CTkScrollableFrame(
            self, fg_color=p.surface, corner_radius=12,
            border_width=1, border_color=p.border,
        )
        form.grid(row=1, column=0, padx=20, pady=8, sticky="nsew")
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

        row = 0

        # ── AUDIO
        row = self._sec(form, "\U0001f3a4 AUDIO", row, p)

        ctk.CTkLabel(form, text="Microphone", **_lbl).grid(row=row, column=0, padx=12, pady=8, sticky="w")
        mic_list = _input_devices()
        self.cb_mic = ctk.CTkComboBox(form, values=mic_list, **_cmb)
        self.cb_mic.grid(row=row, column=1, padx=12, pady=8, sticky="ew")
        mic_name = cfg.get("microphone_name")
        self.cb_mic.set(mic_name if mic_name and mic_name in mic_list else "(System Default)")
        row += 1

        ctk.CTkLabel(form, text="Recording Mode", **_lbl).grid(row=row, column=0, padx=12, pady=8, sticky="w")
        self.cb_rec_mode = ctk.CTkComboBox(form, values=["toggle", "hold"], **_cmb)
        self.cb_rec_mode.grid(row=row, column=1, padx=12, pady=8, sticky="ew")
        self.cb_rec_mode.set(cfg.get("recording_mode", "toggle"))
        row += 1

        ctk.CTkLabel(form, text="Auto Stop", **_lbl).grid(row=row, column=0, padx=12, pady=8, sticky="w")
        self.sw_auto_stop = ctk.CTkSwitch(form, text="Stop on silence", **_swi)
        self.sw_auto_stop.grid(row=row, column=1, padx=12, pady=8, sticky="w")
        if cfg.get("auto_stop", True): self.sw_auto_stop.select()
        row += 1

        ctk.CTkLabel(form, text="Silence Delay (s)", **_lbl).grid(row=row, column=0, padx=12, pady=8, sticky="w")
        self.entry_delay = ctk.CTkEntry(form, **_ent)
        self.entry_delay.grid(row=row, column=1, padx=12, pady=8, sticky="ew")
        self.entry_delay.insert(0, str(cfg.get("auto_stop_delay", 1.5)))
        row += 1

        # ── MODEL
        row = self._sec(form, "\U0001f9e0 MODEL", row, p)

        ctk.CTkLabel(form, text="Whisper Model", **_lbl).grid(row=row, column=0, padx=12, pady=8, sticky="w")
        self.cb_model = ctk.CTkComboBox(form, values=[m[1] for m in WHISPER_MODELS], **_cmb)
        self.cb_model.grid(row=row, column=1, padx=12, pady=8, sticky="ew")
        self.cb_model.set(cfg.get("model", "openai/whisper-base"))
        row += 1

        ctk.CTkLabel(form, text="Language", **_lbl).grid(row=row, column=0, padx=12, pady=8, sticky="w")
        self.cb_lang = ctk.CTkComboBox(
            form, values=["auto", "pt", "en", "es", "fr", "de", "it", "ja", "zh", "ko"], **_cmb,
        )
        self.cb_lang.grid(row=row, column=1, padx=12, pady=8, sticky="ew")
        lang = cfg.get("language")
        self.cb_lang.set(lang if lang and lang.lower() != "auto" else "auto")
        row += 1

        ctk.CTkLabel(form, text="Device", **_lbl).grid(row=row, column=0, padx=12, pady=8, sticky="w")
        self.cb_device = ctk.CTkComboBox(
            form, values=["auto", "cpu", "GPU", "cuda", "openvino", "directml"], **_cmb,
        )
        self.cb_device.grid(row=row, column=1, padx=12, pady=8, sticky="ew")
        self.cb_device.set(cfg.get("device", "auto"))
        row += 1

        ctk.CTkLabel(form, text="Compute Type", **_lbl).grid(row=row, column=0, padx=12, pady=8, sticky="w")
        self.cb_compute = ctk.CTkComboBox(
            form, values=["auto", "float16", "int8", "int8_float16", "float32"], **_cmb,
        )
        self.cb_compute.grid(row=row, column=1, padx=12, pady=8, sticky="ew")
        self.cb_compute.set(cfg.get("compute_type", "auto"))
        row += 1

        ctk.CTkLabel(form, text="Model Cache Dir", **_lbl).grid(row=row, column=0, padx=12, pady=8, sticky="w")
        self.entry_cache = ctk.CTkEntry(form, placeholder_text="default", **_ent)
        self.entry_cache.grid(row=row, column=1, padx=12, pady=8, sticky="ew")
        cache = cfg.get("model_cache_dir")
        if cache: self.entry_cache.insert(0, cache)
        row += 1

        # ── HOTKEY
        row = self._sec(form, "\u2328 HOTKEY", row, p)

        ctk.CTkLabel(form, text="Record Hotkey", **_lbl).grid(row=row, column=0, padx=12, pady=8, sticky="w")
        self.entry_hotkey = ctk.CTkEntry(form, **_ent)
        self.entry_hotkey.grid(row=row, column=1, padx=12, pady=8, sticky="ew")
        self.entry_hotkey.insert(0, cfg.get("hotkey", "<f8>"))
        row += 1

        # ── TYPING
        row = self._sec(form, "\u270d TYPING", row, p)

        ctk.CTkLabel(form, text="Live Typing", **_lbl).grid(row=row, column=0, padx=12, pady=8, sticky="w")
        self.sw_live = ctk.CTkSwitch(form, text="Type while recording", **_swi)
        self.sw_live.grid(row=row, column=1, padx=12, pady=8, sticky="w")
        if cfg.get("live_typing", True): self.sw_live.select()
        row += 1

        ctk.CTkLabel(form, text="Auto Paste", **_lbl).grid(row=row, column=0, padx=12, pady=8, sticky="w")
        self.sw_paste = ctk.CTkSwitch(form, text="Paste on finish", **_swi)
        self.sw_paste.grid(row=row, column=1, padx=12, pady=8, sticky="w")
        if cfg.get("auto_paste", True): self.sw_paste.select()
        row += 1

        # ── GENERAL
        row = self._sec(form, "\u2699 GENERAL", row, p)

        ctk.CTkLabel(form, text="Theme", **_lbl).grid(row=row, column=0, padx=12, pady=8, sticky="w")
        self.cb_theme = ctk.CTkComboBox(form, values=["dark", "light"], **_cmb)
        self.cb_theme.grid(row=row, column=1, padx=12, pady=8, sticky="ew")
        self.cb_theme.set(cfg.get("theme", "dark"))
        row += 1

        for label, attr, cfg_key, text, default in [
            ("Show Overlay", "sw_overlay", "show_overlay", "Floating status", True),
            ("Refocus Window", "sw_refocus", "refocus_window", "Switch back after paste", True),
            ("Save History", "sw_history", "save_history", "Save transcriptions", True),
            ("Run at Startup", "sw_startup", "run_at_startup", "Windows auto-start", False),
            ("Debug Mode", "sw_debug", "debug", "Verbose logging", False),
        ]:
            ctk.CTkLabel(form, text=label, **_lbl).grid(row=row, column=0, padx=12, pady=8, sticky="w")
            sw = ctk.CTkSwitch(form, text=text, **_swi)
            sw.grid(row=row, column=1, padx=12, pady=8, sticky="w")
            if cfg.get(cfg_key, default):
                sw.select()
            setattr(self, attr, sw)
            row += 1

        # ── Buttons
        bb = ctk.CTkFrame(self, fg_color="transparent")
        bb.grid(row=2, column=0, padx=20, pady=(8, 16), sticky="ew")
        bb.grid_columnconfigure(0, weight=1)

        ctk.CTkButton(
            bb, text="Save", width=120, height=36,
            font=ctk.CTkFont(family=_F, size=13, weight="bold"),
            fg_color=p.accent_dim, hover_color=p.accent_hover,
            text_color="white", corner_radius=10, command=self._save,
        ).grid(row=0, column=0, padx=4, sticky="e")

        ctk.CTkButton(
            bb, text="Cancel", width=100, height=36,
            font=ctk.CTkFont(family=_F, size=13),
            fg_color="transparent", hover_color=p.surface2,
            text_color=p.muted, border_width=1, border_color=p.border,
            corner_radius=10, command=self.destroy,
        ).grid(row=0, column=1, padx=4, sticky="e")

    @staticmethod
    def _sec(parent: ctk.CTkFrame, title: str, row: int, p: object) -> int:
        ctk.CTkLabel(
            parent, text=title,
            font=ctk.CTkFont(family=_F, size=10, weight="bold"), text_color=p.accent,
        ).grid(row=row, column=0, columnspan=2, padx=12, pady=(16, 4), sticky="w")
        return row + 1

    def _save(self) -> None:
        mic = self.cb_mic.get()
        new_cfg = {
            "hotkey": self.entry_hotkey.get().strip() or "<f8>",
            "model": self.cb_model.get(),
            "language": self.cb_lang.get() if self.cb_lang.get() != "auto" else None,
            "device": self.cb_device.get(),
            "compute_type": self.cb_compute.get(),
            "microphone_name": mic if mic != "(System Default)" else None,
            "recording_mode": self.cb_rec_mode.get(),
            "auto_stop": bool(self.sw_auto_stop.get()),
            "auto_stop_delay": float(self.entry_delay.get() or 1.5),
            "live_typing": bool(self.sw_live.get()),
            "auto_paste": bool(self.sw_paste.get()),
            "theme": self.cb_theme.get(),
            "show_overlay": bool(self.sw_overlay.get()),
            "refocus_window": bool(self.sw_refocus.get()),
            "save_history": bool(self.sw_history.get()),
            "run_at_startup": bool(self.sw_startup.get()),
            "debug": bool(self.sw_debug.get()),
            "model_cache_dir": self.entry_cache.get().strip() or None,
        }
        self.controller.update_config(new_cfg)
        self.destroy()
