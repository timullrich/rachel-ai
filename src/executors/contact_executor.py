from typing import Dict, Any
from ._executor_interface import ExecutorInterface


class ContactExecutor(ExecutorInterface):
    def __init__(self, contacts_service):
        self.contacts_service = contacts_service

    def get_executor_definition(self) -> Dict[str, Any]:
        return {
            "name": "contact_operations",
            "description": (
                f"Performs contact listing operations. "
                f"Currently supports only the 'list' operation to retrieve all contacts."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "operation": {
                        "type": "string",
                        "description": "The contact operation to perform: 'list'"
                    }
                },
                "required": ["operation"]
            }
        }

    def exec(self, arguments: Dict[str, Any]) -> str:
        operation = arguments.get("operation")

        if operation == "list":
            contacts = self.contacts_service.list()
            if not contacts:
                return "No contacts found."

            return "\n".join([
                f"Name: {contact['name']}, Emails: {', '.join(contact['emails'])}, Phones: {', '.join(contact['phones'])}"
                for contact in contacts
            ])

        else:
            return f"Invalid operation: {operation}"

    def get_result_interpreter_instructions(self, user_language="en") -> str:
        return "Please summarize the contacts retrieved and ask if the user needs any further action."
