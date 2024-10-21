import imaplib

class ImapConnector:
    """
    A connector class for handling IMAP (email receiving) configuration.

    This class is responsible for managing the IMAP connection details required to receive emails.
    """

    def __init__(self, imap_server: str, imap_user: str, imap_password: str):
        self.imap_server = imap_server
        self.imap_user = imap_user
        self.imap_password = imap_password

    def connect_and_login(self) -> imaplib.IMAP4_SSL:
        """
        Establishes a connection to the IMAP server and logs in with the provided credentials.

        Returns:
            imaplib.IMAP4_SSL: The authenticated IMAP connection object.
        """
        try:
            mail = imaplib.IMAP4_SSL(self.imap_server)
            mail.login(self.imap_user, self.imap_password)
            return mail
        except Exception as e:
            raise ConnectionError(f"Failed to connect or authenticate with IMAP server: {e}")