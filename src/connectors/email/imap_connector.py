from imapclient import IMAPClient

from .._connector_interface import ConnectorInterface


class ImapConnector(ConnectorInterface):
    """
    A connector class for handling IMAP (email receiving) configuration.

    This class is responsible for managing the IMAP connection details required to receive emails.
    """

    def __init__(self, imap_server: str, imap_user: str, imap_password: str):
        self.imap_server = imap_server
        self.imap_user = imap_user
        self.imap_password = imap_password

    def connect(self) -> IMAPClient:
        """
        Establishes a connection to the IMAP server and logs in with the provided credentials.

        Returns:
            IMAPClient: The authenticated IMAP connection object.
        """
        try:
            # Establish an IMAP connection using SSL
            mail = IMAPClient(self.imap_server, ssl=True)
            # Log in to the IMAP server
            mail.login(self.imap_user, self.imap_password)
            return mail
        except Exception as e:
            raise ConnectionError(
                f"Failed to connect or authenticate with IMAP server: {e}"
            )
