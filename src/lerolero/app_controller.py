"""Main application controller for whisper-typing — 100% offline."""

import contextlib
import json
import logging
import os
import subprocess
import sys
import threading
import time
from collections.abc import Callable
from datetime import UTC, datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any

import pyperclip
import pystray
import sounddevice as sd
from PIL import Image
from pynput import keyboard

from lerolero.audio_capture import AudioRecorder
from lerolero.context_prompts import get_prompt_for_process
from lerolero.metrics import SessionMetric, save_metric
from lerolero.overlay_container import StatusOverlay
from lerolero.paths import get_config_path, get_data_dir, get_history_dir
from lerolero.text_cleaner import clean_transcript
from lerolero.transcriber import Transcriber
from lerolero.transcriber_parakeet import ParakeetTranscriber, is_available as parakeet_available
from lerolero.window_manager import WindowManager

logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    import numpy as np


DEFAULT_CONFIG: dict[str, Any] = {
    "hotkey": "<f8>",
    "model": None,
    "language": None,
    "microphone_name": None,
    "device": "auto",
    "compute_type": "auto",
    "debug": False,
    "typing_wpm": 40,
    "refocus_window": True,
    "model_cache_dir": None,
    "auto_stop": True,
    "auto_paste": True,
    "auto_stop_delay": 1.5,
    "save_history": True,
    "run_at_startup": False,
    "recording_mode": "toggle",
    "show_overlay": True,
    "live_typing": True,
    "theme": "dark",
    "accent_color": "#a78bfa",
}


def load_config() -> dict[str, Any]:
    """Load configuration from AppData JSON file."""
    path = get_config_path()
    if path.exists():
        try:
            with path.open() as f:
                return json.load(f)
        except Exception:  # noqa: BLE001, S110
            logger.debug("Failed to load config from %s", path, exc_info=True)
    return {}


def save_config(config: dict[str, Any]) -> None:
    """Save configuration to AppData JSON file."""
    try:
        save_data = config.copy()
        for key in ("gemini_api_key", "gemini_model", "gemini_prompt", "improve_hotkey"):
            save_data.pop(key, None)
        with get_config_path().open("w") as f:
            json.dump(save_data, f, indent=4)
    except Exception:  # noqa: BLE001, S110
        logger.debug("Failed to save config", exc_info=True)


