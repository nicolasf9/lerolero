"""pywebview bridge — exposes Python backend to React frontend."""

from __future__ import annotations

import ctypes
import json
import logging
import os
import sys
import threading
from dataclasses import asdict
from typing import Any

# pythonnet env vars (PYTHONNET_PYDLL, PYTHONNET_RUNTIME) are configured
# by the PyInstaller runtime hook (rthook_pythonnet.py) before this module loads.
import webview


def _set_windows_icon() -> None:
    """Set the Windows taskbar icon to LeroLero's icon instead of Python's."""
    if sys.platform != "win32":
        return
    try:
        app_id = "lerolero.lerolero.1.0"
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(app_id)
    except Exception:
        pass


def _apply_window_icon() -> None:
    """Force the LeroLero .ico onto the window title bar and taskbar via Win32 API."""
    if sys.platform != "win32":
        return
    try:
        from pathlib import Path

        ico = Path(__file__).parent / "assets" / "icon.ico"
        if not ico.exists():
            return

        user32 = ctypes.windll.user32
        # Load icon from file
        IMAGE_ICON = 1
        LR_LOADFROMFILE = 0x0010
        LR_DEFAULTSIZE = 0x0040

        hicon_big = user32.LoadImageW(
            0, str(ico), IMAGE_ICON, 48, 48, LR_LOADFROMFILE
        )
        hicon_small = user32.LoadImageW(
            0, str(ico), IMAGE_ICON, 16, 16, LR_LOADFROMFILE
        )

        if not hicon_big and not hicon_small:
            return

        # Find the pywebview window by title
        import time
        for _ in range(50):  # retry up to 5 seconds
            hwnd = user32.FindWindowW(None, "LeroLero")
            if hwnd:
                break
            time.sleep(0.1)

        if not hwnd:
            return

        WM_SETICON = 0x0080
        ICON_BIG = 1
        ICON_SMALL = 0

        if hicon_big:
            user32.SendMessageW(hwnd, WM_SETICON, ICON_BIG, hicon_big)
        if hicon_small:
            user32.SendMessageW(hwnd, WM_SETICON, ICON_SMALL, hicon_small)
    except Exception:
        pass

from lerolero.app_controller import WhisperAppController
from lerolero.constants import WHISPER_MODELS
from lerolero.gui.personality import greeting, status_text
from lerolero.metrics import aggregate, backfill_from_transcripts, format_duration
from lerolero.paths import get_data_dir, get_history_dir

logger = logging.getLogger(__name__)


