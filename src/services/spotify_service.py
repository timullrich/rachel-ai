import logging
from typing import Dict, List, Optional, Any
from src.connectors import SpotifyConnector


class SpotifyService:
    """
    A service class for interacting with the Spotify API using the SpotifyConnector.
    This class provides methods to retrieve current user's playlists, search tracks, and get track details.
    """

    def __init__(self, spotify_connector: SpotifyConnector):
        """
        Initializes the SpotifyService with the required SpotifyConnector.

        Args:
            spotify_connector (SpotifyConnector): An instance of SpotifyConnector to handle API communication.
        """
        self.spotify_connector = spotify_connector
        self.logger = logging.getLogger(self.__class__.__name__)

    def set_volume(self, volume_percent: int, device_id: str = None) -> str:
        """
        Sets the playback volume on the specified device or the active device.

        Args:
            volume_percent (int): The target volume percentage (0 to 100).
            device_id (str, optional): The ID of the device to set the volume on. Defaults to None.

        Returns:
            str: A confirmation message if the volume was successfully set.

        Raises:
            ValueError: If volume_percent is not within the range 0-100.
            ConnectionError: If there is a connection issue with the Spotify API.
        """
        if not 0 <= volume_percent <= 100:
            raise ValueError("Volume must be between 0 and 100.")

        self.logger.info(
            f"Setting volume to {volume_percent}% on device {device_id or 'active device'}.")

        try:
            self.spotify_connector.connect()
            self.spotify_connector.client.volume(volume_percent, device_id=device_id)

            self.logger.info(f"Volume set to {volume_percent}%.")
            return f"Volume set to {volume_percent}% on device {device_id or 'active device'}."

        except Exception as e:
            self.logger.error(f"Failed to set volume to {volume_percent}%.", exc_info=True)
            raise ConnectionError(f"Could not set volume to {volume_percent}%: {e}")

    def get_available_devices(self) -> List[Dict[str, str]]:
        """
        Retrieves a list of available Spotify devices for playback.

        Returns:
            List[Dict[str, str]]: A list of dictionaries containing device details (id, name, type, is_active).

        Raises:
            ConnectionError: If there is a connection issue with the Spotify API.
        """
        self.logger.info("Fetching available devices.")

        try:
            self.spotify_connector.connect()
            devices = self.spotify_connector.client.devices()
            device_list = [
                {
                    "id": device["id"],
                    "name": device["name"],
                    "type": device["type"],
                    "is_active": device["is_active"]
                }
                for device in devices["devices"]
            ]

            self.logger.info(f"Retrieved {len(device_list)} available devices.")
            return device_list

        except Exception as e:
            self.logger.error("Failed to fetch available devices.", exc_info=True)
            raise ConnectionError("Could not fetch available devices.")

    def pause_playback(self, device_id: str = None) -> str:
        """
        Pauses playback on the specified device or the active device.

        Args:
            device_id (str, optional): The ID of the device to pause playback on. Defaults to None.

        Returns:
            str: A confirmation message if playback was successfully paused.

        Raises:
            ConnectionError: If there is a connection issue with the Spotify API.
        """
        self.logger.info(f"Attempting to pause playback on device {device_id or 'active device'}.")

        try:
            self.spotify_connector.connect()
            self.spotify_connector.client.pause_playback(device_id=device_id)

            self.logger.info("Playback paused.")
            return f"Playback paused on device {device_id or 'active device'}."

        except Exception as e:
            self.logger.error("Failed to pause playback.", exc_info=True)
            raise ConnectionError(f"Could not pause playback: {e}")

    def skip_to_next_track(self, device_id: str = None) -> str:
        """
        Skips to the next track in the queue on the specified device or the active device.

        Args:
            device_id (str, optional): The ID of the device to skip on. Defaults to None.

        Returns:
            str: A confirmation message if skip was successful.

        Raises:
            ConnectionError: If there is a connection issue with the Spotify API.
        """
        self.logger.info(
            f"Attempting to skip to the next track on device {device_id or 'active device'}.")

        try:
            self.spotify_connector.connect()
            self.spotify_connector.client.next_track(device_id=device_id)

            self.logger.info("Skipped to the next track.")
            return f"Skipped to the next track on device {device_id or 'active device'}."

        except Exception as e:
            self.logger.error("Failed to skip to the next track.", exc_info=True)
            raise ConnectionError(f"Could not skip to the next track: {e}")

    def get_current_playback_info(self) -> Optional[Dict[str, Any]]:
        """
        Retrieves the current playback information.

        Returns:
            Optional[Dict[str, Any]]: A dictionary containing current playback details, or None if no playback is active.

        Raises:
            ConnectionError: If there is a connection issue with the Spotify API.
        """
        self.logger.info("Fetching current playback information.")

        try:
            self.spotify_connector.connect()
            playback_info = self.spotify_connector.client.current_playback()

            if playback_info:
                return {
                    "is_playing": playback_info["is_playing"],
                    "progress_ms": playback_info["progress_ms"],
                    "track": {
                        "name": playback_info["item"]["name"],
                        "artist": ", ".join(
                            [artist["name"] for artist in playback_info["item"]["artists"]]),
                        "album": playback_info["item"]["album"]["name"],
                        "track_id": playback_info["item"]["id"]
                    },
                    "device": playback_info["device"]["name"] if playback_info["device"] else None
                }
            else:
                self.logger.info("No active playback.")
                return None

        except Exception as e:
            self.logger.error("Failed to fetch current playback information.", exc_info=True)
            raise ConnectionError("Could not fetch current playback information.")

    def get_liked_songs(self, limit: int = 20, offset: int = 0) -> list:
        """
        Retrieves the user's liked songs.

        Args:
            limit (int): The maximum number of tracks to return (default is 20).
            offset (int): The index of the first track to return (useful for pagination).

        Returns:
            list: A list of dictionaries containing liked songs' details.

        Raises:
            ConnectionError: If there is a connection issue with the Spotify API.
        """
        self.logger.info("Fetching liked songs")

        try:
            self.spotify_connector.connect()
            results = self.spotify_connector.client.current_user_saved_tracks(limit=limit,
                                                                              offset=offset)

            liked_songs = [
                {
                    "track_name": item["track"]["name"],
                    "artist": ", ".join(artist["name"] for artist in item["track"]["artists"]),
                    "album": item["track"]["album"]["name"],
                    "added_at": item["added_at"],
                    "track_id": item["track"]["id"]
                }
                for item in results["items"]
            ]

            self.logger.info(f"Retrieved {len(liked_songs)} liked songs")
            return liked_songs

        except Exception as e:
            self.logger.error("Failed to retrieve liked songs.", exc_info=True)
            raise ConnectionError(f"Could not fetch liked songs: {e}")

    def get_user_playlists(self) -> List[Dict]:
        """
        Retrieves the playlists of the authenticated user.

        Returns:
            List[Dict]: A list of dictionaries containing playlist details.

        Raises:
            ConnectionError: If there is a connection issue with the Spotify API.
        """
        self.logger.info("Fetching user playlists.")

        try:
            self.spotify_connector.connect()
            playlists = self.spotify_connector.client.current_user_playlists()
            playlist_data = [
                {
                    "name": playlist["name"],
                    "total_tracks": playlist["tracks"]["total"],
                    "id": playlist["id"],
                    "owner": playlist["owner"]["display_name"]
                }
                for playlist in playlists["items"]
            ]
            self.logger.info("Successfully retrieved user playlists.")
            return playlist_data

        except Exception as e:
            self.logger.error("Failed to retrieve user playlists.", exc_info=True)
            raise ConnectionError(f"Could not fetch user playlists: {e}")

    def search_track(self, query: str, limit: int = 10) -> List[Dict[str, str]]:
        """
        Searches for tracks based on a query string.

        Args:
            query (str): The search query for the track (e.g., track name or artist).
            limit (int): The number of results to return (default is 10).

        Returns:
            List[Dict[str, str]]: A list of dictionaries containing track details (name, artist, and album).

        Raises:
            ConnectionError: If there is a connection issue with the Spotify API.
        """
        self.logger.info(f"Searching for tracks with query: {query}")

        try:
            self.spotify_connector.connect()
            results = self.spotify_connector.client.search(q=query, type="track", limit=limit)
            tracks = [
                {
                    "name": track["name"],
                    "artist": ", ".join([artist["name"] for artist in track["artists"]]),
                    "album": track["album"]["name"],
                    "uri": track["uri"]
                }
                for track in results["tracks"]["items"]
            ]
            self.logger.info(f"Found {len(tracks)} tracks for query '{query}'.")
            return tracks

        except Exception as e:
            self.logger.error("Failed to search tracks.", exc_info=True)
            raise ConnectionError(f"Could not search tracks: {e}")

    def get_track_details(self, track_id: str) -> Optional[Dict[str, str]]:
        """
        Fetches details for a specific track by track ID.

        Args:
            track_id (str): The Spotify track ID.

        Returns:
            Optional[Dict[str, str]]: A dictionary with details about the track (name, artist, album, and release date).

        Raises:
            ConnectionError: If there is a connection issue with the Spotify API.
        """
        self.logger.info(f"Fetching details for track ID: {track_id}")

        try:
            self.spotify_connector.connect()
            track = self.spotify_connector.client.track(track_id)

            audio_features = self.spotify_connector.client.audio_features([track_id])[0]
            track["audio_features"] = audio_features

            self.logger.info(
                f"Successfully retrieved track details, including BPM, for {track['name']}")
            return dict(track)

        except Exception as e:
            self.logger.error("Failed to retrieve track details.", exc_info=True)
            raise ConnectionError(f"Could not fetch track details for {track_id}: {e}")

    def play_track(self, track_id: str, device_id: str = None) -> str:
        """
        Plays a specific track on an active Spotify device.

        Args:
            track_id (str): The Spotify track ID to play.
            device_id (str, optional): The ID of the device to play the track on. Defaults to None,
                                       which will use the currently active device.

        Returns:
            str: A confirmation message if playback was successful.

        Raises:
            ConnectionError: If there is a connection issue with the Spotify API.
        """
        self.logger.info(f"Attempting to play track ID: {track_id}")

        try:
            self.spotify_connector.connect()

            # Start playback for the specified track
            self.spotify_connector.client.start_playback(device_id=device_id,
                                                         uris=[f"spotify:track:{track_id}"])

            self.logger.info(f"Playback started for track ID {track_id}")
            return f"Playing track ID {track_id} on device {device_id or 'default'}."

        except Exception as e:
            self.logger.error(f"Failed to play track ID '{track_id}': {e}", exc_info=True)
            raise ConnectionError(f"Could not start playback for track ID '{track_id}': {e}")

    def add_track_to_queue(self, track_id: str, device_id: str = None) -> str:
        """
        Adds a specific track to the playback queue.

        Args:
            track_id (str): The Spotify track ID to add to the queue.
            device_id (str, optional): The ID of the device to add the track on. Defaults to None.

        Returns:
            str: A confirmation message if the track was successfully added to the queue.

        Raises:
            ConnectionError: If there is a connection issue with the Spotify API.
        """
        self.logger.info(
            f"Attempting to add track ID {track_id} to the queue on device {device_id or 'active device'}.")

        try:
            self.spotify_connector.connect()
            self.spotify_connector.client.add_to_queue(uri=f"spotify:track:{track_id}",
                                                       device_id=device_id)

            self.logger.info(f"Track {track_id} added to the queue.")
            return f"Track {track_id} added to the queue on device {device_id or 'active device'}."

        except Exception as e:
            self.logger.error(f"Failed to add track {track_id} to the queue.", exc_info=True)
            raise ConnectionError(f"Could not add track {track_id} to the queue: {e}")

    def play_playlist(self, playlist_id: str, device_id: str = None) -> str:
        """
        Plays a specified playlist on an active Spotify device.

        Args:
            playlist_id (str): The Spotify ID of the playlist to play.
            device_id (str, optional): The ID of the device to play the playlist on. Defaults to None,
                                       which will use the currently active device.

        Returns:
            str: A confirmation message if the playlist was successfully started.

        Raises:
            ConnectionError: If there is a connection issue with the Spotify API.
        """
        self.logger.info(f"Attempting to play playlist ID: {playlist_id}")

        try:
            self.spotify_connector.connect()

            # Start playback for the specified playlist
            self.spotify_connector.client.start_playback(device_id=device_id,
                                                         context_uri=f"spotify:playlist:{playlist_id}")

            self.logger.info(f"Playback started for playlist ID {playlist_id}")
            return f"Playing playlist ID {playlist_id} on device {device_id or 'default'}."

        except Exception as e:
            self.logger.error(f"Failed to play playlist ID '{playlist_id}': {e}", exc_info=True)
            raise ConnectionError(f"Could not start playback for playlist ID '{playlist_id}': {e}")
