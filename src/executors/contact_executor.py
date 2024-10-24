from typing import Dict, Any
from ._executor_interface import ExecutorInterface


class ContactExecutor(ExecutorInterface):
    def __init__(self, contacts_service):
        self.contacts_service = contacts_service

    def get_executor_definition(self) -> Dict[str, Any]:
        return {
            "name": "contact_operations",
            "description": (
                f"Performs contact listing and search operations. "
                f"Supports 'list' operation to retrieve all contacts and "
                f"'search' to filter contacts by name or email."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "operation": {
                        "type": "string",
                        "description": "The contact operation to perform: 'list' or 'search'",
                    },
                    "search_string": {
                        "type": "string",
                        "description": "The string to search for in contacts' names or emails",
                        "default": "",
                    },
                },
                "required": ["operation"],
            },
        }

    def exec(self, arguments: Dict[str, Any]) -> str:
        operation = arguments.get("operation")
        search_string = arguments.get("search_string", "")

        if operation == "list":
            contacts = self.contacts_service.list()
        elif operation == "search":
            contacts = self.contacts_service.list(search_string)
        else:
            return f"Invalid operation: {operation}"

        if not contacts:
            return "No contacts found."

        return "\n".join(
            [
                f"Name: {contact['name']}, Emails: {', '.join(contact['emails'])}, Phones: {', '.join(contact['phones'])}"
                for contact in contacts
            ]
        )

    def get_result_interpreter_instructions(self, user_language="en") -> str:
        return (
            "Please summarize the contacts retrieved as short as possible and ask if the user "
            "needs any further action."
            f"Please always answer in Language '{user_language}'"
        )
