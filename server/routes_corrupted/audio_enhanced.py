from flask import Blueprint, jsonify, request
import os, json, re
from datetime import datetime
import requests
import hashlib

audio_enhanced_bp = Blueprint('audio_enhanced', __name__)

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
STO = os.path.join(ROOT, 'storage')
AUDIO_DIR = os.path.join(STO, 'audio')
AUDIO_DB = os.path.join(STO, 'audio_database.json')
AUDIO_CONFIG = os.path.join(STO, 'config', 'audio_config.json')

# Pre-configured API keys
DISCOGS_API_KEY = "DlYcCvjWkCSKwuoxWznBrUDFitmPFTqBpIuoqizm"
ACOUSTID_API_KEY = "W48qHR6eir"

def _load_config():
    """Load audio configuration"""
    try:
        with open(AUDIO_CONFIG, 'r', encoding='utf-8') as f:
        return json.load(f)
    except Exception:
        return {
            'discogs_enabled': True,
            'discogs_api_key': DISCOGS_API_KEY,
            'acoustid_enabled': True,
            'acoustid_api_key': ACOUSTID_API_KEY,
            'audio_quality': {
                'preferred_format': 'flac',
                'min_bitrate': 320,
                'enable_replaygain': True
            },
            'library_path': AUDIO_DIR
        }

def _save_config(data):
    """Save audio configuration"""
    os.makedirs(os.path.dirname(AUDIO_CONFIG), exist_ok=True)
    tmp = AUDIO_CONFIG + '.tmp'
    with open(tmp, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)
    os.replace(tmp, AUDIO_CONFIG)

def _load_audio_db():
    """Load audio database"""
    try:
        with open(AUDIO_DB, 'r', encoding='utf-8') as f:
        return json.load(f)
    except Exception:
        return {
            'tracks': [],
            'albums': [],
            'artists': [],
            'playlists': [],
            'smart_playlists': []
        }

def _save_audio_db(data):
    """Save audio database"""
    os.makedirs(os.path.dirname(AUDIO_DB), exist_ok=True)
    tmp = AUDIO_DB + '.tmp'
    with open(tmp, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)
    os.replace(tmp, AUDIO_DB)

def _search_discogs(query, search_type='release'):
    """Search Discogs API"""
    config = _load_config()
    if not config.get('discogs_enabled'):
        return []
    
    api_key = config.get('discogs_api_key', DISCOGS_API_KEY)
    url = 'https://api.discogs.com/database/search'
    headers = {'User-Agent': 'MediaHub/1.0'}
    params = {
        'q': query,
        'type': search_type,  # release, master, artist, label
        'token': api_key
    }
    
    try:
        response = requests.get(url, headers=headers, params=params, timeout=10)
        if response.status_code == 200:
            data = response.json()
        return data.get('results', [])
    except Exception as e:
        print(f"Discogs API error: {e}")
    
        return []

def _identify_audio_acoustid(file_path):
    """Identify audio file using AcoustID"""
    config = _load_config()
    if not config.get('acoustid_enabled'):
        return None
    
    api_key = config.get('acoustid_api_key', ACOUSTID_API_KEY)
    
    # In a real implementation, this would:
    # 1. Generate audio fingerprint using chromaprint
    # 2. Send fingerprint to AcoustID API
    # 3. Return matched metadata
    
    # Placeholder for demonstration
    return {
        'title': 'Unknown',
        'artist': 'Unknown',
        'album': 'Unknown',
        'duration': 0
    }

