# Standard library imports
import sys
from typing import Any, Dict, List

# Third-party imports
from colorama import Fore, Style

# Local application imports
from src.connectors import OpenAiConnector


class ChatService:
    """
        A service class for interacting with the OpenAI ChatGPT model.

        This class manages conversation history and handles interactions with the OpenAI ChatGPT model.
        It provides methods for sending user inputs to the model, streaming responses, and displaying
        responses in a formatted manner.

        Attributes:
            openai_connector (OpenAiConnector): An instance of OpenAiConnector to interact with the
                OpenAI API.
            conversation_history (List[Dict[str, str]]): A list containing the history of the conversation
                with the model, including both user and assistant messages.

        Methods:
            format_and_print_content(content: str) -> None:
                Formats the given content with color and style for console output and prints it.

            ask_chat_gpt(user_input: str, conversation_history: List[Dict[str, str]]) -> Any:
                Sends user input to the OpenAI ChatGPT model and returns the streaming response.

            print_stream_text(stream: Any) -> str:
                Continuously reads text content from a ChatGPT response stream and prints it
                in real-time.
    """

    def __init__(self, openai_connector: OpenAiConnector):
        self.openai_connector: OpenAiConnector = openai_connector

        self.conversation_history: List[Dict[str, str]] = \
            [{"role": "system", "content": "You are a helpful assistant."}]

    def format_and_print_content(self, content: str) -> None:
        """Formats content for console output."""
        formatted_content: str = Fore.CYAN + Style.BRIGHT + content + Style.RESET_ALL
        sys.stdout.write(formatted_content)
        sys.stdout.flush()

    def ask_chat_gpt(self, user_input: str,
                     conversation_history: List[Dict[str, str]]) -> Any:
        """
        Sends a user input to ChatGPT and returns the streaming response.

        Args:
            user_input (str): The text input from the user.
            conversation_history (List[Dict[str, str]]): The conversation history containing
                                                            previous messages.

        Returns:
            Any: The stream object containing the ChatGPT response.
        """
        conversation_history.append({"role": "user", "content": user_input})

        # Stream ChatGPT response
        stream = self.openai_connector.client.chat.completions.create(
            model="gpt-4o-mini",
            messages=conversation_history,
            stream=True
        )

        return stream

    def print_stream_text(self, stream: Any) -> str:
        """
            Prints text content from a ChatGPT stream continuously.

            Args:
                stream (Any): The ChatGPT stream object containing response chunks.
        """
        text_buffer: str = ""
        assistant_reply: str = ""

        for chunk in stream:
            if chunk.choices[0].delta.content is not None:
                content: str = chunk.choices[0].delta.content

                self.format_and_print_content(content)

                assistant_reply += content
                text_buffer += content

        return assistant_reply
