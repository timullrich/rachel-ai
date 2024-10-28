import pyowm

from .._connector_interface import ConnectorInterface


class OpenWeatherMapConnector(ConnectorInterface):
    """
    A connector class for handling weather data retrieval via the OpenWeatherMap API.

    This class manages the connection details and API interaction required to get weather data.
    """

    def __init__(self, api_key: str):
        """
        Initializes the connector with the OpenWeatherMap API key.

        Args:
            api_key (str): The API key to authenticate with the OpenWeatherMap service.
        """
        self.api_key = api_key
        self.client = None

    def connect(self):
        """
        Initializes the connection to the OpenWeatherMap API.
        """
        try:
            self.client = pyowm.OWM(self.api_key)
        except Exception as e:
            raise ConnectionError(
                f"Failed to initialize OpenWeatherMap connection: {e}"
            )
