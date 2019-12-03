#!/usr/bin/env python3

import argparse
import os

from demo.spotify import SpotifyClient

CLIENT_ID = os.environ["SPOTIFY_CLIENT_ID"]
CLIENT_SECRET = os.environ["SPOTIFY_CLIENT_SECRET"]

parser = argparse.ArgumentParser()
parser.add_argument("artist", type=str)
args = vars(parser.parse_args())
artist_name = args["artist"]

client = SpotifyClient(client_id=CLIENT_ID, client_secret=CLIENT_SECRET)
data = client.get_all_artist_tracks_data(artist_name=artist_name)

print(f"Downloaded {len(data)} tracks for {artist_name}!")
