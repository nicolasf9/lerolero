"""Main entry point for LeroLero — 100% offline speech-to-text."""

import argparse
import logging
import sys


def _show_setup_window() -> bool:
    """Show a setup/progress window while installing ML dependencies.

    Returns True if setup succeeded, False otherwise.
    """
    import tkinter as tk

    from whisper_typing.runtime_setup import check_deps_installed, detect_gpu_simple

    backend = detect_gpu_simple()

    if check_deps_installed(backend):
        return True

    # Need to install — show progress UI
    root = tk.Tk()
    root.title("LeroLero — First Run Setup")
    root.configure(bg="#0D0D0D")
    root.geometry("480x220")
    root.resizable(False, False)

    # Center on screen
    root.update_idletasks()
    x = (root.winfo_screenwidth() - 480) // 2
    y = (root.winfo_screenheight() - 220) // 2
    root.geometry(f"+{x}+{y}")

    gpu_labels = {
        "openvino": "Intel GPU (OpenVINO)",
        "cuda": "NVIDIA GPU (CUDA)",
        "directml": "AMD GPU (DirectML)",
        "cpu": "CPU (OpenVINO)",
    }

    title = tk.Label(
        root, text="LeroLero", font=("Segoe UI", 18, "bold"),
        bg="#0D0D0D", fg="#E0E0E0",
    )
    title.pack(pady=(20, 5))

    status = tk.Label(
        root,
        text=f"Detected: {gpu_labels.get(backend, backend)}\nInstalling dependencies...",
        font=("Segoe UI", 11), bg="#0D0D0D", fg="#A0A0A0",
    )
    status.pack(pady=5)

    progress_var = tk.IntVar(value=0)
    progress = tk.Canvas(root, width=400, height=8, bg="#1A1A1A", highlightthickness=0)
    progress.pack(pady=10)
    bar = progress.create_rectangle(0, 0, 0, 8, fill="#4FC3F7", outline="")

    detail = tk.Label(
        root, text="", font=("Segoe UI", 9), bg="#0D0D0D", fg="#666666",
    )
    detail.pack(pady=5)

    success = [False]

    def update_progress(message: str, percent: int) -> None:
        detail.config(text=message)
        if percent >= 0:
            progress.coords(bar, 0, 0, 4 * percent, 8)
        root.update()

    def run_install() -> None:
        from whisper_typing.runtime_setup import install_deps
        success[0] = install_deps(backend, update_progress)
        root.after(500, root.destroy)

    root.after(100, run_install)
    root.mainloop()
    return success[0]


def main() -> None:
    """Run the LeroLero application."""
    logging.basicConfig(
        filename="whisper_typing_debug.log",
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
    from whisper_typing.runtime_setup import _add_deps_to_path
    _add_deps_to_path()

    # First-run: detect GPU and install ML deps if needed
    if not _show_setup_window():
        print("ERROR: Failed to install dependencies. Check your internet connection.")
        sys.exit(1)

    from whisper_typing.app_controller import WhisperAppController
    controller = WhisperAppController()
    controller.load_configuration(args)

    from whisper_typing.gui.app import WhisperAppGUI
    app = WhisperAppGUI(controller)
    app.mainloop()


if __name__ == "__main__":
    main()
