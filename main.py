import logging
import os
import sys
from typing import List, Dict

from dotenv import load_dotenv

from connectors.open_ai_connector import OpenAiConnector
from services.chat_service import ChatService
from services.audio_service import AudioService, SilenceDetection


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
    audio_service = AudioService(open_ai_connector, sound_theme=sound_theme)

    # # Example for simple text to speech output (using openAI API)
    # audio_service.simple_speak("Das ist ein Test")

    try:
        while True:
            audio_service.play_sound("sent")
            audio = audio_service.record()
            if audio is not None:
                audio_service.save_audio_to_wav(audio, sample_rate, recorded_wav_file)

                audio_service.play_sound("sent")

                # Transcribe the saved audio file using OpenAI API
                user_input: str = audio_service.transcribe_audio(recorded_wav_file)
                audio_service.delete_wav_file(recorded_wav_file)

                print(f"You: {user_input}")

                # Stream the transcribed input to GPT and speak it in real-time
                reply: str = chat_service.talk_with_chat_gpt(user_input, conversation_history)

    except SilenceDetection:
        logger.info("Silence detected. Exiting...")
        audio_service.play_sound("standby")
        sys.exit()  # Exit the entire script

    except Exception as e:
        logger.error(f"An unexpected error occurred: {e}")
        sys.exit()
