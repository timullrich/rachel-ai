from abc import ABC, abstractmethod


class ConnectorInterface(ABC):
    """
    Abstract base class to enforce a consistent connection interface for various API connectors.
    """

    @abstractmethod
    def connect(self):
        """
        Establishes the connection to the respective API.
        This method should be implemented by each connector subclass.
        """
        pass
