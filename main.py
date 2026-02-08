"""
ChatGPT Assistant Script

This script implements an interactive ChatGPT assistant that operates with both text and
voice interaction modes. It configures various services, including Email, Weather, Spotify, and
Crypto Data, and uses GPT to process user queries and generate responses. The application supports
a silent mode (text-only) and a voice mode (audio).

The script utilizes:
- Logging for error tracking and debugging,
- Environment variables to configure APIs and services,
- Multiple third-party libraries, including Colorama and dotenv.

Main functions:
- setup_logging: Configures logging for the script.
- format_and_print_content: Formats text for console output.
- Main loop for silent and voice modes, including audio recording and playback.

Author: Tim Ullrich
"""

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

from src.executors import (
    CommandExecutor,
    ContactExecutor,
    CryptoDataExecutor,
    EmailExecutor,
    SpotifyExecutor,
    WeatherExecutor,
    WebScraperExecutor,
)
from src.gtaf import GtafRuntimeClient, GtafRuntimeConfig
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


def setup_logging(level: str = "info") -> logging.Logger:
    """Set up logging configuration."""

    # Convert the log_level string into the corresponding logging level
    numeric_log_level = getattr(logging, level.upper(), logging.INFO)

    logging.basicConfig(
        level=numeric_log_level,  # Dynamically set log level
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=[
            logging.FileHandler("app.log"),  # Log to a file
            logging.StreamHandler(sys.stdout),  # Log output to the console
        ],
    )
    configured_logger = logging.getLogger(__name__)
    return configured_logger


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
    gtaf_artifact_dir: str = os.getenv(
        "GTAF_ARTIFACT_DIR", f"{script_dir}/gtaf_artifacts"
    )
    gtaf_scope: str = os.getenv("GTAF_SCOPE", "local:rachel")
    gtaf_component: str = os.getenv("GTAF_COMPONENT", "chat-service")
    gtaf_interface: str = os.getenv("GTAF_INTERFACE", "tool-calls")
    gtaf_system: str = os.getenv("GTAF_SYSTEM", "rachel-local-agent")

    # Configure logging
    logger: logging.Logger = setup_logging(log_level)

    # Init OpenAiConnector
    open_ai_connector: OpenAiConnector = OpenAiConnector(os.getenv("OPENAI_API_KEY"))

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
        CommandExecutor(platform, user_language),
        EmailExecutor(email_service, username),
        ContactExecutor(contacts_service),
        WeatherExecutor(weather_service),
        WebScraperExecutor(web_scraper_service),
        CryptoDataExecutor(crypto_data_service),
        SpotifyExecutor(spotify_service),
    ]

    # chat service needs to be initialized after the executors
    gtaf_config = GtafRuntimeConfig(
        artifact_dir=gtaf_artifact_dir,
        scope=gtaf_scope,
        component=gtaf_component,
        interface=gtaf_interface,
        system=gtaf_system,
        default_user=username or "unknown",
    )
    gtaf_runtime_client = GtafRuntimeClient(config=gtaf_config)
    warmup_decision = gtaf_runtime_client.warmup()
    if warmup_decision.outcome == "DENY":
        logger.error(
            "GTAF warmup failed: reason=%s details=%s",
            warmup_decision.reason_code,
            warmup_decision.details,
        )
    else:
        logger.info("GTAF warmup successful: reason=%s", warmup_decision.reason_code)

    chat_service = ChatService(
        open_ai_connector,
        user_language=user_language,
        executors=executors,
        gtaf_runtime_client=gtaf_runtime_client,
        gtaf_context_defaults={"user": username or "unknown"},
    )

    while True:
        try:
            if args.silent:
                # Textmodus
                user_input_text = input(
                    Fore.YELLOW + Style.BRIGHT + "You: " + Style.RESET_ALL
                )
                stream = chat_service.ask_chat_gpt(
                    user_input_text, conversation_history, mode="text"
                )
                chat_service.print_stream_text(stream)

            else:
                # Voice modus
                audio_service.play_sound("sent")
                user_input_audio = audio_service.record()
                audio_service.play_sound("sent")

                if user_input_audio.silence_timeout:
                    logger.info("No speech detected for 3 seconds. Exiting...")
                    audio_service.play_sound("standby")
                    sys.exit()

                user_input_text = audio_service.transcribe_audio(
                    user_input_audio, user_language
                )
                print(
                    Fore.YELLOW
                    + Style.BRIGHT
                    + f"You: {user_input_text}"
                    + Style.RESET_ALL
                )

                stream = chat_service.ask_chat_gpt(
                    user_input_text, conversation_history, mode="voice"
                )

                splitter = StreamSplitter(stream)
                splitter.start()

                text_output_thread = threading.Thread(
                    target=chat_service.print_stream_text, args=(splitter.get(),)
                )
                audio_output_thread = threading.Thread(
                    target=audio_service.play_stream_audio, args=(splitter.get(),)
                )

                text_output_thread.start()
                audio_output_thread.start()

                text_output_thread.join()
                audio_output_thread.join()

        except Exception as e:
            logger.error("An unexpected error occurred: %s", e, exc_info=True)
            conversation_history.append(
                {
                    "role": "system",
                    "content": f"Error encountered: {str(e)}. Interpret this for the user.",
                }
            )
            error_stream = chat_service.ask_chat_gpt(
                "Error Interpretation Request", conversation_history, mode="text"
            )
            chat_service.print_stream_text(error_stream)
