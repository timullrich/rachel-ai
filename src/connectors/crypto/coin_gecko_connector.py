from pycoingecko import CoinGeckoAPI


class CoinGeckoConnector:
    """
        A connector class for interacting with the CoinGecko API.

        This class is responsible for initializing a connection to the CoinGecko API and provides methods to
        retrieve cryptocurrency data such as OHLC (Open, High, Low, Close) prices.

        Attributes:
            client (CoinGeckoAPI): The CoinGeckoAPI client used to make requests to CoinGecko's data services.

        Methods:
            get_ohlc_data(coin_id: str, vs_currency: str, days: int):
                Fetches OHLC data for a specific coin and time range.
    """

    def __init__(self):
        self.client = CoinGeckoAPI()