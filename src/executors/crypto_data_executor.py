from typing import Any, Dict

from ._executor_interface import ExecutorInterface


class CryptoDataExecutor(ExecutorInterface):
    """
    Executor class for fetching OHLC data for a specific cryptocurrency.

    This executor interacts with the CryptoDataService to retrieve OHLC data for a
    specified cryptocurrency, reference currency, and time range.
    """

    def __init__(self, crypto_data_service):
        self.crypto_data_service = crypto_data_service

    def get_executor_definition(self) -> Dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": "crypto_data_operations",
                "description": (
                    f"Fetches OHLC (Open, High, Low, Close) data for a specific cryptocurrency. "
                    f"Supports specifying a coin, reference currency (e.g., 'usd', 'eur'), and time range (in days)."
                ),
                "parameters": {
                    "type": "object",
                    "properties": {
                        "coin_id": {
                            "type": "string",
                            "description": "The ID of the cryptocurrency (e.g., 'bitcoin', 'ethereum').",
                        },
                        "vs_currency": {
                            "type": "string",
                            "description": "The reference currency (e.g., 'usd', 'eur').",
                            "default": "usd",
                        },
                        "days": {
                            "type": "integer",
                            "description": "The number of days to fetch OHLC data for (e.g., 1, 7, 30).",
                            "default": 7,
                        },
                    },
                    "required": ["coin_id"],
                },
            },
        }

    def exec(self, arguments: Dict[str, Any]) -> str:
        coin_id = arguments.get("coin_id")
        vs_currency = arguments.get("vs_currency", "usd")  # Standardwert 'usd'
        days = arguments.get("days", 7)  # Standardwert 7 Tage

        if not coin_id:
            return "Please provide a valid cryptocurrency coin ID."

        try:
            # Abrufen der OHLC-Daten über den Service
            ohlc_data = self.crypto_data_service.get_ohlc(
                coin_id=coin_id, vs_currency=vs_currency, days=days
            )
        except Exception as e:
            return f"An error occurred while fetching data: {str(e)}"

        if not ohlc_data:
            return f"No OHLC data found for {coin_id}."

        # Formatieren der OHLC-Daten für die Ausgabe
        formatted_data = "\n".join(
            [
                f"Date: {ohlc[0]}, Open: {ohlc[1]}, High: {ohlc[2]}, Low: {ohlc[3]}, Close: {ohlc[4]}"
                for ohlc in ohlc_data
            ]
        )

        return f"OHLC data for {coin_id} (last {days} days in {vs_currency}):\n{formatted_data}"

    def get_result_interpreter_instructions(self, user_language="en") -> str:
        return (
            "Summarize the OHLC data as short as possible and check if the user needs "
            "further information or action."
            f"Please always answer in Language '{user_language}'"
        )
