# Standard library imports
import sys
import json
from typing import Any, Dict, List

# Third-party imports
from colorama import Fore, Style

# Local application imports
from src.connectors import OpenAiConnector, StreamSplitter
from src.executors import ExecutorInterface

class ChatService:
    """
    A service class for interacting with the OpenAI ChatGPT model.

    This class manages conversation history and handles interactions with the OpenAI ChatGPT model.
        It provides methods for sending user inputs to the model, streaming responses, and displaying
        responses in a formatted manner.

    Attributes:
        openai_connector (OpenAiConnector): An instance of OpenAiConnector to interact with the
            OpenAI API.
        executers (List[ExecutorInterface]): A list of available executors that can handle tasks.
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

    def __init__(
            self,
            openai_connector: OpenAiConnector,
            user_language="en",
            executors: List[ExecutorInterface]=[]
    ):
        self.openai_connector: OpenAiConnector = openai_connector
        self.user_language = user_language
        self.executors: List[ExecutorInterface] = executors
        self.conversation_history: List[Dict[str, str]] = \
            [{"role": "system", "content": "You are a helpful assistant."}]

    def format_and_print_content(self, content: str) -> None:
        """Formats content for console output."""
        formatted_content: str = Fore.CYAN + Style.BRIGHT + content + Style.RESET_ALL
        sys.stdout.write(formatted_content)
        sys.stdout.flush()

    def ask_chat_gpt(self, user_input: str, conversation_history: List[Dict[str, str]]) -> Any:
        conversation_history.append({"role": "user", "content": user_input})

        # Stream GPT response
        stream = self.openai_connector.client.chat.completions.create(
            model="gpt-4o-mini",
            messages=conversation_history,
            stream=True,
            functions=[executor.get_executor_definition() for executor in self.executors],
            function_call="auto"
        )

        # Split the stream for inspection
        splitter = StreamSplitter(stream)
        splitter.start()

        # Check the first chunk
        function_call_name = None
        function_call_arguments = ""

        first_chunk = next(splitter.get())
        choice = first_chunk.choices[0].delta

        # Check if it's a function call
        if hasattr(choice, 'function_call') and choice.function_call is not None:

            for chunk in splitter.get():
                choice = chunk.choices[0].delta

                # Get the function call name from the first chunk
                if hasattr(choice, 'function_call') and choice.function_call is not None:
                    if function_call_name is None:
                        function_call_name = choice.function_call.name  # Store the function name
                    if choice.function_call.arguments:
                        function_call_arguments += choice.function_call.arguments  # Collect arguments

                # Keep collecting arguments across multiple chunks
                if function_call_name and function_call_arguments.endswith('}'):
                    break  # We have all arguments needed, exit the loop

            # Process the function call if detected
            if function_call_name:
                # excecute function
                arguments = json.loads(function_call_arguments)
                result = self.handle_function_call(function_call_name, arguments)

                # Executer-Anweisungen abrufen
                executor = next((e for e in self.executors if
                                 e.get_executor_definition()["name"] == function_call_name), None)
                if not executor:
                    raise Exception(f"No Executer found for function: {function_call_name}")

                # send result to with interpreter instructions to chatGPT
                interpretation_request = {
                    "model": "gpt-4o-mini",
                    "messages": conversation_history + [
                        {"role": "system", "content":
                            executor.get_result_interpreter_instructions(
                                user_language=self.user_language
                            )
                         },
                        {"role": "user", "content": result}
                    ]
                }

                # return interpreted executer result stream
                interpreted_stream = self.openai_connector.client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=interpretation_request["messages"],
                    stream=True
                )
                return interpreted_stream

        else:
            # normal content stream
            return splitter.get()  # Return the original stream

    def handle_function_call(self, function_name: str, arguments: Dict[str, Any]) -> str:
        """
        Executes the corresponding function based on the function name provided by GPT.

        Args:
            function_name (str): The name of the function to be executed.
            arguments (Dict[str, Any]): The arguments provided by GPT for the function execution.

        Returns:
            str: The result of the function execution.
        """
        for executor in self.executors:
            if executor.get_executor_definition()["name"] == function_name:
                return executor.exec(arguments)
        return f"Function {function_name} not found."

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
