import smtplib


class SmtpConnector:
    """
    A connector class for handling SMTP (email sending) configuration.

    This class is responsible for managing the SMTP connection details required to send emails.
    """

    def __init__(self, smtp_server: str, smtp_user: str, smtp_password: str):
        self.smtp_server = smtp_server
        self.smtp_user = smtp_user
        self.smtp_password = smtp_password

    def connect_and_login(self) -> smtplib.SMTP:
        """
        Establishes a connection to the SMTP server and logs in with the provided credentials.

        Returns:
            smtplib.SMTP: The authenticated SMTP connection object.
        """
        try:
            server = smtplib.SMTP(self.smtp_server)
            server.login(self.smtp_user, self.smtp_password)

            return server
        except Exception as e:
            raise ConnectionError(
                f"Failed to connect or authenticate with SMTP server: {e}"
            )
