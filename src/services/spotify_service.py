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
                return playback_info
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

    def get_playlist(self, playlist_id: str) -> dict:
        """
        Retrieves all available information about a specified playlist.

        Args:
            playlist_id (str): The Spotify ID of the playlist to retrieve details from.

        Returns:
            dict: A dictionary containing all playlist information, including metadata and tracks.

        Raises:
            ConnectionError: If there is a connection issue with the Spotify API.
        """
        self.logger.info(f"Attempting to retrieve details for playlist ID: {playlist_id}")

        try:
            self.spotify_connector.connect()

            # Retrieve full playlist details
            playlist_data = self.spotify_connector.client.playlist(playlist_id)

            # Extracting key information
            playlist_details = {
                "name": playlist_data.get("name"),
                "description": playlist_data.get("description"),
                "owner": playlist_data.get("owner", {}).get("display_name"),
                "followers": playlist_data.get("followers", {}).get("total"),
                "public": playlist_data.get("public"),
                "collaborative": playlist_data.get("collaborative"),
                "total_tracks": playlist_data.get("tracks", {}).get("total"),
                "tracks": [
                    {
                        "name": item["track"]["name"],
                        "artists": [artist["name"] for artist in item["track"]["artists"]],
                        "duration_ms": item["track"]["duration_ms"],
                        "track_id": item["track"]["id"],
                        "album": item["track"]["album"]["name"],
                        "album_id": item["track"]["album"]["id"],
                        "added_at": item["added_at"],
                    }
                    for item in playlist_data["tracks"]["items"] if item["track"] is not None
                ]
            }

            self.logger.info(f"Retrieved details for playlist ID {playlist_id}")
            return playlist_details

        except Exception as e:
            self.logger.error(f"Failed to retrieve details for playlist ID '{playlist_id}': {e}",
                              exc_info=True)
            raise ConnectionError(
                f"Could not retrieve details for playlist ID '{playlist_id}': {e}")

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

            self.logger.info(f"Found {len(results['tracks']['items'])} tracks for query '{query}'.")
            return results

        except Exception as e:
            self.logger.error("Failed to search tracks.", exc_info=True)
            raise ConnectionError(f"Could not search tracks: {e}")

    def get_similar_tracks(self, seed_track_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Recommends similar tracks based on a provided track ID.

        Args:
            seed_track_id (str): The Spotify track ID to base recommendations on.
            limit (int): The maximum number of recommended tracks to return (default is 10).

        Returns:
            List[Dict[str, Any]]: A list of recommended tracks, each with details like name, artist, and album.

        Raises:
            ConnectionError: If there is a connection issue with the Spotify API.
        """
        self.logger.info(f"Fetching similar tracks for track ID: {seed_track_id}")

        try:
            self.spotify_connector.connect()

            # Call Spotify's recommendations endpoint
            results = self.spotify_connector.client.recommendations(seed_tracks=[seed_track_id],
                                                                    limit=limit)

            similar_tracks = [
                {
                    "name": track["name"],
                    "artist": ", ".join(artist["name"] for artist in track["artists"]),
                    "album": track["album"]["name"],
                    "track_id": track["id"]
                }
                for track in results["tracks"]
            ]

            self.logger.info(f"Retrieved {len(similar_tracks)} similar tracks.")
            return similar_tracks

        except Exception as e:
            self.logger.error(f"Failed to retrieve similar tracks for track ID '{seed_track_id}'.",
                              exc_info=True)
            raise ConnectionError(
                f"Could not fetch similar tracks for track ID '{seed_track_id}': {e}")

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

    def add_tracks_to_queue(self, track_ids: List[str], device_id: str = None) -> str:
        """
        Adds multiple tracks to the playback queue.

        Args:
            track_ids (List[str]): A list of Spotify track IDs to add to the queue.
            device_id (str, optional): The ID of the device to add the tracks on. Defaults to None.

        Returns:
            str: A confirmation message if the tracks were successfully added to the queue.

        Raises:
            ConnectionError: If there is a connection issue with the Spotify API.
        """
        self.logger.info(
            f"Attempting to add {len(track_ids)} tracks to the queue on device {device_id or 'active device'}.")

        try:
            self.spotify_connector.connect()

            for track_id in track_ids:
                self.spotify_connector.client.add_to_queue(uri=f"spotify:track:{track_id}",
                                                           device_id=device_id)
                self.logger.info(f"Track {track_id} added to the queue.")

            return f"{len(track_ids)} tracks added to the queue on device {device_id or 'active device'}."

        except Exception as e:
            self.logger.error("Failed to add tracks to the queue.", exc_info=True)
            raise ConnectionError(f"Could not add tracks to the queue: {e}")

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

    def get_album_details(self, album_id: str) -> Optional[Dict[str, Any]]:
        """
        Fetches details for a specific album by album ID.

        Args:
            album_id (str): The Spotify album ID.

        Returns:
            Optional[Dict[str, Any]]: A dictionary with details about the album (name, artist, release date, total tracks, and track list).

        Raises:
            ConnectionError: If there is a connection issue with the Spotify API.
        """
        self.logger.info(f"Fetching details for album ID: {album_id}")

        try:
            self.spotify_connector.connect()
            album = self.spotify_connector.client.album(album_id)

            self.logger.info(f"Successfully retrieved details for album '{album['name']}'.")
            return dict(album)

        except Exception as e:
            self.logger.error(f"Failed to retrieve album details for ID '{album_id}'.",
                              exc_info=True)
            raise ConnectionError(f"Could not fetch album details for ID '{album_id}': {e}")

    def get_multiple_albums(self, album_ids: List[str]) -> List[Dict[str, Any]]:
        """
        Fetches details for multiple albums by their IDs.

        Args:
            album_ids (List[str]): A list of Spotify album IDs.

        Returns:
            Dict: A list of dictionaries with details for each album.

        Raises:
            ConnectionError: If there is a connection issue with the Spotify API.
        """
        self.logger.info(f"Fetching details for multiple albums: {album_ids}")

        try:
            self.spotify_connector.connect()
            albums = self.spotify_connector.client.albums(album_ids)["albums"]

            self.logger.info(f"Successfully retrieved details for {len(albums)} albums.")
            return albums

        except Exception as e:
            self.logger.error("Failed to retrieve multiple albums.", exc_info=True)
            raise ConnectionError(f"Could not fetch album details: {e}")

    def add_tracks_to_playlist(self, playlist_id: str, track_ids: List[str]) -> str:
        """
        Adds multiple tracks to a specified playlist.

        Args:
            playlist_id (str): The Spotify playlist ID where the tracks should be added.
            track_ids (List[str]): A list of Spotify track IDs to add to the playlist.

        Returns:
            str: A confirmation message if the tracks were successfully added to the playlist.

        Raises:
            ConnectionError: If there is a connection issue with the Spotify API.
        """
        self.logger.info(f"Attempting to add {len(track_ids)} tracks to playlist {playlist_id}.")

        try:
            self.spotify_connector.connect()

            # Adding tracks to the playlist
            self.spotify_connector.client.playlist_add_items(playlist_id, track_ids)

            self.logger.info(
                f"Successfully added {len(track_ids)} tracks to playlist {playlist_id}.")
            return f"Successfully added {len(track_ids)} tracks to playlist {playlist_id}."

        except Exception as e:
            self.logger.error(f"Failed to add tracks to playlist {playlist_id}.", exc_info=True)
            raise ConnectionError(f"Could not add tracks to playlist {playlist_id}: {e}")

    def create_playlist(self, name: str, description: str = "", public: bool = False, track_ids: List[str] = None) -> Dict[str, Any]:
        """
        Creates a new playlist for the current user and optionally adds tracks to it.

        Args:
            name (str): The name of the new playlist.
            description (str, optional): A description for the playlist. Defaults to an empty string.
            public (bool, optional): Whether the playlist should be public. Defaults to False.
             track_ids (List[str]): A list of Spotify track IDs to add to the playlist.

        Returns:
            Dict[str, Any]: A dictionary with details about the created playlist.

        Raises:
            ConnectionError: If there is a connection issue with the Spotify API.
        """
        self.logger.info(f"Creating playlist '{name}' with description '{description}'.")

        try:
            self.spotify_connector.connect()

            # Create the playlist
            user_id = self.spotify_connector.client.current_user()["id"]
            playlist = self.spotify_connector.client.user_playlist_create(
                user=user_id,
                name=name,
                public=public,
                description=description
            )

            self.logger.info(f"Playlist '{name}' created with ID: {playlist['id']}.")

            # Optionally add tracks to the new playlist
            if track_ids:
                self.logger.info(f"Adding {len(track_ids)} tracks to playlist '{name}'.")
                self.spotify_connector.client.playlist_add_items(playlist_id=playlist['id'], items=track_ids)
                self.logger.info(f"Successfully added tracks to playlist '{name}'.")

            return playlist

        except Exception as e:
            self.logger.error("Failed to create playlist or add tracks.", exc_info=True)
            raise ConnectionError(f"Could not create playlist '{name}': {e}")
