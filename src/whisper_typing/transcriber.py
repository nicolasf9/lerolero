"""Auto-detect GPU backend transcriber — Intel (OpenVINO), NVIDIA (CUDA), AMD (DirectML), CPU."""

from __future__ import annotations

import logging
import os

import numpy as np

logger = logging.getLogger(__name__)

# VAD tuning constants
_VAD_FRAME_MS = 30
_VAD_SAMPLE_RATE = 16000
_VAD_FRAME_SAMPLES = int(_VAD_SAMPLE_RATE * _VAD_FRAME_MS / 1000)
_VAD_MIN_SPEECH_FRAMES = 3
_VAD_ENERGY_FLOOR = 1e-6


def _detect_backend(device_pref: str) -> str:
    """Auto-detect the best available backend.

    Returns one of: 'openvino', 'cuda', 'directml', 'cpu'.
    """
    pref = device_pref.lower().strip()

    # Explicit CPU request
    if pref == "cpu":
        return "cpu"

    # Try NVIDIA CUDA first (most common discrete GPU)
    if pref in ("cuda", "nvidia", "gpu", "auto", ""):
        try:
            import torch
            if torch.cuda.is_available():
                name = torch.cuda.get_device_name(0)
                logger.info("Detected NVIDIA GPU: %s — using CUDA backend", name)
                return "cuda"
        except ImportError:
            pass

    # Try Intel OpenVINO
    if pref in ("openvino", "intel", "gpu", "auto", ""):
        try:
            from openvino import Core
            core = Core()
            devices = core.available_devices
            if "GPU" in devices:
                logger.info("Detected Intel GPU via OpenVINO — using OpenVINO backend")
                return "openvino"
            if pref in ("openvino", "intel"):
                # User explicitly asked for Intel but no GPU — use CPU via OpenVINO
                logger.info("No Intel GPU found, using OpenVINO on CPU")
                return "openvino"
        except ImportError:
            pass

    # Try AMD DirectML
    if pref in ("directml", "amd", "gpu", "auto", ""):
        try:
            import onnxruntime as ort
            providers = ort.get_available_providers()
            if "DmlExecutionProvider" in providers:
                logger.info("Detected AMD/DirectML GPU — using DirectML backend")
                return "directml"
        except ImportError:
            pass

    # Fallback: OpenVINO on CPU if available, else pure torch CPU
    try:
        import openvino  # noqa: F401
        logger.info("Falling back to OpenVINO on CPU")
        return "openvino"
    except ImportError:
        pass

    logger.info("No GPU acceleration found — using PyTorch CPU")
    return "cpu"


def _build_openvino_pipeline(
    model_id: str, device: str, cache_dir: str | None,
) -> object:
    """Build an OpenVINO ASR pipeline (Intel GPUs and CPUs)."""
    from optimum.intel import OVModelForSpeechSeq2Seq
    from transformers import AutoProcessor, pipeline

    ov_device = "GPU" if device != "cpu" else "CPU"

    processor = AutoProcessor.from_pretrained(model_id, cache_dir=cache_dir)
    model = OVModelForSpeechSeq2Seq.from_pretrained(
        model_id, export=True, device=ov_device, cache_dir=cache_dir,
    )
    return pipeline(
        "automatic-speech-recognition",
        model=model,
        tokenizer=processor.tokenizer,
        feature_extractor=processor.feature_extractor,
        chunk_length_s=30,
    )


def _build_cuda_pipeline(
    model_id: str, compute_type: str, cache_dir: str | None,
) -> object:
    """Build a PyTorch CUDA pipeline (NVIDIA GPUs)."""
    import torch
    from transformers import AutoModelForSpeechSeq2Seq, AutoProcessor, pipeline

    dtype = torch.float16 if compute_type in ("float16", "auto") else torch.float32

    processor = AutoProcessor.from_pretrained(model_id, cache_dir=cache_dir)
    model = AutoModelForSpeechSeq2Seq.from_pretrained(
        model_id, torch_dtype=dtype, cache_dir=cache_dir,
    ).to("cuda")

    return pipeline(
        "automatic-speech-recognition",
        model=model,
        tokenizer=processor.tokenizer,
        feature_extractor=processor.feature_extractor,
        chunk_length_s=30,
        torch_dtype=dtype,
        device="cuda",
    )


