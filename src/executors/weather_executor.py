from typing import Dict, Any
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
                return (
                    f"Weather in {city_name}: {weather_details['description']}, "
                    f"Temperature: {weather_details['temperature']}°C, "
                    f"Humidity: {weather_details['humidity']}%, "
                    f"Wind speed: {weather_details['wind_speed']} m/s"
                )
            except Exception as e:
                return f"Error fetching weather data for {city_name}: {e}"

        elif operation == "get_forecast":
            try:
                # Abrufen der Vorhersage über den WeatherService
                forecast_details = self.weather_service.get_forecast(
                    city_name, days_ahead
                )
                forecast_str = (
                    f"Forecast for {city_name} for the next {days_ahead} day(s):\n"
                )

                for entry in forecast_details:
                    forecast_str += (
                        f"Time: {entry['time']}, "
                        f"Status: {entry['detailed_status']}, "
                        f"Temp: {entry['temperature']}°C, "
                        f"Humidity: {entry['humidity']}%, "
                        f"Wind speed: {entry['wind_speed']} m/s\n"
                    )
                return forecast_str.strip()

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
            "Please summarize the weather or forecast details as short as possible and ask if "
            "the user needs any further information."
            f"Please always answer in Language '{user_language}'"
        )
