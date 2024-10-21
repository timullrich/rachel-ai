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

        This method uses the ImapConnector to connect to the IMAP server, fetches the email with the
        given ID, and logs all significant steps.

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
                mail.select("inbox")
                status, message_data = mail.fetch(email_id, "(RFC822)")

                if status != "OK":
                    self.logger.warning(f"Failed to fetch email with ID {email_id}")
                    raise EmailNotFound(f"Email with ID {email_id} not found.")

                email_message = message_data[0][1].decode("utf-8")
                self.logger.info(f"Successfully fetched email with ID {email_id}")
                return email_message

        except Exception as e:
            self.logger.error(f"Error fetching email with ID {email_id}: {e}", exc_info=True)
            raise

    def list(self, count: int = 5, unread_only: bool = False,
             filters: Optional[Dict[str, str]] = None) -> List[Dict[str, str]]:
        """
        Lists emails from the inbox with optional filtering.

        If unread_only is True, it lists only unread emails without marking them as read.
        Otherwise, it lists the last `count` emails.

        Filters can be passed as a dictionary to filter emails by different fields, e.g.:
            - "from": Filters by the sender's email address (contains match).
            - "name": Filters by the sender's name (contains match).
            - "subject": Filters by the subject of the email (contains match).
            - "before": Filters emails sent before a specific date (format: YYYY-MM-DD).
            - "after": Filters emails sent after a specific date (format: YYYY-MM-DD).
            - "date": Filters emails sent on a specific date (format: YYYY-MM-DD).
            - "body": Filters emails whose body contains a specific string (requires fetching full email content).

        By default, the method fetches emails from the last 4 weeks if no time range is provided.

        Args:
            count (int): The maximum number of emails to return.
            unread_only (bool): Whether to list only unread emails.
            filters (Optional[Dict[str, str]]): A dictionary of filters to apply.

        Returns:
            List[Dict[str, str]]: A list of dictionaries containing email details.

        Raises:
            EmailListingError: If there is an issue retrieving emails.
        """
        filters = filters or {}

        # Set default "after" filter to 4 weeks ago if no "before" or "after" filter is provided
        if "after" not in filters and "before" not in filters:
            four_weeks_ago = (datetime.now() - timedelta(weeks=4)).strftime("%Y-%m-%d")
            filters["after"] = four_weeks_ago

        operation_type = "unread" if unread_only else "filtered"
        self.logger.info(f"Attempting to list {operation_type} emails with filters: {filters}")

        try:
            with self.imap_connector.connect_and_login() as mail:
                mail.select("inbox")

                # Search for unread or all emails
                if unread_only:
                    status, messages = mail.search(None, "UNSEEN")
                else:
                    search_criteria = ["ALL"]

                    # Apply time-based filters (before and after)
                    if "after" in filters:
                        search_criteria.append(
                            f'SINCE {datetime.strptime(filters["after"], "%Y-%m-%d").strftime("%d-%b-%Y")}')
                    if "before" in filters:
                        search_criteria.append(
                            f'BEFORE {datetime.strptime(filters["before"], "%Y-%m-%d").strftime("%d-%b-%Y")}')

                    status, messages = mail.search(None, *search_criteria)

                if status != "OK":
                    raise EmailListingError("Failed to retrieve emails.")

                email_ids = messages[0].split()

                emails = []
                for email_id in reversed(email_ids):  # Reverse to get newest first
                    # Use BODY.PEEK to avoid marking the email as read
                    status, message_data = mail.fetch(email_id,
                                                      "(BODY.PEEK[HEADER] BODY.PEEK[TEXT])")
                    if status == "OK":
                        # Parse the email content
                        email_message = BytesParser().parsebytes(message_data[0][1])
                        email_from = email_message.get("from")
                        email_subject = email_message.get("subject")
                        email_date = email_message.get("date")
                        email_body = message_data[1][1].decode('utf-8',
                                                               errors='ignore')  # Fetch body text

                        # Apply dynamic filters
                        if self._apply_filters(filters, email_from, email_subject, email_body,
                                               email_date):
                            emails.append({
                                "email_id": email_id.decode(),
                                "subject": email_subject,
                                "from": email_from,
                                "date": email_date
                            })

                        # Stop collecting emails once the desired count is reached
                        if len(emails) >= count:
                            break

                self.logger.info(f"Successfully retrieved {operation_type} emails.")
                return emails
        except Exception as e:
            self.logger.error(f"Error listing emails: {e}", exc_info=True)
            raise EmailListingError(f"Error listing emails: {e}")

    def _apply_filters(self, filters: Dict[str, str], email_from: str, email_subject: str,
                       email_body: str, email_date: str) -> bool:
        """
        Applies dynamic filters to the email data.

        Args:
            filters (Dict[str, str]): The filters to apply.
            email_from (str): The email sender's address.
            email_subject (str): The subject of the email.
            email_body (str): The body content of the email.
            email_date (str): The date of the email.

        Returns:
            bool: True if the email passes all filters, False otherwise.
        """
        # Filter by sender email (contains match)
        if "from" in filters and filters["from"].lower() not in email_from.lower():
            return False

        # Filter by sender name (contains match in the "from" field)
        if "name" in filters and filters["name"].lower() not in email_from.lower():
            return False

        # Filter by subject (contains match)
        if "subject" in filters and filters["subject"].lower() not in email_subject.lower():
            return False

        # Filter by body content (contains match)
        if "body" in filters and filters["body"].lower() not in email_body.lower():
            return False

        # Parse the email date and convert to a standard format for comparison
        try:
            parsed_date = datetime.strptime(email_date, "%a, %d %b %Y %H:%M:%S %z")
        except ValueError:
            self.logger.warning(f"Failed to parse date: {email_date}")
            return False

        # Filter by specific date (YYYY-MM-DD)
        if "date" in filters:
            filter_date = datetime.strptime(filters["date"], "%Y-%m-%d")
            if parsed_date.date() != filter_date.date():
                return False

        return True

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
                mail.select("inbox")

                # Mark the email for deletion
                status, _ = mail.store(email_id, '+FLAGS', '\\Deleted')
                if status != "OK":
                    self.logger.warning(f"Failed to mark email with ID {email_id} as deleted.")
                    raise EmailDeletionError(f"Failed to mark email with ID {email_id} as deleted.")

                # Permanently delete the email
                status, _ = mail.expunge()
                if status != "OK":
                    self.logger.warning(f"Failed to expunge deleted email with ID {email_id}.")
                    raise EmailDeletionError(f"Failed to expunge deleted email with ID {email_id}.")

                self.logger.info(f"Successfully deleted email with ID {email_id}")
        except Exception as e:
            self.logger.error(f"Failed to delete email with ID {email_id}: {e}", exc_info=True)
            raise
