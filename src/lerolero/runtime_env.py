"""Configure runtime environment for frozen exe before network libs load.

MUST be imported before huggingface_hub, requests, urllib3 or onnx_asr.

In a PyInstaller frozen exe:
  - requests/urllib3 don't automatically find certifi's cacert.pem → SSL fails
  - HF_HOME may default to a path inside _internal that's read-only
  - The default download backend (hf_xet) native binaries may not load

We fix all three here, deterministically, with paths that always exist
and always resolve the same way whether running from source or frozen.
"""

from __future__ import annotations

import logging
import os
import sys
from pathlib import Path

logger = logging.getLogger(__name__)

_APPLIED = False


def apply() -> None:
    """Idempotently wire up SSL certs, HF cache dir, and disable hf_xet."""
    global _APPLIED
    if _APPLIED:
        return
    _APPLIED = True

    _setup_ssl_certs()
    _setup_hf_cache()
    _disable_hf_xet()


def _setup_ssl_certs() -> None:
    """Point requests/urllib3 at certifi's CA bundle."""
    try:
        import certifi
    except ImportError:
        logger.warning("certifi not available; SSL may fail on frozen exe")
        return

    ca = certifi.where()
    if not os.path.exists(ca):
        logger.warning("certifi cacert not found at %s", ca)
        return

    os.environ.setdefault("SSL_CERT_FILE", ca)
    os.environ.setdefault("REQUESTS_CA_BUNDLE", ca)
    os.environ.setdefault("CURL_CA_BUNDLE", ca)


def _setup_hf_cache() -> None:
    """Pin HF cache to %APPDATA%/LeroLero/hf_cache (always writable)."""
    try:
        from lerolero.paths import get_data_dir
        cache = get_data_dir() / "hf_cache"
        cache.mkdir(parents=True, exist_ok=True)
    except Exception:
        cache = Path.home() / ".cache" / "lerolero" / "hf_cache"
        try:
            cache.mkdir(parents=True, exist_ok=True)
        except Exception:
            return

    os.environ.setdefault("HF_HOME", str(cache))
    os.environ.setdefault("HF_HUB_CACHE", str(cache / "hub"))


def _disable_hf_xet() -> None:
    """Force plain-HTTP downloads — hf_xet's Rust backend is fragile in frozen exe."""
    os.environ.setdefault("HF_HUB_DISABLE_XET", "1")
    os.environ.setdefault("HF_XET_HIGH_PERFORMANCE", "0")
