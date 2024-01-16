from flask import Flask, render_template, url_for, request, session, redirect
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import time
from datetime import datetime

#initialize app
app = Flask(__name__)

app.config['SESSION_COOKIE_NAME'] = 'Spotify Cookie'
app.secret_key = 'oidfu9-37uf93#232#1'
TOKEN_INFO = 'tokenInfo'

#index route
@app.route('/', methods=['POST', 'GET'])
def login():
    auth_url = create_spotify_oauth().get_authorize_url()
    return redirect(auth_url)
    
@app.route('/redirect')
def redirect_oauth():
    session.clear()
    code = request.args.get('code')
    token_info = create_spotify_oauth().get_access_token(code)
    session[TOKEN_INFO] = token_info
    return redirect(url_for('save_playlist', external=True))

@app.route('/savePlaylist', methods=['POST', 'GET'])
def save_playlist():
    try:
        token_info = get_token()
    except:
        print('Not logged in')
        return redirect('/')
    
    sp = spotipy.Spotify(auth=token_info['access_token'])
    user_id = sp.current_user()['id']
    
    #get user playlists
    current_playlists = sp.current_user_playlists()['items']

    if request.method == 'POST':
        PlName = request.form.get('PlName', '')
        PlName_with_date = f"{PlName} - {datetime.now().strftime('%m/%d/%Y')}"
    
        playlist_id = None

        for playlist in current_playlists:
            print(f"Playlist name: {playlist['name']}")
            if playlist['name'].lower() == PlName.lower():
                playlist_id = playlist['id']
            
        if not playlist_id:
            return 'Playlist not found'
        
        #create new playlist
        new_playlist = sp.user_playlist_create(user_id, name=PlName_with_date ) 
        
        playlist_tracks = sp.playlist_items(playlist_id=playlist_id)
        song_uris = []
        for song in playlist_tracks['items']:
            song_uri = song['track']['uri']
            song_uris.append(song_uri)
        
        sp.user_playlist_add_tracks(user_id, new_playlist['id'], song_uris, None)

    return render_template('index.html')

def get_token():
    token_info = session.get(TOKEN_INFO, None)
    if not token_info:
        redirect(url_for('login', external=False))
    
    now = int(time.time())
    is_expired = token_info['expires_at'] - now < 60
    if is_expired:
        spotify_oauth = create_spotify_oauth()
        token_info = spotify_oauth.refresh_access_token(token_info['refresh_token'])
    return token_info

def create_spotify_oauth():
    return SpotifyOAuth(client_id="c9354d5aaf464466aa88e959f5f1fb98",
                        client_secret="dd461f6007634943bd3c1a88b4a483db",
                        redirect_uri= url_for('redirect_oauth', _external=True),
                        scope='user-library-read playlist-modify-public playlist-modify-private playlist-read-private playlist-read-collaborative')

if __name__ == "__main__":
    app.run(debug=True)