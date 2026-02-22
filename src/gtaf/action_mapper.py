"""SDK-aligned action normalization wiring."""

from __future__ import annotations

from typing import Any, Dict

from gtaf_sdk.actions import normalize_action


# Deterministic tool-name -> action-prefix mapping used by SDK normalize_action.
TOOL_ACTION_MAPPING: Dict[str, str] = {
    "execute_command": "execute_command",
    "email_operations.send": "email_operations.send",
    "email_operations.list": "email_operations.list",
    "email_operations.get": "email_operations.get",
    "email_operations.delete": "email_operations.delete",
    "contact_operations.list": "contact_operations.list",
    "contact_operations.search": "contact_operations.search",
    "weather_operations.get_weather": "weather_operations.get_weather",
    "weather_operations.get_forecast": "weather_operations.get_forecast",
    "generic_web_scraping": "generic_web_scraping",
    "crypto_data_operations.ohlc": "crypto_data_operations.ohlc",
    "crypto_data_operations.market": "crypto_data_operations.market",
    "spotify_operations.get_user_playlists": "spotify_operations.get_user_playlists",
    "spotify_operations.search_track": "spotify_operations.search_track",
    "spotify_operations.get_track_details": "spotify_operations.get_track_details",
    "spotify_operations.get_liked_songs": "spotify_operations.get_liked_songs",
    "spotify_operations.play_track": "spotify_operations.play_track",
    "spotify_operations.get_available_devices": "spotify_operations.get_available_devices",
    "spotify_operations.pause_playback": "spotify_operations.pause_playback",
    "spotify_operations.skip_to_next_track": "spotify_operations.skip_to_next_track",
    "spotify_operations.get_current_playback_info": "spotify_operations.get_current_playback_info",
    "spotify_operations.add_track_to_queue": "spotify_operations.add_track_to_queue",
    "spotify_operations.add_tracks_to_queue": "spotify_operations.add_tracks_to_queue",
    "spotify_operations.set_volume": "spotify_operations.set_volume",
    "spotify_operations.play_playlist": "spotify_operations.play_playlist",
    "spotify_operations.get_similar_tracks": "spotify_operations.get_similar_tracks",
    "spotify_operations.get_album_details": "spotify_operations.get_album_details",
    "spotify_operations.get_multiple_albums": "spotify_operations.get_multiple_albums",
    "spotify_operations.get_playlist": "spotify_operations.get_playlist",
    "spotify_operations.create_playlist": "spotify_operations.create_playlist",
    "spotify_operations.add_tracks_to_playlist": "spotify_operations.add_tracks_to_playlist",
}


def build_action_id(function_name: str, arguments: Dict[str, Any]) -> str:
    """Build canonical action IDs via gtaf_sdk.actions.normalize_action()."""
    operation = arguments.get("operation")
    tool_name = function_name
    if isinstance(operation, str) and operation.strip():
        tool_name = f"{function_name}.{operation.strip().lower()}"

    return normalize_action(
        tool_name=tool_name,
        arguments=arguments,
        mapping=TOOL_ACTION_MAPPING,
        on_unknown="return_unknown",
    )
