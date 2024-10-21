# Standard library imports
import logging
import smtplib
import imaplib

# Email handling imports
from email.mime.text import MIMEText
from email.parser import BytesParser

# Typing imports
from typing import List, Optional


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

    def list(self, count: int = 5, unread_only: bool = False) -> List[dict]:
        """
        Lists emails from the inbox.

        If unread_only is True, it lists only unread emails without marking them as read.
        Otherwise, it lists the last `count` emails.
        """
        operation_type = "unread" if unread_only else f"last {count}"
        self.logger.info(f"Attempting to list {operation_type} emails.")
        try:
            with imaplib.IMAP4_SSL(self.imap_server) as mail:
                mail.login(self.imap_user, self.imap_password)
                mail.select("inbox")

                # Search for unread or all emails
                if unread_only:
                    status, messages = mail.search(None, "UNSEEN")
                else:
                    status, messages = mail.search(None, "ALL")

                if status == "OK":
                    email_ids = messages[0].split()

                    # Only fetch the last `count` emails if not listing unread emails
                    if not unread_only:
                        email_ids = email_ids[-count:]

                    emails = []
                    for email_id in reversed(email_ids):  # Reverse to get newest first
                        # Use BODY.PEEK to avoid marking the email as read
                        status, message_data = mail.fetch(email_id, "(BODY.PEEK[HEADER])")
                        if status == "OK":
                            # Parse the email content
                            email_message = BytesParser().parsebytes(message_data[0][1])
                            emails.append({
                                "email_id": email_id.decode(),  # Add email_id here
                                "subject": email_message.get("subject"),
                                "from": email_message.get("from"),
                                "date": email_message.get("date")
                            })

                    self.logger.info(f"Successfully retrieved {operation_type} emails.")
                    return emails
                else:
                    self.logger.warning(f"Failed to retrieve emails.")
                    return []
        except Exception as e:
            self.logger.error(f"Error listing emails: {e}", exc_info=True)
            raise

