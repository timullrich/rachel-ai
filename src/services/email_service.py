# Standard library imports
import logging

# Email handling imports
from email.mime.text import MIMEText

# Typing imports
from datetime import datetime
from typing import Dict, List, Optional, Any

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

    def list(
            self,
            count: Optional[int] = None,
            from_filter: Optional[str] = None,
            subject_filter: Optional[str] = None,
            unread_only: bool = False,
            date_from: Optional[datetime] = None,
            date_to: Optional[datetime] = None
    ) -> List[Dict[str, str]]:
        """
        Fetches a list of emails with optional filters applied.

        Args:
            count (Optional[int]): The number of emails to search through.
            from_filter (Optional[str]): Filter emails by sender.
            subject_filter (Optional[str]): Filter emails by subject content.
            unread_only (bool): If True, only return unread emails.
            date_from (Optional[datetime]): Start date for filtering emails.
            date_to (Optional[datetime]): End date for filtering emails.

        Returns:
            List[Dict[str, str]]: A list of dictionaries containing email details (subject, from, date).
        """
        self.logger.info(
            f"Fetching emails with filters: count={count}, from_filter={from_filter}, subject_filter={subject_filter}, unread_only={unread_only}, date_from={date_from}, date_to={date_to}")

        try:
            with self.imap_connector.connect_and_login() as mail:
                mail.select_folder("INBOX")

                # Build the search criteria
                search_criteria = ['ALL']  # Default to all emails

                if unread_only:
                    search_criteria.append('UNSEEN')

                if from_filter:
                    search_criteria.extend(['FROM', from_filter])

                if subject_filter:
                    search_criteria.extend(['SUBJECT', subject_filter])

                if date_from:
                    search_criteria.extend(['SINCE', date_from.strftime('%d-%b-%Y')])

                if date_to:
                    search_criteria.extend(['BEFORE', date_to.strftime('%d-%b-%Y')])

                # Search for messages based on the search criteria
                messages = mail.search(search_criteria)

                if not messages:
                    self.logger.info("No emails found.")
                    return []

                # Limit to the last 'count' emails if count is provided
                if count:
                    email_ids = messages[-count:]  # Limit to the last 'count' emails
                else:
                    email_ids = messages

                # Fetch the email details
                emails = []
                for email_id in reversed(email_ids):
                    message_data = mail.fetch([email_id], ['ENVELOPE'])
                    envelope = message_data[email_id][b'ENVELOPE']
                    email_subject = envelope.subject.decode('utf-8')
                    email_from = envelope.from_[0]
                    email_date = envelope.date.strftime('%Y-%m-%d %H:%M:%S')

                    emails.append({
                        "email_id": str(email_id),
                        "subject": email_subject,
                        "from": str(email_from),
                        "date": email_date
                    })

                self.logger.info(f"Successfully fetched {len(emails)} emails.")
                return emails

        except Exception as e:
            self.logger.error(f"Error fetching emails: {e}", exc_info=True)
            raise EmailListingError(f"Error fetching emails: {e}")

    def delete(self, email_ids: Any) -> None:
        """
        Deletes one or more emails with the given email ID(s) from the inbox.

        This method marks the email(s) as deleted and then permanently removes them
        by expunging the mailbox. If any part of the process fails, it raises
        an EmailDeletionError.

        Args:
            email_ids (Union[str, List[str]]): A single email ID or a list of email IDs to delete.

        Raises:
            EmailDeletionError: If any email could not be marked as deleted or permanently expunged.
            Exception: For other general errors during the deletion process.
        """
        # Ensure email_ids is a list to handle both single and multiple emails
        if isinstance(email_ids, str):
            email_ids = [email_ids]

        self.logger.info(f"Attempting to delete emails with IDs {email_ids}")
        try:
            # Connection and login via ImapConnector
            with self.imap_connector.connect_and_login() as mail:
                mail.select_folder("INBOX")  # Select the inbox folder

                # Convert email_ids to integers if necessary
                email_ids = [int(email_id) for email_id in email_ids]

                # Mark the emails for deletion
                response = mail.add_flags(email_ids, ['\\Deleted'])
                if response is None:
                    self.logger.warning(f"Failed to mark emails with IDs {email_ids} as deleted.")
                    raise EmailDeletionError(
                        f"Failed to mark emails with IDs {email_ids} as deleted.")

                # Permanently delete the emails by expunging
                mail.expunge()  # This permanently removes emails marked with \\Deleted
                self.logger.info(f"Successfully deleted emails with IDs {email_ids}")

        except Exception as e:
            self.logger.error(f"Failed to delete emails with IDs {email_ids}: {e}", exc_info=True)
            raise EmailDeletionError(f"Failed to delete emails with IDs {email_ids}: {e}")


