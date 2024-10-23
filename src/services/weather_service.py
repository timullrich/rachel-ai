import logging
from typing import Dict
from src.connectors import OpenWeatherMapConnector


class WeatherService:
    """
    A service class for retrieving weather data using the OpenWeatherMapConnector.

    This class is responsible for interacting with the OpenWeatherMapConnector to get current weather details
    for a given location (e.g., city name).
    """

    def __init__(self, weather_connector: OpenWeatherMapConnector, user_language: str = "en"):
        """
        Initializes the WeatherService with the necessary OpenWeatherMapConnector.

        Args:
            weather_connector (OpenWeatherMapConnector): An instance of OpenWeatherMapConnector to handle API communication.
            user_language (str): The language used for user interactions (default is English).
        """
        self.weather_connector = weather_connector
        self.user_language = user_language
        self.logger = logging.getLogger(self.__class__.__name__)

    def get_weather(self, city_name: str) -> Dict[str, str]:
        """
        Fetches the current weather data and detailed weather information for the specified city.

        Args:
            city_name (str): The name of the city for which to retrieve the weather data.

        Returns:
            Dict[str, str]: A dictionary containing weather details such as:
                            - description: Weather description (e.g., "clear sky")
                            - temperature: Temperature in Celsius
                            - humidity: Humidity percentage
                            - wind_speed: Wind speed in meters per second

        Raises:
            ConnectionError: If there is a connection issue with the Weather API.
            ValueError: If the city name is invalid or no weather data is found.
        """
        self.logger.info(f"Fetching weather information for {city_name}")

        try:
            self.weather_connector.connect()
            # Zugriff auf den OpenWeatherMap client, um Wetterdaten abzurufen
            mgr = self.weather_connector.client.weather_manager()
            observation = mgr.weather_at_place(city_name)
            weather = observation.weather

            # Extrahiere die Wetterdetails
            weather_details = {
                'description': weather.detailed_status,
                'temperature': weather.temperature('celsius')['temp'],
                'humidity': weather.humidity,
                'wind_speed': weather.wind()['speed']
            }

            self.logger.info(f"Successfully retrieved weather for {city_name}: {weather_details}")
            return weather_details

        except Exception as e:
            self.logger.error(f"Failed to retrieve weather data for {city_name}: {e}",
                              exc_info=True)
            raise ValueError(f"Could not fetch weather data for {city_name}: {e}")
