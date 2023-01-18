#!/usr/bin/env -S python3 -u

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

default_device = "GTKing"

import os
import json
import sys
import random

def spotify_auth():
  global sp
  sp = spotipy.Spotify(auth_manager=SpotifyOAuth(client_id=client_id, client_secret=client_secret, redirect_uri=redirect_uri, scope="playlist-read-private playlist-read-collaborative user-read-private user-read-playback-state user-modify-playback-state user-read-currently-playing user-read-playback-position user-read-recently-played app-remote-control user-library-read", cache_path="./auth/cache_auth.json"))

def search_active_device():
  print("Search active device")
  devices = sp.devices()
  for device in devices['devices']:
    if device['is_active'] == True:
      print("Found active device: " + device['name'] + ", ID " + device['id'] + " (active: " + str(device['is_active']) + ")")
      return device['id']
  print("Not found active device")
  return None

def search_device(name):
  print("Search device: " + name)
  devices = sp.devices()
  for device in devices['devices']:
    if device['name'] == name:
      print("Found device: " + device['name'] + ", ID " + device['id'] + " (active: " + str(device['is_active']) + ")")
      return device['id'], device['is_active']
  print("Not found device: " + name)
  print("Devices: ")
  print(devices)
  return None, None

def get_active_or_default_device():
  active_device_id = search_active_device()
  if active_device_id is not None:
    print("Select active device")
    return active_device_id
  else:
    print("Select default device")
    default_device_id, default_device_active = search_device(default_device)
    return default_device_id

def resolve_and_transfer_playback(device_name):
  device_id, device_active = search_device(device_name)
  if device_active is None and device_name is None:
    print("Not found device: " + device_name)
    return
  if device_active == False:
    print("Device found, and is not active, transferred")
    sp.transfer_playback(device_id=device_id)
    return
  if device_active == True:
    print("Device already is active, not transferred")
    return
  else:
    print("Error transfer playback. device_id, device_active:", device_id, device_active)
    return

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

def next_track():
  print("Next track")
  sp.next_track()

def previous_track():
  print("Previous track")
  sp.previous_track()

def pause_playback():
  print("Pause playback")
  sp.pause_playback()

def start_playback():
  print("Start playback")
  device_id = get_active_or_default_device()
  sp.transfer_playback(device_id=device_id)


def ha_autodiscover(client):
  device_section = {"identifiers":["mqtt2spotify"],"name":"mqtt2spotify", "manufacturer": "vvzvlad", "model": "mqtt2spotify bridge"}
  client.publish("homeassistant/switch/spotify/play/config", json.dumps({
      "name": "Spotify play",
      "unique_id": "spotify.play",
      "state_topic": "spotify/play/state",
      "command_topic": "spotify/play",
      "payload_on":"ON",
      "device":device_section
  }), retain=True)


  client.publish("homeassistant/switch/spotify/pause/config", json.dumps({
      "name": "Spotify pause",
      "unique_id": "spotify.pause",
      "state_topic": "spotify/pause/state",
      "command_topic": "spotify/pause",
      "payload_on":"ON",
      "device": device_section
  }), retain=True)

  client.publish("homeassistant/switch/spotify/next/config", json.dumps({
      "name": "Spotify next",
      "unique_id": "spotify.next",
      "state_topic": "spotify/next/state",
      "command_topic": "spotify/next",
      "payload_on":"ON",
      "device": device_section
  }), retain=True)

  client.publish("homeassistant/switch/spotify/previous/config", json.dumps({
      "name": "Spotify previous",
      "unique_id": "spotify.previous",
      "state_topic": "spotify/previous/state",
      "command_topic": "spotify/previous",
      "payload_on":"ON",
      "device": device_section
  }), retain=True)

  client.publish("homeassistant/switch/spotify/transfer/config", json.dumps({
      "name": "Spotify transfer",
      "unique_id": "spotify.transfer",
      "state_topic": "spotify/transfer/state",
      "command_topic": "spotify/transfer",
      "payload_on":"AppleTV",
      "device": device_section
  }), retain=True)


def on_connect(client, userdata, flags, rc):
  print("Connected with result code "+str(rc))
  client.subscribe("spotify/wakeup")
  client.subscribe("spotify/transfer")
  client.subscribe("spotify/next")
  client.subscribe("spotify/previous")
  client.subscribe("spotify/pause")
  client.subscribe("spotify/play")
  ha_autodiscover(client)
  client.publish("spotify/status", payload="mqtt2spotify daemon started", qos=0, retain=False)



