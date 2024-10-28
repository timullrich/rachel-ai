import json
from typing import Any, Dict

from ._executor_interface import ExecutorInterface


class WeatherExecutor(ExecutorInterface):
    def __init__(self, weather_service):
        """
        Initializes the WeatherExecutor with the provided WeatherService.

        Args:
            weather_service (WeatherService): The service responsible for fetching weather data.
        """
        self.weather_service = weather_service

    def get_executor_definition(self) -> Dict[str, Any]:
        """
        Provides a definition of the available operations and parameters.

        Returns:
            Dict[str, Any]: The executor definition including the available operations.
        """
        return {
            "type": "function",
            "function": {
                "name": "weather_operations",
                "description": (
                    "Performs weather operations. "
                    "Supports 'get_weather' for current weather and 'get_forecast' for weather forecast."
                ),
                "parameters": {
                    "type": "object",
                    "properties": {
                        "operation": {
                            "type": "string",
                            "description": "The weather operation to perform: 'get_weather', 'get_forecast'",
                        },
                        "city_name": {
                            "type": "string",
                            "description": "The name of the city to retrieve the weather data for.",
                        },
                        "days_ahead": {
                            "type": "integer",
                            "description": "Number of days ahead for the forecast (optional, default is 1).",
                        },
                    },
                    "required": ["operation", "city_name"],
                    "additionalProperties": False,
                },
            },
        }

    def exec(self, arguments: Dict[str, Any]) -> str:
        """
        Executes the requested weather operation.

        Args:
            arguments (Dict[str, Any]): The operation, city name, and optional forecast days provided as input.

        Returns:
            str: The result of the weather operation, either current weather or forecast data.
        """
        operation = arguments.get("operation")
        city_name = arguments.get("city_name")
        days_ahead = arguments.get("days_ahead", 1)

        if operation == "get_weather":
            try:
                # Abrufen der aktuellen Wetterdaten über den WeatherService
                weather_details = self.weather_service.get_weather(city_name)
                weather_json = json.dumps(weather_details)
                return weather_json
            except Exception as e:
                return f"Error fetching weather data for {city_name}: {e}"

        elif operation == "get_forecast":
            try:
                # Abrufen der Vorhersage über den WeatherService
                forecast_details = self.weather_service.get_forecast(
                    city_name, days_ahead
                )

                weather_json = json.dumps(forecast_details)
                return weather_json

            except Exception as e:
                return f"Error fetching forecast data for {city_name} (for {days_ahead} day(s)): {e}"

        else:
            return f"Invalid operation: {operation}"

    def get_result_interpreter_instructions(self, user_language="en") -> str:
        """
        Provides instructions for interpreting the result of the weather operation.

        Args:
            user_language (str): The language used for user communication (default is English).

        Returns:
            str: Instructions for interpreting the result.
        """
        return (
            "Interpret the weather forecast in a clear, user-friendly format. "
            "For general questions about the forecast (e.g., whether rain is expected), provide only a brief summary answer. "
            "If the user asks for detailed information (like temperatures, humidity, or specific conditions for each day), include these details as requested. "
            "Always use concise descriptions and avoid excessive details unless explicitly requested. "
            "For multi-day forecasts, summarize key information instead of providing full daily reports unless the user specifically asks. "
            f"Always respond in the language '{user_language}'."
        )
