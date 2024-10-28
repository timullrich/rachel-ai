from datetime import datetime
from typing import Any, Dict

from ._executor_interface import ExecutorInterface


class EmailExecutor(ExecutorInterface):
    def __init__(self, email_service, username: str):
        self.email_service = email_service
        self.username: str = username

    def get_executor_definition(self) -> Dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": "email_operations",
                "description": (
                    "Performs various email operations like sending, listing emails, fetching, or deleting specific emails. "
                    f"When sending an email, it must include the signature with some nice greetings and my name '{self.username}' at the end of the email body. "
                    "Always do a new list function call and don't use results from before! For the 'list' operation, at least one filter (e.g., count, from_filter, subject_filter, unread_only, or a date range) must be provided. "
                    "Before sending the email, always ask the user for confirmation explicitly and ensure they respond with 'yes', 'confirm', or a similar affirmative reply. "
                    "If the user does not explicitly confirm, do not send the email. Always clarify the intent to send and wait for explicit confirmation. "
                    "Never assume confirmation unless the user clearly responds affirmatively. For the 'delete' operation, you can provide either a single email ID or a list of email IDs to delete."
                ),
                "parameters": {
                    "type": "object",
                    "properties": {
                        "operation": {
                            "type": "string",
                            "description": "The email operation to perform: 'send', 'list', 'get', 'delete'",
                        },
                        "to": {
                            "type": "string",
                            "description": "Recipient email address (only required for 'send' operation). Always ask before you really send the Email!",
                        },
                        "subject": {
                            "type": "string",
                            "description": "Email subject (only required for 'send' operation)",
                        },
                        "body": {
                            "type": "string",
                            "description": (
                                "Email body text (only required for 'send' operation). Ensure to include the message body followed "
                                "with some nice greetings and my name '{self.username}' as the signature. "
                                "Before sending, always ask for confirmation, and only send if the user responds affirmatively."
                            ),
                        },
                        "email_id": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": (
                                "The ID or a list of IDs of the email(s) to retrieve or delete (required for 'get' and 'delete' operations). "
                                "If providing a list, all listed emails will be processed."
                            ),
                        },
                        "count": {
                            "type": "integer",
                            "description": "Number of emails to search through (only used for 'list' operation). Ignored if date range is provided.",
                        },
                        "from_filter": {
                            "type": "string",
                            "description": "Filter for sender email address (only used for 'list' operation)",
                        },
                        "subject_filter": {
                            "type": "string",
                            "description": "Filter for email subject (only used for 'list' operation)",
                        },
                        "unread_only": {
                            "type": "boolean",
                            "description": "If true, only return unread emails (only used for 'list' operation)",
                        },
                        "date_from": {
                            "type": "string",
                            "description": "Start date for filtering emails (only used for 'list' operation)",
                        },
                        "date_to": {
                            "type": "string",
                            "description": "End date for filtering emails (only used for 'list' operation)",
                        },
                    },
                    "required": ["operation"],
                },
            },
        }

    def exec(self, arguments: Dict[str, Any]) -> str:
        operation = arguments.get("operation")

        if operation == "send":
            to = arguments.get("to")
            subject = arguments.get("subject")
            body = arguments.get("body")
            return self.email_service.send(to, subject, body)

        elif operation == "list":
            count = arguments.get("count")
            from_filter = arguments.get("from_filter")
            subject_filter = arguments.get("subject_filter")
            unread_only = arguments.get("unread_only", False)
            date_from = arguments.get("date_from")
            date_to = arguments.get("date_to")

            if date_from:
                date_from = datetime.strptime(date_from, "%Y-%m-%d")

            if date_to:
                date_to = datetime.strptime(date_to, "%Y-%m-%d")

            if date_from or date_to:
                count = None  # Ignore count if date range is used

            emails = self.email_service.list(
                count=count,
                from_filter=from_filter,
                subject_filter=subject_filter,
                unread_only=unread_only,
                date_from=date_from,
                date_to=date_to,
            )

            if not emails:
                return "No emails found."

            return "\n".join(
                [
                    f"ID: {email['email_id']}, From: {email['from']}, Subject: {email['subject']}, Date: {email['date']}"
                    for email in emails
                ]
            )

        elif operation == "get":

            email_id = arguments.get("email_id")

            # Ensure email_id is a string and not a list

            if isinstance(email_id, list):
                email_id = email_id[0]

            email_content = self.email_service.get(email_id)

            if email_content:
                return email_content

            return f"No email found with ID {email_id}."

        elif operation == "delete":
            email_ids = arguments.get("email_id")
            if not email_ids:
                return "No email ID(s) provided for deletion."

            # Ensure email_ids is a list to handle both single and multiple deletions
            if isinstance(email_ids, str):
                email_ids = [email_ids]

            try:
                self.email_service.delete(email_ids)
                return f"Emails with IDs {email_ids} successfully deleted."
            except Exception as e:
                return f"An unexpected error occurred while deleting emails with IDs {email_ids}: {str(e)}"

        else:
            return f"Invalid operation: {operation}"

    def get_result_interpreter_instructions(self, user_language="en") -> str:
        return (
            f"Please summarize the result of the requested email operation as concisely and clearly as possible. "
            f"Ensure that any numbers (such as counts of emails, file sizes, or other numerical values), dates, and times are "
            f"presented in a human-friendly format, with descriptive context."
            f"Always answer in language '{user_language}'. "
            f"Ask if the user needs further actions or clarification."
        )
