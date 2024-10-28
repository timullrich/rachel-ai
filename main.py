import argparse
import logging
import os
import sys
import threading
from typing import Dict, List

# 3rd party libraries
from colorama import Fore, Style
from dotenv import load_dotenv

# local modules
from src.connectors import (
    CoinGeckoConnector,
    ImapConnector,
    OpenAiConnector,
    OpenWeatherMapConnector,
    SmtpConnector,
    SpotifyConnector,
    StreamSplitter,
)
from src.entities import AudioRecordResult
from src.executors import (
    CommandExecutor,
    ContactExecutor,
    CryptoDataExecutor,
    EmailExecutor,
    SpotifyExecutor,
    WeatherExecutor,
    WebScraperExecutor,
)
from src.services import (
    AudioService,
    ChatService,
    ContactService,
    CryptoDataService,
    EmailService,
    SpotifyService,
    WeatherService,
    WebScraperService,
)


def setup_logging(log_level: str = "info") -> logging.Logger:
    """Set up logging configuration."""

    # Convert the log_level string into the corresponding logging level
    numeric_log_level = getattr(logging, log_level.upper(), logging.INFO)

    logging.basicConfig(
        level=numeric_log_level,  # Dynamically set log level
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=[
            logging.FileHandler("app.log"),  # Log to a file
            logging.StreamHandler(sys.stdout),  # Log output to the console
        ],
    )
    logger = logging.getLogger(__name__)
    return logger


def format_and_print_content(self, content: str) -> None:
    """Formats content for console output."""
    formatted_content: str = Fore.CYAN + Style.BRIGHT + content + Style.RESET_ALL
    sys.stdout.write(formatted_content)
    sys.stdout.flush()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="ChatGPT Assistant with Silent Mode")
    parser.add_argument(
        "--silent",
        action="store_true",
        help="Run in silent mode (text input/output only)",
    )
    args = parser.parse_args()

    script_dir: str = os.path.dirname(os.path.realpath(__file__))

    # Load environment variables from .env file
    load_dotenv()
    platform: str = os.getenv("PLATFORM", "raspberry-pi")
    log_level: str = os.getenv("LOG_LEVEL", "info")
    user_language: str = os.getenv("USER_LANGUAGE", "en")
    sound_theme: str = os.getenv("SOUND_THEME", "default")

    username: str = os.getenv("USERNAME")

    # Configure logging
    logger: logging.Logger = setup_logging(log_level)

    # Init OpenAiConnector
    open_ai_connector: OpenAiConnector = OpenAiConnector(os.getenv("OPENAI_API_KEY"))

    icloud_user = "[REDACTED_EMAIL]"
    # icloud_password = "[REDACTED]"
    icloud_password = "[REDACTED]"

    # Init email connectors
    smtp_connector: SmtpConnector = SmtpConnector(
        os.getenv("SMTP_SERVER"),
        smtp_user=os.getenv("SMTP_USER"),
        smtp_password=os.getenv("SMTP_PASSWORD"),
    )
    imap_connector: ImapConnector = ImapConnector(
        imap_server=os.getenv("IMAP_SERVER"),
        imap_user=os.getenv("IMAP_USER"),
        imap_password=os.getenv("IMAP_PASSWORD"),
    )

    weather_connector: OpenWeatherMapConnector = OpenWeatherMapConnector(
        os.getenv("OPEN_WEATHER_MAP_API_KEY")
    )

    spotify_connector = SpotifyConnector(
        client_id=os.getenv("SPOTIFY_CLIENT_ID"),
        client_secret=os.getenv("SPOTIFY_CLIENT_SECRET"),
        redirect_uri=os.getenv("SPOTIFY_REDIRECT_URI"),
        scope="user-library-read playlist-read-private playlist-modify-private "
        "playlist-modify-public user-modify-playback-state user-read-playback-state",
    )

    coin_gecko_connector: CoinGeckoConnector = CoinGeckoConnector()

    # Init services
    email_service = EmailService(smtp_connector, imap_connector)
    contacts_service = ContactService(f"{script_dir}/resources/contacts.vcf")
    weather_service = WeatherService(weather_connector)
    web_scraper_service = WebScraperService()
    crypto_data_service = CryptoDataService(coin_gecko_connector)
    spotify_service = SpotifyService(spotify_connector)

    audio_service = AudioService(
        open_ai_connector, user_language=user_language, sound_theme=sound_theme
    )

    # application variables
    conversation_history: List[Dict[str, str]] = [
        {"role": "system", "content": "You are a helpful assistant."}
    ]

    # Register available task executors
    executors = [
        CommandExecutor(user_language, platform),
        EmailExecutor(email_service, username),
        ContactExecutor(contacts_service),
        WeatherExecutor(weather_service),
        WebScraperExecutor(web_scraper_service),
        CryptoDataExecutor(crypto_data_service),
        SpotifyExecutor(spotify_service),
    ]

    # chat service needs to be initialized after the executors
    chat_service = ChatService(
        open_ai_connector, user_language=user_language, executors=executors
    )

    while True:
        try:
            if args.silent:
                # Silent mode: Use text input/output
                user_input_text = input(
                    Fore.YELLOW + Style.BRIGHT + "You: " + Style.RESET_ALL
                )

                # Send user input to GPT and get response stream
                stream = chat_service.ask_chat_gpt(
                    user_input_text, conversation_history
                )

                # Print text stream output
                chat_service.print_stream_text(stream)

            else:
                # Non-silent mode: Use microphone for input and audio for output

                # Start user input recording and saves the input into user_input_audio
                audio_service.play_sound("sent")
                user_input_audio: AudioRecordResult = audio_service.record()
                audio_service.play_sound("sent")

                # Handle silence timeout (3 seconds with no speech)
                if user_input_audio.silence_timeout:
                    logger.info("No speech detected for 3 seconds. Exiting...")
                    audio_service.play_sound("standby")
                    sys.exit()  # Exit the entire script

                # Transcribe and print the AudioRecordResult using OpenAI's Whisper API
                user_input_text: str = audio_service.transcribe_audio(
                    user_input_audio, user_language
                )
                formatted_user_input_text: str = (
                    Fore.YELLOW
                    + Style.BRIGHT
                    + f"You: {user_input_text}"
                    + Style.RESET_ALL
                )
                print(formatted_user_input_text)

                # Stream the transcribed input to GPT and handle the response
                stream = chat_service.ask_chat_gpt(
                    user_input_text, conversation_history
                )

                # Create a StreamSplitter to share the stream
                splitter = StreamSplitter(stream)
                splitter.start()

                # Start the threads for text and audio playback
                text_output_thread = threading.Thread(
                    target=chat_service.print_stream_text, args=(splitter.get(),)
                )

                audio_output_thread = threading.Thread(
                    target=audio_service.play_stream_audio, args=(splitter.get(),)
                )

                text_output_thread.start()
                audio_output_thread.start()

                # Wait for both threads to complete
                text_output_thread.join()
                audio_output_thread.join()

        except Exception as e:
            logger.error(f"An unexpected error occurred: {e}", exc_info=True)
