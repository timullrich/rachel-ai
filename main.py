import logging
import os
import sys
from typing import List, Dict

from dotenv import load_dotenv

from src.connectors.open_ai_connector import OpenAiConnector
from src.services.chat_service import ChatService
from src.services.audio_service import AudioService
from src.entities.audio_record_result import AudioRecordResult


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


if __name__ == "__main__":
    # Configure logging
    logger: logging.Logger = setup_logging()

    # Load environment variables from .env file
    load_dotenv()

    platform: str = os.getenv("PLATFORM", "raspberry-pi")
    user_language: str = os.getenv("USER_LANGUAGE", "en")
    sound_theme: str = os.getenv("SOUND_THEME", "default")
    script_dir: str = os.path.dirname(os.path.realpath(__file__))

    sample_rate: int = 16000  # Standard sample rate for Whisper

    conversation_history: List[Dict[str, str]] = [{"role": "system", "content": "You are a helpful assistant."}]

    # Init OpenAiConnector
    openai_api_key: str = os.getenv("OPENAI_API_KEY", "")
    open_ai_connector: OpenAiConnector = OpenAiConnector(openai_api_key)

    # Init services
    chat_service = ChatService(open_ai_connector)
    audio_service = AudioService(
        open_ai_connector,
        user_language=user_language,
        sound_theme=sound_theme
    )

    try:
        while True:
            audio_service.play_sound("sent")

            # Start recording
            user_input_audio: AudioRecordResult = audio_service.record()

            # Handle silence timeout (3 seconds with no speech)
            if user_input_audio.silence_timeout:
                logger.info("No speech detected for 3 seconds. Exiting...")
                audio_service.play_sound("standby")
                sys.exit()  # Exit the entire script

            # transcribe audio result
            audio_service.play_sound("sent")

            # Transcribe the AudioRecordResult using OpenAI API
            user_input_text: str = audio_service.transcribe_audio(user_input_audio, user_language)

            print(f"You: {user_input_text}")

            # Stream the transcribed input to GPT and speak it in real-time
            reply: str = chat_service.talk_with_chat_gpt(user_input_text, conversation_history)

    except Exception as e:
        logger.error(f"An unexpected error occurred: {e}")
        sys.exit()  # Exit the entire script



