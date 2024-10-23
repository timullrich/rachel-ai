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
                f"Performs weather operations. "
                f"Supports 'get_weather' operation to retrieve current weather data for a city."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "operation": {
                        "type": "string",
                        "description": "The weather operation to perform: 'get_weather'"
                    },
                    "city_name": {
                        "type": "string",
                        "description": "The name of the city to retrieve the weather data for."
                    }
                },
                "required": ["operation", "city_name"]
            }
        }

    def exec(self, arguments: Dict[str, Any]) -> str:
        """
        Executes the requested weather operation.

        Args:
            arguments (Dict[str, Any]): The operation and city name provided as input.

        Returns:
            str: The result of the weather operation, usually a description of the weather for the city.
        """
        operation = arguments.get("operation")
        city_name = arguments.get("city_name")

        if operation == "get_weather":
            try:
                # Abrufen der Wetterdaten über den WeatherService
                weather_details = self.weather_service.get_weather(city_name)
                return (
                    f"Weather in {city_name}: {weather_details['description']}, "
                    f"Temperature: {weather_details['temperature']}°C, "
                    f"Humidity: {weather_details['humidity']}%, "
                    f"Wind speed: {weather_details['wind_speed']} m/s"
                )
            except Exception as e:
                return f"Error fetching weather data for {city_name}: {e}"

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
        return "Please summarize the weather details and ask if the user needs any further information."
