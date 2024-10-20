from typing import Dict, Any
from ._executor_interface import ExecutorInterface


class EmailExecutor(ExecutorInterface):
    def __init__(self, email_service):
        self.email_service = email_service

    def get_executor_definition(self) -> Dict[str, Any]:
        return {
            "name": "email_operations",
            "description": "Performs various email operations like sending, listing emails, or fetching specific emails.",
            "parameters": {
                "type": "object",
                "properties": {
                    "operation": {
                        "type": "string",
                        "description": "The email operation to perform: 'send', 'list', 'get_email'"
                    },
                    "to": {
                        "type": "string",
                        "description": "Recipient email address (only required for 'send' operation)"
                    },
                    "subject": {
                        "type": "string",
                        "description": "Email subject (only required for 'send' operation)"
                    },
                    "body": {
                        "type": "string",
                        "description": "Email body text (only required for 'send' operation)"
                    },
                    "email_id": {
                        "type": "string",
                        "description": "The ID of the email to retrieve (only required for 'get_email' operation)"
                    },
                    "unread_only": {
                        "type": "boolean",
                        "description": "Whether to list only unread emails (only used for 'list' operation)"
                    },
                    "count": {
                        "type": "integer",
                        "description": "Number of emails to list (only used for 'list' operation)"
                    }
                },
                "required": ["operation"]
            }
        }

    def exec(self, arguments: Dict[str, Any]) -> str:
        operation = arguments.get("operation")

        if operation == "send":
            to = arguments.get("to")
            subject = arguments.get("subject")
            body = arguments.get("body")
            return self.email_service.send_email(to, subject, body)
        elif operation == "list":
            unread_only = arguments.get("unread_only", False)
            count = arguments.get("count", 5)
            emails = self.email_service.list(count=count, unread_only=unread_only)
            if not emails:
                return "No emails found."
            return "\n".join([f"From: {email['from']}, Subject: {email['subject']}, Date: {email['date']}" for email in emails])
        elif operation == "get_email":
            email_id = arguments.get("email_id")
            email_content = self.email_service.get_email(email_id)
            return email_content or f"No email found with ID {email_id}."
        else:
            return f"Invalid operation: {operation}"

    def get_result_interpreter_instructions(self, user_language="en") -> str:
        return f"Please summarize the result of the requested email operation and ask if the user needs further actions."
