"""Main entry point for whisper-typing — 100% offline."""

import argparse
import logging


def main() -> None:
    """Run the whisper-typing application."""
    logging.basicConfig(
        filename="whisper_typing_debug.log",
        level=logging.DEBUG,
        format="%(asctime)s %(name)s %(levelname)s %(message)s",
        force=True,
    )

    parser = argparse.ArgumentParser(
        description="Lero Lero - Background Speech to Text (Offline)",
    )
    parser.add_argument("--hotkey", help="Global hotkey to toggle recording")
    parser.add_argument("--model", help="Whisper model ID")
    parser.add_argument("--language", help="Language code")
    args = parser.parse_args()

    from whisper_typing.app_controller import WhisperAppController
    controller = WhisperAppController()
    controller.load_configuration(args)

    from whisper_typing.gui.app import WhisperAppGUI
    app = WhisperAppGUI(controller)
    app.mainloop()


if __name__ == "__main__":
    main()
