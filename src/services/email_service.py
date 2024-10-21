# Standard library imports
import logging
import smtplib
import imaplib

# Email handling imports
from email.mime.text import MIMEText
from email.parser import BytesParser

# Typing imports
from datetime import datetime, timedelta
from typing import Dict, List, Optional


class EmailService:
    def __init__(self, smtp_server: str, smtp_user: str, smtp_password: str,
                 imap_server: str, imap_user: str, imap_password: str):
        self.smtp_server = smtp_server
        self.smtp_user = smtp_user
        self.smtp_password = smtp_password
        self.imap_server = imap_server
        self.imap_user = imap_user
        self.imap_password = imap_password
        self.logger = logging.getLogger(self.__class__.__name__)

    def send(self, to: str, subject: str, body: str) -> str:
        """Sends an email via SMTP with error handling and logging."""
        self.logger.info(f"Attempting to send email to {to}")
        try:
            msg = MIMEText(body)
            msg["Subject"] = subject
            msg["From"] = self.smtp_user
            msg["To"] = to

            with smtplib.SMTP(self.smtp_server) as server:
                server.login(self.smtp_user, self.smtp_password)
                server.send_message(msg)

            self.logger.info(f"Email successfully sent to {to}")
            return f"Email successfully sent to {to} with subject '{subject}'."
        except Exception as e:
            self.logger.error(f"Failed to send email to {to}: {e}", exc_info=True)
            raise

    def get(self, id: str) -> Optional[str]:
        """Fetches the content of a specific email with error handling and logging."""
        self.logger.info(f"Attempting to fetch email with ID {id}")
        try:
            with imaplib.IMAP4_SSL(self.imap_server) as mail:
                mail.login(self.imap_user, self.imap_password)
                mail.select("inbox")
                status, message_data = mail.fetch(id, "(RFC822)")

                if status == "OK":
                    email_message = message_data[0][1].decode("utf-8")
                    self.logger.info(f"Successfully fetched email with ID {id}")
                    return email_message
                else:
                    self.logger.warning(f"Failed to fetch email with ID {id}")
                    return None
        except Exception as e:
            self.logger.error(f"Error fetching email with ID {id}: {e}", exc_info=True)
            raise

    from datetime import datetime, timedelta

    def list(self, count: int = 5, unread_only: bool = False,
             filters: Optional[Dict[str, str]] = None) -> List[dict]:
        """
        Lists emails from the inbox.

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

        Default behavior will fetch emails from the last 4 weeks if no time range filter is provided.
        """
        filters = filters or {}

        # Set default "after" filter to 4 weeks ago if no "before" or "after" filter is provided
        if "after" not in filters and "before" not in filters:
            four_weeks_ago = (datetime.now() - timedelta(weeks=4)).strftime("%Y-%m-%d")
            filters["after"] = four_weeks_ago

        operation_type = "unread" if unread_only else "filtered"
        self.logger.info(f"Attempting to list {operation_type} emails with filters: {filters}")

        try:
            with imaplib.IMAP4_SSL(self.imap_server) as mail:
                mail.login(self.imap_user, self.imap_password)
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

                if status == "OK":
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

                            # Filter by sender email (contains match)
                            if "from" in filters and filters[
                                "from"].lower() not in email_from.lower():
                                continue

                            # Filter by sender name (contains match in the "from" field)
                            if "name" in filters and filters[
                                "name"].lower() not in email_from.lower():
                                continue

                            # Filter by subject (contains match)
                            if "subject" in filters and filters[
                                "subject"].lower() not in email_subject.lower():
                                continue

                            # Filter by body content (contains match)
                            if "body" in filters and filters[
                                "body"].lower() not in email_body.lower():
                                continue

                            # Parse the email date and convert to a standard format for comparison
                            try:
                                parsed_date = datetime.strptime(email_date,
                                                                "%a, %d %b %Y %H:%M:%S %z")
                            except ValueError:
                                self.logger.warning(f"Failed to parse date: {email_date}")
                                continue

                            # Filter by specific date (YYYY-MM-DD)
                            if "date" in filters:
                                filter_date = datetime.strptime(filters["date"], "%Y-%m-%d")
                                if parsed_date.date() != filter_date.date():
                                    continue

                            # Add the email to the result list if all filters pass
                            emails.append({
                                "email_id": email_id.decode(),  # Add email_id here
                                "subject": email_subject,
                                "from": email_from,
                                "date": email_date
                            })

                            # Stop collecting emails once the desired count is reached
                            if len(emails) >= count:
                                break

                    self.logger.info(f"Successfully retrieved {operation_type} emails.")
                    return emails
                else:
                    self.logger.warning(f"Failed to retrieve emails.")
                    return []
        except Exception as e:
            self.logger.error(f"Error listing emails: {e}", exc_info=True)
            raise

    def delete(self, email_id: str) -> bool:
        """
        Deletes an email with the given email ID from the inbox.

        Returns True if the email was successfully deleted, False otherwise.
        """
        self.logger.info(f"Attempting to delete email with ID {email_id}")
        try:
            with imaplib.IMAP4_SSL(self.imap_server) as mail:
                mail.login(self.imap_user, self.imap_password)
                mail.select("inbox")

                # Mark the email for deletion
                mail.store(email_id, '+FLAGS', '\\Deleted')

                # Permanently delete the email
                mail.expunge()

                self.logger.info(f"Successfully deleted email with ID {email_id}")
                return True
        except Exception as e:
            self.logger.error(f"Failed to delete email with ID {email_id}: {e}", exc_info=True)
            return False

