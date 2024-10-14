import logging
import os
import sys
from dotenv import load_dotenv

from connectors.open_ai_connector import OpenAiConnector

from services.chat_service import ChatService
from services.audio_service import AudioService, SilenceDetection


def setup_logging():
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
    logger = setup_logging()

    # Load environment variables from .env file
    load_dotenv()

    platform = os.getenv("PLATFORM")
    script_dir = os.path.dirname(os.path.realpath(__file__))

    sample_rate = 16000  # Standard sample rate for Whisper
    recorded_wav_file = "record.wav"

    conversation_history = [{"role": "system", "content": "You are a helpful assistant."}]

    # Init OpenAiConnector
    openai_api_key = os.getenv("OPENAI_API_KEY")
    open_ai_connector = OpenAiConnector(openai_api_key)

    # Init services
    chat_service = ChatService(open_ai_connector)
    audio_service = AudioService(open_ai_connector)

    # # Example for simple text to speech output (using openAI API)
    # audio_service.simple_speak("Das ist ein Test")

    try:
        while True:
            audio_service.play_sound(os.path.join(script_dir, "resources/sounds/sent.wav"))
            audio = audio_service.record()
            audio_service.save_audio_to_wav(audio, sample_rate, recorded_wav_file)

            audio_service.play_sound(os.path.join(script_dir, "resources/sounds/sent.wav"))

            # Transcribe the saved audio file using OpenAI API
            user_input = audio_service.transcribe_audio(recorded_wav_file)
            audio_service.delete_wav_file(recorded_wav_file)

            print(f"You: {user_input}")

            # Stream the transcribed input to GPT and speak it in real-time
            reply = chat_service.talk_with_chat_gpt(user_input, conversation_history)

    except SilenceDetection:
        logger.info("Silence detected. Exiting...")
        audio_service.play_sound(
            os.path.join(script_dir, "resources/sounds/standby.wav"))
        sys.exit()  # Exit the entire script

    except Exception as e:
        logger.error(f"An unexpected error occurred: {e}")
        sys.exit()
