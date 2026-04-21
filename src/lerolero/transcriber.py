"""Speech-to-text via ONNX Runtime — Parakeet TDT v3.

Uses onnxruntime-openvino which provides:
  - CPUExecutionProvider (always available)
  - OpenVINOExecutionProvider (Intel GPUs / iGPU / NPU)
  - CUDAExecutionProvider (NVIDIA, if CUDA libs present)
  - DmlExecutionProvider (AMD, if DirectML available)

Everything runs on ONNX — no PyTorch/transformers/export conversion.
Model is pre-trained ONNX, loaded directly. No hanging.
"""

from __future__ import annotations

import logging

import numpy as np

logger = logging.getLogger(__name__)

# Default model alias recognized by onnx-asr. This downloads from HF on first use.
DEFAULT_MODEL = "nemo-parakeet-tdt-0.6b-v3"


def detect_best_provider() -> str:
    """Return the best available ONNX Runtime Execution Provider."""
    try:
        import onnxruntime as ort
    except ImportError:
        return "CPUExecutionProvider"

    providers = ort.get_available_providers()
    # Preference order: CUDA > OpenVINO > DirectML > CPU
    for ep in ("CUDAExecutionProvider", "OpenVINOExecutionProvider",
               "DmlExecutionProvider", "CPUExecutionProvider"):
        if ep in providers:
            return ep
    return "CPUExecutionProvider"


def _provider_label(provider: str) -> str:
    """Short human-readable label."""
    return {
        "CUDAExecutionProvider": "cuda",
        "OpenVINOExecutionProvider": "openvino",
        "DmlExecutionProvider": "directml",
        "CPUExecutionProvider": "cpu",
    }.get(provider, "cpu")


def _normalize_model_id(model_id: str) -> str:
    """Map common full HF paths to onnx-asr's short aliases."""
    aliases = {
        "istupakov/parakeet-tdt-0.6b-v3-onnx": "nemo-parakeet-tdt-0.6b-v3",
    }
    return aliases.get(model_id, model_id)


class Transcriber:
    """Fast speech-to-text via ONNX Runtime + Parakeet TDT v3."""

    def __init__(
        self,
        model_id: str = DEFAULT_MODEL,
        language: str | None = None,
        device: str = "auto",
        download_root: str | None = None,  # noqa: ARG002 (onnx-asr manages cache)
    ) -> None:
        import onnx_asr

        self.model_id = _normalize_model_id(model_id)
        self.language = language

        provider = self._pick_provider(device)
        self.backend = _provider_label(provider)

        providers = [provider]
        if provider != "CPUExecutionProvider":
            providers.append("CPUExecutionProvider")

        logger.info("Transcriber: provider=%s model=%s", provider, self.model_id)
        self.recognizer = onnx_asr.load_model(self.model_id, providers=providers)

    @staticmethod
    def _pick_provider(device_pref: str) -> str:
        """Pick the best EP based on user preference."""
        pref = device_pref.lower().strip()
        try:
            import onnxruntime as ort
            available = set(ort.get_available_providers())
        except ImportError:
            return "CPUExecutionProvider"

        explicit = {
            "cpu": "CPUExecutionProvider",
            "cuda": "CUDAExecutionProvider",
            "nvidia": "CUDAExecutionProvider",
            "openvino": "OpenVINOExecutionProvider",
            "intel": "OpenVINOExecutionProvider",
            "directml": "DmlExecutionProvider",
            "amd": "DmlExecutionProvider",
        }
        if pref in explicit and explicit[pref] in available:
            return explicit[pref]
        return detect_best_provider()

    def transcribe(
        self,
        audio_input: "str | np.ndarray",
        initial_prompt: str = "",  # noqa: ARG002 (Parakeet ignores prompts)
        task: str = "transcribe",  # noqa: ARG002 (Parakeet only transcribes)
    ) -> str:
        """Transcribe audio to text."""
        try:
            if isinstance(audio_input, np.ndarray):
                audio = audio_input.flatten().astype(np.float32)
                result = self.recognizer.recognize(audio, sample_rate=16000)
            else:
                result = self.recognizer.recognize(audio_input)

            if isinstance(result, str):
                return result.strip()
            if hasattr(result, "text"):
                return result.text.strip()
            if isinstance(result, list) and result:
                first = result[0]
                return first.text.strip() if hasattr(first, "text") else str(first).strip()
            return str(result).strip()
        except Exception:
            logger.exception("Transcription failed")
            return ""
