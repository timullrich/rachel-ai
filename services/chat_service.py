import sys
import re
import threading
import concurrent.futures

from colorama import Fore, Style

from connectors.open_ai_connector import OpenAiConnector
from services.audio_service import AudioService


class ChatService:
    def __init__(self, openai_connector: OpenAiConnector):
        self.openai_connector = openai_connector
        self.audio_service = AudioService(openai_connector)

        self.conversation_history = [{"role": "system", "content": "You are a helpful assistant."}]

    def format_and_print_content(self, content: str):
        """Formats content for console output."""
        formatted_content = Fore.CYAN + Style.BRIGHT + content + Style.RESET_ALL
        sys.stdout.write(formatted_content)
        sys.stdout.flush()

    def collect_until_sentence_end(self, text_buffer: str):
        """Collect text until a sentence end is detected (., !, ?)."""
        match = re.search(r'[.!?]', text_buffer)  # Look for sentence-ending punctuation
        if match:
            return text_buffer[:match.end()], text_buffer[
                                              match.end():]  # Return the sentence and the remaining text
        return "", text_buffer

    def talk_with_chat_gpt(self, user_input: str, conversation_history):
        """Stream GPT responses and handle function calls like executing system commands."""

        # Starte den Audio-Thread
        audio_thread = threading.Thread(target=self.audio_service.play_audio)
        audio_thread.start()

        conversation_history.append({"role": "user", "content": user_input})

        # GPT-Antwort streamen
        stream = self.openai_connector.client.chat.completions.create(
            model="gpt-4o-mini",
            messages=conversation_history,
            stream=True
        )

        # Verarbeite den GPT-Stream
        assistant_reply = self.process_gpt_stream(stream)

        # Signalisiere das Ende des Streams
        self.audio_service.stop_audio()

        # Warte, bis der Audio-Thread beendet ist
        audio_thread.join()

        # Füge die Antwort in den Gesprächsverlauf ein
        conversation_history.append({"role": "assistant", "content": assistant_reply})

        return assistant_reply

    def process_gpt_stream(self, stream):
        """Verarbeite GPT-Stream und führe Sprachverarbeitung aus."""
        text_buffer = ""
        assistant_reply = ""

        with concurrent.futures.ThreadPoolExecutor() as executor:
            future = None
            for chunk in stream:
                if chunk.choices[0].delta.content is not None:
                    content = chunk.choices[0].delta.content

                    self.format_and_print_content(content)

                    assistant_reply += content
                    text_buffer += content

                    # Satzende erkennen und Sprachverarbeitung starten
                    sentence, remaining_text = self.collect_until_sentence_end(text_buffer)
                    if sentence:
                        future = executor.submit(self.audio_service.process_speech, sentence)
                        text_buffer = remaining_text

            # Verarbeite verbleibenden Text (falls es kein ganzer Satz war).
            if text_buffer:
                future = executor.submit(self.audio_service.process_speech, text_buffer)

            if future:
                future.result()

        return assistant_reply
