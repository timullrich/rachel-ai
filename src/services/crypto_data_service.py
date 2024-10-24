import logging
from typing import List

from src.connectors import CoinGeckoConnector


class CryptoDataService:
    """
    A service class for fetching cryptocurrency data, including OHLC data.

    This class is responsible for interacting with the CoinGeckoConnector to retrieve daily OHLC
    data for a specified cryptocurrency over the last 7 days. The base currency is always USD.

    Attributes:
        connector (CoinGeckoConnector): The CoinGecko API connector used to fetch cryptocurrency data.

    Methods:
        get_daily_ohlc_last_7_days(coin_id: str):
            Fetches daily OHLC data for a specific coin for the last 7 days.
    """

    def __init__(self, connector: CoinGeckoConnector, user_language: str = "en"):
        self.connector = connector
        self.user_language = user_language
        self.logger = logging.getLogger(self.__class__.__name__)

    def get_ohlc(self, coin_id: str, vs_currency: str = "usd", days: int = 7):
        """
        Fetch OHLC data for a specific cryptocurrency.

        Args:
            coin_id (str): The ID of the cryptocurrency (e.g., 'bitcoin', 'ethereum').
            vs_currency (str): The reference currency (e.g., 'usd', 'eur'). Default is 'usd'.
            days (int): The number of days to retrieve data for (e.g., 1, 7, 30). Default is 7.

        Returns:
            List: A list of OHLC data where each entry contains [timestamp, open, high, low, close].
        """
        # Abrufen der OHLC-Daten über den Connector
        return self.connector.client.get_coin_ohlc_by_id(
            id=coin_id, vs_currency=vs_currency, days=days
        )
