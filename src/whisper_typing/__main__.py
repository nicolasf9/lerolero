"""Main entry point for whisper-typing."""

import argparse
import logging

from dotenv import load_dotenv

from whisper_typing.app_controller import WhisperAppController
from whisper_typing.gui.app import WhisperAppGUI


def main() -> None:
    """Run the whisper-typing application."""
    logging.basicConfig(
        filename="whisper_typing_debug.log",
        level=logging.DEBUG,
        format="%(asctime)s %(name)s %(levelname)s %(message)s",
        force=True,
    )
    parser = argparse.ArgumentParser(
        description="Whisper Typing - Background Speech to Text"
    )
    parser.add_argument("--hotkey", help="Global hotkey to toggle recording")
    parser.add_argument("--type-hotkey", help="Global hotkey to type")
    parser.add_argument("--improve-hotkey", help="Global hotkey to improve text")
    parser.add_argument("--model", help="Whisper model ID")
    parser.add_argument("--language", help="Language code")
    parser.add_argument("--api-key", help="Gemini API Key")
    args = parser.parse_args()

    load_dotenv(override=True)

    # Initialize Controller
    controller = WhisperAppController()
    controller.load_configuration(args)

    # Start Native GUI
    # The GUI will handle component initialization and starting the listener
    app = WhisperAppGUI(controller)
    app.mainloop()


if __name__ == "__main__":
    main()
