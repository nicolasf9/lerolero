"""Main entry point for whisper-typing."""

import argparse
import logging

from dotenv import load_dotenv

from whisper_typing.app_controller import WhisperAppController
from whisper_typing.gui.app import WhisperAppGUI


def main() -> None:
    """Run the whisper-typing application."""
    # Configure logging to write debug information to a file
    logging.basicConfig(
        filename="whisper_typing_debug.log",
        level=logging.DEBUG,
        format="%(asctime)s %(name)s %(levelname)s %(message)s",
        force=True,
    )

    # Set up command-line argument parsing
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

    # Load environment variables from a .env file, overriding existing ones
    load_dotenv(override=True)

    # Initialize the application controller with configuration from command-line arguments
    controller = WhisperAppController()
    controller.load_configuration(args)

    # Start the native GUI application
    # The GUI will handle component initialization and starting the listener
    app = WhisperAppGUI(controller)
    app.mainloop()


if __name__ == "__main__":
    main()
