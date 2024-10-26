import logging
from typing import Dict, List, Optional
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
