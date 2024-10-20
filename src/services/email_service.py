import smtplib
import imaplib
from email.mime.text import MIMEText
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

    def send_email(self, to: str, subject: str, body: str) -> str:
        """Sends an email via SMTP."""
        try:
            msg = MIMEText(body)
            msg["Subject"] = subject
            msg["From"] = self.smtp_user
            msg["To"] = to

            with smtplib.SMTP(self.smtp_server) as server:
                server.login(self.smtp_user, self.smtp_password)
                server.send_message(msg)

            return f"Email sent to {to} successfully."
        except Exception as e:
            return f"Failed to send email: {e}"

    def list_unread_emails(self) -> List[str]:
        """Lists unread emails from the inbox."""
        try:
            with imaplib.IMAP4_SSL(self.imap_server) as mail:
                mail.login(self.imap_user, self.imap_password)
                mail.select("inbox")
                status, messages = mail.search(None, "UNSEEN")

                if status == "OK":
                    unread_emails = messages[0].split()
                    return unread_emails
                else:
                    return []
        except Exception as e:
            return [f"Error listing unread emails: {e}"]

    def get_email(self, email_id: str) -> Optional[str]:
        """Fetches the content of a specific email."""
        try:
            with imaplib.IMAP4_SSL(self.imap_server) as mail:
                mail.login(self.imap_user, self.imap_password)
                mail.select("inbox")
                status, message_data = mail.fetch(email_id, "(RFC822)")

                if status == "OK":
                    email_message = message_data[0][1].decode("utf-8")
                    return email_message
                else:
                    return None
        except Exception as e:
            return f"Error fetching email: {e}"
