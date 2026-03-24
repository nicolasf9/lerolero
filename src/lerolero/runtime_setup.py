"""First-run dependency installer — downloads embedded Python + deps.

Strategy:
1. Download Python embeddable (15MB) to %APPDATA%/LeroLero/python/
2. Bootstrap pip into that Python
3. Use that Python's pip to install ML deps into deps/ folder
4. Add deps/ to sys.path at runtime

This works reliably because we use a REAL Python, not the frozen exe.
"""

from __future__ import annotations

import io
import json
import logging
import os
import platform
import subprocess
import sys
import zipfile
from pathlib import Path
from urllib.error import URLError
from urllib.request import urlopen

logger = logging.getLogger(__name__)

# Python embeddable download URL (Windows only)
_PYTHON_VERSION = "3.13.7"
_PYTHON_EMBED_URL = f"https://www.python.org/ftp/python/{_PYTHON_VERSION}/python-{_PYTHON_VERSION}-embed-amd64.zip"
_GET_PIP_URL = "https://bootstrap.pypa.io/get-pip.py"

# Packages per backend
_BACKEND_PACKAGES: dict[str, list[str]] = {
    "openvino": [
        "openvino",
        "optimum-intel",
        "optimum",
        "transformers",
        "huggingface-hub",
        "tokenizers",
        "safetensors",
        "numpy",
        "scipy",
    ],
    "cuda": [
        "torch",
        "torchaudio",
        "transformers",
        "accelerate",
        "huggingface-hub",
        "tokenizers",
        "safetensors",
        "numpy",
        "scipy",
    ],
    "directml": [
        "onnxruntime-directml",
        "optimum",
        "transformers",
        "huggingface-hub",
        "tokenizers",
        "safetensors",
        "numpy",
        "scipy",
    ],
    "cpu": [
        "openvino",
        "optimum-intel",
        "optimum",
        "transformers",
        "huggingface-hub",
        "tokenizers",
        "safetensors",
        "numpy",
        "scipy",
    ],
}

_PYTORCH_INDEX = "https://download.pytorch.org/whl/cu124"


def _get_base_dir() -> Path:
    """Return %APPDATA%/LeroLero."""
    appdata = os.environ.get("APPDATA")
    if appdata:
        base = Path(appdata) / "LeroLero"
    elif getattr(sys, "frozen", False):
        base = Path(sys.executable).parent / "_data"
    else:
        base = Path(__file__).resolve().parent.parent.parent / "_data"
    base.mkdir(parents=True, exist_ok=True)
    return base


def _get_python_dir() -> Path:
    return _get_base_dir() / "python"


def _get_deps_dir() -> Path:
    return _get_base_dir() / "deps"


def _get_log_path() -> Path:
    return _get_base_dir() / "setup_log.txt"


def _log_to_file(msg: str) -> None:
    """Append message to setup log file for debugging."""
    try:
        log_path = _get_log_path()
        log_path.parent.mkdir(parents=True, exist_ok=True)
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(msg + "\n")
    except Exception:
        pass


def _get_embedded_python() -> Path | None:
    """Return path to embedded python.exe if it exists."""
    python_dir = _get_python_dir()
    python_exe = python_dir / "python.exe"
    if python_exe.exists():
        return python_exe
    return None


def _download_file(url: str, desc: str, progress_callback=None) -> bytes:
    """Download a file with progress reporting."""
    _log_to_file(f"Downloading: {url}")
    if progress_callback:
        progress_callback(f"Baixando {desc}...", -2)

    try:
        response = urlopen(url, timeout=60)
        total = int(response.headers.get("content-length", 0))
        data = bytearray()
        block_size = 65536

        while True:
            chunk = response.read(block_size)
            if not chunk:
                break
            data.extend(chunk)
            if total > 0 and progress_callback:
                pct = int(len(data) / total * 100)
                mb_done = len(data) / (1024 * 1024)
                mb_total = total / (1024 * 1024)
                progress_callback(
                    f"Baixando {desc}... {mb_done:.0f}/{mb_total:.0f} MB",
                    pct,
                )

        _log_to_file(f"Downloaded {len(data)} bytes from {url}")
        return bytes(data)

    except URLError as e:
        _log_to_file(f"Download failed: {e}")
        raise RuntimeError(f"Falha ao baixar {desc}: {e}") from e


def _get_system_python() -> Path | None:
    """Find system Python on macOS/Linux."""
    for name in ["python3", "python"]:
        try:
            result = subprocess.run(
                [name, "--version"], capture_output=True, text=True, timeout=5,
            )
            if result.returncode == 0:
                # Verify it has pip
                pip_check = subprocess.run(
                    [name, "-m", "pip", "--version"], capture_output=True, timeout=5,
                )
                if pip_check.returncode == 0:
                    import shutil
                    path = shutil.which(name)
                    if path:
                        return Path(path)
        except Exception:
            continue
    return None


