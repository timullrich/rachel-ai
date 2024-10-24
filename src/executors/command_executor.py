import subprocess
from typing import Dict, Any

from ._executor_interface import ExecutorInterface


class CommandExecutor(ExecutorInterface):
    def get_executor_definition(self) -> Dict[str, Any]:
        return {
            "name": "execute_command",
            "description": "Executes a system command on the Linux OS",
            "parameters": {
                "type": "object",
                "properties": {
                    "command": {
                        "type": "string",
                        "description": "The shell command to be executed"
                    }
                },
                "required": ["command"]
            }
        }

    def exec(self, arguments: Dict[str, Any]) -> str:
        command = arguments.get("command")
        if command:
            try:
                result = subprocess.run(command, shell=True, capture_output=True, text=True)
                if result.returncode == 0:
                    return result.stdout.strip()
                else:
                    return f"Command failed: {result.stderr.strip()}"
            except Exception as e:
                return f"Error executing command: {e}"
        return "No command provided."

    def get_result_interpreter_instructions(self, user_language="en") -> str:
        return f"Please explain the output of the previous executed command to the user as short" \
               " as possible. Also ask for further instructions! " \
               f"Please always answer in Language '{user_language}'"