@audio_enhanced_bp.route('/api/audio/config', methods=['GET'])
def get_config():
    try:
        """Get audio configuration"""
        config = _load_config()
        return jsonify({
        'ok': True,
        'config': config
        })

        # DUPLICATE REMOVED: @audio_enhanced_bp.route('/api/audio/config', methods=['GET'])
        # DUPLICATE REMOVED: def update_config():
        # DUPLICATE REMOVED:     """Update audio configuration"""
        # DUPLICATE REMOVED:     req_data = request.get_json(silent=True) or {}
        # DUPLICATE REMOVED:     
        # DUPLICATE REMOVED:     config = _load_config()
        # DUPLICATE REMOVED:     config.update(req_data)
        # DUPLICATE REMOVED:     _save_config(config)
        # DUPLICATE REMOVED:     
        # DUPLICATE REMOVED:     return jsonify({
        # DUPLICATE REMOVED:         'ok': True,
        # DUPLICATE REMOVED:         'message': 'Configuration updated',
        # DUPLICATE REMOVED:         'config': config
        # DUPLICATE REMOVED:     })
        # DUPLICATE REMOVED: 
        # DUPLICATE REMOVED: @audio_enhanced_bp.route('/api/audio/library/tracks', methods=['GET'])
        # DUPLICATE REMOVED: def get_tracks():
        """Get all tracks in library"""
        db = _load_audio_db()
        tracks = db.get('tracks', [])

        # Apply filters
        artist = request.args.get('artist')
        album = request.args.get('album')
        genre = request.args.get('genre')

        if artist:
        tracks = [t for t in tracks if artist.lower() in t.get('artist', '').lower()]
        if album:
        tracks = [t for t in tracks if album.lower() in t.get('album', '').lower()]
        if genre:
        tracks = [t for t in tracks if genre.lower() in t.get('genre', '').lower()]

        return jsonify({
        'ok': True,
        'tracks': tracks,
        'total': len(tracks)
        })

        @audio_enhanced_bp.route('/api/audio/library/albums', methods=['GET'])
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

def get_albums():
    try:
        """Get all albums in library"""
        db = _load_audio_db()
        albums = db.get('albums', [])

        # Apply filters
        artist = request.args.get('artist')
        year = request.args.get('year')

        if artist:
        albums = [a for a in albums if artist.lower() in a.get('artist', '').lower()]
        if year:
        albums = [a for a in albums if str(a.get('year', '')) == year]

        return jsonify({
        'ok': True,
        'albums': albums,
        'total': len(albums)
        })

        @audio_enhanced_bp.route('/api/audio/library/artists', methods=['GET'])
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

def get_artists():
    try:
        """Get all artists in library"""
        db = _load_audio_db()
        artists = db.get('artists', [])

        return jsonify({
        'ok': True,
        'artists': artists,
        'total': len(artists)
        })

        @audio_enhanced_bp.route('/api/audio/search/discogs', methods=['GET'])
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

def search_discogs():
    try:
        """Search Discogs for music metadata"""
        query = request.args.get('q', '')
        search_type = request.args.get('type', 'release')

        if not query:
        return jsonify({'ok': False, 'error': 'Query required'}), 400

        results = _search_discogs(query, search_type)

        return jsonify({
        'ok': True,
        'results': results,
        'total': len(results)
        })

        @audio_enhanced_bp.route('/api/audio/identify', methods=['POST'])
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

def identify_audio():
    try:
        """Identify audio file using AcoustID"""
        req_data = request.get_json(silent=True) or {}

        if not req_data.get('file_path'):
        return jsonify({'ok': False, 'error': 'file_path required'}), 400

        file_path = req_data.get('file_path')
        metadata = _identify_audio_acoustid(file_path)

        return jsonify({
        'ok': True,
        'metadata': metadata
        })


        @audio_enhanced_bp.route('/api/audio/tracks/add', methods=['POST'])
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

def add_track():
    try:
        """Add a track to library"""
        req_data = request.get_json(silent=True) or {}

        if not req_data.get('title') or not req_data.get('file_path'):
        return jsonify({'ok': False, 'error': 'title and file_path required'}), 400

        db = _load_audio_db()
        tracks = db.get('tracks', [])

        track = {
        'id': f"track_{datetime.utcnow().timestamp()}",
        'title': req_data.get('title'),
        'artist': req_data.get('artist', 'Unknown'),
        'album': req_data.get('album', ''),
        'album_artist': req_data.get('album_artist', ''),
        'genre': req_data.get('genre', ''),
        'year': req_data.get('year', ''),
        'track_number': req_data.get('track_number', 0),
        'disc_number': req_data.get('disc_number', 1),
        'duration': req_data.get('duration', 0),
        'bitrate': req_data.get('bitrate', 0),
        'format': req_data.get('format', 'mp3'),
        'file_path': req_data.get('file_path'),
        'artwork_url': req_data.get('artwork_url', ''),
        'lyrics': req_data.get('lyrics', ''),
        'added_at': datetime.utcnow().isoformat() + 'Z',
        'play_count': 0,
        'rating': 0,
        'tags': []
        }

        tracks.append(track)
        db['tracks'] = tracks
        _save_audio_db(db)

        return jsonify({
        'ok': True,
        'message': 'Track added to library',
        'track': track
        })


        @audio_enhanced_bp.route('/api/audio/tracks/<track_id>', methods=['PUT'])
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

