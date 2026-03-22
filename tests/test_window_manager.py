"""Tests for window_manager module."""

from unittest.mock import MagicMock, patch

from whisper_typing.window_manager import WindowManager


@patch("ctypes.windll.user32")
def test_get_active_window(mock_user32: MagicMock) -> None:  # noqa: ARG001
    """Test retrieving the active window."""
    with patch("pygetwindow.getActiveWindow") as mock_get_active:
        mock_window = MagicMock()
        mock_get_active.return_value = mock_window
        wm = WindowManager()
        assert wm.get_active_window() == mock_window


@patch("ctypes.windll.user32")
def test_focus_window_success(mock_user32: MagicMock) -> None:
    """Test successfully focusing a window."""
    wm = WindowManager()
    mock_window = MagicMock()
    mock_window._hWnd = 12345
    mock_window.isMinimized = False

    assert wm.focus_window(mock_window) is True
    mock_user32.SetForegroundWindow.assert_called_with(12345)
    mock_user32.SetActiveWindow.assert_called_with(12345)


@patch("ctypes.windll.user32")
def test_focus_window_minimized(mock_user32: MagicMock) -> None:
    """Test focus_window when window is minimized."""
    wm = WindowManager()
    mock_window = MagicMock()
    mock_window._hWnd = 12345
    mock_window.isMinimized = True

    assert wm.focus_window(mock_window) is True
    # SW_RESTORE = 9
    mock_user32.ShowWindow.assert_called_with(12345, 9)
    mock_user32.SetForegroundWindow.assert_called_with(12345)


@patch("ctypes.windll.user32")
def test_focus_window_failure(mock_user32: MagicMock) -> None:
    """Test failure when focusing a window."""
    wm = WindowManager()
    mock_window = MagicMock()
    mock_window._hWnd = 12345
    mock_window.isMinimized = False

    # Simulate exception during activation
    mock_user32.SetForegroundWindow.side_effect = Exception("Focus error")

    assert wm.focus_window(mock_window) is False


def test_focus_window_none() -> None:
    """Test focus_window with None window."""
    wm = WindowManager()
    assert wm.focus_window(None) is False


def test_focus_window_no_hwnd() -> None:
    """Test focus_window with window missing _hWnd."""
    wm = WindowManager()
    mock_window = MagicMock(spec=[])
    assert wm.focus_window(mock_window) is False


@patch("ctypes.windll.user32")
def test_hide_window(mock_user32: MagicMock) -> None:
    """Test hiding a window."""
    wm = WindowManager()
    mock_window = MagicMock()
    mock_window._hWnd = 12345

    assert wm.hide_window(mock_window) is True
    # SW_HIDE = 0
    mock_user32.ShowWindow.assert_called_with(12345, 0)


@patch("ctypes.windll.user32")
def test_show_window(mock_user32: MagicMock) -> None:
    """Test showing a window."""
    wm = WindowManager()
    mock_window = MagicMock()
    mock_window._hWnd = 12345
    mock_window.isMinimized = False

    assert wm.show_window(mock_window) is True
    # SW_SHOW = 5
    mock_user32.ShowWindow.assert_any_call(12345, 5)
    mock_user32.SetForegroundWindow.assert_called_with(12345)


def test_show_window_none() -> None:
    """Test show_window with None window."""
    wm = WindowManager()
    assert wm.show_window(None) is False


def test_hide_window_none() -> None:
    """Test hide_window with None window."""
    wm = WindowManager()
    assert wm.hide_window(None) is False


@patch("ctypes.windll.user32")
def test_focus_window_exception(mock_user32: MagicMock) -> None:
    """Test focus_window with exception in ShowWindow."""
    wm = WindowManager()
    mock_window = MagicMock()
    mock_window._hWnd = 12345
    mock_window.isMinimized = True
    mock_user32.ShowWindow.side_effect = Exception("error")
    assert wm.focus_window(mock_window) is False


@patch("ctypes.windll.user32")
def test_hide_window_exception(mock_user32: MagicMock) -> None:
    """Test hide_window with exception."""
    wm = WindowManager()
    mock_window = MagicMock()
    mock_window._hWnd = 12345
    mock_user32.ShowWindow.side_effect = Exception("error")
    assert wm.hide_window(mock_window) is False


@patch("ctypes.windll.user32")
def test_show_window_exception(mock_user32: MagicMock) -> None:
    """Test show_window with exception."""
    wm = WindowManager()
    mock_window = MagicMock()
    mock_window._hWnd = 12345
    mock_window.isMinimized = False
    mock_user32.ShowWindow.side_effect = Exception("error")
    assert wm.show_window(mock_window) is False


def test_get_active_window_exception() -> None:
    """Test get_active_window with exception."""
    with patch("pygetwindow.getActiveWindow", side_effect=Exception("error")):
        wm = WindowManager()
        assert wm.get_active_window() is None

