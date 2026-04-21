"""LeroLero — 100% offline speech-to-text.

Startup is deliberately small: set up logging, create the controller,
hand off to the webview. All heavy lifting (model load, transcription)
happens in background threads after the UI is visible.
"""

from __future__ import annotations

import argparse
import logging
import sys
import traceback


def _show_error_dialog(title: str, message: str) -> None:
    """Show a native error dialog (Windows) or print fallback."""
    if sys.platform == "win32":
        try:
            import ctypes
            ctypes.windll.user32.MessageBoxW(0, message, title, 0x10)
            return
        except Exception:
            pass
    print(f"\n{title}\n{'=' * len(title)}\n{message}\n")


def _maybe_reset_onboarding_on_upgrade() -> None:
    """If the stored app version differs, reset the onboarding flag.

    This ensures users upgrading from an older build see the onboarding
    once more (they may need to re-download the model on the new stack).
    Silent no-op on any error.
    """
    try:
        import json
        from lerolero.paths import get_config_path
        from lerolero.updater import get_current_version

        cfg_path = get_config_path()
        if not cfg_path.exists():
            return
        with cfg_path.open() as f:
            cfg = json.load(f)
        if cfg.get("_app_version") == get_current_version():
            return
        cfg.pop("_onboarding_done", None)
        cfg.pop("model", None)
        cfg["_app_version"] = get_current_version()
        with cfg_path.open("w") as f:
            json.dump(cfg, f, indent=2)
    except Exception:
        pass


def main() -> None:
    """Application entry point."""
    try:
        from lerolero.paths import get_log_path, migrate_legacy_data
        from lerolero.runtime_env import apply as apply_runtime_env

        migrate_legacy_data()
        apply_runtime_env()  # SSL certs + HF cache path — must precede any import that hits the network
        _maybe_reset_onboarding_on_upgrade()

        logging.basicConfig(
            filename=str(get_log_path()),
            level=logging.INFO,
            format="%(asctime)s %(name)s %(levelname)s %(message)s",
            force=True,
        )

        parser = argparse.ArgumentParser(description="LeroLero")
        parser.add_argument("--hotkey", help="Global hotkey")
        parser.add_argument("--model", help="Model ID override")
        parser.add_argument("--language", help="Language code")
        args = parser.parse_args()

        from lerolero.app_controller import WhisperAppController
        from lerolero.webview_bridge import start_webview_app

        controller = WhisperAppController()
        controller.load_configuration(args)
        start_webview_app(controller)

    except Exception as e:
        logging.exception("Fatal error")
        _show_error_dialog(
            "LeroLero — Erro Fatal",
            f"{e}\n\nDetalhes em %APPDATA%\\LeroLero\\lerolero_debug.log",
        )
        print(traceback.format_exc())
        sys.exit(1)


if __name__ == "__main__":
    main()
