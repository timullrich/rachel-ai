from typing import Dict, Any
from ._executor_interface import ExecutorInterface

class CryptoDataExecutor(ExecutorInterface):
    """
    Executor class for fetching OHLC data for a specific cryptocurrency.

    This executor interacts with the CryptoDataService to retrieve daily OHLC data
    for the last 7 days for a specified cryptocurrency, with USD as the base currency.
    """

    def __init__(self, crypto_data_service):
        self.crypto_data_service = crypto_data_service

    def get_executor_definition(self) -> Dict[str, Any]:
        return {
            "name": "crypto_data_operations",
            "description": (
                f"Fetches OHLC (Open, High, Low, Close) data for a specific cryptocurrency over the last 7 days. "
                f"Supports specifying a coin (e.g., 'bitcoin', 'ethereum') to retrieve data in USD."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "coin_id": {
                        "type": "string",
                        "description": "The ID of the cryptocurrency (e.g., 'bitcoin', 'ethereum')."
                    }
                },
                "required": ["coin_id"]
            }
        }

    def exec(self, arguments: Dict[str, Any]) -> str:
        coin_id = arguments.get("coin_id")

        if not coin_id:
            return "Please provide a valid cryptocurrency coin ID."

        try:
            # Abrufen der OHLC-Daten über den Service
            ohlc_data = self.crypto_data_service.get_daily_ohlc_last_7_days(coin_id=coin_id)
        except Exception as e:
            return f"An error occurred while fetching data: {str(e)}"

        if not ohlc_data:
            return f"No OHLC data found for {coin_id}."

        # Formatieren der OHLC-Daten für die Ausgabe
        formatted_data = "\n".join([
            f"Date: {ohlc[0]}, Open: {ohlc[1]}, High: {ohlc[2]}, Low: {ohlc[3]}, Close: {ohlc[4]}"
            for ohlc in ohlc_data
        ])

        return f"OHLC data for {coin_id} (last 7 days):\n{formatted_data}"

    def get_result_interpreter_instructions(self, user_language="en") -> str:
        return "Summarize the OHLC data and check if the user needs further information or action."
