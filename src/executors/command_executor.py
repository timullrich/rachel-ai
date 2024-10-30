"""
This module defines the CommandExecutor class, which implements the ExecutorInterface to execute
system commands on a specified platform shell. It supports the execution of commands by writing
them to a temporary shell script and capturing the output, allowing integration with GPT command
execution requests.
"""

import subprocess
import tempfile
from typing import Any, Dict

from ._executor_interface import ExecutorInterface


class CommandExecutor(ExecutorInterface):
    """
    A class to execute system commands on a specified platform shell.

    This class implements the ExecutorInterface and provides methods to define,
    execute, and interpret system commands. Commands are written to a temporary
    shell script file, which is then executed to capture and return the output or errors.

    Attributes:
        platform (str): The platform (e.g., "linux", "macos") on which commands are executed.
        user_language (str): The language in which results should be interpreted and presented.
    """

    def __init__(self, platform: str, user_language: str = "en"):
        self.platform = platform
        self.user_language = user_language

    def get_executor_definition(self) -> Dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": "execute_command",
                "description": f"Executes a system command on the {self.platform} shell!",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "command": {
                            "type": "string",
                            "description": "The shell command to be executed",
                        }
                    },
                    "required": ["command"],
                },
            },
        }

    def exec(self, arguments: Dict[str, Any]) -> str:
        command = arguments.get("command")
        if command:
            try:
                # Schreibe das Kommando in eine temporäre Datei, um es direkt auszuführen
                with tempfile.NamedTemporaryFile(
                    "w", delete=False, suffix=".sh"
                ) as temp_file:
                    # Schreibe den Befehl und überprüfe die Syntax für sed -i '' auf macOS
                    if "sed -i ''" in command:
                        command = command.replace("sed -i ''", "sed -i ''")
                    temp_file.write(command)
                    temp_file_path = temp_file.name

                # execute temp file in shell
                result = subprocess.run(
                    f"bash {temp_file_path}", shell=True, capture_output=True, text=True,
                    check=False
                )

                # remove temp file
                temp_file.close()

                # combine stdout und stderr to get all infos
                output = result.stdout.strip()
                error = result.stderr.strip()

                if result.returncode == 0:
                    return output if output else "Command executed successfully."

                return (
                    f"Command returned non-zero exit code {result.returncode}.\n"
                    f"Output: {output}\nError: {error}"
                )
            except Exception as e:
                return f"Error executing command: {e}"
        return "No command provided."

    def get_result_interpreter_instructions(self, user_language: str = "en") -> str:
        return (
            "Analyze the user's request and provide the response as briefly as possible. "
            "If the user's request contains indications for specific details, a list, or "
            "extended information, provide an appropriately detailed response. If unsure whether "
            "further details are needed, ask the user."
            f"Always respond in the language '{user_language}'. "
        )
