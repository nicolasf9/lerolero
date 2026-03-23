"""Parakeet TDT v3 transcriber — NVIDIA's fast multilingual ASR via ONNX."""

from __future__ import annotations

import logging

import numpy as np

logger = logging.getLogger(__name__)

# Supported models (HuggingFace IDs)
PARAKEET_MODELS = {
    "parakeet-v3": "istupakov/parakeet-tdt-0.6b-v3-onnx",
    "parakeet-v3-int8": "sherpa-onnx-nemo-parakeet-tdt-0.6b-v3-int8",
}

DEFAULT_MODEL = "istupakov/parakeet-tdt-0.6b-v3-onnx"


def is_available() -> bool:
    """Check if onnx-asr is installed."""
    try:
        import onnx_asr  # noqa: F401
        return True
    except ImportError:
        return False


class ParakeetTranscriber:
    """Fast speech-to-text using NVIDIA Parakeet TDT v3 via ONNX Runtime.

    Supports OpenVINO EP (Intel), CUDA EP (NVIDIA), DirectML EP (AMD), CPU.
    ~10-50x faster than Whisper with comparable accuracy for European languages.
    """

    def __init__(
        self,
        model_id: str = DEFAULT_MODEL,
        language: str | None = None,
        device: str = "auto",
        download_root: str | None = None,
    ) -> None:
        import onnx_asr

        self.language = language
        self.model_id = model_id
        self.backend = self._pick_ep(device)

        logger.info("Parakeet using EP: %s, model: %s", self.backend, model_id)

        # onnx-asr handles model download and setup
        ep = self._get_execution_provider()
        self.recognizer = onnx_asr.Recognizer(
            model=model_id,
            execution_providers=ep,
        )

    @staticmethod
    def _pick_ep(device: str) -> str:
        """Pick the best ONNX Runtime Execution Provider."""
        pref = device.lower().strip()

        if pref == "cpu":
            return "cpu"

        # Try CUDA
        if pref in ("cuda", "nvidia", "gpu", "auto", ""):
            try:
                import onnxruntime as ort
                if "CUDAExecutionProvider" in ort.get_available_providers():
                    return "cuda"
            except ImportError:
                pass

        # Try OpenVINO
        if pref in ("openvino", "intel", "gpu", "auto", ""):
            try:
                import onnxruntime as ort
                if "OpenVINOExecutionProvider" in ort.get_available_providers():
                    return "openvino"
            except ImportError:
                pass

        # Try DirectML
        if pref in ("directml", "amd", "gpu", "auto", ""):
            try:
                import onnxruntime as ort
                if "DmlExecutionProvider" in ort.get_available_providers():
                    return "directml"
            except ImportError:
                pass

        return "cpu"

    def _get_execution_provider(self) -> list[str]:
        """Map backend to ONNX Runtime EP list."""
        ep_map = {
            "cuda": ["CUDAExecutionProvider", "CPUExecutionProvider"],
            "openvino": ["OpenVINOExecutionProvider", "CPUExecutionProvider"],
            "directml": ["DmlExecutionProvider", "CPUExecutionProvider"],
            "cpu": ["CPUExecutionProvider"],
        }
        return ep_map.get(self.backend, ["CPUExecutionProvider"])

    def transcribe(
        self,
        audio_input: str | np.ndarray,
        initial_prompt: str = "",
        task: str = "transcribe",
    ) -> str:
        """Transcribe audio to text.

        Note: Parakeet v3 does not support translation (task="translate").
        If translate is requested, returns empty string — caller should
        fall back to Whisper.
        """
        if task == "translate":
            logger.warning("Parakeet does not support translation, returning empty")
            return ""

        try:
            if isinstance(audio_input, np.ndarray):
                # onnx-asr expects float32 mono 16kHz
                audio = audio_input.flatten().astype(np.float32)
                result = self.recognizer.recognize(audio, sample_rate=16000)
            else:
                # File path
                result = self.recognizer.recognize_file(audio_input)

            if isinstance(result, str):
                return result.strip()
            if hasattr(result, "text"):
                return result.text.strip()
            return str(result).strip()

        except Exception:
            logger.exception("Parakeet transcription failed")
            return ""

    @staticmethod
    def detect_backend_info() -> str:
        """Return info about available Parakeet backend."""
        if not is_available():
            return "parakeet-unavailable"
        return "parakeet-onnx"
