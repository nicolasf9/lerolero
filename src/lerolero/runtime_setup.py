"""First-run dependency installer — downloads only what the user's GPU needs."""

from __future__ import annotations

import logging
import os
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
    """Return the local packages directory — %APPDATA%/LeroLero/deps for stability."""
    # Prefer AppData so deps survive app updates
    appdata = os.environ.get("APPDATA")
    if appdata:
        deps_dir = Path(appdata) / "LeroLero" / "deps"
    elif getattr(sys, "frozen", False):
        deps_dir = Path(sys.executable).parent / "deps"
    else:
        deps_dir = Path(__file__).resolve().parent.parent.parent / "deps"

    deps_dir.mkdir(parents=True, exist_ok=True)
    return deps_dir


def _add_deps_to_path() -> None:
    """Add the local deps directory to sys.path if it exists."""
    deps_dir = _get_deps_dir()
    deps_str = str(deps_dir)
    if deps_dir.exists() and deps_str not in sys.path:
        sys.path.insert(0, deps_str)


def _get_pip_executable() -> list[str]:
    """Find the best way to run pip — handles frozen exe and normal Python."""
    # Try using the current Python's pip module
    try:
        result = subprocess.run(
            [sys.executable, "-m", "pip", "--version"],
            capture_output=True, text=True, timeout=10,
        )
        if result.returncode == 0:
            return [sys.executable, "-m", "pip"]
    except Exception:
        pass

    # For frozen exe: try system Python
    for python in ["python", "python3", "py"]:
        try:
            result = subprocess.run(
                [python, "-m", "pip", "--version"],
                capture_output=True, text=True, timeout=10,
            )
            if result.returncode == 0:
                return [python, "-m", "pip"]
        except Exception:
            continue

    # Last resort: try pip directly
    for pip_cmd in ["pip", "pip3"]:
        try:
            result = subprocess.run(
                [pip_cmd, "--version"],
                capture_output=True, text=True, timeout=10,
            )
            if result.returncode == 0:
                return [pip_cmd]
        except Exception:
            continue

    raise RuntimeError(
        "pip não encontrado. Instale Python de https://python.org\n"
        "Marque 'Add Python to PATH' durante a instalação."
    )


def detect_gpu_simple() -> str:
    """Lightweight GPU detection without importing heavy libraries."""
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
    """Install dependencies for the detected backend."""
    deps_dir = _get_deps_dir()

    try:
        pip_cmd = _get_pip_executable()
    except RuntimeError as e:
        if progress_callback:
            progress_callback(str(e), -1)
        return False

    packages = _COMMON_PACKAGES + _BACKEND_PACKAGES.get(backend, _BACKEND_PACKAGES["cpu"])

    total = len(packages)
    for i, pkg in enumerate(packages):
        pkg_name = pkg.split(">=")[0].split("[")[0]
        percent = int((i / total) * 100)
        if progress_callback:
            progress_callback(f"Instalando {pkg_name}... ({i+1}/{total})", percent)
        logger.info("Installing %s to %s", pkg, deps_dir)

        cmd = pip_cmd + [
            "install", pkg,
            "--target", str(deps_dir),
            "--no-warn-script-location",
            "--disable-pip-version-check",
        ]

        # For CUDA, use PyTorch index
        if backend == "cuda" and pkg_name in ("torch", "torchaudio"):
            cmd.extend(["--index-url", "https://download.pytorch.org/whl/cu124"])

        try:
            result = subprocess.run(
                cmd, capture_output=True, text=True, timeout=600,
                creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0,
            )
            if result.returncode != 0:
                logger.error("Failed to install %s: %s", pkg, result.stderr)
                if progress_callback:
                    progress_callback(f"Erro ao instalar {pkg_name}: {result.stderr[:100]}", -1)
                return False
        except subprocess.TimeoutExpired:
            logger.error("Timeout installing %s", pkg)
            if progress_callback:
                progress_callback(f"Timeout ao instalar {pkg_name}", -1)
            return False
        except Exception as e:
            logger.error("Error installing %s: %s", pkg, e)
            if progress_callback:
                progress_callback(f"Erro: {e}", -1)
            return False

    if progress_callback:
        progress_callback("✅ Instalação concluída!", 100)

    _add_deps_to_path()
    return True


def ensure_deps(progress_callback=None) -> str:
    """Detect GPU, install deps if needed, return backend name."""
    _add_deps_to_path()

    backend = detect_gpu_simple()
    logger.info("Detected GPU backend: %s", backend)

    if check_deps_installed(backend):
        logger.info("Dependencies already installed for %s", backend)
        return backend

    if progress_callback:
        progress_callback(f"Configurando para {backend.upper()}...", 0)

    success = install_deps(backend, progress_callback)
    if not success and backend != "cpu":
        logger.warning("Failed to install %s deps, falling back to CPU", backend)
        backend = "cpu"
        success = install_deps(backend, progress_callback)

    if not success:
        raise RuntimeError("Falha ao instalar dependências necessárias")

    return backend