def on_message(client, userdata, msg):

  data = msg.payload.decode('utf-8')
  print("Received MQTT message:" + msg.topic + ": " + data)

  try:
    spotify_auth()
    if msg.topic == "spotify/wakeup":
      json_data = json.loads(data)
      playlist_name = json_data.get('playlist')
      device_name = json_data.get('device')
      if playlist_name is not None and device_name is not None:
        check_play_and_start_playlist(playlist_name, device_name)
    elif msg.topic == "spotify/transfer":
      resolve_and_transfer_playback(data)

    elif msg.topic == "spotify/next":
      next_track()
    elif msg.topic == "spotify/previous":
      previous_track()
    elif msg.topic == "spotify/pause":
      pause_playback()
    elif msg.topic == "spotify/play":
      start_playback()
  except spotipy.exceptions.SpotifyException as e:
    print(e)

  client.publish(msg.topic+"/state", 1)
  time.sleep(1)
  client.publish(msg.topic+"/state", 0)


#Search active device
#Not found active device
#Select default device
#Search device: AppleTV
#Found device: AppleTV, ID 85DCA6F7-81DF-4331-A39E-8C93AC692CE7 (active: False)
#HTTP Error for PUT to https://api.spotify.com/v1/me/player with Params: {} returned 403 due to Player command failed: Premium required
#Exception in thread Thread-1 (_thread_main):
#Traceback (most recent call last):
#  File "/usr/local/lib/python3.10/site-packages/spotipy/client.py", line 245, in _internal_call
#    response.raise_for_status()
#  File "/usr/local/lib/python3.10/site-packages/requests/models.py", line 1021, in raise_for_status
#    raise HTTPError(http_error_msg, response=self)
#requests.exceptions.HTTPError: 403 Client Error: Forbidden for url: https://api.spotify.com/v1/me/player
#


#  File "/root/pyapp/app.py", line 229, in on_message
#    start_playback()
#  File "/root/pyapp/app.py", line 143, in start_playback
#    sp.transfer_playback(device_id=device_id)
#  File "/usr/local/lib/python3.10/site-packages/spotipy/client.py", line 1726, in transfer_playback
#    return self._put("me/player", payload=data)
#  File "/usr/local/lib/python3.10/site-packages/spotipy/client.py", line 312, in _put
#    return self._internal_call("PUT", url, payload, kwargs)
#  File "/usr/local/lib/python3.10/site-packages/spotipy/client.py", line 267, in _internal_call
#    raise SpotifyException(
#spotipy.exceptions.SpotifyException: http status: 403, code:-1 - https://api.spotify.com/v1/me/player:
# Player command failed: Premium required, reason: PREMIUM_REQUIRED
#-- Not first container startup --

#    start_playback()
#  File "/root/pyapp/app.py", line 143, in start_playback
#    sp.transfer_playback(device_id=device_id)
#  File "/usr/local/lib/python3.10/site-packages/spotipy/client.py", line 1735, in transfer_playback
#    return self._put("me/player", payload=data)
#  File "/usr/local/lib/python3.10/site-packages/spotipy/client.py", line 312, in _put
#    return self._internal_call("PUT", url, payload, kwargs)
#  File "/usr/local/lib/python3.10/site-packages/spotipy/client.py", line 267, in _internal_call
#    raise SpotifyException(
#spotipy.exceptions.SpotifyException: http status: 404, code:-1 - https://api.spotify.com/v1/me/player:
# Player command failed: No active device found, reason: NO_ACTIVE_DEVICE


#HTTP Error for PUT to https://api.spotify.com/v1/me/player/pause with Params: {} returned 404 due to Player command failed: No active device found
#Exception in thread Thread-1 (_thread_main):
#Traceback (most recent call last):
#  File "/usr/local/lib/python3.10/site-packages/spotipy/client.py", line 245, in _internal_call
#    response.raise_for_status()
#  File "/usr/local/lib/python3.10/site-packages/requests/models.py", line 1021, in raise_for_status
#    raise HTTPError(http_error_msg, response=self)
#requests.exceptions.HTTPError: 404 Client Error: Not Found for url: https://api.spotify.com/v1/me/player/pause
#


#  File "/root/pyapp/app.py", line 138, in pause_playback
#    sp.pause_playback()
#  File "/usr/local/lib/python3.10/site-packages/spotipy/client.py", line 1777, in pause_playback
#    return self._put(self._append_device_id("me/player/pause", device_id))
#  File "/usr/local/lib/python3.10/site-packages/spotipy/client.py", line 312, in _put
#    return self._internal_call("PUT", url, payload, kwargs)
#  File "/usr/local/lib/python3.10/site-packages/spotipy/client.py", line 267, in _internal_call
#    raise SpotifyException(
#spotipy.exceptions.SpotifyException: http status: 404, code:-1 - https://api.spotify.com/v1/me/player/pause:
# Player command failed: No active device found, reason: NO_ACTIVE_DEVICE





def main():
  counter = 0
  period = 60
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
