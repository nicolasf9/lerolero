"""Tests for constants module."""

from whisper_typing.constants import WHISPER_MODELS


def test_whisper_models_list() -> None:
    """Test that the whisper models list contains expected tuples."""
    expected_tuple_len = 2
    assert len(WHISPER_MODELS) > 0
    assert isinstance(WHISPER_MODELS[0], tuple)
    assert len(WHISPER_MODELS[0]) == expected_tuple_len
