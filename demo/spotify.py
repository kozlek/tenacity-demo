import base64
from typing import Dict, List

import requests

from .decorators import spotify_retry


class SpotifyClient:
    AUTH_URL = "https://accounts.spotify.com/api/token"
    API_BASE_URL = "https://api.spotify.com/v1"

    def __init__(self, client_id: str, client_secret: str):
        self.client_id = client_id
        self.client_secret = client_secret

        self.token = self.retrieve_token(
            client_id=client_id, client_secret=client_secret
        )
        self.default_headers = {"Authorization": f"Bearer {self.token}"}

    @classmethod
    def retrieve_token(cls, client_id: str, client_secret: str) -> str:
        encoded_auth_data = base64.b64encode(
            f"{client_id}:{client_secret}".encode("utf8")
        ).decode("utf8")
        res = requests.post(
            url=cls.AUTH_URL,
            data={"grant_type": "client_credentials"},
            headers={"Authorization": f"Basic {encoded_auth_data}"},
        )
        res.raise_for_status()
        return res.json()["access_token"]

    @spotify_retry(max_retries=10)
    def search_artist_id(self, artist_name: str) -> str:
        res = requests.get(
            url=f"{self.API_BASE_URL}/search",
            headers=self.default_headers,
            params={"q": artist_name, "type": "artist"},
        )
        res.raise_for_status()
        return res.json()["artists"]["items"][0]["id"]

    @spotify_retry(max_retries=10)
    def get_artist_albums(self, artist_id: str) -> List[str]:
        res = requests.get(
            f"{self.API_BASE_URL}/artists/{artist_id}/albums",
            headers=self.default_headers,
        )
        res.raise_for_status()
        albums = res.json()["items"]
        return [item["id"] for item in albums]

    @spotify_retry(max_retries=10)
    def get_album_tracks(self, album_id: str) -> List[str]:
        res = requests.get(
            f"{self.API_BASE_URL}/albums/{album_id}/tracks",
            headers=self.default_headers,
        )
        res.raise_for_status()
        tracks = res.json()["items"]
        return [item["id"] for item in tracks]

    @spotify_retry(max_retries=10)
    def get_track(self, track_id: str) -> Dict:
        res = requests.get(
            f"{self.API_BASE_URL}/tracks/{track_id}", headers=self.default_headers
        )
        res.raise_for_status()
        track_data = res.json()
        return track_data

    def get_all_artist_tracks_data(self, artist_name: str) -> List[Dict]:
        artist_id = self.search_artist_id(artist_name=artist_name)
        albums = self.get_artist_albums(artist_id=artist_id)

        tracks = []
        for album_id in albums:
            album_tracks = self.get_album_tracks(album_id=album_id)
            tracks.extend(album_tracks)
        tracks = list(set(tracks))

        tracks_data = [self.get_track(track_id=track_id) for track_id in tracks]
        return tracks_data
