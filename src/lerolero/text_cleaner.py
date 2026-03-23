"""Post-processing text cleaner — removes stutters, filler words, and Whisper artifacts."""

from __future__ import annotations

import re

# Whisper artifacts to strip entirely
_ARTIFACTS = re.compile(
    r"\(inaudível\)|\(inaudible\)|\[music\]|\[Music\]|\[silence\]"
    r"|\(Silence\)|\[Applause\]|\[applause\]|\(aplausos\)"
    r"|♪+|\.{4,}",
)

# Repeated words: "eu eu eu" → "eu", "the the" → "the"
_REPEATED_WORDS = re.compile(r"\b(\w+)(?:\s+\1){1,}\b", re.IGNORECASE)

# Portuguese filler/stutter patterns
_FILLERS_PT = re.compile(
    r"\b(?:é{2,}|ã{2,}h*|ah{2,}|eh{2,}|hm{2,}|uhm*|ahn*)"
    r"(?:\s*,?\s*)?",
    re.IGNORECASE,
)

# English filler patterns
_FILLERS_EN = re.compile(
    r"\b(?:uh+|um+|hmm+|uhm+)\b"
    r"(?:\s*,?\s*)?",
    re.IGNORECASE,
)

# Common Portuguese verbal tics (only when standalone, not mid-sentence meaning)
_TICS_PT = re.compile(
    r"(?:^|\.\s+)(?:tipo assim|tipo,?\s+)",
    re.IGNORECASE,
)

# Multiple spaces / leading-trailing cleanup
_MULTI_SPACE = re.compile(r" {2,}")
_LEADING_PUNCT = re.compile(r"^[\s,;.]+")
_TRAILING_SPACE_PUNCT = re.compile(r"[\s,;]+$")


def clean_transcript(text: str) -> str:
    """Clean a raw Whisper transcript.

    Removes:
    - Whisper hallucination artifacts ([music], (inaudível), etc.)
    - Repeated consecutive words (stutters)
    - Filler sounds in Portuguese and English
    - Common verbal tics
    - Extra whitespace
    """
    if not text or not text.strip():
        return text

    t = text

    # Strip artifacts
    t = _ARTIFACTS.sub("", t)

    # Strip fillers
    t = _FILLERS_PT.sub(" ", t)
    t = _FILLERS_EN.sub(" ", t)

    # Strip verbal tics at sentence starts
    t = _TICS_PT.sub(". ", t)

    # Deduplicate repeated words
    t = _REPEATED_WORDS.sub(r"\1", t)

    # Clean whitespace
    t = _MULTI_SPACE.sub(" ", t)
    t = _LEADING_PUNCT.sub("", t)
    t = _TRAILING_SPACE_PUNCT.sub("", t)

    return t.strip()
