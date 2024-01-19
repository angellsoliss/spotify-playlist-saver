from flask import Flask, render_template, url_for, request, session, redirect
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import time
import os
from datetime import datetime
from flask_sqlalchemy import SQLAlchemy

#initialize app
app = Flask(__name__)

app.config['SESSION_COOKIE_NAME'] = 'Spotify Cookie'
app.secret_key = 'oidfu9-37uf93#232#1'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'  # Use SQLite for simplicity
db = SQLAlchemy(app)

class User(db.Model):
    id = db.Column(db.String, primary_key=True)
    token_info = db.Column(db.PickleType)

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
    user = User.query.filter_by(id=token_info['access_token']).first()
    
    if not user:
        user = User(id=token_info['access_token'], token_info=token_info)
        db.session.add(user)
    else:
        user.token_info = token_info
    
    db.session.commit()
    
    session['user_id'] = token_info['access_token']
    
    return redirect(url_for('save_playlist'))


@app.route('/savePlaylist', methods=['POST', 'GET'])
def save_playlist():
    #get authorization token
    try:
        token_info = get_token()
    except:
        print('Not logged in')
        return redirect('/')
    
    #create spotipy object using authorization token
    sp = spotipy.Spotify(auth=token_info['access_token'])
    #get user id, needed to create playlists and access existing playlists
    user_id = sp.current_user()['id']
    
    #get user playlists
    current_playlists = sp.current_user_playlists()['items']
    
    #create array, used to hold playlist names
    playlist_names = []

    #append playlist names to array
    for playlist in current_playlists:
        playlist_names.append(f"{playlist['name']}")

    #if playlist name is entered
    if request.method == 'POST':
        #get user input text
        PlName = request.form.get('PlName', '')
        #format title for new playlist
        PlName_with_date = f"{PlName} - {datetime.now().strftime('%m/%d/%Y')}"

        #initialize playlist id before it is used
        playlist_id = None

        #iterate through user playlists
        for playlist in current_playlists:
            #check if user entered text matches existing playlist
            if playlist['name'].lower() == PlName.lower():
                #if so, grab playlist id
                playlist_id = playlist['id']
                #break if playlist is found
                break

        #if no matching playlist is found, redirect to error screen  
        if not playlist_id:
            return redirect(url_for('not_found'))
            
        
        #create new playlist
        new_playlist = sp.user_playlist_create(user_id, name=PlName_with_date ) 
        
        #grab existing playlist tracks
        playlist_tracks = sp.playlist_items(playlist_id=playlist_id)

        #add songs to new playlist
        song_uris = []
        for song in playlist_tracks['items']:
            song_uri = song['track']['uri']
            song_uris.append(song_uri)
        
        sp.user_playlist_add_tracks(user_id, new_playlist['id'], song_uris, None)

    #render html template, pass playlist_names array to display on screen
    return render_template('index.html', playlist_names=playlist_names)

#playlist not found route
@app.route('/not_found')
def not_found():
    return render_template('notFound.html')

#spotify authorization
def get_token():
    user_id = session.get('user_id')
    
    if not user_id:
        return redirect(url_for('login', external=False))
    
    user = User.query.get(user_id)
    
    if not user:
        return redirect(url_for('login', external=False))
    
    now = int(time.time())
    is_expired = user.token_info['expires_at'] - now < 60
    
    if is_expired:
        spotify_oauth = create_spotify_oauth()
        user.token_info = spotify_oauth.refresh_access_token(user.token_info['refresh_token'])
        db.session.commit()
    
    return user.token_info

def create_spotify_oauth():
    return SpotifyOAuth(client_id=os.environ.get("SPOTIFY_CLIENT_ID"),
                        client_secret=os.environ.get("SPOTIFY_CLIENT_SECRET"),
                        redirect_uri="https://playlist-saver.onrender.com/redirect",
                        scope='user-library-read playlist-modify-public playlist-modify-private playlist-read-private playlist-read-collaborative')

if __name__ == "__main__":
    db.create_all()  # Create database tables
    app.run(debug=False, host='0.0.0.0')