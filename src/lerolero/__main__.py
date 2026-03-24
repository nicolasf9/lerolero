"""Main entry point for LeroLero — 100% offline speech-to-text."""

import argparse
import logging
import os
import sys
import traceback


def _show_error_dialog(title: str, message: str) -> None:
    """Show a native Windows error dialog if possible."""
    try:
        import ctypes
        ctypes.windll.user32.MessageBoxW(0, message, title, 0x10)  # MB_ICONERROR
    except Exception:
        print(f"\n{'='*50}")
        print(f"ERROR: {title}")
        print(f"{'='*50}")
        print(message)
        print(f"{'='*50}")
        input("\nPressione Enter para fechar...")


def _ensure_model_downloaded(model_id: str) -> bool:
    """Check if model is already cached, download if not. Returns True always."""
    try:
        from lerolero.runtime_setup import _add_deps_to_path
        _add_deps_to_path()

        is_parakeet = "parakeet" in model_id.lower()
        if is_parakeet:
            # Parakeet caching is handled internally by onnx-asr, skip check
            return True

        from huggingface_hub import try_to_load_from_cache
        # If any model file is cached, assume model is downloaded
        result = try_to_load_from_cache(model_id, "config.json")
        if result is not None:
            return True
    except Exception:
        return True  # Can't check, let it download later

    # Model not cached — show a quick download window
    import tkinter as tk
    from tkinter import ttk
    from lerolero.runtime_setup import download_model

    root = tk.Tk()
    root.title("LeroLero — Baixando Modelo")
    root.configure(bg="#0D0D0D")
    root.geometry("480x180")
    root.resizable(False, False)

    root.update_idletasks()
    x = (root.winfo_screenwidth() - 480) // 2
    y = (root.winfo_screenheight() - 180) // 2
    root.geometry(f"+{x}+{y}")

    tk.Label(
        root, text=f"Baixando modelo {model_id.split('/')[-1]}...",
        font=("Segoe UI", 12), bg="#0D0D0D", fg="#E0E0E0",
    ).pack(pady=(30, 10))

    style = ttk.Style()
    style.theme_use("clam")
    style.configure(
        "Custom.Horizontal.TProgressbar",
        troughcolor="#1A1A1A", background="#7C4DFF", thickness=12,
    )
    progress = ttk.Progressbar(
        root, style="Custom.Horizontal.TProgressbar",
        orient="horizontal", length=400, mode="indeterminate",
    )
    progress.pack(pady=10)
    progress.start(15)

    status = tk.Label(
        root, text="Isso pode levar alguns minutos...",
        font=("Segoe UI", 9), bg="#0D0D0D", fg="#888888",
    )
    status.pack(pady=5)

    def run_download():
        def cb(msg, pct):
            status.config(text=msg)
            root.update()
        download_model(model_id, cb)
        root.after(500, root.destroy)

    root.after(300, run_download)
    root.mainloop()
    return True


