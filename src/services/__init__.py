"""Lazy exports for service classes.

Avoid eager importing heavy optional dependencies during package import
(e.g. audio stack) so lightweight tests can import specific services in isolation.
"""

from importlib import import_module

__all__ = [
    "AudioService",
    "ChatService",
    "EmailService",
    "ContactService",
    "WeatherService",
    "WebScraperService",
    "CryptoDataService",
    "SpotifyService",
]

_MODULE_BY_ATTR = {
    "AudioService": ".audio_service",
    "ChatService": ".chat_service",
    "EmailService": ".email_service",
    "ContactService": ".contact_service",
    "WeatherService": ".weather_service",
    "WebScraperService": ".web_scraper_service",
    "CryptoDataService": ".crypto_data_service",
    "SpotifyService": ".spotify_service",
}


def __getattr__(name: str):
    if name not in _MODULE_BY_ATTR:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

    module = import_module(_MODULE_BY_ATTR[name], __name__)
    value = getattr(module, name)
    globals()[name] = value
    return value


def __dir__():
    return sorted(set(globals().keys()) | set(__all__))
