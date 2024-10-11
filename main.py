import logging
import os
import re
import sys
import concurrent.futures
import threading

from colorama import Fore, Style
from dotenv import load_dotenv
from openai import OpenAI

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


def collect_until_sentence_end(text_buffer):
    """Collect text until a sentence end is detected (., !, ?)."""
    match = re.search(r'[.!?]', text_buffer)  # Look for sentence-ending punctuation
    if match:
        return text_buffer[:match.end()], text_buffer[
                                          match.end():]  # Return the sentence and the remaining text
    return "", text_buffer


def talk_with_chat_gpt(client, user_input, conversation_history, audio_service):
    """Stream GPT responses and handle function calls like executing system commands."""
    assistant_reply = ""
    text_buffer = ""

    # Starte den Audio-Thread
    audio_thread = threading.Thread(target=audio_service.play_audio)
    audio_thread.start()

    conversation_history.append({"role": "user", "content": user_input})

    # GPT-Antwort streamen
    stream = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=conversation_history,
        stream=True
    )

    # Verarbeite den GPT-Stream
    assistant_reply = process_gpt_stream(stream, audio_service, text_buffer)

    # Signalisiere das Ende des Streams
    audio_service.stop_audio()

    # Warte, bis der Audio-Thread beendet ist
    audio_thread.join()

    # Füge die Antwort in den Gesprächsverlauf ein
    conversation_history.append({"role": "assistant", "content": assistant_reply})

    return assistant_reply


def process_gpt_stream(stream, audio_service, text_buffer):
    """Verarbeite GPT-Stream und führe Sprachverarbeitung aus."""
    assistant_reply = ""

    with concurrent.futures.ThreadPoolExecutor() as executor:
        future = None
        for chunk in stream:
            if chunk.choices[0].delta.content is not None:
                content = chunk.choices[0].delta.content

                format_and_print_content(content)

                assistant_reply += content
                text_buffer += content

                # Satzende erkennen und Sprachverarbeitung starten
                sentence, remaining_text = collect_until_sentence_end(text_buffer)
                if sentence:
                    future = executor.submit(audio_service.process_speech, sentence)
                    text_buffer = remaining_text

        # Verarbeite verbleibenden Text (falls es kein ganzer Satz war).
        if text_buffer:
            future = executor.submit(audio_service.process_speech, text_buffer)

        if future:
            future.result()

    return assistant_reply


def format_and_print_content(content):
    """Formats content for console output."""
    formatted_content = Fore.CYAN + Style.BRIGHT + content + Style.RESET_ALL
    sys.stdout.write(formatted_content)
    sys.stdout.flush()


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

    openai_api_key = os.getenv("OPENAI_API_KEY")
    client = OpenAI(api_key=openai_api_key)

    audio_service = AudioService(client)

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
            reply = talk_with_chat_gpt(
                client, user_input, conversation_history, audio_service)

    except SilenceDetection:
        logger.info("No speech detected. Exiting...")
        audio_service.play_sound(
            os.path.join(script_dir, "resources/sounds/standby.wav"))
        sys.exit()  # Exit the entire script

    except Exception as e:
        logger.error(f"An unexpected error occurred: {e}")
        sys.exit()
