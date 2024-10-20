import smtplib
import imaplib
import logging
from email.mime.text import MIMEText
from email.parser import BytesParser
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

    def send_email(self, to: str, subject: str, body: str) -> None:
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
        except Exception as e:
            self.logger.error(f"Failed to send email to {to}: {e}", exc_info=True)
            raise

    def list_unread_emails(self) -> List[str]:
        """Lists unread emails from the inbox with error handling and logging."""
        self.logger.info("Attempting to list unread emails.")
        try:
            with imaplib.IMAP4_SSL(self.imap_server) as mail:
                mail.login(self.imap_user, self.imap_password)
                mail.select("inbox")
                status, messages = mail.search(None, "UNSEEN")

                if status == "OK":
                    unread_emails = messages[0].split()
                    self.logger.info(f"Found {len(unread_emails)} unread emails.")
                    return unread_emails
                else:
                    self.logger.warning("No unread emails found.")
                    return []
        except Exception as e:
            self.logger.error(f"Error listing unread emails: {e}", exc_info=True)
            raise

    def get_email(self, email_id: str) -> Optional[str]:
        """Fetches the content of a specific email with error handling and logging."""
        self.logger.info(f"Attempting to fetch email with ID {email_id}")
        try:
            with imaplib.IMAP4_SSL(self.imap_server) as mail:
                mail.login(self.imap_user, self.imap_password)
                mail.select("inbox")
                status, message_data = mail.fetch(email_id, "(RFC822)")

                if status == "OK":
                    email_message = message_data[0][1].decode("utf-8")
                    self.logger.info(f"Successfully fetched email with ID {email_id}")
                    return email_message
                else:
                    self.logger.warning(f"Failed to fetch email with ID {email_id}")
                    return None
        except Exception as e:
            self.logger.error(f"Error fetching email with ID {email_id}: {e}", exc_info=True)
            raise

    def list(self, count: int = 5) -> List[dict]:
        """Lists the last `count` emails from the inbox efficiently."""
        self.logger.info(f"Attempting to list the last {count} emails.")
        try:
            with imaplib.IMAP4_SSL(self.imap_server) as mail:
                mail.login(self.imap_user, self.imap_password)
                mail.select("inbox")

                # Search for the last `count` emails only
                status, messages = mail.search(None, "ALL")

                if status == "OK":
                    email_ids = messages[0].split()

                    # Only fetch the last `count` email IDs (avoid fetching all emails)
                    latest_email_ids = email_ids[-count:]
                    emails = []

                    for email_id in reversed(latest_email_ids):  # Reverse to get newest first
                        status, message_data = mail.fetch(email_id, "(RFC822)")
                        if status == "OK":
                            # Parse the email content
                            email_message = BytesParser().parsebytes(message_data[0][1])
                            emails.append({
                                "subject": email_message.get("subject"),
                                "from": email_message.get("from"),
                                "date": email_message.get("date")
                            })

                    self.logger.info(f"Successfully retrieved the last {count} emails.")
                    return emails
                else:
                    self.logger.warning(f"Failed to retrieve emails.")
                    return []
        except Exception as e:
            self.logger.error(f"Error listing emails: {e}", exc_info=True)
            raise
