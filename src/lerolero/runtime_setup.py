"""Model download helper.

All ML libraries (onnxruntime-openvino, onnx-asr) are BUNDLED in the exe.
No runtime install, no Python download, no pip. This module only handles
downloading the ASR model weights via onnx-asr on first run.
"""

from __future__ import annotations

import logging
import traceback
from typing import Callable

logger = logging.getLogger(__name__)


def download_model(model_id: str, progress_callback: Callable | None = None) -> bool:
    """Download the model weights if not already cached.

    onnx-asr caches models to the HuggingFace cache dir (pinned to
    %APPDATA%/LeroLero/hf_cache by runtime_env.apply()). Loading it once
    triggers the download; subsequent loads are instant.
    """
    # Ensure SSL certs + cache dir are set, even if this was called without main() running first
    try:
        from lerolero.runtime_env import apply as apply_runtime_env
        apply_runtime_env()
    except Exception as e:  # noqa: BLE001
        logger.warning("runtime_env.apply failed: %s", e)

    if progress_callback:
        progress_callback(f"Baixando {model_id.split('/')[-1]}...", 5)

    try:
        if progress_callback:
            progress_callback("Importando onnx-asr...", 10)
        import onnx_asr
        from lerolero.transcriber import _normalize_model_id
        name = _normalize_model_id(model_id)

        if progress_callback:
            progress_callback(f"Baixando {name} (pode levar 1-2 min)...", 25)

        onnx_asr.load_model(name, providers=["CPUExecutionProvider"])

        if progress_callback:
            progress_callback("✅ Modelo pronto!", 100)
        return True

    except ImportError as e:
        msg = f"Biblioteca não encontrada: {e}"
        logger.exception("Import failed during download")
        if progress_callback:
            progress_callback(msg, -1)
        return False

    except Exception as e:  # noqa: BLE001
        # Surface the concrete exception class + message + short traceback tail
        tb = traceback.format_exc()
        # Keep only the last 400 chars so the error toast stays readable
        tb_tail = tb[-400:] if len(tb) > 400 else tb
        err_type = type(e).__name__
        msg = f"{err_type}: {e!s}"
        logger.error("Model download failed: %s\n%s", msg, tb)
        if progress_callback:
            # Send the human-readable message (percent=-1 signals error)
            progress_callback(msg, -1)
            # Also push traceback tail so we can actually diagnose
            progress_callback(f"Detalhes: {tb_tail}", -1)
        return False