class WhisperAppController:
    """Controller — fully offline, no AI APIs."""

    def __init__(self) -> None:
        self.config: dict[str, Any] = {}
        self.recorder: AudioRecorder | None = None
        self.transcriber: Transcriber | None = None
        self.listener: keyboard.GlobalHotKeys | None = None
        self.window_manager: WindowManager = WindowManager()
        self.target_window_handle: Any | None = None

        self.is_processing: bool = False
        self.pending_text: str | None = None
        self.paused: bool = False

        self.current_model_id: str | None = None
        self.current_language: str | None = None
        self.current_mic_index: int | None = None
        self.current_device: str | None = None
        self.current_compute_type: str | None = None

        self.stop_live_transcribe: threading.Event = threading.Event()
        self.live_transcribe_thread: threading.Thread | None = None
        self._stop_lock = threading.Lock()

        self._stop_watchdog: threading.Event = threading.Event()
        self._watchdog_thread: threading.Thread | None = None

        self.tray_icon: pystray.Icon | None = None
        self._tray_thread: threading.Thread | None = None

        self.overlay: StatusOverlay = StatusOverlay(
            audio_level_fn=self._get_audio_level,
            on_copy=self._overlay_copy,
            on_cancel=self._overlay_cancel,
        )

        self.on_status_change: Callable[[str], None] | None = None
        self.on_log: Callable[[str], None] | None = None
        self.on_preview_update: Callable[[str, str | None], None] | None = None

        self.is_recording_starting: bool = False
        self.recording_start_time: float = 0.0
        self.live_typed_text: str = ""
        self.last_target_window_title: str = ""
        self.last_target_process: str = ""
        self.last_recording_duration: float = 0.0

    def _overlay_copy(self) -> None:
        """Copy the last transcription to clipboard (triggered from overlay)."""
        if self.pending_text:
            pyperclip.copy(self.pending_text)
            self.log("Copied to clipboard.")

    def _overlay_cancel(self) -> None:
        """Cancel the pending text injection (triggered from overlay)."""
        self.pending_text = None
        self.log("Transcription cancelled.")
        self.set_status("Ready")

    def _get_audio_level(self) -> float:
        """Return current mic RMS level (0.0-1.0) for waveform visualization."""
        if self.recorder and self.recorder.recording:
            return self.recorder.current_level
        return 0.0

    def log(self, message: str) -> None:
        if self.on_log:
            self.on_log(message)

    def set_status(self, status: str) -> None:
        self.log(f"Status changed to: {status}")
        if self.on_status_change:
            self.on_status_change(status)
        if self.config.get("show_overlay", True):
            self.overlay.update_status(status)

    def load_configuration(self, args: Any = None) -> None:  # noqa: ANN401
        self.config = DEFAULT_CONFIG.copy()
        file_config = load_config()
        self.config.update(file_config)

        if args:
            if args.hotkey:
                self.config["hotkey"] = args.hotkey
            if args.model:
                self.config["model"] = args.model
            if args.language:
                self.config["language"] = args.language

    def get_mic_index_from_config(self) -> int | None:
        mic_name = self.config.get("microphone_name")
        if not mic_name:
            return None
        devices = sd.query_devices()
        for i, dev in enumerate(devices):
            if dev["max_input_channels"] > 0 and mic_name in dev["name"]:
                return i
        return None

    def list_input_devices(self) -> list[tuple[int, str]]:
        return AudioRecorder.list_devices()

    def update_config(self, new_config: dict[str, Any]) -> None:
        self.config.update(new_config)
        save_config(self.config)
        self._update_startup_shortcut()
        self.log("Configuration saved.")

    def initialize_components(self) -> bool:
        self.log("Initializing components...")
        mic_index = self.get_mic_index_from_config()
        self.current_mic_index = mic_index

        try:
            # No model selected yet — skip transcriber init (onboarding will set it)
            if not self.config.get("model"):
                self.log("No model configured — waiting for model selection.")
                self.recorder = AudioRecorder(device_index=self.current_mic_index)
                return True

            if (
                not self.transcriber
                or self.current_model_id != self.config["model"]
                or self.current_language != self.config["language"]
                or self.current_device != self.config.get("device", "auto")
                or self.current_compute_type != self.config.get("compute_type", "auto")
            ):
                model_id = self.config["model"]
                device = self.config.get("device", "auto")
                compute_type = self.config.get("compute_type", "auto")

                # Use Parakeet if user selected a parakeet model
                if model_id.startswith("parakeet") or "parakeet" in model_id:
                    if not parakeet_available():
                        self.log("Instalando Parakeet automaticamente...")
                        try:
                            from lerolero.runtime_setup import _get_deps_dir, _get_embedded_python, _pip_install
                            python_exe = _get_embedded_python()
                            if python_exe:
                                deps_dir = _get_deps_dir()
                                deps_dir.mkdir(parents=True, exist_ok=True)
                                success, error = _pip_install(python_exe, ["onnx-asr"], deps_dir)
                                if success:
                                    self.log("Parakeet instalado com sucesso!")
                                else:
                                    raise RuntimeError(error)
                            else:
                                raise RuntimeError("Embedded Python not found")
                        except Exception as e:
                            self.log(f"Falha ao instalar Parakeet: {e}")
                            self.log("Voltando para Whisper...")
                            model_id = "openai/whisper-small"

                    if parakeet_available():
                        self.log(f"Carregando Parakeet ({model_id})...")
                        self.transcriber = ParakeetTranscriber(
                            model_id=model_id,
                            language=self.config["language"],
                            device=device,
                            download_root=self.config.get("model_cache_dir"),
                        )
                    else:
                        self.log("Parakeet indisponível. Usando Whisper...")
                        model_id = "openai/whisper-small"
                        self.transcriber = Transcriber(
                            model_id=model_id,
                            language=self.config["language"],
                            device=device,
                            compute_type=compute_type,
                            download_root=self.config.get("model_cache_dir"),
                        )
                else:
                    self.log(f"Loading Whisper ({model_id})...")
                    self.transcriber = Transcriber(
                        model_id=model_id,
                        language=self.config["language"],
                        device=device,
                        compute_type=compute_type,
                        download_root=self.config.get("model_cache_dir"),
                    )
                self.current_model_id = self.config["model"]
                self.current_language = self.config["language"]
                self.current_device = device
                self.current_compute_type = compute_type

            self.recorder = AudioRecorder(device_index=self.current_mic_index)

            self.log("Components initialized.")
            if self.config.get("show_overlay", True):
                self.overlay.start()

            self._stop_watchdog.clear()
            self._watchdog_thread = threading.Thread(
                target=self._listener_watchdog_loop, daemon=True,
            )
            self._watchdog_thread.start()
        except Exception as e:
            self.log(f"Error initializing components: {e}")
            logger.exception("Component initialization error")
            self._last_init_error = str(e)
            return False
        else:
            return True

    def start_listener(self) -> None:
        if self.listener:
            self.listener.stop()

        mode = self.config.get("recording_mode", "toggle")
        hotkey_str = self.config.get("hotkey", "<f8>")

        try:
            if mode == "hold":
                hotkey = keyboard.HotKey(
                    keyboard.HotKey.parse(hotkey_str), self._start_recording,
                )

                def _on_press(key: object) -> None:
                    hotkey.press(self.listener.canonical(key))

                def _on_release(key: object) -> None:
                    canonical_key = self.listener.canonical(key)
                    keys_list = hotkey.__dict__.get("_keys", [])
                    if any(
                        k == canonical_key for k in keys_list
                    ) and self.recorder and self.recorder.recording:
                        self._stop_recording()
                    hotkey.release(canonical_key)

                self.listener = keyboard.Listener(
                    on_press=_on_press, on_release=_on_release,
                )
            else:
                self.listener = keyboard.GlobalHotKeys(
                    {hotkey_str: self.on_record_toggle},
                )

            self.listener.start()
            self.log(f"Hotkey registered ({mode} mode). Press {hotkey_str} to record.")
            self.set_status("Ready")
        except ValueError as e:
            self.log(f"Invalid hotkey format: {e}")
            self.set_status("Hotkey Error")

    def stop(self) -> None:
        if self.listener:
            self.listener.stop()
            self.listener = None

    def shutdown(self) -> None:
        self._stop_watchdog.set()
        if self.tray_icon:
            self.tray_icon.stop()
        self.stop()
        if self.overlay:
            self.overlay.stop()

    def toggle_pause(self) -> None:
        self.paused = not self.paused
        if self.paused:
            self.set_status("Paused")
            self.log("App paused.")
        else:
            self.set_status("Ready")
            self.log("App resumed.")

    def on_record_toggle(self) -> None:
        if self.paused or self.is_processing or not self.recorder:
            return
        if self.recorder.recording:
            self._stop_recording()
        else:
            self._start_recording()

    def _start_recording(self) -> None:
        if self.config.get("refocus_window", True) and self.window_manager:
            active_window = self.window_manager.get_active_window()
            if active_window and "LeroLero" not in active_window.title:
                self.target_window_handle = active_window
                self.last_target_window_title = active_window.title
                self.last_target_process = WindowManager.get_process_name(active_window) or ""
            else:
                self.target_window_handle = None
                self.last_target_window_title = ""
                self.last_target_process = ""
        else:
            self.target_window_handle = None
            self.last_target_window_title = ""
            self.last_target_process = ""

        self.pending_text = None
        self.live_typed_text = ""
        if self.on_preview_update:
            self.on_preview_update("", None)

        if self.recorder:
            self.recorder.start()
        self.recording_start_time = time.time()
        self.overlay.set_target_app(self.last_target_window_title)
        self.set_status("Recording")
        self.log("Recording started...")
        self._play_beep(660, 150)

        self.stop_live_transcribe.clear()
        self.live_transcribe_thread = threading.Thread(
            target=self._live_transcription_loop, daemon=True,
        )
        self.live_transcribe_thread.start()

    def _stop_recording(self) -> None:
        if not self._stop_lock.acquire(blocking=False):
            return

        try:
            self.log("Stopping recording...")
            self.set_status("Processing")
            self._play_beep(440, 150)

            self.stop_live_transcribe.set()
            if (
                self.live_transcribe_thread
                and threading.current_thread() != self.live_transcribe_thread
            ):
                self.live_transcribe_thread.join()

            if not self.recorder:
                return

            audio_data = self.recorder.stop()
            if audio_data is not None:
                self.is_processing = True
                threading.Thread(
                    target=self._finish_transcription,
                    args=(audio_data,), daemon=True,
                ).start()
            else:
                self.log("No audio data.")
                self.set_status("Ready")
        finally:
            self._stop_lock.release()

    def _update_startup_shortcut(self) -> None:
        run_at_startup = self.config.get("run_at_startup", False)
        try:
            from lerolero.platform import get_platform
            get_platform().update_startup_shortcut(run_at_startup)
        except Exception as e:
            self.log(f"Error updating startup shortcut: {e}")
            logger.exception("Error updating startup shortcut")

    def _finish_transcription(self, audio_data: "np.ndarray") -> None:
        proc_start = time.time()
        try:
            # Grab a local reference to avoid race condition if model is
            # changed mid-transcription (reinitialize sets self.transcriber to a new instance)
            transcriber = self.transcriber
            if transcriber:
                ctx_prompt = get_prompt_for_process(self.last_target_process)
                task = self.config.get("whisper_task", "transcribe")
                text = transcriber.transcribe(audio_data, initial_prompt=ctx_prompt, task=task)
                if text and self.config.get("clean_transcription", True):
                    text = clean_transcript(text)
                proc_duration = time.time() - proc_start
                rec_duration = proc_start - self.recording_start_time

                if text:
                    self.pending_text = text
                    self.last_recording_duration = rec_duration
                    self.log(f"Transcription: {text}")
                    audio_filename = None
                    if self.config.get("save_audio", False):
                        audio_filename = self._save_audio(audio_data)
                    self._save_to_history(text, audio_file=audio_filename)
                    self._save_metric(text, rec_duration, proc_duration)
                    if self.on_preview_update:
                        self.on_preview_update(text, None)
                    self.set_status("Text Ready")

                    if self.config.get("live_typing", True):
                        self._live_type_diff(text)
                    elif self.config.get("auto_paste", True):
                        self._auto_paste(text)
                else:
                    self.log("No speech detected.")
                    if not self.pending_text:
                        self.set_status("Ready")
        except Exception as e:
            self.log(f"Transcription error: {e}")
            logger.exception("Transcription error")
            self.set_status("Error")
            # Auto-recover to Ready after 3 seconds
            threading.Timer(3.0, lambda: self.set_status("Ready")).start()
        finally:
            self.is_processing = False

    def _save_to_history(self, text: str, audio_file: str | None = None) -> None:
        if not self.config.get("save_history", True):
            return
        try:
            history_dir = get_history_dir()
            history_file = history_dir / "transcripts.jsonl"
            words = len(text.split()) if text else 0
            entry = {
                "timestamp": datetime.now(UTC).isoformat(),
                "text": text,
                "window": self.last_target_window_title or "",
                "duration": round(self.last_recording_duration, 1),
                "words": words,
            }
            if audio_file:
                entry["audio_file"] = audio_file
            with history_file.open("a", encoding="utf-8") as f:
                f.write(json.dumps(entry, ensure_ascii=False) + "\n")
        except Exception as e:
            self.log(f"Error saving history: {e}")

    def _save_audio(self, audio_data: "np.ndarray") -> str | None:
        """Save audio as .wav file alongside the transcript. Returns filename."""
        try:
            import scipy.io.wavfile as wavfile
            audio_dir = get_history_dir() / "audio"
            audio_dir.mkdir(exist_ok=True)
            ts = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")
            filename = f"{ts}.wav"
            filepath = audio_dir / filename
            wavfile.write(str(filepath), 16000, audio_data)
            self.log(f"Audio saved: {filename}")
            return filename
        except Exception as e:
            self.log(f"Audio save error: {e}")
            return None

    def _save_metric(self, text: str, rec_duration: float, proc_duration: float) -> None:
        words = len(text.split()) if text else 0
        metric = SessionMetric(
            timestamp=datetime.now(UTC).isoformat(),
            words=words, chars=len(text),
            recording_duration_s=round(rec_duration, 2),
            processing_duration_s=round(proc_duration, 2),
            model=self.config.get("model", ""),
            device=self.config.get("device", "auto"),
        )
        save_metric(metric)
        self.log(f"Session: {words} words, rec {rec_duration:.1f}s, proc {proc_duration:.1f}s")

    def _live_transcription_loop(self) -> None:
        last_transcription_time = time.time()
        while not self.stop_live_transcribe.is_set():
            time.sleep(0.5)
            if time.time() - last_transcription_time < 0.8:
                continue
            if not self.recorder or not self.transcriber:
                continue

            audio_data = self.recorder.get_current_data()
            if audio_data is not None and len(audio_data) > 8000:
                try:
                    ctx_prompt = get_prompt_for_process(self.last_target_process)
                    task = self.config.get("whisper_task", "transcribe")
                    text = self.transcriber.transcribe(audio_data, initial_prompt=ctx_prompt, task=task)
                    if text and text != self.pending_text:
                        self.pending_text = text
                        if self.on_preview_update:
                            self.on_preview_update(text, None)
                        if self.config.get("live_typing", True):
                            self._live_type_diff(text)

                    if self._should_auto_stop(audio_data):
                        self.log("Silence detected. Auto-stopping...")
                        self._stop_recording()
                        break

                    last_transcription_time = time.time()
                except Exception:  # noqa: BLE001
                    logger.debug("Live transcription error", exc_info=True)

    def _should_auto_stop(self, audio_data: "np.ndarray | None") -> bool:
        if not self.config.get("auto_stop", True):
            return False
        if time.time() - self.recording_start_time <= self.config.get("auto_stop_delay", 1.5):
            return False
        if audio_data is None or len(audio_data) < 16000:
            return False
        return not self.transcriber._has_speech(audio_data[-16000:])  # noqa: SLF001

    def _play_beep(self, frequency: int, duration: int) -> None:
        def beep() -> None:
            with contextlib.suppress(Exception):
                from lerolero.platform import get_platform
                get_platform().play_beep(frequency, duration)
        threading.Thread(target=beep, daemon=True).start()

    def _auto_paste(self, text: str) -> None:
        try:
            pyperclip.copy(text)
            time.sleep(0.1)
            if self.config.get("refocus_window", True) and self.window_manager and self.target_window_handle:
                if not self.window_manager.focus_window(self.target_window_handle):
                    return
                time.sleep(0.7)
            else:
                time.sleep(0.2)
            kb = keyboard.Controller()
            from lerolero.platform import get_platform
            mod_name = get_platform().get_paste_modifier()
            mod_key = keyboard.Key.cmd if mod_name == "cmd" else keyboard.Key.ctrl
            with kb.pressed(mod_key):
                time.sleep(0.05)
                kb.press("v")
                time.sleep(0.05)
                kb.release("v")
        except Exception as e:
            self.log(f"Auto-paste error: {e}")

    def _live_type_diff(self, new_text: str) -> None:
        try:
            old_text = self.live_typed_text
            kb = keyboard.Controller()
            if new_text.startswith(old_text):
                kb.type(new_text[len(old_text):])
                self.live_typed_text = new_text
            else:
                common_len = 0
                for i in range(min(len(old_text), len(new_text))):
                    if old_text[i] == new_text[i]:
                        common_len += 1
                    else:
                        break
                for _ in range(len(old_text) - common_len):
                    kb.press(keyboard.Key.backspace)
                    kb.release(keyboard.Key.backspace)
                    time.sleep(0.005)
                kb.type(new_text[common_len:])
                self.live_typed_text = new_text
        except Exception as e:
            self.log(f"Live typing error: {e}")

    def _listener_watchdog_loop(self) -> None:
        while not self._stop_watchdog.is_set():
            for _ in range(50):
                if self._stop_watchdog.is_set():
                    return
                time.sleep(0.1)
            if self.paused or self._stop_watchdog.is_set():
                continue
            if self.listener is None or not self.listener.is_alive():
                self.log("Hotkey listener stopped. Restarting...")
                self.start_listener()

    def setup_tray(self, on_open: Callable[[], None]) -> None:
        icon_path = Path(__file__).parent / "assets" / "icon.png"
        try:
            image = Image.open(icon_path) if icon_path.exists() else Image.new("RGB", (64, 64), color=(127, 90, 240))

            def _on_open(_i: pystray.Icon, _item: object) -> None:
                on_open()

            def _on_pause(_i: pystray.Icon, _item: object) -> None:
                self.toggle_pause()

            def _on_exit(_i: pystray.Icon, _item: object) -> None:
                self.shutdown()
                os._exit(0)

            menu = pystray.Menu(
                pystray.MenuItem("Abrir LeroLero", _on_open, default=True),
                pystray.MenuItem("Pausar / Retomar", _on_pause),
                pystray.MenuItem("Sair", _on_exit),
            )
            self.tray_icon = pystray.Icon("whisper-typing", image, "LeroLero", menu)

            def run_icon() -> None:
                try:
                    self.tray_icon.run()
                except Exception:
                    logger.exception("Tray icon crashed")

            self._tray_thread = threading.Thread(target=run_icon, daemon=True)
            self._tray_thread.start()
        except Exception as e:
            logger.exception("Failed to setup tray")
            self.log(f"Tray setup failed: {e}")
