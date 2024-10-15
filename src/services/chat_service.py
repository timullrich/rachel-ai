import sys
import re
import threading
import concurrent.futures
from typing import List, Tuple, Dict, Any

from colorama import Fore, Style
from src.connectors.open_ai_connector import OpenAiConnector
from src.services.audio_service import AudioService


class ChatService:
    def __init__(self, openai_connector: OpenAiConnector):
        self.openai_connector: OpenAiConnector = openai_connector
        self.audio_service: AudioService = AudioService(openai_connector)

        self.conversation_history: List[Dict[str, str]] = [{"role": "system", "content": "You are a helpful assistant."}]

    def format_and_print_content(self, content: str) -> None:
        """Formats content for console output."""
        formatted_content: str = Fore.CYAN + Style.BRIGHT + content + Style.RESET_ALL
        sys.stdout.write(formatted_content)
        sys.stdout.flush()

    def collect_until_sentence_end(self, text_buffer: str) -> Tuple[str, str]:
        """Collect text until a sentence end is detected (., !, ?)."""
        match = re.search(r'[.!?]', text_buffer)  # Look for sentence-ending punctuation
        if match:
            return text_buffer[:match.end()], text_buffer[match.end():]  # Return the sentence and the remaining text
        return "", text_buffer

    def talk_with_chat_gpt(self, user_input: str, conversation_history: List[Dict[str, str]]) -> str:
        """Stream GPT responses and handle function calls like executing system commands."""

        # starts the audio thread (playing responses)
        audio_thread: threading.Thread = threading.Thread(target=self.audio_service.play_audio)
        audio_thread.start()

        conversation_history.append({"role": "user", "content": user_input})

        # stream chatGPT-response
        stream = self.openai_connector.client.chat.completions.create(
            model="gpt-4o-mini",
            messages=conversation_history,
            stream=True
        )

        # process the chatGPT-Stream
        assistant_reply: str = self.process_gpt_stream(stream)

        # signaling end of stream
        self.audio_service.stop_audio()

        # wait until audio stream ended
        audio_thread.join()

        # adding the reponse to conversation history
        conversation_history.append({"role": "assistant", "content": assistant_reply})

        return assistant_reply

    def process_gpt_stream(self, stream: Any) -> str:
        """process chatGPT-Stream and excecute speech processing."""
        text_buffer: str = ""
        assistant_reply: str = ""

        with concurrent.futures.ThreadPoolExecutor() as executor:
            future: concurrent.futures.Future = None
            for chunk in stream:
                if chunk.choices[0].delta.content is not None:
                    content: str = chunk.choices[0].delta.content

                    self.format_and_print_content(content)

                    assistant_reply += content
                    text_buffer += content

                    # Satzende erkennen und Sprachverarbeitung starten
                    sentence, remaining_text = self.collect_until_sentence_end(text_buffer)
                    if sentence:
                        future = executor.submit(self.audio_service.process_speech, sentence)
                        text_buffer = remaining_text

            # process remaining text (e.g. no complete sentence)
            if text_buffer:
                future = executor.submit(self.audio_service.process_speech, text_buffer)

            if future:
                future.result()

        return assistant_reply