def _install_embedded_python(progress_callback=None) -> Path:
    """Get a Python with pip for installing deps.

    Windows: Downloads Python embeddable + bootstraps pip.
    macOS/Linux: Uses system Python (must have pip).
    """
    # On macOS/Linux, just use system Python
    if sys.platform != "win32":
        system_py = _get_system_python()
        if system_py:
            _log_to_file(f"Using system Python: {system_py}")
            return system_py
        # If running as frozen app, try sys.executable
        if not getattr(sys, "frozen", False):
            return Path(sys.executable)
        raise RuntimeError(
            "Python não encontrado. Instale Python 3.10+ de https://python.org"
        )

    python_dir = _get_python_dir()
    python_exe = python_dir / "python.exe"

    if python_exe.exists():
        _log_to_file("Embedded Python already exists")
        return python_exe

    if progress_callback:
        progress_callback("Baixando Python embarcado...", 5)

    # Download Python embeddable
    data = _download_file(_PYTHON_EMBED_URL, "Python", progress_callback)

    # Extract
    if progress_callback:
        progress_callback("Extraindo Python...", 15)

    python_dir.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(io.BytesIO(data)) as zf:
        zf.extractall(python_dir)

    # Enable pip: edit python312._pth to add site-packages
    pth_files = list(python_dir.glob("python*._pth"))
    for pth_file in pth_files:
        content = pth_file.read_text()
        if "#import site" in content:
            content = content.replace("#import site", "import site")
            pth_file.write_text(content)
            _log_to_file(f"Enabled site-packages in {pth_file.name}")

    # Bootstrap pip
    if progress_callback:
        progress_callback("Instalando pip...", 20)

    get_pip_data = _download_file(_GET_PIP_URL, "pip", progress_callback)
    get_pip_path = python_dir / "get-pip.py"
    get_pip_path.write_bytes(get_pip_data)

    _log_to_file(f"Running: {python_exe} {get_pip_path}")
    result = subprocess.run(
        [str(python_exe), str(get_pip_path), "--no-warn-script-location"],
        capture_output=True,
        text=True,
        timeout=120,
        cwd=str(python_dir),
        creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0,
    )

    if result.returncode != 0:
        _log_to_file(f"pip bootstrap failed: {result.stderr}")
        raise RuntimeError(f"Falha ao instalar pip: {result.stderr[:200]}")

    _log_to_file("pip bootstrap succeeded")
    get_pip_path.unlink(missing_ok=True)

    return python_exe


def _pip_install(python_exe: Path, packages: list[str], target: Path,
                 extra_args: list[str] | None = None) -> tuple[bool, str]:
    """Use the embedded Python's pip to install packages."""
    cmd = [
        str(python_exe), "-m", "pip", "install",
        *packages,
        "--target", str(target),
        "--no-warn-script-location",
        "--disable-pip-version-check",
    ]
    if extra_args:
        cmd.extend(extra_args)

    _log_to_file(f"Running: {' '.join(cmd)}")

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=600,
            creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0,
        )
        _log_to_file(f"pip returned {result.returncode}")
        if result.stdout:
            _log_to_file(f"stdout: {result.stdout[-500:]}")
        if result.stderr:
            _log_to_file(f"stderr: {result.stderr[-500:]}")

        if result.returncode == 0:
            return (True, "")
        return (False, result.stderr[:300] or f"Exit code {result.returncode}")
    except subprocess.TimeoutExpired:
        return (False, "Timeout — o download pode estar lento. Tente novamente.")
    except Exception as e:
        _log_to_file(f"pip exception: {e}")
        return (False, str(e)[:200])


def _add_deps_to_path() -> None:
    """Add the deps directory to sys.path."""
    deps_dir = _get_deps_dir()
    deps_str = str(deps_dir)
    if deps_dir.exists() and deps_str not in sys.path:
        sys.path.insert(0, deps_str)
        if sys.platform == "win32":
            # DLL loading on Windows
            os.add_dll_directory(deps_str)
            for sub in ["openvino/libs", "Library/bin"]:
                dll_dir = deps_dir / sub
                if dll_dir.exists():
                    os.add_dll_directory(str(dll_dir))
        elif sys.platform == "linux":
            # Shared library path on Linux
            ld_path = os.environ.get("LD_LIBRARY_PATH", "")
            new_paths = [deps_str]
            for sub in ["openvino/libs"]:
                lib_dir = deps_dir / sub
                if lib_dir.exists():
                    new_paths.append(str(lib_dir))
            os.environ["LD_LIBRARY_PATH"] = ":".join(new_paths) + (":" + ld_path if ld_path else "")
        elif sys.platform == "darwin":
            # macOS dynamic library path
            dyld_path = os.environ.get("DYLD_LIBRARY_PATH", "")
            if dyld_path:
                os.environ["DYLD_LIBRARY_PATH"] = deps_str + ":" + dyld_path
            else:
                os.environ["DYLD_LIBRARY_PATH"] = deps_str


def detect_gpu_simple() -> str:
    """Lightweight GPU detection using system commands."""
    from lerolero.platform import get_platform
    backend = get_platform().detect_gpu()
    _log_to_file(f"GPU detected: {backend}")
    return backend


def check_deps_installed(backend: str) -> bool:
    """Check if required packages are importable."""
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
            _log_to_file(f"Module {mod} not found")
            return False
    _log_to_file(f"All deps for {backend} are installed")
    return True


