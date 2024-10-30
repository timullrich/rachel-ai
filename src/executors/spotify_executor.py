"""
This module defines the SpotifyExecutor class, which implements the ExecutorInterface to
perform various operations with the Spotify API. The SpotifyExecutor class allows for operations
such as searching tracks, retrieving playlists, controlling playback, and managing user libraries.
"""

import json
from typing import Any, Dict

from ._executor_interface import ExecutorInterface


class SpotifyExecutor(ExecutorInterface):
    """
    Executor class for handling Spotify-related operations.

    This class interacts with the SpotifyService to execute a wide range of Spotify actions,
    including searching for tracks, controlling playback, retrieving playlists, and managing
    user libraries. Each operation is designed to handle different Spotify API endpoints.

    Attributes:
        spotify_service (SpotifyService): The service used to interact with Spotify's API.
    """

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
            "type": "function",
            "function": {
                "name": "spotify_operations",
                "description": (
                    "Performs Spotify-related operations. "
                    "Supports 'get_user_playlists', 'search_track', 'get_track_details', "
                    "'get_liked_songs', 'play_track', 'get_available_devices', 'pause_playback', "
                    "'skip_to_next_track', 'get_current_playback_info', 'add_track_to_queue', "
                    "'add_tracks_to_queue', 'set_volume', 'play_playlist', 'get_similar_tracks', "
                    "'get_album_details', 'get_multiple_albums', 'get_playlist', "
                    "'create_playlist', 'add_tracks_to_playlist'."
                ),
                "parameters": {
                    "type": "object",
                    "properties": {
                        "operation": {
                            "type": "string",
                            "description": (
                                "The Spotify operation to perform: 'get_user_playlists', "
                                "'search_track', 'get_track_details', 'get_liked_songs', "
                                "'play_track', 'get_available_devices', 'pause_playback', "
                                "'skip_to_next_track', 'get_current_playback_info', "
                                "'add_track_to_queue', 'add_tracks_to_queue', 'set_volume',"
                                "'play_playlist', 'get_similar_tracks', 'get_album_details', "
                                "'get_multiple_albums', 'get_playlist'."
                            ),
                        },
                        "query": {
                            "type": "string",
                            "description": "The search query, required only for 'search_track'. "
                                           "Example: track name or artist name.",
                        },
                        "seed_track_id": {
                            "type": "string",
                            "description": (
                                "The Spotify track ID to base recommendations on. Required for "
                                "'get_similar_tracks' operation."
                            ),
                        },
                        "track_id": {
                            "type": "string",
                            "description": (
                                "The Spotify track ID, required for 'get_track_details', "
                                "'play_track', and 'add_track_to_queue'."
                            ),
                        },
                        "playlist_id": {
                            "type": "string",
                            "description": (
                                "The Spotify playlist ID, required for 'play_playlist' operation. "
                                "Example: Spotify URI or playlist ID."
                            ),
                        },
                        "track_ids": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": (
                                "A list of Spotify track IDs to add to the playlist or queue. "
                                "Optional for 'create_playlist' (adds tracks upon creation), "
                                "required for 'add_tracks_to_queue' and 'add_tracks_to_playlist'."
                            ),
                        },
                        "limit": {
                            "type": "integer",
                            "description": "The number of results to return "
                                           "(optional, default is 10). Applicable to "
                                           "'search_track', 'get_liked_songs', "
                                           "and 'get_similar_tracks'.",
                        },
                        "offset": {
                            "type": "integer",
                            "description": "The index of the first result to return, useful for "
                                           "pagination in 'get_liked_songs'.",
                        },
                        "device_id": {
                            "type": "string",
                            "description": (
                                "The ID of the device to play or control playback on (optional). "
                                "Applicable to 'play_track', 'pause_playback', "
                                "'skip_to_next_track', and 'add_track_to_queue'."
                            ),
                        },
                        "volume_percent": {
                            "type": "integer",
                            "description": (
                                "The target volume percentage (0 to 100) for "
                                "'set_volume' operation."
                            ),
                        },
                        "album_id": {
                            "type": "string",
                            "description": (
                                "The Spotify album ID, required for 'get_album_details' operation. "
                                "Example: Spotify URI or album ID."
                            ),
                        },
                        "album_ids": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": (
                                "A list of Spotify album IDs to fetch multiple albums. Required "
                                "for 'get_multiple_albums'."
                            ),
                        },
                        "playlist_name": {
                            "type": "string",
                            "description": "The name for the new playlist, required "
                                           "for 'create_playlist'.",
                        },
                        "playlist_description": {
                            "type": "string",
                            "description": "A description for the playlist, optional "
                                           "for 'create_playlist'.",
                        },
                        "public": {
                            "type": "boolean",
                            "description": "Whether the playlist should be public or private. "
                                           "Default is private.",
                        },
                    },
                    "required": ["operation"],
                    "additionalProperties": False,
                },
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
        result = ""

        if operation == "get_user_playlists":
            result = self._get_user_playlists()

        elif operation == "get_playlist":
            result = self._get_playlist(arguments)

        elif operation == "search_track":
            result = self._search_track(arguments)

        elif operation == "get_track_details":
            result = self._get_track_details(arguments)

        elif operation == "get_liked_songs":
            result = self._get_liked_songs(arguments)

        elif operation == "play_track":
            result = self._play_track(arguments)

        elif operation == "play_playlist":
            result = self._play_playlist(arguments)

        elif operation == "get_available_devices":
            result = self._get_available_devices()

        elif operation == "pause_playback":
            result = self._pause_playback(arguments)

        elif operation == "skip_to_next_track":
            result = self._skip_to_next_track(arguments)

        elif operation == "get_current_playback_info":
            result = self._get_current_playback_info()

        elif operation == "add_track_to_queue":
            result = self._add_track_to_queue(arguments)

        elif operation == "add_tracks_to_queue":
            result = self._add_tracks_to_queue(arguments)

        elif operation == "set_volume":
            result = self._set_volume(arguments)

        elif operation == "get_similar_tracks":
            result = self._get_similar_tracks(arguments)

        elif operation == "get_album_details":
            result = self._get_album_details(arguments)

        elif operation == "get_multiple_albums":
            result = self._get_multiple_albums(arguments)

        elif operation == "create_playlist":
            result = self._create_playlist(arguments)

        elif operation == "add_tracks_to_playlist":
            result = self._add_tracks_to_playlist(arguments)

        else:
            result = f"Invalid operation: {operation}"

        return result

    def _get_user_playlists(self) -> str:
        playlists = self.spotify_service.get_user_playlists()
        return json.dumps(playlists)

    def _get_playlist(self, arguments: Dict[str, Any]) -> str:
        playlist_id = arguments.get("playlist_id")
        if not playlist_id:
            return "Missing required parameter 'playlist_id' for 'get_playlist' operation."
        try:
            playlist_data = self.spotify_service.get_playlist(playlist_id)
            return json.dumps(playlist_data)
        except Exception as e:
            return f"Error retrieving playlist details for ID '{playlist_id}': {e}"

    def _search_track(self, arguments: Dict[str, Any]) -> str:
        query = arguments.get("query")
        limit = arguments.get("limit", 10)
        if not query:
            return "Missing required parameter 'query' for 'search_track' operation."
        tracks = self.spotify_service.search_track(query, limit)
        return json.dumps(tracks)

    def _get_track_details(self, arguments: Dict[str, Any]) -> str:
        track_id = arguments.get("track_id")
        if not track_id:
            return "Missing required parameter 'track_id' for 'get_track_details' operation."
        track_details = self.spotify_service.get_track_details(track_id)
        return json.dumps(track_details)

    def _get_liked_songs(self, arguments: Dict[str, Any]) -> str:
        limit = arguments.get("limit", 10)
        offset = arguments.get("offset", 0)
        liked_songs = self.spotify_service.get_liked_songs(limit=limit, offset=offset)
        return json.dumps(liked_songs)

    def _play_track(self, arguments: Dict[str, Any]) -> str:
        track_id = arguments.get("track_id")
        device_id = arguments.get("device_id")
        if not track_id:
            return "Missing required parameter 'track_id' for 'play_track' operation."
        playback_message = self.spotify_service.play_track(track_id, device_id=device_id)
        return playback_message

    def _play_playlist(self, arguments: Dict[str, Any]) -> str:
        playlist_id = arguments.get("playlist_id")
        device_id = arguments.get("device_id")
        if not playlist_id:
            return "Missing required parameter 'playlist_id' for 'play_playlist' operation."
        try:
            playlist_message = self.spotify_service.play_playlist(playlist_id, device_id=device_id)
            return playlist_message
        except Exception as e:
            return f"Error playing playlist with ID '{playlist_id}': {e}"

    def _get_available_devices(self) -> str:
        devices = self.spotify_service.get_available_devices()
        return json.dumps(devices)

    def _pause_playback(self, arguments: Dict[str, Any]) -> str:
        device_id = arguments.get("device_id")
        pause_message = self.spotify_service.pause_playback(device_id=device_id)
        return pause_message

    def _skip_to_next_track(self, arguments: Dict[str, Any]) -> str:
        device_id = arguments.get("device_id")
        skip_message = self.spotify_service.skip_to_next_track(device_id=device_id)
        return skip_message

    def _get_current_playback_info(self) -> str:
        playback_info = self.spotify_service.get_current_playback_info()
        return json.dumps(playback_info) if playback_info else "No active playback found."

    def _add_track_to_queue(self, arguments: Dict[str, Any]) -> str:
        track_id = arguments.get("track_id")
        device_id = arguments.get("device_id")
        if not track_id:
            return "Missing required parameter 'track_id' for 'add_track_to_queue' operation."
        queue_message = self.spotify_service.add_track_to_queue(track_id, device_id=device_id)
        return queue_message

    def _add_tracks_to_queue(self, arguments: Dict[str, Any]) -> str:
        track_ids = arguments.get("track_ids")
        device_id = arguments.get("device_id")
        if not track_ids:
            return "Missing required parameter 'track_ids' for 'add_tracks_to_queue' operation."
        queue_message = self.spotify_service.add_tracks_to_queue(track_ids, device_id=device_id)
        return queue_message

    def _set_volume(self, arguments: Dict[str, Any]) -> str:
        volume_percent = arguments.get("volume_percent")
        device_id = arguments.get("device_id")
        if volume_percent is None:
            return "Missing required parameter 'volume_percent' for 'set_volume' operation."
        try:
            volume_message = self.spotify_service.set_volume(volume_percent, device_id=device_id)
            return volume_message
        except Exception as e:
            return f"Error setting volume to {volume_percent}%: {e}"

    def _get_similar_tracks(self, arguments: Dict[str, Any]) -> str:
        seed_track_id = arguments.get("seed_track_id")
        limit = arguments.get("limit", 10)
        if not seed_track_id:
            return "Missing required parameter 'seed_track_id' for 'get_similar_tracks' operation."
        similar_tracks = self.spotify_service.get_similar_tracks(seed_track_id, limit=limit)
        return json.dumps(similar_tracks)

    def _get_album_details(self, arguments: Dict[str, Any]) -> str:
        album_id = arguments.get("album_id")
        if not album_id:
            return "Missing required parameter 'album_id' for 'get_album_details' operation."
        try:
            album_details = self.spotify_service.get_album_details(album_id)
            return json.dumps(album_details)
        except Exception as e:
            return f"Error fetching album details for ID '{album_id}': {e}"

    def _get_multiple_albums(self, arguments: Dict[str, Any]) -> str:
        album_ids = arguments.get("album_ids")
        if not album_ids:
            return "Missing required parameter 'album_ids' for 'get_multiple_albums' operation."
        try:
            multiple_albums = self.spotify_service.get_multiple_albums(album_ids)
            return json.dumps(multiple_albums)
        except Exception as e:
            return f"Error fetching multiple albums: {e}"

    def _create_playlist(self, arguments: Dict[str, Any]) -> str:
        playlist_name = arguments.get("playlist_name")
        playlist_description = arguments.get("playlist_description", "")
        public = arguments.get("public", False)
        track_ids = arguments.get("track_ids")
        if not playlist_name:
            return "Missing required parameter 'playlist_name' for 'create_playlist' operation."
        try:
            playlist = self.spotify_service.create_playlist(
                name=playlist_name,
                description=playlist_description,
                public=public,
                track_ids=track_ids,
            )
            return json.dumps(playlist)
        except Exception as e:
            return f"Error creating playlist '{playlist_name}': {e}"

    def _add_tracks_to_playlist(self, arguments: Dict[str, Any]) -> str:
        playlist_id = arguments.get("playlist_id")
        track_ids = arguments.get("track_ids")
        if not playlist_id or not track_ids:
            return "Missing required parameters 'playlist_id' and/or 'track_ids' for " \
                   "'add_tracks_to_playlist' operation."
        try:
            message = self.spotify_service.add_tracks_to_playlist(
                playlist_id=playlist_id, track_ids=track_ids
            )
            return message
        except Exception as e:
            return f"Error adding tracks to playlist with ID '{playlist_id}': {e}"


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
            "Always retrieve fresh, real-time data for each request and avoid referring to any "
            "chat history. Provide very brief and general responses, focusing on key points "
            "like artist, album, and track names. Only offer more detailed information, such as "
            "track duration or release dates, if explicitly requested. Confirm actions like adding "
            "to the queue, playback controls (play, pause, volume), and recommendations concisely. "
            "For requests involving paginated data, indicate how users can access additional "
            "results if necessary. "
            f"Always respond in the language '{user_language}'."
        )
