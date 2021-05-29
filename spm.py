import json
import sys
import spotipy
import maya
from http.server import BaseHTTPRequestHandler, HTTPServer
import time
from spotipy.oauth2 import SpotifyClientCredentials
from spotipy.oauth2 import SpotifyOAuth
import configparser

debug_mode = True

playlists_dict = {}
tracks_dict = {}
sorted_tracks_dict = {}
hostName = "localhost"
serverPort = 8080
scope = 'playlist-read-private'

config = configparser.ConfigParser()
config.read('config.ini')





sp = spotipy.Spotify(   auth_manager    = SpotifyOAuth
                        (
                            client_id       = config['General']['client_id'],
                            client_secret   = config['General']['client_secret'],
                            redirect_uri    = config['General']['redirect_uri'],
                            scope           = scope
                        )
                    )

# user_playlists = sp.current_user_playlists(limit=50)



class SPM_Server(BaseHTTPRequestHandler):
    def list_tracks(self):
        global sp
        playlists = sp.current_user_playlists(limit=50)
        playlist_count = 0

        uprint('-- list tracks --')
        while playlists:
            for i, playlist in enumerate(playlists['items']):
                playlist_count += 1
                playlists_dict.update({playlist['id'] : playlist['name']})
                # if (i < 2):
                get_playlist_songs(playlist['id'])
                print("%4d %s %s" % (i + 1 + playlists['offset'], playlist['id'],  playlist['name']))
            if playlists['next']:
                playlists = sp.next(playlists)
            else:
                playlists = None

        uprint(str(len(tracks_dict)) + " tracks total in " + str(playlist_count) + " playlists")
        uprint('----------------')

        dic2={}
        for i in sorted(tracks_dict):
           sorted_tracks_dict[i] = tracks_dict[i]

        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()
        self.wfile.write(bytes("<html><head><title>Spotify Playlist Manager</title><style>body {font-family: sans-serif;} input[type='checkbox'] {width: 1.5em;height:1.5em} .b td {border: 1px solid #ff0;}.b th.playlist{word-break: break-all; word-wrap: break-word;width:3em;} table.b {margin-top:80px; border-spacing:0; position:relative;} th {text-align:left; position: sticky;top: 80px; background:#ddd;color:#222; } td.track_title:hover {background:#ff0;} table.b td {background:#eee;border-top:1px solid #fff;border-left:1px solid #fff;border-right:1px solid #ddd;border-bottom:1px solid #ddd;font-size:1.5em} #sp_embed {width:100%; position:fixed; top: 0px;z-index:2;background:black;}</style></head>", "utf-8"))
        self.wfile.write(bytes("<body>", "utf-8"))

        self.wfile.write(bytes('<script>function play_track(track_id){document.getElementById("sp_embed").src="https://open.spotify.com/embed/track/" + track_id}</script>', "utf-8"))

        # self.wfile.write(bytes('<tr><th colspan='+str(len(playlists_dict) + 2)+'>', "utf-8"))
        self.wfile.write(bytes('<iframe id="sp_embed" src="" width="300" height="80" frameborder="0" allowtransparency="true" allow="encrypted-media"></iframe>', "utf-8"))
        # self.wfile.write(bytes('</th></tr>', "utf-8"))

        self.wfile.write(bytes('<table class=b>', "utf-8"))

        self.wfile.write(bytes('<tr>', "utf-8"))
        self.wfile.write(bytes('<th>artist</th>', "utf-8"))
        self.wfile.write(bytes('<th>title</th>', "utf-8"))
        playlist_index = 0
        for playlist_id in playlists_dict:
            self.wfile.write(bytes('<th class=playlist style="background:hsla('+str(playlist_index * 72)+',100%, 95%, 1);">', "utf-8"))
            playlist_index += 1
            self.wfile.write(bytes(playlists_dict[playlist_id], "utf-8"))
            self.wfile.write(bytes('</th>', "utf-8"))
        self.wfile.write(bytes('</tr>', "utf-8"))

        # list tracks
        for track_id in sorted_tracks_dict:
            track = sorted_tracks_dict[track_id]
            self.wfile.write(bytes('<tr>', "utf-8"))
            self.wfile.write(bytes('<td>' + str(track['artist']) + '</td>', "utf-8"))

            # uhm
            if track_id is None:
                self.wfile.write(bytes('<td><b>????</b>  ' + str(track['title']) + '</td>', "utf-8"))
            else:
                self.wfile.write(bytes('<td class=track_title onclick=play_track("'+track_id+'")>' + str(track['title']) + '</td>', "utf-8"))

            # for playlist_id in track['playlists']:
            playlist_index = 0
            for playlist_id in playlists_dict:
                self.wfile.write(bytes('<td style="background:hsla('+str(playlist_index * 72)+',100%, 90%, 1);">', "utf-8"))
                playlist_index += 1
                self.wfile.write(bytes('<input type=checkbox', "utf-8"))
                if (playlist_id in track['playlists']):
                    self.wfile.write(bytes(' checked', "utf-8"))
                self.wfile.write(bytes('>', "utf-8"))
                self.wfile.write(bytes('</td>', "utf-8"))
            self.wfile.write(bytes('</tr>', "utf-8"))
        self.wfile.write(bytes('</table>', "utf-8"))
        self.wfile.write(bytes("</body></html>", "utf-8"))

    def do_GET(self):
        if (self.path == '/'):
            self.list_tracks()
        else:
            path_frags = self.path.split('/')
            uprint(json.dumps(path_frags))
            # self.send_response(200)
            # self.send_header("Content-type", "text/html")
            # self.end_headers()
            # self.wfile.write(bytes("<html><head><title>https://pythonbasics.org</title></head>", "utf-8"))
            # self.wfile.write(bytes("<p>Request: %s</p>" % self.path, "utf-8"))
            # self.wfile.write(bytes("<body>", "utf-8"))
            # self.wfile.write(bytes("<p>This is an example web server.</p>", "utf-8"))
            # self.wfile.write(bytes("</body></html>", "utf-8"))

def uprint(*objects, sep=' ', end='\n', file=sys.stdout):
    enc = file.encoding
    if enc == 'UTF-8':
        print(*objects, sep=sep, end=end, file=file)
    else:
        f = lambda obj: str(obj).encode(enc, errors='backslashreplace').decode(enc)
        print(*map(f, objects), sep=sep, end=end, file=file)

def get_playlist_songs(playlist_id):
    global tracks_array
    reached_end = False
    offset = 0
    first = True
    while (reached_end == False):
        playlist_items = sp.playlist_items(playlist_id, limit=100, offset = offset)
        idx = 0
        for idx, item in enumerate(playlist_items['items']):
            track_id = item['track']['id']
            track_artist = '?'
            if (len(item['track']['album']['artists']) > 0):
                track_artist = item['track']['album']['artists'][0]['name']
            if (track_id in tracks_dict and track_id is not None):
                tracks_dict[track_id]['playlists'].update({playlist_id : True})
            elif (track_id is not None):
                tracks_dict.update({track_id : {'artist': track_artist, 'title': item['track']['name'], 'playlists': {playlist_id: True}}})
        offset = offset + 100;
        if (idx < 99):
            reached_end = True

if __name__ == "__main__":
    webServer = HTTPServer((hostName, serverPort), SPM_Server)
    print("Server started http://%s:%s" % (hostName, serverPort))
    try:
        webServer.serve_forever()
    except KeyboardInterrupt:
        pass
    webServer.server_close()
    print("Server stopped.")

# uprint(json.dumps(tracks_dict))