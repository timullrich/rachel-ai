import subprocess
import tempfile
from typing import Dict, Any

from ._executor_interface import ExecutorInterface


class CommandExecutor(ExecutorInterface):
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

                # Führe die temporäre Datei aus und führe sie in einer Shell aus
                result = subprocess.run(
                    f"bash {temp_file_path}", shell=True, capture_output=True, text=True
                )

                # Entferne die temporäre Datei nach Ausführung
                temp_file.close()

                # Kombiniere stdout und stderr, um immer alle Infos zu haben
                output = result.stdout.strip()
                error = result.stderr.strip()

                if result.returncode == 0:
                    return output if output else "Command executed successfully."
                else:
                    return f"Command returned non-zero exit code {result.returncode}.\nOutput: {output}\nError: {error}"
            except Exception as e:
                return f"Error executing command: {e}"
        return "No command provided."

    def get_result_interpreter_instructions(self, user_language: str = "en") -> str:
        return (
            "Analyze the user's request and provide the response as briefly as possible. "
            "If the user's request contains indications for specific details, a list, or extended information, "
            "provide an appropriately detailed response. If unsure whether further details are needed, ask the user."
            f"Always respond in the language '{user_language}'. "
        )
