import logging
import os
import sys
from typing import List, Dict

from dotenv import load_dotenv

from src.connectors.open_ai_connector import OpenAiConnector
from src.services.chat_service import ChatService
from src.services.audio_service import AudioService


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
    user_language = os.getenv("USER_LANGUAGE", "en")
    sound_theme = os.getenv("SOUND_THEME", "default")
    script_dir: str = os.path.dirname(os.path.realpath(__file__))

    sample_rate: int = 16000  # Standard sample rate for Whisper
    recorded_wav_file: str = "record.wav"

    conversation_history: List[Dict[str, str]] = [{"role": "system", "content": "You are a helpful assistant."}]

    # Init OpenAiConnector
    openai_api_key: str = os.getenv("OPENAI_API_KEY", "")
    open_ai_connector: OpenAiConnector = OpenAiConnector(openai_api_key)

    # Init services
    chat_service: ChatService = ChatService(open_ai_connector)
    audio_service = AudioService(
        open_ai_connector,
        user_language=user_language,
        sound_theme=sound_theme
    )

    try:
        while True:
            audio_service.play_sound("sent")

            # Start recording
            result = audio_service.record()

            # Handle silence timeout (3 seconds with no speech)
            if result.silence_timeout:
                logger.info("No speech detected for 3 seconds. Exiting...")
                audio_service.play_sound("standby")
                sys.exit()  # Exit the entire script

            # Save audio and transcribe it
            audio_service.save_audio_to_wav(result.data, sample_rate, recorded_wav_file)
            audio_service.play_sound("sent")

            # Transcribe the saved audio file using OpenAI API
            user_input = audio_service.transcribe_audio(recorded_wav_file, user_language)

            # Handle transcription result
            if not user_input:
                logger.error("Transcription failed. Restarting...")
                continue  # Restart the loop if transcription failed

            audio_service.delete_wav_file(recorded_wav_file)
            print(f"You: {user_input}")

            # Stream the transcribed input to GPT and speak it in real-time
            reply: str = chat_service.talk_with_chat_gpt(user_input, conversation_history)

    except Exception as e:
        logger.error(f"An unexpected error occurred: {e}")
        sys.exit()  # Exit the entire script



