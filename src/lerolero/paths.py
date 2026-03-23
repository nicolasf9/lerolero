"""Centralized path management — store user data in OS-appropriate AppData."""

from __future__ import annotations

import os
import shutil
import sys
from pathlib import Path

_APP_NAME = "LeroLero"


def get_data_dir() -> Path:
    """Return the OS-appropriate data directory for user data.

    - Windows: %APPDATA%/LeroLero
    - macOS: ~/Library/Application Support/LeroLero
    - Linux: ~/.config/LeroLero
    """
    if os.name == "nt":
        base = Path(os.environ.get("APPDATA", Path.home()))
    elif sys.platform == "darwin":
        base = Path.home() / "Library" / "Application Support"
    else:
        base = Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config"))

    data_dir = base / _APP_NAME
    data_dir.mkdir(parents=True, exist_ok=True)
    return data_dir


def get_config_path() -> Path:
    """Return path to config.json in AppData."""
    return get_data_dir() / "config.json"


def get_history_dir() -> Path:
    """Return path to history/ directory in AppData."""
    d = get_data_dir() / "history"
    d.mkdir(parents=True, exist_ok=True)
    return d


def get_log_path() -> Path:
    """Return path to debug log in AppData."""
    return get_data_dir() / "lerolero_debug.log"


def migrate_legacy_data() -> int:
    """Migrate data from cwd-relative paths to AppData (one-time).

    Returns number of files migrated.
    """
    migrated = 0
    cwd = Path.cwd()
    data_dir = get_data_dir()

    # Migrate config.json
    old_config = cwd / "config.json"
    new_config = data_dir / "config.json"
    if old_config.exists() and not new_config.exists():
        shutil.copy2(old_config, new_config)
        migrated += 1

    # Migrate history/
    old_history = cwd / "history"
    new_history = data_dir / "history"
    new_history.mkdir(parents=True, exist_ok=True)
    if old_history.exists():
        for f in old_history.iterdir():
            dest = new_history / f.name
            if f.is_file() and not dest.exists():
                shutil.copy2(f, dest)
                migrated += 1

    return migrated
