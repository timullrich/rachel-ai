import sys
import types
import unittest
from dataclasses import dataclass
from typing import Any, Dict

from src.executors import ExecutorInterface


def _install_import_stubs() -> None:
    """Keep this test importable without full optional runtime dependencies."""
    if "colorama" not in sys.modules:
        colorama = types.ModuleType("colorama")
        colorama.Fore = types.SimpleNamespace(MAGENTA="", GREEN="", RED="")
        colorama.Style = types.SimpleNamespace(BRIGHT="", RESET_ALL="")
        sys.modules["colorama"] = colorama

    if "openai" not in sys.modules:
        openai_pkg = types.ModuleType("openai")

        class OpenAI:  # noqa: D401 - tiny stub for imports only
            def __init__(self, *args, **kwargs):
                pass

        openai_pkg.OpenAI = OpenAI
        sys.modules["openai"] = openai_pkg

    if "openai._streaming" not in sys.modules:
        streaming = types.ModuleType("openai._streaming")

        class Stream:  # noqa: D401 - tiny stub for type imports only
            @classmethod
            def __class_getitem__(cls, item):
                return cls

        streaming.Stream = Stream
        sys.modules["openai._streaming"] = streaming

    if "openai.types.chat.chat_completion_chunk" not in sys.modules:
        openai_types = types.ModuleType("openai.types")
        openai_chat = types.ModuleType("openai.types.chat")
        openai_chunk = types.ModuleType("openai.types.chat.chat_completion_chunk")

        class ChatCompletionChunk:  # noqa: D401 - tiny stub for type imports only
            pass

        openai_chunk.ChatCompletionChunk = ChatCompletionChunk
        sys.modules["openai.types"] = openai_types
        sys.modules["openai.types.chat"] = openai_chat
        sys.modules["openai.types.chat.chat_completion_chunk"] = openai_chunk


_install_import_stubs()
from src.services.chat_service import ChatService


class FakeOpenAiConnector:
    def connect(self):
        return None


class FakeExecutor(ExecutorInterface):
    def __init__(self):
        self.called = False

    def get_executor_definition(self) -> Dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": "execute_command",
                "description": "fake",
                "parameters": {"type": "object"},
            },
        }

    def exec(self, arguments: Dict[str, Any]) -> str:
        self.called = True
        return f"executed:{arguments.get('command', '')}"

    def get_result_interpreter_instructions(self, user_language="en") -> str:
        return "interpret"


@dataclass
class FakeDecision:
    outcome: str
    reason_code: str


class FakeGtafClient:
    def __init__(self, outcome: str, reason_code: str = "OK"):
        self.outcome = outcome
        self.reason_code = reason_code

    def enforce(self, action: str, context=None):
        return FakeDecision(outcome=self.outcome, reason_code=self.reason_code)


class TestChatServiceGtaf(unittest.TestCase):
    def test_deny_blocks_executor(self):
        executor = FakeExecutor()
        chat_service = ChatService(
            openai_connector=FakeOpenAiConnector(),
            executors=[executor],
            gtaf_runtime_client=FakeGtafClient("DENY", "DRC_NOT_PERMITTED"),
        )

        outcome = chat_service.handle_function_call(
            "execute_command", {"command": "rm -f test.txt"}
        )

        self.assertTrue(outcome.denied)
        self.assertIn("GTAF_DENY:DRC_NOT_PERMITTED", outcome.result)
        self.assertFalse(executor.called)

    def test_execute_runs_executor(self):
        executor = FakeExecutor()
        chat_service = ChatService(
            openai_connector=FakeOpenAiConnector(),
            executors=[executor],
            gtaf_runtime_client=FakeGtafClient("EXECUTE", "OK"),
        )

        outcome = chat_service.handle_function_call(
            "execute_command", {"command": "date"}
        )

        self.assertFalse(outcome.denied)
        self.assertEqual("executed:date", outcome.result)
        self.assertTrue(executor.called)


if __name__ == "__main__":
    unittest.main()
