"""Constants for LeroLero."""

from typing import Final

# Models shown to the user. Uses onnx-asr's built-in aliases.
MODELS: Final[list[tuple[str, str]]] = [
    ("⚡ Parakeet v3 (recomendado)", "nemo-parakeet-tdt-0.6b-v3"),
]

# Legacy alias (some tests still reference WHISPER_MODELS).
WHISPER_MODELS = MODELS
