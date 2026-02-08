"""
This module provides the ChatService class for interacting with the OpenAI ChatGPT model.

The ChatService class manages conversation history, handles user interactions, and streams
responses from the model. It supports various methods for sending user inputs, formatting,
and outputting responses.
"""

# Standard library imports
import json
import logging
import sys
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

# Third-party imports
from colorama import Fore, Style
from openai._streaming import Stream
from openai.types.chat.chat_completion_chunk import ChatCompletionChunk

# Local application imports
from src.connectors import OpenAiConnector, StreamSplitter
from src.exceptions import FunctionNotFound
from src.executors import ExecutorInterface
from src.gtaf.action_mapper import build_action_id
from src.gtaf.runtime_client import GtafRuntimeClient


@dataclass(frozen=True)
class FunctionCallOutcome:
    result: str
    executor: ExecutorInterface
    denied: bool
    reason_code: Optional[str] = None


class ChatService:
    """
    A service class for interacting with the OpenAI ChatGPT model.

    This class manages conversation history and handles interactions with the OpenAI ChatGPT model.
    It provides methods for sending user inputs to the model, streaming responses, and displaying
    responses in a formatted manner.

    Attributes:
        openai_connector (OpenAiConnector): An instance of OpenAiConnector to interact with the
            OpenAI API.
        executors (List[ExecutorInterface]): A list of available executors that can handle tasks.
        conversation_history (List[Dict[str, str]]): A list containing the history
                                                        of the conversation
                                                        with the model, including both user and
                                                        assistant messages.

        Methods:
            ask_chat_gpt(
                user_input: str,
                conversation_history: List[Dict[str, str]])
                    -> Stream[ChatCompletionChunk]:
                Sends user input to the OpenAI ChatGPT model and returns the streaming response.

            print_stream_text(stream: Stream[ChatCompletionChunk]) -> str:
                Continuously reads text content from a ChatGPT response stream and prints it
                in real-time.

            format_and_print_content(content: str) -> None:
                Formats the given content with color and style for console output and prints it.
    """

    def __init__(
        self,
        openai_connector: OpenAiConnector,
        user_language="en",
        executors: Optional[List[ExecutorInterface]] = None,
        gtaf_runtime_client: Optional[GtafRuntimeClient] = None,
        gtaf_context_defaults: Optional[Dict[str, str]] = None,
    ):
        self.openai_connector: OpenAiConnector = openai_connector
        self.openai_connector.connect()
        self.logger = logging.getLogger(self.__class__.__name__)
        self.user_language = user_language
        self.executors: List[ExecutorInterface] = executors or []
        self.gtaf_runtime_client = gtaf_runtime_client
        self.gtaf_context_defaults = gtaf_context_defaults or {}
        self.current_mode = "text"
        self.conversation_history: List[Dict[str, str]] = [
            {"role": "system", "content": "You are a helpful assistant."}
        ]

    def ask_chat_gpt(
        self, user_input: str, conversation_history: List[Dict[str, str]], mode: str = "text"
    ) -> Stream[ChatCompletionChunk]:
        """
        Sends user input to the OpenAI ChatGPT model and processes the streaming response.

        Args:
            user_input (str): The user's input message.
            conversation_history (List[Dict[str, str]]): The conversation history to
                                                            maintain context.

        Returns:
            Any: A streaming response from ChatGPT, which can either be normal text or
                    a function call result.

        Raises:
            FunctionNotFoundError: If no executor is found for the given function name.
        """
        self.logger.info("Sending user input to GPT: %s", user_input)
        self.current_mode = mode
        conversation_history.append({"role": "user", "content": user_input})

        # Stream GPT response
        stream = self.openai_connector.client.chat.completions.create(
            model="gpt-4o-mini",
            messages=conversation_history,
            stream=True,
            parallel_tool_calls=False,
            tools=[executor.get_executor_definition() for executor in self.executors],
        )

        # Split the stream for inspection
        splitter = StreamSplitter(stream)
        splitter.start()

        # Initialize variables for function call handling
        function_call_name = None
        function_call_arguments = ""

        first_chunk: ChatCompletionChunk = next(splitter.get())
        choice = first_chunk.choices[0].delta

        # Check if it's a function call
        if hasattr(choice, "tool_calls") and choice.tool_calls is not None:
            self.logger.info(
                "Function call detected: %s", choice.tool_calls[0].function.name
            )

            for chunk in splitter.get():
                choice = chunk.choices[0].delta

                # Get the function call name from the first chunk
                if (
                    hasattr(choice, "tool_calls")
                    and choice.tool_calls is not None
                    and choice.tool_calls[0].function is not None
                ):
                    if function_call_name is None:
                        function_call_name = choice.tool_calls[
                            0
                        ].function.name  # Store the function name
                    if choice.tool_calls[0].function.arguments:
                        # Collect arguments
                        function_call_arguments += choice.tool_calls[
                            0
                        ].function.arguments

            # Process the function call if detected
            if function_call_name:
                self.logger.info(
                    "Executing function: %s with arguments: %s",
                    function_call_name,
                    function_call_arguments,
                )
                arguments = json.loads(function_call_arguments)
                outcome = self.handle_function_call(function_call_name, arguments)

                # Create the interpretation request for GPT
                conversation_history.append({"role": "system", "content": outcome.result})

                if outcome.denied:
                    conversation_history.append(
                        {
                            "role": "system",
                            "content": (
                                "The last tool call was denied by GTAF governance enforcement. "
                                f"Reason code: {outcome.reason_code}. "
                                "Explain briefly and clearly that the action is not delegated "
                                "and therefore was not executed. Keep the answer concise and "
                                "natural. In German voice conversations, include a clear refusal "
                                "like 'Zugriff verweigert'."
                            ),
                        }
                    )
                else:
                    conversation_history.append(
                        {
                            "role": "system",
                            "content": outcome.executor.get_result_interpreter_instructions(
                                user_language=self.user_language
                            ),
                        }
                    )

                interpretation_request = {
                    "model": "gpt-4o-mini",
                    "messages": conversation_history,
                }

                # Return the interpreted executor result stream
                interpreted_stream = (
                    self.openai_connector.client.chat.completions.create(
                        model="gpt-4o-mini",
                        messages=interpretation_request["messages"],
                        stream=True,
                    )
                )
                return interpreted_stream

        # Normal content stream
        self.logger.info("Returning normal content stream.")
        return splitter.get()

    def handle_function_call(
        self, function_name: str, arguments: Dict[str, Any]
    ) -> FunctionCallOutcome:
        """
        Executes the corresponding function based on the function name provided by GPT.

        Args:
            function_name (str): The name of the function to be executed.
            arguments (Dict[str, Any]): The arguments provided by GPT for the function execution.

        Returns:
            str: The result of the function execution.

        Raises:
            FunctionNotFoundError: If no executor is found for the given function name.
        """
        print(
            Fore.MAGENTA + Style.BRIGHT + f"Function call: {function_name} with "
            f"arguments: {arguments}" + Style.RESET_ALL
        )

        self.logger.info(
            "Handling function call: %s with arguments: %s", function_name, arguments
        )

        executor = self._find_executor(function_name)

        if self.gtaf_runtime_client is not None:
            action = build_action_id(function_name, arguments)
            context = dict(self.gtaf_context_defaults)
            context["mode"] = self.current_mode
            decision = self.gtaf_runtime_client.enforce(action=action, context=context)
            self._log_gtaf_decision(action, decision.outcome, decision.reason_code)

            if decision.outcome == "DENY":
                denial_message = (
                    f"GTAF_DENY:{decision.reason_code}. "
                    "Error: Action denied by governance policy and was not executed."
                )
                return FunctionCallOutcome(
                    result=denial_message,
                    executor=executor,
                    denied=True,
                    reason_code=decision.reason_code,
                )

        return FunctionCallOutcome(
            result=executor.exec(arguments),
            executor=executor,
            denied=False,
        )

    def _find_executor(self, function_name: str) -> ExecutorInterface:
        for executor in self.executors:
            if executor.get_executor_definition()["function"]["name"] == function_name:
                return executor

        error_message = f"Function {function_name} not found."
        self.logger.error(error_message)
        raise FunctionNotFound(error_message)

    def _log_gtaf_decision(self, action: str, outcome: str, reason_code: str) -> None:
        if outcome == "EXECUTE":
            print(
                Fore.GREEN
                + Style.BRIGHT
                + f"GTAF EXECUTE: {action}"
                + Style.RESET_ALL
            )
            self.logger.info("GTAF EXECUTE action=%s", action)
            return

        print(
            Fore.RED
            + Style.BRIGHT
            + f"GTAF DENY: {action} reason={reason_code}"
            + Style.RESET_ALL
        )
        self.logger.error("GTAF DENY action=%s reason=%s", action, reason_code)

    def print_stream_text(self, stream: Stream[ChatCompletionChunk]) -> str:
        """
        Prints text content from a ChatGPT stream continuously.

        Args:
            stream (Any): The ChatGPT stream object containing response chunks.

        Returns:
            str: The complete text that was printed.
        """
        text_buffer: str = ""
        assistant_reply: str = ""

        for chunk in stream:
            if chunk.choices[0].delta.content is not None:
                content: str = chunk.choices[0].delta.content

                self.format_and_print_content(content)

                assistant_reply += content
                text_buffer += content

        print()  # adds linebreak at the end
        self.logger.debug(
            "Completed stream output. Total characters: %s", len(assistant_reply)
        )

        return assistant_reply

    def format_and_print_content(self, content: str) -> None:
        """Formats content for console output."""
        formatted_content: str = Fore.CYAN + Style.BRIGHT + content + Style.RESET_ALL
        sys.stdout.write(formatted_content)
        sys.stdout.flush()

        # Logging for debugging
        self.logger.debug(
            "Printed formatted content: %s...", content[:50]
        )  # Truncate long content
