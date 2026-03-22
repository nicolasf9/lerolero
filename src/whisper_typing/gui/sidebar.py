"""Animated sidebar navigation — inspired by anime-navbar."""

from __future__ import annotations

import math
from collections.abc import Callable
from pathlib import Path

import customtkinter as ctk

from whisper_typing.gui.theme import Theme

_W = 220
_ITEM_H = 44
_PAD = 8
_ANIM_STEPS = 10
_ANIM_MS = 12


class SidebarItem:
    """A single navigation item."""

    __slots__ = ("key", "icon", "label")

    def __init__(self, key: str, icon: str, label: str) -> None:
        self.key = key
        self.icon = icon
        self.label = label


TABS = [
    SidebarItem("general", "\U0001f399", "Geral"),
    SidebarItem("metrics", "\U0001f4ca", "Métricas"),
    SidebarItem("settings", "\u2699", "Configurações"),
    SidebarItem("about", "\u2139", "Sobre"),
]


class Sidebar(ctk.CTkFrame):
    """Vertical sidebar with animated active indicator."""

    def __init__(
        self,
        master: ctk.CTk,
        on_tab_change: Callable[[str], None],
        **kwargs: object,
    ) -> None:
        p = Theme.get()
        super().__init__(master, width=_W, fg_color=p.surface, corner_radius=0, **kwargs)
        self.grid_propagate(False)
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(len(TABS) + 1, weight=1)  # spacer before brand

        self._on_tab_change = on_tab_change
        self._active = TABS[0].key
        self._item_frames: dict[str, ctk.CTkFrame] = {}
        self._item_labels: dict[str, ctk.CTkLabel] = {}
        self._indicator: ctk.CTkFrame | None = None
        self._indicator_y: float = 0
        self._target_y: float = 0
        self._anim_step: int = 0
        self._glow_tick: int = 0

        self._build(p)
        self._start_glow_pulse()

    def _build(self, p: object) -> None:
        _F = "Segoe UI"

        # Items
        for i, tab in enumerate(TABS):
            item = ctk.CTkFrame(self, fg_color="transparent", height=_ITEM_H, cursor="hand2")
            item.grid(row=i, column=0, padx=_PAD, pady=2, sticky="ew")
            item.grid_propagate(False)
            item.grid_columnconfigure(1, weight=1)

            icon_lbl = ctk.CTkLabel(
                item, text=tab.icon, font=ctk.CTkFont(size=18),
                text_color=p.accent if tab.key == self._active else p.muted,
                width=32,
            )
            icon_lbl.grid(row=0, column=0, padx=(12, 4), pady=8)

            text_lbl = ctk.CTkLabel(
                item, text=tab.label,
                font=ctk.CTkFont(family=_F, size=13, weight="bold" if tab.key == self._active else "normal"),
                text_color=p.text if tab.key == self._active else p.muted,
                anchor="w",
            )
            text_lbl.grid(row=0, column=1, padx=(0, 8), pady=8, sticky="w")

            self._item_frames[tab.key] = item
            self._item_labels[tab.key] = text_lbl

            # Click binding
            for widget in (item, icon_lbl, text_lbl):
                widget.bind("<Button-1>", lambda e, k=tab.key: self._select(k))
                widget.bind("<Enter>", lambda e, k=tab.key: self._on_hover(k, True))
                widget.bind("<Leave>", lambda e, k=tab.key: self._on_hover(k, False))

        # Active indicator (glow behind active item)
        self._indicator = ctk.CTkFrame(
            self, fg_color=p.accent_dim, corner_radius=10,
            height=_ITEM_H - 4, width=_W - 2 * _PAD,
        )
        self._indicator.place(x=_PAD, y=_PAD + 2)
        self._indicator.lower()  # behind items
        self._indicator_y = _PAD + 2

        # Brand at bottom
        brand = ctk.CTkFrame(self, fg_color="transparent")
        brand.grid(row=len(TABS) + 2, column=0, padx=12, pady=(0, 12), sticky="sew")
        brand.grid_columnconfigure(0, weight=1)

        # Try to load icon
        icon_path = Path(__file__).parent.parent / "assets" / "icon.png"
        if icon_path.exists():
            try:
                from PIL import Image
                img = Image.open(icon_path)
                self._brand_icon = ctk.CTkImage(light_image=img, dark_image=img, size=(24, 24))
                ctk.CTkLabel(brand, text="", image=self._brand_icon, width=24).pack(
                    side="left", padx=(0, 6))
            except Exception:  # noqa: BLE001
                pass

        try:
            _brand_font = "Modak"
            import ctypes
            font_path = Path(__file__).parent.parent / "assets" / "Modak-Regular.ttf"
            if font_path.exists():
                ctypes.windll.gdi32.AddFontResourceExW(str(font_path), 0x10, 0)
        except Exception:  # noqa: BLE001
            _brand_font = "Segoe UI"

        ctk.CTkLabel(
            brand, text="LeroLero",
            font=ctk.CTkFont(family=_brand_font, size=16),
            text_color=p.muted,
        ).pack(side="left")

        ctk.CTkLabel(
            brand, text="  v1.0",
            font=ctk.CTkFont(family="Consolas", size=9),
            text_color=p.muted_dim,
        ).pack(side="left", pady=(4, 0))

    def _select(self, key: str) -> None:
        if key == self._active:
            return
        old = self._active
        self._active = key

        p = Theme.get()

        # Update text styles
        for tab in TABS:
            is_active = tab.key == key
            lbl = self._item_labels[tab.key]
            lbl.configure(
                text_color=p.text if is_active else p.muted,
                font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold" if is_active else "normal"),
            )
            # Update icon color
            for child in self._item_frames[tab.key].winfo_children():
                if isinstance(child, ctk.CTkLabel) and len(child.cget("text")) <= 2:
                    child.configure(text_color=p.accent if is_active else p.muted)

        # Animate indicator to new position
        idx = next(i for i, t in enumerate(TABS) if t.key == key)
        # Each item is at row idx, with pady=2, so Y = _PAD + idx * (_ITEM_H + 4) + 2
        self._target_y = _PAD + idx * (_ITEM_H + 4) + 2
        self._anim_step = 0
        self._animate_indicator()

        self._on_tab_change(key)

    def _animate_indicator(self) -> None:
        if self._indicator is None:
            return
        self._anim_step += 1
        t = self._anim_step / _ANIM_STEPS
        # Ease out cubic
        t = 1 - (1 - t) ** 3
        current_y = self._indicator_y + (self._target_y - self._indicator_y) * t
        self._indicator.place(x=_PAD, y=current_y)

        if self._anim_step < _ANIM_STEPS:
            self.after(_ANIM_MS, self._animate_indicator)
        else:
            self._indicator_y = self._target_y

    def _on_hover(self, key: str, entering: bool) -> None:
        if key == self._active:
            return
        p = Theme.get()
        frame = self._item_frames[key]
        frame.configure(fg_color=p.surface2 if entering else "transparent")

    def _start_glow_pulse(self) -> None:
        """Subtle opacity pulse on active indicator (like anime-navbar)."""
        if self._indicator is None:
            return
        self._glow_tick += 1
        p = Theme.get()
        # Pulse between accent_dim and a slightly brighter version
        phase = (math.sin(self._glow_tick * 0.15) + 1) / 2  # 0..1
        # Simple: alternate between accent_dim and accent for the indicator
        if phase > 0.6:
            self._indicator.configure(fg_color=p.accent)
        else:
            self._indicator.configure(fg_color=p.accent_dim)
        self.after(80, self._start_glow_pulse)

    def set_active(self, key: str) -> None:
        """Programmatically set the active tab."""
        self._select(key)

    def refresh_theme(self) -> None:
        """Rebuild after theme change."""
        p = Theme.get()
        self.configure(fg_color=p.surface)
        if self._indicator:
            self._indicator.configure(fg_color=p.accent_dim)
