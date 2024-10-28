import logging
from datetime import datetime, timedelta
from typing import Dict, List

from src.connectors import OpenWeatherMapConnector


class WeatherService:
    """
    A service class for retrieving weather data using the OpenWeatherMapConnector.

    This class is responsible for interacting with the OpenWeatherMapConnector to get current weather details
    and weather forecasts for a given location (e.g., city name).
    """

    def __init__(
        self, weather_connector: OpenWeatherMapConnector, user_language: str = "en"
    ):
        """
        Initializes the WeatherService with the necessary OpenWeatherMapConnector.

        Args:
            weather_connector (OpenWeatherMapConnector): An instance of OpenWeatherMapConnector to handle API communication.
            user_language (str): The language used for user interactions (default is English).
        """
        self.weather_connector = weather_connector
        self.user_language = user_language
        self.logger = logging.getLogger(self.__class__.__name__)

    def get_weather(self, city_name: str) -> Dict:
        """
        Fetches the current weather data and detailed weather information for the specified city.

        Args:
            city_name (str): The name of the city for which to retrieve the weather data.

        Returns:
            Dict

        Raises:
            ConnectionError: If there is a connection issue with the Weather API.
            ValueError: If the city name is invalid or no weather data is found.
        """
        self.logger.info(f"Fetching weather information for {city_name}")

        try:
            self.weather_connector.connect()
            mgr = self.weather_connector.client.weather_manager()
            observation = mgr.weather_at_place(city_name)
            weather = observation.weather

            weather_dict = {
                "status": weather.status,
                "detailed_status": weather.detailed_status,
                "temperature": {
                    "temp": round(weather.temperature("celsius")["temp"]),
                    "temp_min": round(weather.temperature("celsius")["temp_min"]),
                    "temp_max": round(weather.temperature("celsius")["temp_max"]),
                },
                "humidity": weather.humidity,
                "pressure": {
                    "press": weather.pressure["press"],
                    "sea_level": weather.pressure.get("sea_level", None),
                },
                "wind": {
                    "speed": round(weather.wind()["speed"], 1),
                    "deg": weather.wind().get("deg", None),
                },
                "clouds": weather.clouds,
                "rain": weather.rain if hasattr(weather, "rain") else None,
                "snow": weather.snow if hasattr(weather, "snow") else None,
                "visibility_distance": weather.visibility_distance,
            }

            self.logger.info(
                f"Successfully retrieved weather for {city_name}: {weather}"
            )

            return weather_dict

        except Exception as e:
            self.logger.error(
                f"Failed to retrieve weather data for {city_name}: {e}", exc_info=True
            )
            raise ValueError(f"Could not fetch weather data for {city_name}: {e}")

    def get_forecast(self, city_name: str, days: int = 1) -> List[Dict[str, str]]:
        """
        Fetches the weather forecast for a specified number of days (in 3-hour intervals) for a city.

        Args:
            city_name (str): The name of the city for which to retrieve the forecast.
            days (int): The number of days to retrieve the forecast for (default is 1).

        Returns:
            List[Dict[str, str]]: A list of dictionaries containing forecast details, including:
                                  - time: The time of the forecast.
                                  - status: General weather status (e.g., "Clear").
                                  - detailed_status: More specific weather description (e.g., "clear sky").
                                  - temperature: The forecast temperature in Celsius.
                                  - wind_speed: Wind speed in meters per second.
                                  - humidity: Humidity percentage.
        """
        self.logger.info(
            f"Fetching weather forecast for {city_name} for {days} day(s)."
        )

        try:
            self.weather_connector.connect()
            mgr = self.weather_connector.client.weather_manager()

            # Abrufen der 5-Tage-Vorhersage in 3-Stunden-Intervallen
            forecast = mgr.forecast_at_place(city_name, "3h")
            forecast_list = forecast.forecast.weathers

            # Filter forecast data to match the number of requested days (up to 5 days)
            filtered_forecast = [
                {
                    "status": weather.status,
                    "detailed_status": weather.detailed_status,
                    "temperature": {
                        "temp": round(weather.temperature("celsius")["temp"]),
                        "temp_min": round(weather.temperature("celsius")["temp_min"]),
                        "temp_max": round(weather.temperature("celsius")["temp_max"]),
                    },
                    "humidity": weather.humidity,
                    "pressure": {
                        "press": weather.pressure["press"],
                        "sea_level": weather.pressure.get("sea_level", None),
                    },
                    "wind": {
                        "speed": round(weather.wind()["speed"], 1),
                        "deg": weather.wind().get("deg", None),
                    },
                    "clouds": weather.clouds,
                    "rain": weather.rain if hasattr(weather, "rain") else None,
                    "snow": weather.snow if hasattr(weather, "snow") else None,
                    "visibility_distance": weather.visibility_distance,
                }
                for weather in forecast_list
                if self._is_within_days(weather.reference_time("iso"), days)
            ]

            self.logger.info(
                f"Successfully retrieved forecast for {city_name} for {days} day(s)."
            )
            return filtered_forecast

        except Exception as e:
            self.logger.error(
                f"Failed to retrieve forecast data for {city_name}: {e}", exc_info=True
            )
            raise ValueError(f"Could not fetch forecast data for {city_name}: {e}")

    def _is_within_days(self, forecast_time: str, days: int) -> bool:
        """
        Helper function to check if a forecast time falls within the requested number of days.

        Args:
            forecast_time (str): The forecast time as a string in ISO format.
            days (int): The number of days to include in the forecast.

        Returns:
            bool: True if the forecast falls within the requested range of days, False otherwise.
        """
        # Parse the forecast time as an offset-aware datetime and remove the timezone information
        forecast_datetime = datetime.fromisoformat(
            forecast_time.replace("Z", "+00:00")
        ).replace(tzinfo=None)
        current_datetime = (
            datetime.utcnow()
        )  # This is an offset-naive datetime (no timezone)

        # Check if the forecast time is within the specified number of days
        return forecast_datetime <= current_datetime + timedelta(days=days)
