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


def _show_setup_window() -> bool:
    """Show a setup/progress window while installing ML dependencies.

    Returns True if setup succeeded, False otherwise.
    """
    import tkinter as tk
    from tkinter import ttk

    from lerolero.runtime_setup import check_deps_installed, detect_gpu_simple

    backend = detect_gpu_simple()

    if check_deps_installed(backend):
        return True

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
                status.config(text="✅ Instalação concluída!", fg="#4CAF50")
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
        except ImportError:
            # Fallback to CustomTkinter GUI if webview not available
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
