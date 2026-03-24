"""Auto-update checker — checks GitHub Releases for new versions.

100% optional: if offline, silently does nothing.
Only makes ONE request to api.github.com on startup.
"""

from __future__ import annotations

import json
import logging
import os
import shutil
import sys
import tempfile
import zipfile
from io import BytesIO
from pathlib import Path
from urllib.error import URLError
from urllib.request import Request, urlopen

logger = logging.getLogger(__name__)

_GITHUB_REPO = "nicolasf9/lerolero"
_RELEASES_URL = f"https://api.github.com/repos/{_GITHUB_REPO}/releases/latest"
_CURRENT_VERSION = "1.0.0"  # Bump this on each release


def get_current_version() -> str:
    return _CURRENT_VERSION


def check_for_update() -> dict | None:
    """Check GitHub for a newer release. Returns info dict or None.

    Returns None if:
    - No internet
    - Already on latest
    - Any error (fail silently)
    """
    try:
        req = Request(
            _RELEASES_URL,
            headers={"Accept": "application/vnd.github+json", "User-Agent": "LeroLero"},
        )
        response = urlopen(req, timeout=5)
        data = json.loads(response.read().decode("utf-8"))

        remote_tag = data.get("tag_name", "").lstrip("v")
        if not remote_tag:
            return None

        # Simple version comparison (works for semver without pre-release)
        if _version_tuple(remote_tag) <= _version_tuple(_CURRENT_VERSION):
            return None

        # Find the zip asset
        download_url = ""
        download_size = 0
        for asset in data.get("assets", []):
            name = asset.get("name", "")
            if name.endswith(".zip") and "win64" in name:
                download_url = asset.get("browser_download_url", "")
                download_size = asset.get("size", 0)
                break

        return {
            "version": remote_tag,
            "current_version": _CURRENT_VERSION,
            "release_url": data.get("html_url", ""),
            "download_url": download_url,
            "download_size_mb": round(download_size / (1024 * 1024), 1) if download_size else 0,
            "body": data.get("body", "")[:500],  # Release notes (truncated)
            "published_at": data.get("published_at", ""),
        }

    except (URLError, TimeoutError, json.JSONDecodeError, OSError):
        # No internet or API error — fail silently
        return None
    except Exception as e:
        logger.debug("Update check failed: %s", e)
        return None


def download_and_apply_update(download_url: str, progress_callback=None) -> bool:
    """Download the update zip and extract it over the current installation.

    Only works for frozen .exe builds (PyInstaller).
    For dev installs, just shows "git pull" instructions.
    """
    if not getattr(sys, "frozen", False):
        logger.info("Dev install — update via git pull")
        return False

    if not download_url:
        return False

    try:
        if progress_callback:
            progress_callback("Baixando atualização...", 10)

        req = Request(download_url, headers={"User-Agent": "LeroLero"})
        response = urlopen(req, timeout=120)
        total = int(response.headers.get("content-length", 0))
        data = bytearray()

        while True:
            chunk = response.read(65536)
            if not chunk:
                break
            data.extend(chunk)
            if total > 0 and progress_callback:
                pct = int(len(data) / total * 80) + 10  # 10-90%
                mb = len(data) / (1024 * 1024)
                progress_callback(f"Baixando... {mb:.0f} MB", pct)

        if progress_callback:
            progress_callback("Extraindo atualização...", 92)

        # Extract to a temp directory first
        app_dir = Path(sys.executable).parent
        temp_dir = Path(tempfile.mkdtemp(prefix="lerolero_update_"))

        with zipfile.ZipFile(BytesIO(bytes(data))) as zf:
            zf.extractall(temp_dir)

        # Find the extracted folder (usually LeroLero/)
        extracted = list(temp_dir.iterdir())
        source_dir = extracted[0] if len(extracted) == 1 and extracted[0].is_dir() else temp_dir

        if progress_callback:
            progress_callback("Aplicando atualização...", 95)

        # Create a batch script that replaces files after we exit
        update_script = app_dir / "_update.bat"
        update_script.write_text(
            '@echo off\n'
            'echo Atualizando LeroLero...\n'
            'timeout /t 2 /nobreak > nul\n'
            f'xcopy /s /y /q "{source_dir}\\*" "{app_dir}\\"\n'
            f'rmdir /s /q "{temp_dir}"\n'
            f'del "%~f0"\n'
            f'start "" "{app_dir}\\LeroLero.exe"\n',
            encoding="utf-8",
        )

        if progress_callback:
            progress_callback("Reiniciando...", 100)

        # Launch the update script and exit
        import subprocess
        subprocess.Popen(
            ["cmd", "/c", str(update_script)],
            creationflags=subprocess.CREATE_NO_WINDOW | subprocess.DETACHED_PROCESS,
        )

        return True

    except Exception as e:
        logger.error("Update failed: %s", e)
        if progress_callback:
            progress_callback(f"Erro: {e}", -1)
        return False


def _version_tuple(v: str) -> tuple[int, ...]:
    """Convert version string to tuple for comparison."""
    try:
        return tuple(int(x) for x in v.split("."))
    except (ValueError, AttributeError):
        return (0,)
