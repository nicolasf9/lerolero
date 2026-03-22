"""First-run dependency installer — downloads only what the user's GPU needs."""

from __future__ import annotations

import logging
import subprocess
import sys
from pathlib import Path

logger = logging.getLogger(__name__)

# Packages per backend (only what's NOT bundled in the exe)
_BACKEND_PACKAGES: dict[str, list[str]] = {
    "openvino": [
        "openvino>=2025.0",
        "optimum-intel>=1.22",
        "optimum>=1.23",
        "transformers>=4.47",
        "huggingface-hub",
        "tokenizers",
        "safetensors",
    ],
    "cuda": [
        "torch>=2.0",
        "torchaudio>=2.0",
        "transformers>=4.47",
        "accelerate>=1.0",
        "huggingface-hub",
        "tokenizers",
        "safetensors",
    ],
    "directml": [
        "onnxruntime-directml>=1.17",
        "optimum>=1.23",
        "transformers>=4.47",
        "huggingface-hub",
        "tokenizers",
        "safetensors",
    ],
    "cpu": [
        "openvino>=2025.0",
        "optimum-intel>=1.22",
        "optimum>=1.23",
        "transformers>=4.47",
        "huggingface-hub",
        "tokenizers",
        "safetensors",
    ],
}

# Shared packages always needed
_COMMON_PACKAGES = [
    "numpy>=1.26",
    "scipy>=1.12",
    "sounddevice>=0.5",
]


def _get_deps_dir() -> Path:
    """Return the local packages directory next to the exe or in the project."""
    if getattr(sys, "frozen", False):
        base = Path(sys.executable).parent
    else:
        base = Path(__file__).resolve().parent.parent.parent
    deps_dir = base / "deps"
    deps_dir.mkdir(exist_ok=True)
    return deps_dir


def _add_deps_to_path() -> None:
    """Add the local deps directory to sys.path if it exists."""
    deps_dir = _get_deps_dir()
    deps_str = str(deps_dir)
    if deps_dir.exists() and deps_str not in sys.path:
        sys.path.insert(0, deps_str)


def detect_gpu_simple() -> str:
    """Lightweight GPU detection without importing heavy libraries.

    Uses system commands to detect GPU vendor before any pip installs.
    """
    import platform

    if platform.system() != "Windows":
        return "cpu"

    try:
        result = subprocess.run(
            ["wmic", "path", "win32_videocontroller", "get", "name"],
            capture_output=True, text=True, timeout=10,
        )
        output = result.stdout.lower()

        if "nvidia" in output and ("geforce" in output or "rtx" in output or "gtx" in output or "quadro" in output):
            return "cuda"
        if "intel" in output and ("arc" in output or "iris" in output or "uhd" in output):
            return "openvino"
        if "amd" in output and ("radeon" in output or "rx " in output):
            return "directml"
    except Exception:
        pass

    return "cpu"


def check_deps_installed(backend: str) -> bool:
    """Check if the required packages for a backend are importable."""
    _add_deps_to_path()

    checks = {
        "openvino": ["openvino", "optimum", "transformers"],
        "cuda": ["torch", "transformers"],
        "directml": ["onnxruntime", "optimum", "transformers"],
        "cpu": ["openvino", "optimum", "transformers"],
    }

    for mod in checks.get(backend, []):
        try:
            __import__(mod)
        except ImportError:
            return False
    return True


def install_deps(backend: str, progress_callback=None) -> bool:
    """Install dependencies for the detected backend.

    Args:
        backend: One of 'openvino', 'cuda', 'directml', 'cpu'.
        progress_callback: Optional callable(message: str, percent: int).

    Returns:
        True if installation succeeded.
    """
    deps_dir = _get_deps_dir()
    packages = _COMMON_PACKAGES + _BACKEND_PACKAGES.get(backend, _BACKEND_PACKAGES["cpu"])

    total = len(packages)
    for i, pkg in enumerate(packages):
        pkg_name = pkg.split(">=")[0].split("[")[0]
        if progress_callback:
            progress_callback(f"Installing {pkg_name}...", int((i / total) * 100))
        logger.info("Installing %s to %s", pkg, deps_dir)

        cmd = [
            sys.executable, "-m", "pip", "install",
            pkg, "--target", str(deps_dir),
            "--no-warn-script-location", "--quiet",
        ]

        # For CUDA, use PyTorch index
        if backend == "cuda" and pkg_name in ("torch", "torchaudio"):
            cmd.extend(["--index-url", "https://download.pytorch.org/whl/cu124"])

        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
            if result.returncode != 0:
                logger.error("Failed to install %s: %s", pkg, result.stderr)
                if progress_callback:
                    progress_callback(f"Error installing {pkg_name}", -1)
                return False
        except subprocess.TimeoutExpired:
            logger.error("Timeout installing %s", pkg)
            return False

    if progress_callback:
        progress_callback("Installation complete!", 100)

    _add_deps_to_path()
    return True


def ensure_deps(progress_callback=None) -> str:
    """Detect GPU, install deps if needed, return backend name.

    This is the main entry point called from the app startup.
    """
    _add_deps_to_path()

    backend = detect_gpu_simple()
    logger.info("Detected GPU backend: %s", backend)

    if check_deps_installed(backend):
        logger.info("Dependencies already installed for %s", backend)
        return backend

    # Fallback: if preferred backend deps fail, try cpu/openvino
    if progress_callback:
        progress_callback(f"Setting up for {backend.upper()} GPU...", 0)

    success = install_deps(backend, progress_callback)
    if not success and backend != "cpu":
        logger.warning("Failed to install %s deps, falling back to CPU", backend)
        backend = "cpu"
        success = install_deps(backend, progress_callback)

    if not success:
        raise RuntimeError("Failed to install required dependencies")

    return backend