def install_deps(backend: str, progress_callback=None) -> bool:
    """Install dependencies for the detected backend.

    1. Downloads Python embeddable (15MB) if not present
    2. Bootstraps pip into it
    3. Installs backend-specific packages
    """
    _log_to_file(f"=== Installing deps for {backend} ===")
    deps_dir = _get_deps_dir()
    deps_dir.mkdir(parents=True, exist_ok=True)

    # Step 1: Get embedded Python
    try:
        python_exe = _install_embedded_python(progress_callback)
    except Exception as e:
        _log_to_file(f"Failed to install Python: {e}")
        if progress_callback:
            progress_callback(f"Erro: {e}", -1)
        return False

    # Step 2: Install all packages in a single pip call (much faster than one-by-one)
    packages = _BACKEND_PACKAGES.get(backend, _BACKEND_PACKAGES["cpu"])

    # CUDA: torch/torchaudio need a custom index, install them first
    if backend == "cuda":
        torch_pkgs = [p for p in packages if p in ("torch", "torchaudio")]
        other_pkgs = [p for p in packages if p not in ("torch", "torchaudio")]

        if torch_pkgs:
            if progress_callback:
                progress_callback(f"Instalando {', '.join(torch_pkgs)}...", 25)
            _log_to_file(f"Installing torch packages: {torch_pkgs}")
            success, error = _pip_install(
                python_exe, torch_pkgs, deps_dir,
                ["--index-url", _PYTORCH_INDEX],
            )
            if not success:
                _log_to_file(f"FAILED: torch — {error}")
                if progress_callback:
                    progress_callback(f"Erro em torch: {error[:80]}", -1)
                return False

        packages = other_pkgs

    if packages:
        if progress_callback:
            progress_callback(f"Instalando {len(packages)} pacotes...", 50)
        _log_to_file(f"Installing all packages in one call: {packages}")
        success, error = _pip_install(python_exe, packages, deps_dir)
        if not success:
            _log_to_file(f"FAILED: {error}")
            if progress_callback:
                progress_callback(f"Erro na instalação: {error[:80]}", -1)
            return False

    if progress_callback:
        progress_callback("✅ Tudo instalado!", 100)

    _add_deps_to_path()
    _log_to_file("=== Installation complete ===")
    return True


def download_model(model_id: str, progress_callback=None) -> bool:
    """Pre-download the configured model so first transcription is instant.

    Supports both Whisper (HuggingFace) and Parakeet (onnx-asr) models.
    Must be called AFTER install_deps so the ML libraries are importable.
    """
    _add_deps_to_path()
    _log_to_file(f"=== Downloading model: {model_id} ===")

    if progress_callback:
        progress_callback(f"Baixando modelo {model_id.split('/')[-1]}...", 0)

    is_parakeet = "parakeet" in model_id.lower()

    try:
        if is_parakeet:
            # Parakeet downloads via onnx-asr Recognizer constructor
            import onnx_asr  # noqa: F401
            if progress_callback:
                progress_callback("Baixando modelo Parakeet v3...", 30)
            _log_to_file("Downloading Parakeet model via onnx-asr...")
            onnx_asr.Recognizer(model=model_id)
        else:
            # Whisper models: download via huggingface_hub (no full pipeline load)
            from huggingface_hub import snapshot_download
            if progress_callback:
                progress_callback(f"Baixando modelo {model_id.split('/')[-1]}...", 30)
            _log_to_file(f"Downloading HuggingFace model: {model_id}")
            snapshot_download(repo_id=model_id)

        _log_to_file(f"Model {model_id} downloaded successfully")
        if progress_callback:
            progress_callback("✅ Modelo baixado!", 100)
        return True

    except Exception as e:
        _log_to_file(f"Model download failed: {e}")
        if progress_callback:
            progress_callback(f"⚠ Modelo será baixado depois: {e!s:.60s}", -1)
        # Non-fatal: model will download on first transcription
        return False


def ensure_deps(progress_callback=None) -> str:
    """Detect GPU, install deps if needed, return backend name.

    This is the main entry point. Call it at app startup.
    """
    _log_to_file(f"=== ensure_deps called, frozen={getattr(sys, 'frozen', False)} ===")
    _add_deps_to_path()

    backend = detect_gpu_simple()
    _log_to_file(f"Backend: {backend}")

    if check_deps_installed(backend):
        return backend

    if progress_callback:
        progress_callback(f"GPU detectada: {backend.upper()}", 0)

    success = install_deps(backend, progress_callback)

    if not success and backend != "cpu":
        _log_to_file(f"{backend} failed, trying CPU")
        if progress_callback:
            progress_callback("Tentando modo CPU...", 0)
        backend = "cpu"
        success = install_deps(backend, progress_callback)

    if not success:
        log_path = _get_log_path()
        raise RuntimeError(
            f"Não foi possível instalar as dependências.\n\n"
            f"Verifique sua conexão com a internet.\n\n"
            f"Log de erros: {log_path}\n\n"
            f"Se o problema persistir, instale Python de https://python.org\n"
            f"e rode: pip install openvino optimum-intel transformers"
        )

    return backend
