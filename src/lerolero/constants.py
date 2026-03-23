"""Constants for the whisper-typing application."""

from typing import Final

# List for TUI options: (label, id)
WHISPER_MODELS: Final[list[tuple[str, str]]] = [
    # Standard Multilingual
    ("Tiny (39M)", "openai/whisper-tiny"),
    ("Base (74M)", "openai/whisper-base"),
    ("Small (244M)", "openai/whisper-small"),
    ("Medium (769M)", "openai/whisper-medium"),
    ("Large v1 (1550M)", "openai/whisper-large-v1"),
    ("Large v2 (1550M)", "openai/whisper-large-v2"),
    ("Large v3 (1550M)", "openai/whisper-large-v3"),
    ("Large (Latest)", "openai/whisper-large"),
    # English-Only
    ("Tiny English", "openai/whisper-tiny.en"),
    ("Base English", "openai/whisper-base.en"),
    ("Small English", "openai/whisper-small.en"),
    ("Medium English", "openai/whisper-medium.en"),
    # Distilled & Turbo
    ("Turbo (Fastest)", "openai/whisper-large-v3-turbo"),
    ("Distil Small En", "distil-whisper/distil-small.en"),
    ("Distil Medium En", "distil-whisper/distil-medium.en"),
    ("Distil Large v2", "distil-whisper/distil-large-v2"),
    ("Distil Large v3", "distil-whisper/distil-large-v3"),
    # NVIDIA Parakeet (requires [parakeet] extra)
    ("⚡ Parakeet v3 (600M) — 10-50x faster", "istupakov/parakeet-tdt-0.6b-v3-onnx"),
]

