import logging
import os
import sys
import threading
from typing import List, Dict, Any

# 3rd party libraries
from colorama import Fore, Style
from dotenv import load_dotenv

# local modules
from src.connectors import OpenAiConnector, StreamSplitter
from src.entities import AudioRecordResult
from src.services import AudioService, ChatService
from src.executors import CommandExecutor


def setup_logging() -> logging.Logger:
    """Set up logging configuration."""
    logging.basicConfig(
        level=logging.INFO,  # Log-Level: DEBUG, INFO, WARNING, ERROR, CRITICAL
        format='%(asctime)s [%(levelname)s] %(message)s',
        handlers=[
            logging.FileHandler("app.log"),  # Log-Datei
            logging.StreamHandler(sys.stdout)  # Log-Ausgabe auf die Konsole
        ]
    )
    logger = logging.getLogger(__name__)
    return logger


def format_and_print_content(self, content: str) -> None:
    """Formats content for console output."""
    formatted_content: str = Fore.CYAN + Style.BRIGHT + content + Style.RESET_ALL
    sys.stdout.write(formatted_content)
    sys.stdout.flush()


if __name__ == "__main__":
    # Configure logging
    logger: logging.Logger = setup_logging()

    # Load environment variables from .env file
    load_dotenv()
    platform: str = os.getenv("PLATFORM", "raspberry-pi")
    user_language: str = os.getenv("USER_LANGUAGE", "en")
    sound_theme: str = os.getenv("SOUND_THEME", "default")

    script_dir: str = os.path.dirname(os.path.realpath(__file__))

    # Init OpenAiConnector
    openai_api_key: str = os.getenv("OPENAI_API_KEY", "")
    open_ai_connector: OpenAiConnector = OpenAiConnector(openai_api_key)

    # application variables
    conversation_history: List[Dict[str, str]] = [
        {"role": "system", "content": "You are a helpful assistant."}]

    # Register available task executors
    executors = [
        CommandExecutor(),
        # Other executors like EmailExecuter(), ReminderExecuter(), etc.
    ]

    # Init services
    chat_service = ChatService(
        open_ai_connector,
        user_language=user_language,
        executors=executors
    )
    audio_service = AudioService(
        open_ai_connector,
        user_language=user_language,
        sound_theme=sound_theme
    )

    try:
        while True:
            audio_service.play_sound("sent")

            # Start user input recording and saves the input into user_input_audio
            user_input_audio: AudioRecordResult = audio_service.record()

            # Handle silence timeout (3 seconds with no speech)
            if user_input_audio.silence_timeout:
                logger.info("No speech detected for 3 seconds. Exiting...")
                audio_service.play_sound("standby")
                sys.exit()  # Exit the entire script

            # Transcribe the AudioRecordResult using OpenAI's Whisper API
            user_input_text: str = audio_service.transcribe_audio(user_input_audio, user_language)
            print(f"You: {user_input_text}")

            # Stream the transcribed input to GPT and handle the response
            stream = chat_service.ask_chat_gpt(user_input_text, conversation_history)

            # Create a StreamSplitter to share the stream
            splitter = StreamSplitter(stream)
            splitter.start()

            # Start the threads for text and audio playback
            text_output_thread = threading.Thread(
                target=chat_service.print_stream_text, args=(splitter.get(),))

            audio_output_thread = threading.Thread(
                target=audio_service.play_stream_audio, args=(splitter.get(),))

            text_output_thread.start()
            audio_output_thread.start()

            # Wait for both threads to complete
            text_output_thread.join()
            audio_output_thread.join()

    except Exception as e:
        logger.error(f"An unexpected error occurred: {e}")
        sys.exit()  # Exit the entire script