class WebViewAPI:
    """Exposed to JavaScript as window.pywebview.api."""

    def __init__(self, controller: WhisperAppController) -> None:
        self.controller = controller
        self._window: webview.Window | None = None

    def set_window(self, window: webview.Window) -> None:
        self._window = window

    def _push_event(self, event: str, data: Any = None) -> None:
        """Push an event to the React frontend."""
        if self._window is None:
            return
        try:
            payload = json.dumps(data, ensure_ascii=False, default=str)
            self._window.evaluate_js(f"window.__lerolero_event('{event}', {payload})")
        except Exception:  # noqa: BLE001
            pass

    # ── Config ───────────────────────────────────────────────────────

    def get_config(self) -> dict:
        return dict(self.controller.config)

    def save_config(self, config: dict) -> None:
        old_model = self.controller.config.get("model")
        old_device = self.controller.config.get("device")
        old_lang = self.controller.config.get("language")
        self.controller.update_config(config)
        # Reinitialize transcriber if model/device/language changed
        new_model = self.controller.config.get("model")
        new_device = self.controller.config.get("device")
        new_lang = self.controller.config.get("language")
        if new_model and (new_model != old_model or new_device != old_device or new_lang != old_lang):
            self._push_event("status_change", {"status": "Loading"})
            def _reinit():
                success = self.controller.initialize_components()
                if success:
                    self.controller.start_listener()
                self._push_event("status_change", self.get_status())
                self._push_event("loading_done", True)
            threading.Thread(target=_reinit, daemon=True).start()

    def get_models(self) -> list[dict]:
        return [{"label": m[0], "value": m[1]} for m in WHISPER_MODELS]

    def get_input_devices(self) -> list[str]:
        try:
            import sounddevice as sd
            result = ["(System Default)"]
            for d in sd.query_devices():
                if d["max_input_channels"] > 0:
                    result.append(d["name"])
            return result
        except Exception:  # noqa: BLE001
            return ["(System Default)"]

    # ── Metrics ──────────────────────────────────────────────────────

    def get_metrics(self) -> dict:
        agg = aggregate()
        return {
            "total_sessions": agg.total_sessions,
            "total_words": agg.total_words,
            "total_time_saved_s": agg.total_time_saved_s,
            "avg_words_per_session": agg.avg_words_per_session,
            "avg_processing_s": agg.avg_processing_s,
            "sessions_today": agg.sessions_today,
            "words_today": agg.words_today,
            "time_saved_today_s": agg.time_saved_today_s,
            "streak_days": agg.streak_days,
            "words_by_day": dict(agg.words_by_day),
        }

    def get_history(self, query: str = "", app_filter: str = "") -> list[dict]:
        """Load filtered history entries with duration data."""
        hist_file = get_history_dir() / "transcripts.jsonl"
        metrics_file = get_history_dir() / "metrics.jsonl"

        entries = []
        if hist_file.exists():
            try:
                with hist_file.open("r", encoding="utf-8") as f:
                    for line in f:
                        try:
                            entries.append(json.loads(line))
                        except json.JSONDecodeError:
                            pass
            except OSError:
                pass

        # Load metrics for duration matching
        metrics_by_ts: dict[str, float] = {}
        if metrics_file.exists():
            try:
                with metrics_file.open("r", encoding="utf-8") as f:
                    for line in f:
                        try:
                            m = json.loads(line)
                            metrics_by_ts[m.get("timestamp", "")[:16]] = m.get("recording_duration_s", 0)
                        except json.JSONDecodeError:
                            pass
            except OSError:
                pass

        q = query.lower().strip()
        af = app_filter.lower().strip()
        result = []
        for e in entries:
            text = e.get("text", "")
            win = e.get("window", "")
            if not text.strip():
                continue
            if q and q not in text.lower():
                continue
            if af and af not in win.lower():
                continue

            ts = e.get("timestamp", "")
            # Prefer duration saved in entry, fallback to metrics match
            dur = e.get("duration", 0) or metrics_by_ts.get(ts[:16], 0)
            words = e.get("words", 0) or len(text.split())
            result.append({
                "text": text,
                "timestamp": ts,
                "window": win,
                "duration": dur,
                "words": words,
                "audio_file": e.get("audio_file", ""),
            })

        return result[-100:]  # Last 100

    def get_audio_base64(self, filename: str) -> str:
        """Return audio file as base64-encoded data URI for playback in browser."""
        import base64
        if not filename:
            return ""
        audio_dir = (get_history_dir() / "audio").resolve()
        audio_path = (audio_dir / filename).resolve()
        if not audio_path.is_relative_to(audio_dir):
            return ""
        if not audio_path.exists():
            return ""
        try:
            data = audio_path.read_bytes()
            b64 = base64.b64encode(data).decode("ascii")
            return f"data:audio/wav;base64,{b64}"
        except Exception:
            return ""

    def get_unique_apps(self) -> list[str]:
        hist_file = get_history_dir() / "transcripts.jsonl"
        apps: set[str] = set()
        if hist_file.exists():
            try:
                with hist_file.open("r", encoding="utf-8") as f:
                    for line in f:
                        try:
                            data = json.loads(line)
                            win = data.get("window", "")
                            if win:
                                short = win.split(" - ")[0].strip() if " - " in win else win
                                if short:
                                    apps.add(short)
                        except json.JSONDecodeError:
                            pass
            except OSError:
                pass
        return sorted(apps)[:20]

    # ── Updates ──────────────────────────────────────────────────────

    def check_update(self) -> dict:
        """Check for a new version on GitHub. Returns {} if up to date or offline."""
        try:
            from lerolero.updater import check_for_update, get_current_version
            result = check_for_update()
            if result:
                return result
            return {"current_version": get_current_version(), "up_to_date": True}
        except Exception:
            return {}

    def apply_update(self, download_url: str) -> dict:
        """Download and apply an update. Returns status dict."""
        try:
            from lerolero.updater import download_and_apply_update
            success = download_and_apply_update(download_url)
            if success:
                return {"status": "restarting"}
            return {"status": "manual", "message": "Atualize via: git pull && cd web && npm run build"}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    def get_version(self) -> str:
        from lerolero.updater import get_current_version
        return get_current_version()

    # ── Model Download ──────────────────────────────────────────────

    def download_model(self, model_id: str) -> dict:
        """Download a model in background, pushing progress events."""
        def _do_download() -> None:
            def progress_cb(msg: str, pct: int) -> None:
                self._push_event("model_download_progress", {
                    "message": msg, "percent": pct, "model": model_id,
                })

            try:
                from lerolero.runtime_setup import download_model, _add_deps_to_path
                _add_deps_to_path()
                progress_cb("Baixando modelo...", 5)
                success = download_model(model_id, progress_cb)
                if success:
                    self._push_event("model_download_done", {
                        "model": model_id, "success": True,
                    })
                else:
                    self._push_event("model_download_done", {
                        "model": model_id, "success": False,
                        "error": "Download falhou",
                    })
            except Exception as e:
                self._push_event("model_download_done", {
                    "model": model_id, "success": False, "error": str(e),
                })

        import threading
        threading.Thread(target=_do_download, daemon=True).start()
        return {"status": "started"}

    def is_onboarding_done(self) -> bool:
        """Check if onboarding has been completed AND a model is set."""
        cfg = self.controller.config
        return bool(cfg.get("_onboarding_done", False)) and bool(cfg.get("model"))

    def complete_onboarding(self, config: dict) -> dict:
        """Mark onboarding as complete and apply initial settings."""
        if not config.get("model"):
            return {"error": "Nenhum modelo selecionado"}
        from lerolero.updater import get_current_version
        config["_onboarding_done"] = True
        config["_app_version"] = get_current_version()
        self.controller.update_config(config)
        return {"ok": True}

    def reinitialize(self) -> dict:
        """Re-initialize components (after model download)."""
        def _do_init() -> None:
            try:
                success = self.controller.initialize_components()
            except Exception as e:
                logger.exception("reinitialize failed")
                success = False
                self.controller._last_init_error = str(e)

            full_status = self.get_status()
            if success:
                self.controller.start_listener()
                self._push_event("status_change", full_status)
            else:
                error_msg = getattr(self.controller, "_last_init_error", "Unknown error")
                full_status["status"] = "Error"
                full_status["error_detail"] = error_msg
                self._push_event("status_change", full_status)
                self._push_event("log", {"message": f"Erro ao inicializar: {error_msg}"})
            self._push_event("loading_done", True)

        import threading
        threading.Thread(target=_do_init, daemon=True).start()
        return {"status": "started"}

    # ── Status ───────────────────────────────────────────────────────

    def get_status(self) -> dict:
        cfg = self.controller.config
        backend = "detecting..."
        if self.controller.transcriber:
            backend = self.controller.transcriber.backend
        return {
            "status": "Ready" if not self.controller.is_processing else "Processing",
            "is_recording": bool(self.controller.recorder and self.controller.recorder.recording),
            "is_processing": self.controller.is_processing,
            "pending_text": self.controller.pending_text,
            "model": cfg.get("model") or "none",
            "backend": backend,
            "hotkey": cfg.get("hotkey", "<f9>"),
        }

    def toggle_pause(self) -> None:
        self.controller.toggle_pause()

    def get_personality(self) -> dict:
        return {"greeting": greeting()}


