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
        # return "Please analyze the result of the previous executed command to the user. Ensure the response is: " \
        #        "Brief and relevant: Avoid unnecessary details. Provide only key insights and point " \
        #        "out anything unusual or noteworthy. If relevant, summarize the outcome instead " \
        #        "of listing all details. " \
        #         "" \
        #        "Ask follow-up questions: If the result could lead to further action, offer clear," \
        #        " concise suggestions or ask if the user needs more details or further actions. " \
        #        "" \
        #        "Error handling: If an error occurs, explain it simply, suggest possible causes, " \
        #        "and recommend logical next steps for resolution. Prioritize solutions. " \
        #        "" \
        #        f"Please always answer in Language '{user_language}'"

        return f"Please explain the output of the previous executed command to the user as short" \
               " as possible and point out the relevant data. Also ask for further instructions! " \
               f"Please always answer in Language '{user_language}'"