def _show_setup_window() -> bool:
    """Show a setup/progress window while installing ML dependencies.

    Returns True if setup succeeded, False otherwise.
    """
    import tkinter as tk
    from tkinter import ttk

    from lerolero.runtime_setup import check_deps_installed, detect_gpu_simple, download_model

    backend = detect_gpu_simple()

    # Read user's configured model (default: whisper-base)
    config_model = "openai/whisper-base"
    try:
        import json
        from lerolero.paths import get_config_path
        cfg_path = get_config_path()
        if cfg_path.exists():
            with cfg_path.open() as f:
                config_model = json.load(f).get("model", config_model)
    except Exception:
        pass

    if check_deps_installed(backend):
        # Deps installed, but check if model needs downloading
        return _ensure_model_downloaded(config_model)

    # Need to install — show progress UI
    root = tk.Tk()
    root.title("LeroLero — Configuração Inicial")
    root.configure(bg="#0D0D0D")
    root.geometry("520x320")
    root.resizable(False, False)

    # Try to set icon
    try:
        icon_path = os.path.join(os.path.dirname(__file__), "assets", "icon.ico")
        if not os.path.exists(icon_path) and getattr(sys, "frozen", False):
            icon_path = os.path.join(sys._MEIPASS, "lerolero", "assets", "icon.ico")
        if os.path.exists(icon_path):
            root.iconbitmap(icon_path)
    except Exception:
        pass

    # Center on screen
    root.update_idletasks()
    x = (root.winfo_screenwidth() - 520) // 2
    y = (root.winfo_screenheight() - 320) // 2
    root.geometry(f"+{x}+{y}")

    gpu_labels = {
        "openvino": "Intel GPU (OpenVINO)",
        "cuda": "NVIDIA GPU (CUDA)",
        "directml": "AMD GPU (DirectML)",
        "cpu": "CPU (modo universal)",
    }

    # Title
    title = tk.Label(
        root, text="🎤 LeroLero", font=("Segoe UI", 22, "bold"),
        bg="#0D0D0D", fg="#E0E0E0",
    )
    title.pack(pady=(25, 5))

    subtitle = tk.Label(
        root, text="Configuração Inicial", font=("Segoe UI", 12),
        bg="#0D0D0D", fg="#888888",
    )
    subtitle.pack(pady=(0, 15))

    # GPU detected
    gpu_text = gpu_labels.get(backend, backend)
    gpu_label = tk.Label(
        root,
        text=f"✅ GPU detectada: {gpu_text}",
        font=("Segoe UI", 11), bg="#0D0D0D", fg="#4FC3F7",
    )
    gpu_label.pack(pady=(0, 5))

    status = tk.Label(
        root,
        text="Baixando dependências de IA...",
        font=("Segoe UI", 10), bg="#0D0D0D", fg="#A0A0A0",
    )
    status.pack(pady=5)

    # Progress bar
    style = ttk.Style()
    style.theme_use("clam")
    style.configure(
        "Custom.Horizontal.TProgressbar",
        troughcolor="#1A1A1A",
        background="#7C4DFF",
        thickness=12,
    )
    progress = ttk.Progressbar(
        root, style="Custom.Horizontal.TProgressbar",
        orient="horizontal", length=440, mode="determinate",
    )
    progress.pack(pady=10)

    detail = tk.Label(
        root, text="Isso pode levar alguns minutos na primeira vez...",
        font=("Segoe UI", 9), bg="#0D0D0D", fg="#666666",
    )
    detail.pack(pady=5)

    # Package counter
    counter = tk.Label(
        root, text="",
        font=("Segoe UI", 9), bg="#0D0D0D", fg="#555555",
    )
    counter.pack(pady=(0, 5))

    success = [False]

    def update_progress(message: str, percent: int) -> None:
        status.config(text=message)
        if percent >= 0:
            progress["value"] = percent
        detail.config(text=f"{percent}% concluído" if percent >= 0 else message)
        root.update()

    def run_install() -> None:
        try:
            from lerolero.runtime_setup import install_deps
            success[0] = install_deps(backend, update_progress)
            if success[0]:
                # Download the configured model right after deps install
                status.config(text="Baixando modelo de IA...", fg="#4FC3F7")
                detail.config(text=f"Modelo: {config_model.split('/')[-1]}")
                root.update()
                download_model(config_model, update_progress)
                status.config(text="✅ Tudo pronto!", fg="#4CAF50")
                detail.config(text="Iniciando LeroLero...")
                root.update()
            else:
                status.config(text="❌ Falha na instalação", fg="#FF5252")
                detail.config(text="Verifique sua conexão com a internet e tente novamente.")
                root.update()
                import time
                time.sleep(3)
        except Exception as e:
            status.config(text=f"❌ Erro: {e}", fg="#FF5252")
            root.update()
            import time
            time.sleep(5)
        root.after(800 if success[0] else 0, root.destroy)

    root.after(300, run_install)
    root.mainloop()
    return success[0]


def main() -> None:
    """Run the LeroLero application."""
    try:
        from lerolero.paths import get_log_path, migrate_legacy_data

        # Migrate legacy data from cwd to AppData on first run
        migrate_legacy_data()

        logging.basicConfig(
            filename=str(get_log_path()),
            level=logging.DEBUG,
            format="%(asctime)s %(name)s %(levelname)s %(message)s",
            force=True,
        )

        parser = argparse.ArgumentParser(
            description="LeroLero - Background Speech to Text (Offline)",
        )
        parser.add_argument("--hotkey", help="Global hotkey to toggle recording")
        parser.add_argument("--model", help="Whisper model ID")
        parser.add_argument("--language", help="Language code")
        args = parser.parse_args()

        # Ensure deps path is on sys.path (for frozen exe builds)
        from lerolero.runtime_setup import _add_deps_to_path
        _add_deps_to_path()

        # First-run: detect GPU and install ML deps if needed
        if not _show_setup_window():
            _show_error_dialog(
                "LeroLero — Erro",
                "Não foi possível instalar as dependências.\n\n"
                "Verifique sua conexão com a internet e tente novamente.\n\n"
                "Se o problema persistir, instale manualmente:\n"
                "  pip install openvino optimum-intel transformers",
            )
            sys.exit(1)

        from lerolero.app_controller import WhisperAppController
        controller = WhisperAppController()
        controller.load_configuration(args)

        # Use React webview UI (new) or fall back to CTk (legacy)
        try:
            from lerolero.webview_bridge import start_webview_app
            start_webview_app(controller)
        except Exception:
            # Fallback to CustomTkinter GUI if webview fails for any reason
            # (ImportError, pythonnet RuntimeError, missing WebView2, etc.)
            logging.warning("Webview failed, falling back to CustomTkinter", exc_info=True)
            from lerolero.gui.app import WhisperAppGUI
            app = WhisperAppGUI(controller)
            app.mainloop()

    except Exception as e:
        error_msg = traceback.format_exc()
        logging.error("Fatal error: %s", error_msg)
        _show_error_dialog(
            "LeroLero — Erro Fatal",
            f"Ocorreu um erro inesperado:\n\n{e}\n\n"
            f"Detalhes técnicos salvos em:\n"
            f"%APPDATA%\\LeroLero\\lerolero.log",
        )
        sys.exit(1)


if __name__ == "__main__":
    main()