def start_webview_app(controller: WhisperAppController) -> None:
    """Launch the pywebview window with the React frontend."""
    from pathlib import Path

    api = WebViewAPI(controller)

    # Wire controller callbacks to push events to frontend
    def _on_status_change(status: str) -> None:
        api._push_event("status_change", {
            "status": status,
            "is_recording": "Recording" in status,
            "is_processing": "Processing" in status or "Loading" in status,
        })

    def _on_log(msg: str) -> None:
        api._push_event("log", {"message": msg})

    def _on_preview_update(text: str, _improved: str | None) -> None:
        api._push_event("preview_update", {"text": text})

    controller.on_status_change = _on_status_change
    controller.on_log = _on_log
    controller.on_preview_update = _on_preview_update

    # Set Windows taskbar icon
    _set_windows_icon()

    # Find the built React app — check multiple locations
    _candidates = [
        Path(__file__).parent.parent.parent / "web" / "dist" / "index.html",  # dev: src/../web/dist
        Path(__file__).parent / "web_dist" / "index.html",  # frozen exe: _internal/lerolero/web_dist
        Path(__file__).parent / "web" / "dist" / "index.html",  # alt layout
    ]
    if getattr(sys, "frozen", False):
        _candidates.insert(0, Path(sys.executable).parent / "_internal" / "lerolero" / "web_dist" / "index.html")
    web_dist = next((p for p in _candidates if p.exists()), _candidates[0])

    # Find icon for window
    icon_path = Path(__file__).parent / "assets" / "icon.ico"
    if not icon_path.exists():
        icon_path = Path(__file__).parent / "assets" / "icon.png"

    window = webview.create_window(
        "LeroLero",
        str(web_dist) if web_dist.exists() else "https://localhost",
        js_api=api,
        width=960, height=640,
        min_size=(700, 500),
    )
    api.set_window(window)

    # Intercept window close: hide to tray instead of destroying
    def _on_closing() -> bool:
        """Return False to prevent window destruction; hide it instead."""
        window.hide()
        return False  # Prevent actual close

    window.events.closing += _on_closing

    # Initialize controller in background
    def _init() -> None:
        n = backfill_from_transcripts()
        if n > 0:
            api._push_event("log", {"message": f"Migrated {n} legacy transcripts."})

        # Always setup tray first so user can exit
        controller.setup_tray(on_open=lambda: window.show())

        # Skip auto-init if onboarding not done or no model selected
        if not controller.config.get("_onboarding_done", False) or not controller.config.get("model"):
            api._push_event("loading_done", True)
            return

        success = controller.initialize_components()
        if success:
            controller.start_listener()
            api._push_event("status_change", api.get_status())
        else:
            api._push_event("status_change", {"status": "Error"})
        api._push_event("loading_done", True)

    def _on_loaded() -> None:
        # Apply icon to window title bar + taskbar
        threading.Thread(target=_apply_window_icon, daemon=True).start()
        threading.Thread(target=_init, daemon=True).start()

    # Wire recording_done event
    original_set_status = controller.set_status

    def _enhanced_set_status(status: str) -> None:
        original_set_status(status)
        if "Ready" in status or "Text Ready" in status:
            api._push_event("recording_done", True)

    controller.set_status = _enhanced_set_status

    # Force EdgeChromium (WebView2) on Windows via pythonnet
    gui_backend = "edgechromium" if sys.platform == "win32" else None
    webview.start(func=_on_loaded, debug=False, gui=gui_backend)
