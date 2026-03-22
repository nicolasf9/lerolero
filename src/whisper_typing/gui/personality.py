"""Playful copy, greetings, milestones, and mascot system."""

from __future__ import annotations

import random
from datetime import datetime, timezone

# ── Status text ────────────────────────────────────────────────────────────

_READY_TEXTS = [
    "Listening...",
    "Say something!",
    "Ready when you are",
    "All ears!",
    "Go ahead, speak",
]

_RECORDING_TEXTS = [
    "Hearing you...",
    "Recording...",
    "Keep talking!",
]


def status_text(status: str) -> str:
    """Map internal status to playful display text."""
    if "Ready" in status or "Success" in status:
        return random.choice(_READY_TEXTS)  # noqa: S311
    if "Recording" in status:
        return random.choice(_RECORDING_TEXTS)  # noqa: S311
    if "Processing" in status:
        return "Thinking"  # dots added by TypingDotsAnimation
    if "Improving" in status:
        return "Polishing"
    if "Loading" in status:
        return "Waking up"
    if "Error" in status or "Failed" in status:
        return "Oops!"
    if "Paused" in status:
        return "Taking a break"
    return status


def mascot(status: str) -> str:
    """Return a unicode mascot character for the current state."""
    if "Recording" in status:
        return "\U0001f534"  # red circle
    if "Processing" in status or "Improving" in status:
        return "\u231b"  # hourglass
    if "Loading" in status:
        return "\U0001f4a4"  # zzz
    if "Error" in status or "Failed" in status:
        return "\U0001f635"  # dizzy face
    if "Ready" in status or "Success" in status:
        return "\U0001f399"  # studio microphone
    if "Paused" in status:
        return "\u23f8"  # pause icon
    return "\U0001f399"


# ── Greetings ──────────────────────────────────────────────────────────────

def greeting() -> str:
    """Return a time-appropriate greeting."""
    hour = datetime.now(timezone.utc).astimezone().hour
    if hour < 6:
        return "Late night session? Let's write something great."
    if hour < 12:
        return "Good morning! Ready to type for you."
    if hour < 18:
        return "Good afternoon! What shall we write?"
    return "Good evening! Let's get some words down."


# ── Milestones ─────────────────────────────────────────────────────────────

def milestone_message(
    total_words: int,
    words_today: int,
    sessions_today: int,
) -> str | None:
    """Return a celebration message at milestones, or None."""
    # First session
    if sessions_today == 1:
        return "\u2728 First session today. Let's go!"

    # Today milestones
    if words_today > 0 and words_today % 100 < 20:
        rounded = (words_today // 100) * 100
        if rounded > 0:
            return f"\U0001f389 {rounded} words today! You're on a roll."

    # Total milestones
    for threshold in (10000, 5000, 1000, 500):
        margin = total_words - threshold
        if 0 <= margin < 20:
            return f"\U0001f3c6 {threshold:,} words total! {_word_comparison(threshold)}"

    # Page comparisons
    if words_today >= 750 and words_today < 770:
        return "\U0001f4d6 That's about 3 pages of text today!"
    if words_today >= 250 and words_today < 270:
        return "\U0001f4c4 That's about a page of text today!"

    return None


# ── Fun comparisons ────────────────────────────────────────────────────────

def _word_comparison(words: int) -> str:
    if words < 250:
        return "A few paragraphs."
    if words < 500:
        return "About a page!"
    if words < 1000:
        return "A short essay!"
    if words < 5000:
        return "A short story!"
    return "A whole chapter!"


def fun_comparison(total_words: int) -> str:
    """Return a fun comparison for a word count."""
    return _word_comparison(total_words)


def time_comparison(seconds: float) -> str:
    """Return a fun comparison for time saved."""
    if seconds < 30:
        return "A quick stretch"
    if seconds < 120:
        return "A coffee sip"
    if seconds < 300:
        return "A coffee break"
    if seconds < 600:
        return "A short walk"
    if seconds < 1800:
        return "A lunch break"
    return "A whole meeting!"


# ── Log message emoji ──────────────────────────────────────────────────────

def log_emoji(message: str) -> str:
    """Prepend a contextual emoji to a log message."""
    ml = message.lower()
    if "recording started" in ml or "recording" in ml and "started" in ml:
        return f"\U0001f3a4 {message}"
    if "recording" in ml and "stop" in ml:
        return f"\u23f9 {message}"
    if "transcription" in ml or "transcrib" in ml:
        return f"\U0001f4dd {message}"
    if "ready" in ml or "success" in ml:
        return f"\u2705 {message}"
    if "error" in ml or "fail" in ml:
        return f"\u26a0\ufe0f {message}"
    if "loading" in ml or "model" in ml:
        return f"\u2699\ufe0f {message}"
    if "hotkey" in ml or "listener" in ml:
        return f"\u2328\ufe0f {message}"
    if "tray" in ml:
        return f"\U0001f4e5 {message}"
    if "session" in ml or "word" in ml:
        return f"\U0001f4ca {message}"
    if "improv" in ml:
        return f"\u2728 {message}"
    if "saved" in ml or "config" in ml:
        return f"\U0001f4be {message}"
    return f"  {message}"
