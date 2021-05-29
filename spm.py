import operator
from collections import OrderedDict
import json
import sys
import spotipy
import maya
from http.server import BaseHTTPRequestHandler, HTTPServer
import time
from spotipy.oauth2 import SpotifyClientCredentials
from spotipy.oauth2 import SpotifyOAuth
import configparser

color_step = -42

debug_mode = True

playlists_dict = {}
tracks_dict = {}
sorted_tracks_dict = {}
hostName = "localhost"
serverPort = 8080
scope = 'playlist-read-private playlist-modify-private playlist-modify-public'

config = configparser.ConfigParser()
config.read('config.ini')

sp = spotipy.Spotify(auth_manager    = SpotifyOAuth(
                            client_id       = config['General']['client_id'],
                            client_secret   = config['General']['client_secret'],
                            redirect_uri    = config['General']['redirect_uri'],
                            scope           = scope))

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

        sorted_tracks_dict_title = {}

        for i in OrderedDict(sorted(tracks_dict.items(), key=lambda x: x[1]['title'])):
           sorted_tracks_dict_title[i] = tracks_dict[i]

        for i in OrderedDict(sorted(sorted_tracks_dict_title.items(), key=lambda x: x[1]['artist'])):
           sorted_tracks_dict[i] = tracks_dict[i]

        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(bytes("""<html>

<head>
    <title>Spotify Playlist Manager</title>
    <style>
        body
        {
            font-family:    sans-serif;
        }
        input[type='checkbox']
        {
            width:          100%;
            height:         1.1em
        }
        input[type='checkbox']:hover
        {
            border:         1px solid #ff0;
        }
        .b td
        {
            border:         1px solid #ff0;
        }
        .b th.playlist
        {
            word-break:     break-all;
            word-wrap:      break-word;
            width:          3em;
        }
        table.b
        {
            margin-top:     80px;
            border-spacing: 0;
            position:       relative;
        }
        th
        {
            position:       sticky;
            top:            80px;
            background:     #ddd;
            color:          #222;
            font-size:      0.8em;
            padding:        0.5em; 0.07em
            text-align:     center;
        }
        td.track_title:hover
        {
            background:     #ff0;
        }
        table.b td
        {
            background:     #eee;
            border-top:     1px solid #fff;
            border-left:    1px solid #fff;
            border-right:   1px solid #ddd;
            border-bottom:  1px solid #ddd;
            font-size:      0.9em
        }
        #sp_embed
        {
            width:          100%;
            position:       fixed;
            top:            0px;
            z-index:        2;
            background:     black;
        }

        table.b td.pc
        {
            border:         none;
            padding:        0;
        }

        table.b td.pc label
        {
            display:        block;
            height:         100%;
        }

        table.b td.pc label input[type=checkbox]
        {
            display:        none;
        }

        table.b td.pc label input[type=checkbox] ~ span
        {
            display:        inline-block;
            width:          90%;
            height:         100%;
            border-radius:  0.5em;
            margin:         0 0.2em;
            border:         2px solid hsla(0,0%,0%,0);
        }

""", "utf-8"))

        self.wfile.write(bytes("""""", "utf-8"))

        playlist_index = 0
        for playlist_id in playlists_dict:
            playlist_index += 1
            self.wfile.write(bytes("""
            .ph_"""+str(playlist_index)+"""
            {
                background:     hsla("""+str(playlist_index * color_step)+""",100%, 35%, 1);
                color:          hsla("""+str(playlist_index * color_step)+""",100%, 90%, 1);
            }""", "utf-8"))
            self.wfile.write(bytes("""

            table.b td label.pc_"""+str(playlist_index)+""" input[type=checkbox]:checked ~ span
            {
                background:     hsla("""+str(playlist_index * color_step)+""",100%, 40%, 1);
            }
            table.b td label.pc_"""+str(playlist_index)+""" input[type=checkbox]:hover:checked ~ span
            {
                background:     hsla("""+str(playlist_index * color_step)+""",100%, 60%, 1);
                border:         2px dotted hsla(0,0%,0%,1);
            }

            table.b td label.pc_"""+str(playlist_index)+""" input[type=checkbox] ~ span
            {
                background:     hsla("""+str(playlist_index * color_step)+""",100%, 95%, 1);
            }
            table.b td label.pc_"""+str(playlist_index)+""" input[type=checkbox]:hover ~ span
            {
                background:     hsla("""+str(playlist_index * color_step)+""",100%, 65%, 1);
                border:         2px solid hsla(0,0%,0%,0.5);
            }
            """, "utf-8"))
        self.wfile.write(bytes("""
    </style></head>
<body>

<script>

    function play_track(track_id)
    {
        document.getElementById("sp_embed").src="https://open.spotify.com/embed/track/" + track_id
    }

    function do_toggle(el)
    {
        if (el.checked)
            ajax('""" + "http://" + hostName + ":" + str(serverPort) + """/add/' + el.dataset.p + '/' + el.dataset.t + '/', '', null, null);
        else
            ajax('""" + "http://" + hostName + ":" + str(serverPort) + """/remove/' + el.dataset.p + '/' + el.dataset.t + '/', '', null, null);
    }

    function ajax(url, post_parameters, callback, data)
    {
        var http = new XMLHttpRequest();
        if (http != undefined)
        {
            http.open(post_parameters == '' ? 'GET' : 'POST', url, true);
            http.setRequestHeader("Content-type", "application/x-www-form-urlencoded");
            http.onreadystatechange = function()
            {
                if (callback != null)
                {
                    callback(this.readyState, this.status, this.responseText, data);
                }
            };
            http.send(post_parameters);
            return true;
        }
        else
        {
            return false;
        }
    }
</script>

<iframe id="sp_embed" src="" width="300" height="80" frameborder="0" allowtransparency="true" allow="encrypted-media"></iframe>

<table class=b>
    <tr>
        <th>artist</th>
        <th>title</th>""", "utf-8"))

        playlist_index = 0
        for playlist_id in playlists_dict:
            playlist_index += 1
            self.wfile.write(bytes("""<th class='playlist ph_""" + str(playlist_index) + """'>""", "utf-8"))
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
                self.wfile.write(bytes("<td class=track_title onclick=play_track('"+track_id+"')>" + str(track['title']) + '</td>', "utf-8"))

            # for playlist_id in track['playlists']:
            playlist_index = 0
            for playlist_id in playlists_dict:
                self.wfile.write(bytes('<td class=pc>', "utf-8"))
                playlist_index += 1
                self.wfile.write(bytes('<label class="pc_' + str(playlist_index) + '"><input type=checkbox data-t='+track_id+' data-p='+playlist_id+' ', "utf-8"))
                if (playlist_id in track['playlists']):
                    self.wfile.write(bytes(' checked', "utf-8"))
                self.wfile.write(bytes(' onchange="do_toggle(this);"><span>&nbsp;</span></label>', "utf-8"))

                self.wfile.write(bytes('</td>', "utf-8"))
            self.wfile.write(bytes("""</tr>
""", "utf-8"))
        self.wfile.write(bytes('</table></body></html>', "utf-8"))

    def do_GET(self):
        if (self.path == '/'):
            self.list_tracks()
        # elif (self.path == '/favicon.ico'):

        else:
            path_frags = self.path.split('/')
            self.send_response(200)
            self.send_header("Content-type", "text/html")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(bytes("<html><head><title>https://pythonbasics.org</title></head>", "utf-8"))
            self.wfile.write(bytes("<body>", "utf-8"))
            if (len(path_frags) == 5):
                if (path_frags[1] == 'add'):
                    add_to_playlist(path_frags[2], path_frags[3])
                    self.wfile.write(bytes("""added x to y""", "utf-8"))
                elif (path_frags[1] == 'remove'):
                    remove_from_playlist(path_frags[2], path_frags[3])
                    self.wfile.write(bytes("""removed x from y""", "utf-8"))
            self.wfile.write(bytes("<p>Request: %s</p>" % json.dumps(path_frags), "utf-8"))
            self.wfile.write(bytes("</body></html>", "utf-8"))

def remove_from_playlist(playlist_id, track_id):
    global sp
    sp.playlist_remove_all_occurrences_of_items(playlist_id, [track_id])

def add_to_playlist(playlist_id, track_id):
    global sp
    sp.playlist_add_items(playlist_id, [track_id])

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