def _build_directml_pipeline(
    model_id: str, cache_dir: str | None,
) -> object:
    """Build an ONNX Runtime DirectML pipeline (AMD GPUs)."""
    from transformers import AutoProcessor, pipeline
    from optimum.onnxruntime import ORTModelForSpeechSeq2Seq

    processor = AutoProcessor.from_pretrained(model_id, cache_dir=cache_dir)
    model = ORTModelForSpeechSeq2Seq.from_pretrained(
        model_id, export=True, cache_dir=cache_dir,
        provider="DmlExecutionProvider",
    )
    return pipeline(
        "automatic-speech-recognition",
        model=model,
        tokenizer=processor.tokenizer,
        feature_extractor=processor.feature_extractor,
        chunk_length_s=30,
    )


def _build_cpu_pipeline(
    model_id: str, cache_dir: str | None,
) -> object:
    """Build a plain PyTorch CPU pipeline (universal fallback)."""
    from transformers import AutoModelForSpeechSeq2Seq, AutoProcessor, pipeline

    processor = AutoProcessor.from_pretrained(model_id, cache_dir=cache_dir)
    model = AutoModelForSpeechSeq2Seq.from_pretrained(model_id, cache_dir=cache_dir)

    return pipeline(
        "automatic-speech-recognition",
        model=model,
        tokenizer=processor.tokenizer,
        feature_extractor=processor.feature_extractor,
        chunk_length_s=30,
        device="cpu",
    )


class Transcriber:
    """Multi-GPU speech-to-text with auto-detection."""

    def __init__(
        self,
        model_id: str = "openai/whisper-base",
        language: str | None = None,
        device: str = "auto",
        compute_type: str = "auto",
        download_root: str | None = None,
    ) -> None:
        self.model_id = model_id
        self.language = language
        self.download_root = download_root
        self.compute_type = compute_type

        # Auto-detect best backend
        self.backend = _detect_backend(device)
        logger.info("Transcriber using backend: %s for model: %s", self.backend, model_id)

        # Build the appropriate pipeline
        if self.backend == "openvino":
            self.pipe = _build_openvino_pipeline(model_id, device, download_root)
        elif self.backend == "cuda":
            self.pipe = _build_cuda_pipeline(model_id, compute_type, download_root)
        elif self.backend == "directml":
            self.pipe = _build_directml_pipeline(model_id, download_root)
        else:
            self.pipe = _build_cpu_pipeline(model_id, download_root)

    @staticmethod
    def _has_speech(
        audio_array: np.ndarray,
        threshold_factor: float = 3.0,
    ) -> bool:
        """Detect speech using frame-level RMS energy analysis."""
        audio = audio_array.flatten().astype(np.float32)

        if len(audio) < _VAD_FRAME_SAMPLES:
            return False

        n_frames = len(audio) // _VAD_FRAME_SAMPLES
        frames = audio[: n_frames * _VAD_FRAME_SAMPLES].reshape(
            n_frames, _VAD_FRAME_SAMPLES,
        )

        rms = np.sqrt(np.mean(frames**2, axis=1))
        sorted_rms = np.sort(rms)
        n_quiet = max(1, int(len(sorted_rms) * 20 / 100))
        noise_floor = float(np.mean(sorted_rms[:n_quiet])) + _VAD_ENERGY_FLOOR
        speech_threshold = noise_floor * threshold_factor
        speech_frame_count = int(np.sum(rms > speech_threshold))

        return speech_frame_count >= _VAD_MIN_SPEECH_FRAMES

    @staticmethod
    def detect_backend_info() -> str:
        """Return a human-readable string about the detected backend."""
        return _detect_backend("auto")

    def transcribe(self, audio_input: str | np.ndarray) -> str:
        """Transcribe audio to text."""
        if isinstance(audio_input, np.ndarray) and not self._has_speech(audio_input):
            return ""

        generate_kwargs = {}
        is_multilingual = not self.model_id.endswith(".en")
        if is_multilingual:
            lang = self.language
            if lang and lang.lower() not in ("auto", "multilingual"):
                generate_kwargs["language"] = lang
            generate_kwargs["task"] = "transcribe"

        result = self.pipe(audio_input, generate_kwargs=generate_kwargs)

        if isinstance(result, list):
            return " ".join([r.get("text", "") for r in result]).strip()
        if isinstance(result, dict):
            return result.get("text", "").strip()
        return ""
