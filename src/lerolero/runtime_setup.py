"""Model download helper.

All ML libraries (onnxruntime-openvino, onnx-asr) are BUNDLED in the exe.
No runtime install, no Python download, no pip. This module only handles
downloading the ASR model weights via onnx-asr on first run.
"""

from __future__ import annotations

import logging
from typing import Callable

logger = logging.getLogger(__name__)


def download_model(model_id: str, progress_callback: Callable | None = None) -> bool:
    """Download the model weights if not already cached.

    onnx-asr caches models to the HuggingFace cache dir automatically.
    Loading it once triggers the download; subsequent loads are instant.
    """
    if progress_callback:
        progress_callback(f"Baixando {model_id.split('/')[-1]}...", 5)

    try:
        if progress_callback:
            progress_callback("Importando onnx-asr...", 10)
        import onnx_asr
        from lerolero.transcriber import _normalize_model_id
        name = _normalize_model_id(model_id)
        if progress_callback:
            progress_callback(f"Baixando {name}...", 25)
        onnx_asr.load_model(name, providers=["CPUExecutionProvider"])
        if progress_callback:
            progress_callback("✅ Modelo pronto!", 100)
        return True
    except ImportError as e:
        msg = f"onnx-asr não encontrado: {e}"
        logger.error(msg)
        if progress_callback:
            progress_callback(msg, -1)
        return False
    except Exception as e:
        msg = f"Erro: {e!s}"
        logger.exception("Model download failed")
        if progress_callback:
            progress_callback(msg, -1)
        return False
