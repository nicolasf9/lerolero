"""Minimal greetings for the React UI."""

from __future__ import annotations

import random

_GREETINGS = (
    "E aí, manda ver!",
    "Bora falar?",
    "Pronto pra ditar.",
    "Fala que eu digito.",
)


def greeting() -> str:
    """Return a random greeting string."""
    return random.choice(_GREETINGS)  # noqa: S311
