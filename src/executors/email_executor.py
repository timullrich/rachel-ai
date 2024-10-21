from typing import Dict, Any
from ._executor_interface import ExecutorInterface


class EmailExecutor(ExecutorInterface):
    def __init__(self, email_service, username: str):
        self.email_service = email_service
        self.username: str = username

    def get_executor_definition(self) -> Dict[str, Any]:
        return {
            "name": "email_operations",
            "description": f"Performs various email operations like sending, listing emails, fetching, or deleting specific emails. When sending an email, it must include the signature 'some nice greetings' and my name '{self.username}' at the end of the email body.",
            "parameters": {
                "type": "object",
                "properties": {
                    "operation": {
                        "type": "string",
                        "description": "The email operation to perform: 'send', 'list', 'get', 'delete'"
                    },
                    "to": {
                        "type": "string",
                        "description": "Recipient email address (only required for 'send' operation). Always ask before you really send the Email!"
                    },
                    "subject": {
                        "type": "string",
                        "description": "Email subject (only required for 'send' operation)"
                    },
                    "body": {
                        "type": "string",
                        "description": f"Email body text (only required for 'send' operation). Ensure to include the message body followed with some nice greetings and my name '{self.username}' as the signature."
                    },
                    "email_id": {
                        "type": "string",
                        "description": "The ID of the email to retrieve or delete (required for 'get' and 'delete' operations)"
                    },
                    "unread_only": {
                        "type": "boolean",
                        "description": "Whether to list only unread emails (only used for 'list' operation)"
                    },
                    "count": {
                        "type": "integer",
                        "description": "Number of emails to list (only used for 'list' operation)"
                    },
                    "filters": {
                        "type": "object",
                        "description": "Optional filters for listing emails, such as 'from', 'subject', 'before', 'after', 'body', and more.",
                        "properties": {
                            "from": {
                                "type": "string",
                                "description": "Filter emails by the sender's email address (contains match)"
                            },
                            "name": {
                                "type": "string",
                                "description": "Filter emails by the sender's name (contains match)"
                            },
                            "subject": {
                                "type": "string",
                                "description": "Filter emails by the subject (contains match)"
                            },
                            "before": {
                                "type": "string",
                                "description": "Filter emails sent before a specific date (YYYY-MM-DD)"
                            },
                            "after": {
                                "type": "string",
                                "description": "Filter emails sent after a specific date (YYYY-MM-DD)"
                            },
                            "date": {
                                "type": "string",
                                "description": "Filter emails sent on a specific date (YYYY-MM-DD)"
                            },
                            "body": {
                                "type": "string",
                                "description": "Filter emails whose body contains a specific string"
                            }
                        }
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
            return self.email_service.send(to, subject, body)
        elif operation == "list":
            unread_only = arguments.get("unread_only", False)
            count = arguments.get("count", 5)
            filters = arguments.get("filters", {})
            emails = self.email_service.list(count=count, unread_only=unread_only, filters=filters)
            if not emails:
                return "No emails found."
            return "\n".join([f"ID: {email['email_id']}, From: {email['from']}, Subject: {email['subject']}, Date: {email['date']}" for email in emails])
        elif operation == "get":
            email_id = arguments.get("email_id")
            email_content = self.email_service.get(email_id)
            return email_content or f"No email found with ID {email_id}."
        elif operation == "delete":
            email_id = arguments.get("email_id")
            if not email_id:
                return "No email ID provided for deletion."
            success = self.email_service.delete(email_id)
            return f"Email with ID {email_id} successfully deleted." if success else f"Failed to delete email with ID {email_id}."
        else:
            return f"Invalid operation: {operation}"

    def get_result_interpreter_instructions(self, user_language="en") -> str:
        return f"Please summarize the result of the requested email operation and ask if the user needs further actions."
