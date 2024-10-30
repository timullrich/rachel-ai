"""
This module defines the CryptoDataExecutor class, which implements the ExecutorInterface to
fetch cryptocurrency data, such as OHLC (Open, High, Low, Close) data and market data, for a
specified cryptocurrency. The data can be retrieved in a specified reference currency and
time range.
"""

from typing import Any, Dict

from ._executor_interface import ExecutorInterface


class CryptoDataExecutor(ExecutorInterface):
    """
    Executor class for fetching OHLC data or market data for a specific cryptocurrency.

    This executor interacts with the CryptoDataService to retrieve either OHLC data or market data
    (current price, market cap, 24-hour volume) for a specified cryptocurrency, reference currency,
    and time range.
    """

    def __init__(self, crypto_data_service):
        self.crypto_data_service = crypto_data_service

    def get_executor_definition(self) -> Dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": "crypto_data_operations",
                "description": (
                    "Fetches OHLC (Open, High, Low, Close) data or market data for a "
                    "specific cryptocurrency. "
                    "Supports 'ohlc' operation to retrieve OHLC data and 'market' "
                    "operation to retrieve current price, market cap, and 24-hour volume."
                ),
                "parameters": {
                    "type": "object",
                    "properties": {
                        "operation": {
                            "type": "string",
                            "description": "The data operation to perform: 'ohlc' or 'market'",
                        },
                        "coin_id": {
                            "type": "string",
                            "description": "The ID of the cryptocurrency "
                                           "(e.g., 'bitcoin', 'ethereum').",
                        },
                        "vs_currency": {
                            "type": "string",
                            "description": "The reference currency (e.g., 'usd', 'eur').",
                            "default": "usd",
                        },
                        "days": {
                            "type": "integer",
                            "description": "The number of days to fetch OHLC data for "
                                           "(e.g., 1, 7, 30). Only required for 'ohlc' operation.",
                            "default": 7,
                        },
                    },
                    "required": ["operation", "coin_id"],
                },
            },
        }

    def exec(self, arguments: Dict[str, Any]) -> str:
        operation = arguments.get("operation")
        coin_id = arguments.get("coin_id")
        vs_currency = arguments.get("vs_currency", "usd")
        days = arguments.get("days", 7)

        if not coin_id:
            return "Please provide a valid cryptocurrency coin ID."

        result = ""

        try:
            if operation == "ohlc":
                # get ohlc data
                ohlc_data = self.crypto_data_service.get_ohlc(
                    coin_id=coin_id, vs_currency=vs_currency, days=days
                )
                if not ohlc_data:
                    result = f"No OHLC data found for {coin_id}."
                else:
                    # format ohlc data
                    formatted_data = "\n".join(
                        [
                            f"Date: {ohlc[0]}, "
                            f"Open: {ohlc[1]}, High: {ohlc[2]}, Low: {ohlc[3]}, Close: {ohlc[4]}"
                            for ohlc in ohlc_data
                        ]
                    )
                    result = f"OHLC data for " \
                             f"{coin_id} (last {days} days in {vs_currency}):\n{formatted_data}"

            elif operation == "market":
                # get market data
                market_data = self.crypto_data_service.get_market_data(
                    coin_id=coin_id, vs_currency=vs_currency
                )
                if not market_data:
                    result = f"No market data found for {coin_id}."
                else:
                    # format market data
                    result = (
                        f"Market data for {coin_id} in {vs_currency}:\n"
                        f"Current Price: {market_data['current_price']}\n"
                        f"Market Cap: {market_data['market_cap']}\n"
                        f"24h Volume: {market_data['volume_24h']}"
                    )
            else:
                result = f"Invalid operation: {operation}"

        except Exception as e:
            result = f"An error occurred while fetching data: {str(e)}"

        return result

    def get_result_interpreter_instructions(self, user_language="en") -> str:
        return (
            "Summarize the cryptocurrency data as short as possible and ask if the user "
            "needs further information or action."
            f"Please always answer in Language '{user_language}'"
        )
