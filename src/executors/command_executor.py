import subprocess
import shlex
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
                        "description": "The shell command to be executed",
                    }
                },
                "required": ["command"],
            },
        }

    def exec(self, arguments: Dict[str, Any]) -> str:
        command = arguments.get("command")
        if command:
            try:
                # Verwende shlex.split, um den Befehl in korrekt gesplittete Teile zu zerlegen
                split_command = shlex.split(command)

                # Debug: Optional - Den gesplitteten Befehl anzeigen, um ihn zu überprüfen
                print(f"Split command: {split_command}")

                # Führe den Befehl aus
                result = subprocess.run(
                    split_command, shell=False, capture_output=True, text=True
                )

                # Kombiniere stdout und stderr, um immer alle Infos zu haben
                output = result.stdout.strip()
                error = result.stderr.strip()

                if result.returncode == 0:
                    return output if output else "Command executed successfully."
                else:
                    # Gebe sowohl stdout als auch stderr zurück, wenn ein Fehler auftritt
                    return f"Command returned non-zero exit code {result.returncode}.\nOutput: {output}\nError: {error}"
            except Exception as e:
                return f"Error executing command: {e}"
        return "No command provided."

    def get_result_interpreter_instructions(self, user_language="en") -> str:
        return (
            f"Please interpret the output of the previously executed command based on its nature. "
            f"If the output is structured (like a directory tree or list), display it in a visually organized format. "
            f"For commands that return textual output, explain the result clearly and concisely, "
            f"but do not omit important details. The output should reflect what would be seen in the terminal. "
            f"Always respond in the language '{user_language}'. "
            "If further instructions from the user are needed, ask for clarification. "
            "Always consider the previous user input if it provides more context, but maintain the correct format of the result."
        )

