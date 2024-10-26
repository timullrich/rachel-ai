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
                "Supports 'get_user_playlists' for user's playlists, 'search_track' for searching tracks, "
                "'get_track_details' for retrieving details of a specific track, 'get_liked_songs' "
                "for retrieving the user's liked songs, and 'play_track' to play a specific track on an active device."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "operation": {
                        "type": "string",
                        "description": (
                            "The Spotify operation to perform: 'get_user_playlists', 'search_track', "
                            "'get_track_details', 'get_liked_songs', 'play_track'."
                        ),
                    },
                    "query": {
                        "type": "string",
                        "description": (
                            "The search query, required only for 'search_track'. Example: track name or artist name."
                        ),
                    },
                    "track_id": {
                        "type": "string",
                        "description": (
                            "The Spotify track ID, required for 'get_track_details' and 'play_track'. "
                            "Example: Spotify URI or track ID."
                        ),
                    },
                    "limit": {
                        "type": "integer",
                        "description": (
                            "The number of results to return (optional, default is 10). Applicable to 'search_track' and 'get_liked_songs'."
                        ),
                    },
                    "offset": {
                        "type": "integer",
                        "description": (
                            "The index of the first result to return, useful for pagination in 'get_liked_songs'."
                        ),
                    },
                    "device_id": {
                        "type": "string",
                        "description": (
                            "The ID of the device to play the track on (optional). "
                            "Applicable only to 'play_track' operation. If omitted, the currently active device will be used."
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

        if operation == "get_user_playlists":
            try:
                playlists = self.spotify_service.get_user_playlists()
                return json.dumps(playlists)
            except Exception as e:
                return f"Error fetching user playlists: {e}"

        elif operation == "search_track":
            if not query:
                return "Missing required parameter 'query' for 'search_track' operation."
            try:
                tracks = self.spotify_service.search_track(query, limit)
                return json.dumps(tracks)
            except Exception as e:
                return f"Error searching for track '{query}': {e}"

        elif operation == "get_track_details":
            if not track_id:
                return "Missing required parameter 'track_id' for 'get_track_details' operation."
            try:
                track_details = self.spotify_service.get_track_details(track_id)
                return json.dumps(track_details)
            except Exception as e:
                return f"Error fetching track details for ID '{track_id}': {e}"

        elif operation == "get_liked_songs":
            try:
                liked_songs = self.spotify_service.get_liked_songs(limit=limit, offset=offset)
                return json.dumps(liked_songs)
            except Exception as e:
                return f"Error fetching liked songs: {e}"

        elif operation == "play_track":
            if not track_id:
                return "Missing required parameter 'track_id' for 'play_track' operation."
            try:
                playback_message = self.spotify_service.play_track(track_id, device_id=device_id)
                return playback_message
            except Exception as e:
                return f"Error playing track with ID '{track_id}': {e}"

        else:
            return f"Invalid operation: {operation}"

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
            "When retrieving liked songs, if the user requests 'next songs' or 'more songs', "
            "use the 'offset' parameter by incrementing it by the 'limit' (typically 50) to retrieve the next set of songs. "
            f"Always respond in the language '{user_language}'."
        )
