"""Tests for app_controller module."""

import threading
from collections.abc import Generator
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from lerolero.app_controller import DEFAULT_CONFIG, WhisperAppController


@pytest.fixture
def mock_dependencies() -> Generator[dict[str, Any]]:
    """Mock all external dependencies for the controller."""
    with (
        patch("lerolero.app_controller.AudioRecorder") as mock_recorder,
        patch("lerolero.app_controller.Transcriber") as mock_transcriber,
        patch("lerolero.app_controller.WindowManager") as mock_window_manager,
        patch("pynput.keyboard.GlobalHotKeys") as mock_hotkeys,
        patch("lerolero.app_controller.sd") as mock_sd,
    ):
        yield {
            "recorder": mock_recorder,
            "transcriber": mock_transcriber,
            "window_manager": mock_window_manager,
            "hotkeys": mock_hotkeys,
            "sd": mock_sd,
        }

    mock_sd.query_devices.return_value = []


def test_initialization(mock_dependencies: dict[str, Any]) -> None:  # noqa: ARG001
    """Test controller initialization."""
    controller = WhisperAppController()
    assert controller.config == {}
    assert controller.recorder is None
    assert controller.transcriber is None


def test_initialize_components(mock_dependencies: dict[str, Any]) -> None:  # noqa: ARG001
    """Test initializing components."""
    controller = WhisperAppController()
    controller.config = DEFAULT_CONFIG.copy()
    success = controller.initialize_components()

    assert success is True
    assert controller.recorder is not None
    assert controller.transcriber is not None
    assert controller.window_manager is not None


def test_start_listener(mock_dependencies: dict[str, Any]) -> None:
    """Test starting the global hotkey listener."""
    controller = WhisperAppController()
    controller.config = DEFAULT_CONFIG.copy()
    controller.initialize_components()

    controller.start_listener()

    expected_hotkeys = mock_dependencies["hotkeys"]
    expected_hotkeys.assert_called_once()

    args, _ = expected_hotkeys.call_args
    hotkey_map = args[0]
    assert controller.config["hotkey"] in hotkey_map


def test_on_record_toggle_start(mock_dependencies: dict[str, Any]) -> None:  # noqa: ARG001
    """Test starting recording."""
    controller = WhisperAppController()
    controller.config = DEFAULT_CONFIG.copy()
    controller.initialize_components()
    mock_wm = controller.window_manager
    mock_recorder = controller.recorder
    mock_recorder.recording = False

    mock_win = MagicMock()
    mock_win.title = "Some Other Window"
    mock_wm.get_active_window.return_value = mock_win

    controller.on_record_toggle()

    mock_wm.get_active_window.assert_called()
    assert controller.target_window_handle == mock_win
    mock_recorder.start.assert_called_once()


def test_on_record_toggle_stop(mock_dependencies: dict[str, Any]) -> None:  # noqa: ARG001
    """Test stopping recording."""
    controller = WhisperAppController()
    controller.config = DEFAULT_CONFIG.copy()
    controller.initialize_components()
    mock_recorder = controller.recorder
    mock_recorder.recording = True
    controller.stop_live_transcribe = threading.Event()

    controller.on_record_toggle()

    mock_recorder.stop.assert_called_once()
    assert controller.stop_live_transcribe.is_set()


def test_finish_transcription_pastes(mock_dependencies: dict[str, Any]) -> None:  # noqa: ARG001
    """Test that finish_transcription triggers auto_paste when enabled."""
    controller = WhisperAppController()
    controller.config = DEFAULT_CONFIG.copy()
    controller.config["auto_paste"] = True
    controller.config["live_typing"] = False
    controller.initialize_components()

    mock_transcriber = controller.transcriber
    mock_transcriber.transcribe.return_value = "Final Text"

    with patch.object(controller, "_auto_paste") as mock_paste:
        import numpy as np
        controller._finish_transcription(np.zeros(1000))
        mock_paste.assert_called_once_with("Final Text")


def test_auto_paste_with_refocus(mock_dependencies: dict[str, Any]) -> None:  # noqa: ARG001
    """Test auto_paste logic with window refocusing."""
    controller = WhisperAppController()
    controller.config = DEFAULT_CONFIG.copy()
    controller.config["refocus_window"] = True
    controller.initialize_components()

    mock_window = MagicMock()
    mock_window.title = "Target Window"
    controller.target_window_handle = mock_window

    with (
        patch("pyperclip.copy") as mock_copy,
        patch("pynput.keyboard.Controller"),
        patch("time.sleep"),
    ):
        controller._auto_paste("Hello")
        mock_copy.assert_called_once_with("Hello")
        controller.window_manager.focus_window.assert_called_with(mock_window)


def test_auto_paste_no_refocus(mock_dependencies: dict[str, Any]) -> None:  # noqa: ARG001
    """Test auto_paste without refocusing."""
    controller = WhisperAppController()
    controller.config = DEFAULT_CONFIG.copy()
    controller.config["refocus_window"] = False
    controller.initialize_components()

    with (
        patch("pyperclip.copy"),
        patch("pynput.keyboard.Controller"),
        patch("time.sleep"),
    ):
        controller._auto_paste("Hello")
        controller.window_manager.focus_window.assert_not_called()


def test_finish_transcription_no_text(mock_dependencies: dict[str, Any]) -> None:  # noqa: ARG001
    """Test finish_transcription when no text is returned."""
    controller = WhisperAppController()
    controller.config = DEFAULT_CONFIG.copy()
    controller.initialize_components()
    controller.transcriber.transcribe.return_value = None

    import numpy as np
    controller._finish_transcription(np.zeros(1000))
    assert controller.is_processing is False
    assert controller.pending_text is None