def update_track(track_id):
    try:
        """Update track metadata"""
        req_data = request.get_json(silent=True) or {}

        db = _load_audio_db()
        tracks = db.get('tracks', [])

        track = next((t for t in tracks if t.get('id') == track_id), None)

        if not track:
        return jsonify({'ok': False, 'error': 'Track not found'}), 404

        # Update fields
        for key in ['title', 'artist', 'album', 'genre', 'year', 'lyrics', 'rating', 'tags']:
        if key in req_data:
        track[key] = req_data[key]

        track['updated_at'] = datetime.utcnow().isoformat() + 'Z'

        _save_audio_db(db)

        return jsonify({
        'ok': True,
        'message': 'Track updated',
        'track': track
        })


        @audio_enhanced_bp.route('/api/audio/playlists', methods=['GET'])
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

def get_playlists():
    try:
        """Get all playlists"""
        db = _load_audio_db()
        playlists = db.get('playlists', [])

        return jsonify({
        'ok': True,
        'playlists': playlists,
        'total': len(playlists)
        })

        # DUPLICATE REMOVED: @audio_enhanced_bp.route('/api/audio/playlists', methods=['POST'])
        # DUPLICATE REMOVED: def create_playlist():
        """Create a new playlist"""
        req_data = request.get_json(silent=True) or {}

        if not req_data.get('name'):
        return jsonify({'ok': False, 'error': 'Playlist name required'}), 400

        db = _load_audio_db()
        playlists = db.get('playlists', [])

        playlist = {
        'id': f"playlist_{datetime.utcnow().timestamp()}",
        'name': req_data.get('name'),
        'description': req_data.get('description', ''),
        'tracks': req_data.get('tracks', []),
        'created_at': datetime.utcnow().isoformat() + 'Z'
        }

        playlists.append(playlist)
        db['playlists'] = playlists
        _save_audio_db(db)

        return jsonify({
        'ok': True,
        'message': 'Playlist created',
        'playlist': playlist
        })


        @audio_enhanced_bp.route('/api/audio/smart-playlists', methods=['POST'])
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

def create_smart_playlist():
    try:
        """Create a smart playlist with dynamic rules"""
        req_data = request.get_json(silent=True) or {}

        if not req_data.get('name') or not req_data.get('rules'):
        return jsonify({'ok': False, 'error': 'name and rules required'}), 400

        db = _load_audio_db()
        smart_playlists = db.get('smart_playlists', [])

        smart_playlist = {
        'id': f"smart_playlist_{datetime.utcnow().timestamp()}",
        'name': req_data.get('name'),
        'description': req_data.get('description', ''),
        'rules': req_data.get('rules'),  # e.g., [{'field': 'genre', 'operator': 'equals', 'value': 'Rock'}]
        'limit': req_data.get('limit', 100),
        'sort_by': req_data.get('sort_by', 'added_at'),
        'sort_order': req_data.get('sort_order', 'desc'),
        'created_at': datetime.utcnow().isoformat() + 'Z'
        }

        smart_playlists.append(smart_playlist)
        db['smart_playlists'] = smart_playlists
        _save_audio_db(db)

        return jsonify({
        'ok': True,
        'message': 'Smart playlist created',
        'smart_playlist': smart_playlist
        })


        @audio_enhanced_bp.route('/api/audio/stats', methods=['GET'])
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

def get_audio_stats():
    try:
        """Get audio library statistics"""
        db = _load_audio_db()
        tracks = db.get('tracks', [])
        albums = db.get('albums', [])
        artists = db.get('artists', [])

        total_tracks = len(tracks)
        total_albums = len(albums)
        total_artists = len(artists)

        # Calculate total duration
        total_duration = sum(t.get('duration', 0) for t in tracks)

        # Get favorite genres
        genre_counts = {}
        for track in tracks:
        genre = track.get('genre', 'Unknown')
        genre_counts[genre] = genre_counts.get(genre, 0) + 1

        favorite_genres = sorted(genre_counts.items(), key=lambda x: x[1], reverse=True)[:5]

        # Get most played tracks
        most_played = sorted(tracks, key=lambda x: x.get('play_count', 0), reverse=True)[:10]

        return jsonify({
        'ok': True,
        'stats': {
        'total_tracks': total_tracks,
        'total_albums': total_albums,
        'total_artists': total_artists,
        'total_duration': total_duration,
        'favorite_genres': [{'genre': g[0], 'count': g[1]} for g in favorite_genres],
        'most_played': most_played
        }
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
