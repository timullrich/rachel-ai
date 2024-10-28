import spotipy
from spotipy.oauth2 import SpotifyOAuth

from .._connector_interface import ConnectorInterface


class SpotifyConnector(ConnectorInterface):
    """
    A connector class for handling Spotify API connection and authentication.
    This class manages the authentication process and initializes the Spotify API client.
    """

    def __init__(self, client_id: str, client_secret: str, redirect_uri: str, scope: str):
        """
        Initializes the connector with Spotify API credentials.

        Args:
            client_id (str): Spotify client ID.
            client_secret (str): Spotify client secret.
            redirect_uri (str): Redirect URI for Spotify authorization.
            scope (str): Scope of permissions required.
        """
        self.client_id = client_id
        self.client_secret = client_secret
        self.redirect_uri = redirect_uri
        self.scope = scope
        self.client = None

    def connect(self):
        """
        Authenticates and initializes the Spotify API client.
        """
        try:
            auth_manager = SpotifyOAuth(
                client_id=self.client_id,
                client_secret=self.client_secret,
                redirect_uri=self.redirect_uri,
                scope=self.scope
            )
            self.client = spotipy.Spotify(auth_manager=auth_manager)
        except Exception as e:
            raise ConnectionError(f"Failed to connect to Spotify API: {e}")
