"""
This module defines the OpenAiConnector class, which provides functionality for initializing
and managing a connection to the OpenAI API using an API key.
"""

from openai import OpenAI

from .._connector_interface import ConnectorInterface


class OpenAiConnector(ConnectorInterface):
    """
    A connector class for interacting with the OpenAI API.

    This class is responsible for initializing a connection to the OpenAI API using a provided
    API key. It serves as an abstraction layer, making it easier to interact with OpenAI's
    capabilities without directly handling low-level API interactions.

    Attributes:
        client (OpenAI): The OpenAI client initialized with the provided API key, used to
        make requests to OpenAI's various models and services.

    Methods:
        (Currently, no specific methods are defined. The client can be accessed directly for making
        API requests.)
    """

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.client = OpenAI(api_key=api_key)

    def connect(self):
        self.client = OpenAI(api_key=self.api_key)
