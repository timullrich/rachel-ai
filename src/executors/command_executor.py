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
            f"Please explain the output of the previous executed command to the user as short"
            " as possible. Also ask for further instructions! "
            f"Please always answer in Language '{user_language}'"
        )
