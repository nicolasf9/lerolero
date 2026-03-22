"""Audio recording utilities using sounddevice."""

import threading
from typing import Final

import numpy as np
import sounddevice as sd


class AudioRecorder:
    """Handles audio capture from input devices."""

    def __init__(
        self,
        sample_rate: int = 16000,
        channels: int = 1,
        device_index: int | str | None = None,
    ) -> None:
        """Initialize the AudioRecorder.

        Args:
            sample_rate: Audio sampling rate in Hz.
            channels: Number of audio channels.
            device_index: Index or name of the input device.

        """
        self.sample_rate = sample_rate
        self.channels = channels
        self.device_index = device_index
        self.recording = False
        self.frames: list[np.ndarray] = []
        self.thread: threading.Thread | None = None
        self._lock: Final[threading.Lock] = threading.Lock()
        # Real-time audio level (RMS 0.0–1.0) for waveform visualization
        self.current_level: float = 0.0

    @staticmethod
    def list_devices() -> list[tuple[int, str]]:
        """List all available input devices.

        Returns:
            A list of tuples containing device index and name.

        """
        devices = sd.query_devices()
        input_devices = []
        for i, dev in enumerate(devices):
            if dev["max_input_channels"] > 0:
                input_devices.append((i, dev["name"]))
        return input_devices

    def _callback(
        self,
        indata: np.ndarray,
        _frames: int,
        _time: sd.RawInputStream,
        status: sd.CallbackFlags,
    ) -> None:
        """Handle audio data from sounddevice callback.

        Args:
            indata: The captured audio data.
            _frames: Missing from signature but provided by sounddevice.
            _time: Missing from signature but provided by sounddevice.
            status: Callback flags.

        """
        if status:
            pass
        with self._lock:
            self.frames.append(indata.copy())
        # Compute RMS level for visualization (clamped to 0.0–1.0)
        rms = float(np.sqrt(np.mean(indata**2)))
        self.current_level = min(1.0, rms * 15.0)  # amplify for visibility

    def _record(self) -> None:
        """Run the internal recording loop."""
        try:
            with sd.InputStream(
                samplerate=self.sample_rate,
                channels=self.channels,
                device=self.device_index,
                callback=self._callback,
            ):
                while self.recording:
                    sd.sleep(100)
        except Exception:  # noqa: BLE001
            self.recording = False

    def start(self) -> None:
        """Start recording."""
        if self.recording:
            return

        self.recording = True
        with self._lock:
            self.frames = []  # Clear frames
        self.thread = threading.Thread(target=self._record)
        self.thread.start()

    def get_current_data(self) -> np.ndarray | None:
        """Get the current accumulated audio data as a numpy array.

        Returns:
            The accumulated audio data as a 1D numpy array, or None if no data.

        """
        with self._lock:
            if not self.frames:
                return None
            data = list(self.frames)  # Copy list

        if not data:
            return None

        # Concatenate and flatten to 1D array for mono
        recording = np.concatenate(data, axis=0)
        if self.channels == 1:
            recording = recording.flatten()
        return recording

    def stop(self) -> np.ndarray | None:
        """Stop recording and return audio data as numpy array (float32).

        Returns:
            The complete audio data as a 1D numpy array, or None if not recording.

        """
        if not self.recording:
            return None

        self.recording = False
        if self.thread:
            self.thread.join()

        return self.get_current_data()
