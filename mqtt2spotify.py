#!/usr/bin/env python3

#
#############################################################################
#
# spotify to mqtt for smarthome
#
#############################################################################
#

import spotipy
from spotipy.oauth2 import SpotifyOAuth
import paho.mqtt.client as mqtt
import time

client_id = "2a233514cdc44daf9b4a2c08d37fc88c"
client_secret = "05e29443545f48a1b4906b53397e5175"
redirect_uri = "http://localhost:8888/"

import os
import json
import sys
import random

def spotify_auth():
  global sp
  sp = spotipy.Spotify(auth_manager=SpotifyOAuth(client_id=client_id, client_secret=client_secret, redirect_uri=redirect_uri, scope="playlist-read-private playlist-read-collaborative user-read-private user-read-playback-state user-modify-playback-state user-read-currently-playing user-read-playback-position user-read-recently-played app-remote-control user-library-read", cache_path="./cache_auth.json"))

def search_device(name):
  print("Search device: " + name)
  devices = sp.devices()
  for device in devices['devices']:
    if device['name'] == name:
      print("Found device: " + device['name'] + ": " + device['id'] + " (active: " + str(device['is_active']) + ")")
      return device['id'], device['is_active']
  return None

def resolve_and_transfer_playback(device_name):
  print("Transfer playback to device: " + device_name)
  device_id, device_active = search_device(device_name)
  if device_active == False:
    print("Device is not active, transferred")
    sp.transfer_playback(device_id=device_id)
  else:
    print("Device is active, not transferred")

def get_user_current_play():
  cp = sp.current_playback()
  if cp is not None:
    is_playing = cp['is_playing']
    device_name = cp['device']['name']
    track_name = cp['item']['name']
    #print(json.dumps(cp, indent=4, sort_keys=True))
  else:
    is_playing = False
    device_name = False
    track_name = None

  print("Current playback: " + str(track_name) + " on " + str(device_name) + " (play: " + str(is_playing) + ")")
  return is_playing, device_name, track_name


def resolve_playlist(playlist_name):
  print("Resolve playlist: " + playlist_name)
  playlists = sp.current_user_playlists(limit=50)
  #print(json.dumps(playlists, indent=4, sort_keys=True))
  for playlist in playlists['items']:
    if playlist['name'] == playlist_name:
      print("Playlist found: " + playlist['id'])
      return playlist['id']
  print("Playlist not found")
  return None

def get_random_track_in_playlist(playlist_id):
  print("Get random track in playlist: " + playlist_id)
  tracks = sp.playlist_tracks(playlist_id)
  playlist_count = len(tracks['items'])
  random_track_number = random.randint(0, playlist_count-1)
  print("Random track number: " + str(random_track_number+1) + "(tracks in playlist: " + str(playlist_count) + ")")
  track_id = tracks['items'][random_track_number]['track']['id']
  track_name = tracks['items'][random_track_number]['track']['name']
  print("Select track: " + track_name + "(id: " + track_id + ")")
  return track_id

#check play, resolve playlist, resolve devices, start playlist, transfer playback
def check_play_and_start_playlist(playlist_name, device_name):
  is_playing, device_active, track_name = get_user_current_play()
  if is_playing == False:
    playlist_id = resolve_playlist(playlist_name)
    device_id, device_active = search_device(device_name)
    track_id = get_random_track_in_playlist(playlist_id)
    sp.start_playback(device_id=device_id, context_uri='spotify:playlist:' + playlist_id, offset={'uri': 'spotify:track:' + track_id})
  else:
    print("Playback is already active")


def on_connect(client, userdata, flags, rc):
  print("Connected with result code "+str(rc))
  client.subscribe("spotify/wakeup/start")
  client.subscribe("spotify/transfer")
  client.publish("spotify/status", payload="mqtt2spotify daemon started", qos=0, retain=False)


def on_message(client, userdata, msg):
  print("Received MQTT message:" + msg.topic + ": " + str(msg.payload))
  spotify_auth()
  if msg.topic == "spotify/wakeup/start":
    json_data = json.loads(msg.payload)
    playlist_name = json_data['playlist']
    device_name = json_data['device']
    check_play_and_start_playlist(playlist_name, device_name)
  elif msg.topic == "spotify/transfer":
    json_data = json.loads(msg.payload)
    device_name = json_data['device']
    resolve_and_transfer_playback(device_name)




def main():
  counter = 0
  period = 10
  client = mqtt.Client()
  client.on_connect = on_connect
  client.on_message = on_message
  client.connect("192.168.88.111", 1883, 60)
  time.sleep(5)
  client.loop_start()
  while True:
    uptime = counter * period
    client.publish("spotify/status/uptime", str(uptime), qos=0, retain=False)
    time.sleep(period)
    counter = counter + 1
  client.loop_stop()



if __name__ == "__main__":
  main()
