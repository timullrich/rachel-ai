# Standard library imports
import logging

# Email handling imports
from email.mime.text import MIMEText
from email.parser import BytesParser

# Typing imports
from datetime import datetime, timedelta
from typing import Dict, List, Optional

# Local application imports
from src.connectors import SmtpConnector, ImapConnector
from src.exceptions import EmailNotFound, EmailDeletionError, EmailListingError


class EmailService:
    def __init__(
            self, smtp_connector: SmtpConnector,
            imap_connector: ImapConnector,
            user_language: str = "en"
    ):
        self.smtp_connector = smtp_connector
        self.imap_connector = imap_connector
        self.user_language = user_language

        self.logger = logging.getLogger(self.__class__.__name__)

    def send(self, to: str, subject: str, body: str) -> str:
        """
        Sends an email to the specified recipient via SMTP.

        This method creates an email message with the given subject and body,
        and uses the SMTP connection provided by the SmtpConnector to send the email.
        It handles errors during the process and logs all significant steps.

        Args:
            to (str): The recipient's email address.
            subject (str): The subject of the email.
            body (str): The body content of the email.

        Returns:
            str: A success message confirming that the email was sent.

        Raises:
            ConnectionError: If the connection or authentication to the SMTP server fails.
            Exception: If any other error occurs during the email sending process.
        """
        self.logger.info(f"Attempting to send email to {to}")
        try:
            msg = MIMEText(body)
            msg["Subject"] = subject
            msg["From"] = self.smtp_connector.smtp_user
            msg["To"] = to

            with self.smtp_connector.connect_and_login() as server:
                server.send_message(msg)

            self.logger.info(f"Email successfully sent to {to}")
            return f"Email successfully sent to {to} with subject '{subject}'."
        except Exception as e:
            self.logger.error(f"Failed to send email to {to}: {e}", exc_info=True)
            raise

    def get(self, email_id: str) -> str:
        """
        Fetches the content of a specific email using its ID.

        Args:
            email_id (str): The ID of the email to fetch.

        Returns:
            str: The raw content of the email as a UTF-8 decoded string.

        Raises:
            EmailNotFoundError: If the email with the given ID cannot be fetched.
            Exception: For any other errors during the fetching process.
        """
        self.logger.info(f"Attempting to fetch email with ID {email_id}")

        try:
            with self.imap_connector.connect_and_login() as mail:
                mail.select_folder("INBOX")  # Use the select_folder method

                # Convert the email_id to integer if necessary
                email_id = int(email_id)

                message_data = mail.fetch([email_id], ['RFC822'])  # Fetch the email using the ID

                # Check if the email was fetched successfully
                if email_id not in message_data:
                    self.logger.warning(f"Failed to fetch email with ID {email_id}")
                    raise EmailNotFound(f"Email with ID {email_id} not found.")

                # Get the email content
                email_message = message_data[email_id][b'RFC822'].decode("utf-8")
                self.logger.info(f"Successfully fetched email with ID {email_id}")
                return email_message

        except Exception as e:
            self.logger.error(f"Error fetching email with ID {email_id}: {e}", exc_info=True)
            raise

    def list(self, count: int = 5) -> List[Dict[str, str]]:
        """
        Fetches the last 'count' received emails from the inbox.

        Args:
            count (int): The number of emails to fetch.

        Returns:
            List[Dict[str, str]]: A list of dictionaries containing email details (subject, from, date).
        """
        self.logger.info(f"Attempting to fetch the last {count} emails")

        try:
            with self.imap_connector.connect_and_login() as mail:
                mail.select_folder("INBOX")  # Select the inbox folder

                # Retrieve the total number of emails
                messages = mail.search(["ALL"])  # Retrieve all email IDs

                if not messages:
                    self.logger.info("No emails found.")
                    return []

                # Get the last 'count' email IDs
                email_ids = messages[-count:]  # Slice the last 'count' emails

                emails = []
                for email_id in reversed(email_ids):  # Reverse to get the newest first
                    # Fetch the email content
                    message_data = mail.fetch([email_id], ['ENVELOPE'])

                    # Extract details
                    envelope = message_data[email_id][b'ENVELOPE']
                    email_subject = envelope.subject.decode('utf-8')
                    email_from = envelope.from_[0]  # Get the first address


                    email_date = envelope.date.strftime('%Y-%m-%d %H:%M:%S')

                    emails.append({
                        "email_id": str(email_id),  # Convert ID to string
                        "subject": email_subject,
                        "from": str(email_from),
                        # Use name or address
                        "date": email_date
                    })

                self.logger.info(f"Successfully fetched the last {count} emails.")
                return emails

        except Exception as e:
            self.logger.error(f"Error fetching emails: {e}", exc_info=True)
            raise EmailListingError(f"Error fetching emails: {e}")

    def delete(self, email_id: str) -> None:
        """
        Deletes an email with the given email ID from the inbox.

        This method marks the email as deleted and then permanently removes it
        by expunging the mailbox. If any part of the process fails, it raises
        an EmailDeletionError.

        Args:
            email_id (str): The ID of the email to delete.

        Raises:
            EmailDeletionError: If the email could not be marked as deleted or permanently expunged.
            Exception: For other general errors during the deletion process.
        """
        self.logger.info(f"Attempting to delete email with ID {email_id}")
        try:
            # Connection and login via ImapConnector
            with self.imap_connector.connect_and_login() as mail:
                mail.select_folder("INBOX")  # Select the inbox folder

                # Convert email_id to integer if necessary
                email_id = int(email_id)

                # Mark the email for deletion
                response = mail.add_flags([email_id], ['\\Deleted'])
                if response is None:
                    self.logger.warning(f"Failed to mark email with ID {email_id} as deleted.")
                    raise EmailDeletionError(f"Failed to mark email with ID {email_id} as deleted.")

                # Permanently delete the email by expunging
                mail.expunge()  # This permanently removes emails marked with \\Deleted
                self.logger.info(f"Successfully deleted email with ID {email_id}")

        except Exception as e:
            self.logger.error(f"Failed to delete email with ID {email_id}: {e}", exc_info=True)
            raise EmailDeletionError(f"Failed to delete email with ID {email_id}: {e}")

