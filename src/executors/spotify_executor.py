import json
from typing import Dict, Any
from ._executor_interface import ExecutorInterface


class SpotifyExecutor(ExecutorInterface):
    def __init__(self, spotify_service):
        """
        Initializes the SpotifyExecutor with the provided SpotifyService.

        Args:
            spotify_service (SpotifyService): The service responsible for Spotify API interactions.
        """
        self.spotify_service = spotify_service

    def get_executor_definition(self) -> Dict[str, Any]:
        """
        Provides a definition of the available operations and parameters.

        Returns:
            Dict[str, Any]: The executor definition including the available Spotify operations.
        """
        return {
            "name": "spotify_operations",
            "description": (
                "Performs Spotify-related operations. "
                "Supports 'get_user_playlists', 'search_track', 'get_track_details', 'get_liked_songs', 'play_track', "
                "'get_available_devices', 'pause_playback', 'skip_to_next_track', 'get_current_playback_info', "
                "and 'add_track_to_queue'."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "operation": {
                        "type": "string",
                        "description": (
                            "The Spotify operation to perform: 'get_user_playlists', 'search_track', 'get_track_details', "
                            "'get_liked_songs', 'play_track', 'get_available_devices', 'pause_playback', "
                            "'skip_to_next_track', 'get_current_playback_info', 'add_track_to_queue', 'set_volume', 'play_playlist'."
                        ),
                    },
                    "query": {
                        "type": "string",
                        "description": "The search query, required only for 'search_track'. Example: track name or artist name.",
                    },
                    "track_id": {
                        "type": "string",
                        "description": (
                            "The Spotify track ID, required for 'get_track_details', 'play_track', and 'add_track_to_queue'."
                        ),
                    },
                    "playlist_id": {
                        "type": "string",
                        "description": (
                            "The Spotify playlist ID, required for 'play_playlist' operation. Example: Spotify URI or playlist ID."
                        ),
                    },
                    "limit": {
                        "type": "integer",
                        "description": "The number of results to return (optional, default is 10). Applicable to 'search_track' and 'get_liked_songs'.",
                    },
                    "offset": {
                        "type": "integer",
                        "description": "The index of the first result to return, useful for pagination in 'get_liked_songs'.",
                    },
                    "device_id": {
                        "type": "string",
                        "description": (
                            "The ID of the device to play or control playback on (optional). "
                            "Applicable to 'play_track', 'pause_playback', 'skip_to_next_track', and 'add_track_to_queue'."
                        ),
                    },
                    "volume_percent": {
                        "type": "integer",
                        "description": (
                            "The target volume percentage (0 to 100) for 'set_volume' operation."
                        ),
                    },
                },
                "required": ["operation"],
                "additionalProperties": False,
            },
        }

    def exec(self, arguments: Dict[str, Any]) -> str:
        """
        Executes the requested Spotify operation.

        Args:
            arguments (Dict[str, Any]): The operation and related parameters for Spotify actions.

        Returns:
            str: The result of the Spotify operation in JSON format or an error message.
        """
        operation = arguments.get("operation")
        query = arguments.get("query")
        track_id = arguments.get("track_id")
        limit = arguments.get("limit", 10)
        offset = arguments.get("offset", 0)
        device_id = arguments.get("device_id")

        try:
            if operation == "get_user_playlists":
                playlists = self.spotify_service.get_user_playlists()
                return json.dumps(playlists)

            elif operation == "search_track":
                if not query:
                    return "Missing required parameter 'query' for 'search_track' operation."
                tracks = self.spotify_service.search_track(query, limit)
                return json.dumps(tracks)

            elif operation == "get_track_details":
                if not track_id:
                    return "Missing required parameter 'track_id' for 'get_track_details' operation."
                track_details = self.spotify_service.get_track_details(track_id)
                return json.dumps(track_details)

            elif operation == "get_liked_songs":
                liked_songs = self.spotify_service.get_liked_songs(limit=limit, offset=offset)
                return json.dumps(liked_songs)

            elif operation == "play_track":
                if not track_id:
                    return "Missing required parameter 'track_id' for 'play_track' operation."
                playback_message = self.spotify_service.play_track(track_id, device_id=device_id)
                return playback_message

            elif operation == "play_playlist":
                playlist_id = arguments.get("playlist_id")
                if not playlist_id:
                    return "Missing required parameter 'playlist_id' for 'play_playlist' operation."
                try:
                    playlist_message = self.spotify_service.play_playlist(playlist_id,
                                                                          device_id=device_id)
                    return playlist_message
                except Exception as e:
                    return f"Error playing playlist with ID '{playlist_id}': {e}"

            elif operation == "get_available_devices":
                devices = self.spotify_service.get_available_devices()
                return json.dumps(devices)

            elif operation == "pause_playback":
                pause_message = self.spotify_service.pause_playback(device_id=device_id)
                return pause_message

            elif operation == "skip_to_next_track":
                skip_message = self.spotify_service.skip_to_next_track(device_id=device_id)
                return skip_message

            elif operation == "get_current_playback_info":
                playback_info = self.spotify_service.get_current_playback_info()
                return json.dumps(playback_info) if playback_info else "No active playback found."

            elif operation == "add_track_to_queue":
                if not track_id:
                    return "Missing required parameter 'track_id' for 'add_track_to_queue' operation."
                queue_message = self.spotify_service.add_track_to_queue(track_id, device_id=device_id)
                return queue_message

            elif operation == "set_volume":
                volume_percent = arguments.get("volume_percent")
                if volume_percent is None:
                    return "Missing required parameter 'volume_percent' for 'set_volume' operation."
                try:
                    volume_message = self.spotify_service.set_volume(volume_percent,
                                                                     device_id=device_id)
                    return volume_message
                except Exception as e:
                    return f"Error setting volume to {volume_percent}%: {e}"
            else:
                return f"Invalid operation: {operation}"

        except Exception as e:
            return f"Error performing operation '{operation}': {e}"

    def get_result_interpreter_instructions(self, user_language="en") -> str:
        """
        Provides instructions for interpreting the result of the Spotify operation.

        Args:
            user_language (str): The language used for user communication (default is English).

        Returns:
            str: Instructions for interpreting the result.
        """
        return (
            "Interpret the Spotify response in a clear, user-friendly format. "
            "For playlist results, list the playlist names and total number of tracks. "
            "For track search results, include the track name, main artist, and album name. "
            "For track details, summarize key information like release date, artist, and album. "
            "For liked songs, list the song names, main artist, and album name. "
            "For playing a track, confirm that the track is now playing and mention the device if specified. "
            "For available devices, list the device names and types. "
            "For pausing playback, confirm that playback is paused. "
            "For skipping to the next track, confirm that the track was skipped. "
            "For current playback info, summarize the track name, artist, and playback position. "
            "For adding a track to the queue, confirm that the track was successfully added. "
            "When retrieving liked songs, if the user requests 'next songs' or 'more songs', "
            "use the 'offset' parameter by incrementing it by the 'limit' (typically 50) to retrieve the next set of songs. "
            f"Always respond in the language '{user_language}'."
        )
