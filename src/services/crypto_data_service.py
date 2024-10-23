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

    def get_daily_ohlc_last_7_days(self, coin_id: str):
        """
        Fetch OHLC data for a specific cryptocurrency for the last 7 days.

        Args:
            coin_id (str): The ID of the cryptocurrency (e.g., 'bitcoin', 'ethereum').

        Returns:
            List: A list of OHLC data where each entry contains [timestamp, open, high, low, close].
        """
        # Auf den Client zugreifen, um OHLC-Daten für die letzten 7 Tage zu erhalten
        return self.connector.client.get_coin_ohlc_by_id(id=coin_id, vs_currency='usd', days=7)
