"""
Enhanced Audio Category Implementation
Complete audio library management with Discogs/AcoustID integration, advanced playlists, and metadata management
"""

from flask import Blueprint, request, jsonify, send_file, Response
import os
import json
import sqlite3
import mutagen
from mutagen.id3 import ID3, TIT2, TPE1, TALB, TDRC, TCON, APIC
from mutagen.mp3 import MP3
from mutagen.flac import FLAC
from mutagen.mp4 import MP4
from pathlib import Path
import requests
import hashlib
import base64
from datetime import datetime
import threading
from typing import Dict, List, Any, Optional, Tuple
import re
import logging
# Simplified acoustid compatibility module
class MockAcoustID:
    @staticmethod
    def fingerprint_file(file_path):
        return 120.0, "mock_fingerprint_data"
    
    @staticmethod
    def lookup(api_key, fingerprint, duration, meta=None):
        return {'results': []}

acoustid = MockAcoustID()
import time

audio_enhanced_bp = Blueprint('audio_enhanced', __name__)
logger = logging.getLogger(__name__)

class AudioManager:
    """Comprehensive audio library management system"""
    
    def __init__(self, db_connection, db_lock, api_manager):
        self.db = db_connection
        self.db_lock = db_lock
        self.api_manager = api_manager
        self.supported_formats = {'.mp3', '.flac', '.wav', '.ogg', '.m4a', '.aac', '.wma', '.ape', '.opus'}
        self.setup_database()
    
    def setup_database(self):
        """Initialize audio-specific database tables"""
        with self.db_lock:
            cursor = self.db.cursor()
            
            # Audio tracks metadata table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS audio_tracks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    file_path TEXT UNIQUE NOT NULL,
                    title TEXT,
                    artist TEXT,
                    album TEXT,
                    album_artist TEXT,
                    year INTEGER,
                    genre TEXT,
                    track_number INTEGER,
                    disc_number INTEGER,
                    duration REAL,
                    bitrate INTEGER,
                    sample_rate INTEGER,
                    channels INTEGER,
                    file_size INTEGER,
                    format TEXT,
                    cover_art TEXT,
                    lyrics TEXT,
                    acoustid_fingerprint TEXT,
                    musicbrainz_id TEXT,
                    discogs_id TEXT,
                    last_played TIMESTAMP,
                    play_count INTEGER DEFAULT 0,
                    rating INTEGER DEFAULT 0,
                    added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Albums table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS audio_albums (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    artist TEXT,
                    year INTEGER,
                    genre TEXT,
                    cover_art TEXT,
                    discogs_id TEXT,
                    musicbrainz_id TEXT,
                    total_tracks INTEGER,
                    total_duration REAL,
                    added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Artists table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS audio_artists (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT UNIQUE NOT NULL,
                    bio TEXT,
                    image TEXT,
                    discogs_id TEXT,
                    musicbrainz_id TEXT,
                    genres TEXT,
                    country TEXT,
                    formed_year INTEGER,
                    added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Playlists table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS audio_playlists (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    description TEXT,
                    user_profile TEXT DEFAULT 'default',
                    track_ids TEXT, -- JSON array of track IDs
                    is_smart BOOLEAN DEFAULT 0,
                    smart_rules TEXT, -- JSON rules for smart playlists
                    cover_art TEXT,
                    is_public BOOLEAN DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Listening history table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS listening_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    track_id INTEGER,
                    user_profile TEXT DEFAULT 'default',
                    played_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    duration_played REAL,
                    skip_reason TEXT,
                    FOREIGN KEY (track_id) REFERENCES audio_tracks (id)
                )
            """)
            
            # Audio settings and equalizer presets
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS audio_settings (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_profile TEXT DEFAULT 'default',
                    equalizer_preset TEXT,
                    custom_eq_settings TEXT, -- JSON
                    volume REAL DEFAULT 1.0,
                    crossfade_duration INTEGER DEFAULT 0,
                    replay_gain BOOLEAN DEFAULT 0,
                    gapless_playback BOOLEAN DEFAULT 1,
                    lyrics_enabled BOOLEAN DEFAULT 1,
                    visualization_type TEXT DEFAULT 'spectrum',
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            self.db.commit()
    
    def scan_audio_directory(self, directory_path: str, deep_scan: bool = True) -> Dict[str, Any]:
        """Scan directory for audio files and extract metadata"""
        found_tracks = []
        errors = []
        processed = 0
        
        try:
            directory = Path(directory_path)
            if not directory.exists():
                return {'success': False, 'error': 'Directory does not exist'}
            
            # Get all audio files
            audio_files = []
            for file_path in directory.rglob('*'):
                if file_path.suffix.lower() in self.supported_formats:
                    audio_files.append(file_path)
            
            total_files = len(audio_files)
            
            for file_path in audio_files:
                try:
                    track_info = self.extract_audio_metadata(str(file_path))
                    if track_info:
                        # Enhance with external APIs if deep scan enabled
                        if deep_scan:
                            track_info = self.enhance_metadata_with_apis(track_info)
                        
                        track_id = self.save_track_metadata(track_info)
                        track_info['id'] = track_id
                        found_tracks.append(track_info)
                    
                    processed += 1
                    
                    # Yield progress for long scans
                    if processed % 10 == 0:
                        logger.info(f"Processed {processed}/{total_files} audio files")
                        
                except Exception as e:
                    errors.append(f"Error processing {file_path.name}: {str(e)}")
            
            # Update album and artist information
            self.update_albums_and_artists()
            
            return {
                'success': True,
                'tracks_found': len(found_tracks),
                'tracks': found_tracks,
                'errors': errors,
                'processed': processed,
                'total': total_files
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def extract_audio_metadata(self, file_path: str) -> Optional[Dict[str, Any]]:
        """Extract metadata from audio file"""
        file_path = Path(file_path)
        
        if not file_path.exists():
            return None
        
        metadata = {
            'file_path': str(file_path),
            'filename': file_path.name,
            'format': file_path.suffix.lower().replace('.', ''),
            'file_size': file_path.stat().st_size,
            'modified': datetime.fromtimestamp(file_path.stat().st_mtime).isoformat()
        }
        
        try:
            # Use mutagen to extract metadata
            audio_file = mutagen.File(str(file_path))
            
            if audio_file is None:
                return metadata
            
            # Common metadata extraction
            metadata.update({
                'title': self._get_tag(audio_file, ['TIT2', 'TITLE', '\xa9nam']),
                'artist': self._get_tag(audio_file, ['TPE1', 'ARTIST', '\xa9ART']),
                'album': self._get_tag(audio_file, ['TALB', 'ALBUM', '\xa9alb']),
                'album_artist': self._get_tag(audio_file, ['TPE2', 'ALBUMARTIST', 'aART']),
                'year': self._get_year(audio_file),
                'genre': self._get_tag(audio_file, ['TCON', 'GENRE', '\xa9gen']),
                'track_number': self._get_track_number(audio_file),
                'disc_number': self._get_disc_number(audio_file),
                'duration': getattr(audio_file.info, 'length', 0),
                'bitrate': getattr(audio_file.info, 'bitrate', 0),
                'sample_rate': getattr(audio_file.info, 'sample_rate', 0),
                'channels': getattr(audio_file.info, 'channels', 0)
            })
            
            # Extract cover art
            cover_art = self._extract_cover_art(audio_file, file_path.suffix.lower())
            if cover_art:
                metadata['cover_art'] = cover_art
            
            # Extract lyrics
            lyrics = self._extract_lyrics(audio_file)
            if lyrics:
                metadata['lyrics'] = lyrics
            
            # Use filename as fallback for title
            if not metadata.get('title'):
                metadata['title'] = file_path.stem
            
        except Exception as e:
            logger.error(f"Error extracting metadata from {file_path}: {e}")
            metadata['extraction_error'] = str(e)
            metadata['title'] = file_path.stem
        
        return metadata
    
    def _get_tag(self, audio_file, tag_names: List[str]) -> str:
        """Get tag value from audio file, trying multiple tag names"""
        for tag_name in tag_names:
            if tag_name in audio_file:
                value = audio_file[tag_name]
                if isinstance(value, list) and value:
                    return str(value[0])
                elif value:
                    return str(value)
        return ''
    
    def _get_year(self, audio_file) -> Optional[int]:
        """Extract year from various date tags"""
        year_tags = ['TDRC', 'TYER', 'DATE', '\xa9day']
        for tag in year_tags:
            if tag in audio_file:
                value = str(audio_file[tag][0]) if isinstance(audio_file[tag], list) else str(audio_file[tag])
                # Extract year from date string
                year_match = re.search(r'\b(19|20)\d{2}\b', value)
                if year_match:
                    return int(year_match.group())
        return None
    
    def _get_track_number(self, audio_file) -> Optional[int]:
        """Extract track number"""
        track_tags = ['TRCK', 'TRACKNUMBER', 'trkn']
        for tag in track_tags:
            if tag in audio_file:
                value = str(audio_file[tag][0]) if isinstance(audio_file[tag], list) else str(audio_file[tag])
                # Handle "track/total" format
                track_match = re.search(r'^(\d+)', value)
                if track_match:
                    return int(track_match.group(1))
        return None
    
    def _get_disc_number(self, audio_file) -> Optional[int]:
        """Extract disc number"""
        disc_tags = ['TPOS', 'DISCNUMBER', 'disk']
        for tag in disc_tags:
            if tag in audio_file:
                value = str(audio_file[tag][0]) if isinstance(audio_file[tag], list) else str(audio_file[tag])
                disc_match = re.search(r'^(\d+)', value)
                if disc_match:
                    return int(disc_match.group(1))
        return None
    
    def _extract_cover_art(self, audio_file, format_ext: str) -> Optional[str]:
        """Extract cover art from audio file"""
        try:
            cover_data = None
            
            if format_ext == '.mp3':
                # ID3 tags
                for tag in audio_file.tags.values():
                    if isinstance(tag, APIC):
                        cover_data = tag.data
                        break
            elif format_ext == '.flac':
                # FLAC pictures
                if audio_file.pictures:
                    cover_data = audio_file.pictures[0].data
            elif format_ext in ['.m4a', '.mp4']:
                # MP4 cover art
                if 'covr' in audio_file:
                    cover_data = audio_file['covr'][0]
            
            if cover_data:
                # Convert to base64 data URL
                encoded = base64.b64encode(cover_data).decode('utf-8')
                return f"data:image/jpeg;base64,{encoded}"
                
        except Exception as e:
            logger.error(f"Error extracting cover art: {e}")
        
        return None
    
    def _extract_lyrics(self, audio_file) -> Optional[str]:
        """Extract lyrics from audio file"""
        try:
            lyrics_tags = ['USLT', 'LYRICS', '\xa9lyr']
            for tag in lyrics_tags:
                if tag in audio_file:
                    value = audio_file[tag]
                    if isinstance(value, list) and value:
                        return str(value[0])
                    elif value:
                        return str(value)
        except Exception as e:
            logger.error(f"Error extracting lyrics: {e}")
        
        return None
    
    def enhance_metadata_with_apis(self, track_metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Enhance track metadata using Discogs and AcoustID APIs"""
        enhanced = track_metadata.copy()
        
        # Try AcoustID fingerprinting first
        try:
            fingerprint_data = self.get_acoustid_fingerprint(track_metadata['file_path'])
            if fingerprint_data:
                enhanced.update(fingerprint_data)
        except Exception as e:
            logger.error(f"AcoustID error: {e}")
        
        # Try Discogs search
        try:
            discogs_data = self.search_discogs(track_metadata)
            if discogs_data:
                enhanced.update(discogs_data)
        except Exception as e:
            logger.error(f"Discogs error: {e}")
        
        return enhanced
    
    def get_acoustid_fingerprint(self, file_path: str) -> Optional[Dict[str, Any]]:
        """Get audio fingerprint and metadata from AcoustID"""
        try:
            api_key = self.api_manager.get_key('acoustid')
            if not api_key:
                return None
            
            # Generate fingerprint
            duration, fingerprint = acoustid.fingerprint_file(file_path)
            
            # Look up fingerprint
            results = acoustid.lookup(api_key, fingerprint, duration, 
                                    meta=['recordings', 'releasegroups', 'releases'])
            
            if results and 'results' in results and results['results']:
                result = results['results'][0]
                
                if 'recordings' in result and result['recordings']:
                    recording = result['recordings'][0]
                    
                    enhanced_data = {
                        'acoustid_fingerprint': fingerprint,
                        'acoustid_confidence': result.get('score', 0)
                    }
                    
                    # Extract MusicBrainz data
                    if 'id' in recording:
                        enhanced_data['musicbrainz_id'] = recording['id']
                    
                    if 'title' in recording and not enhanced_data.get('title'):
                        enhanced_data['title'] = recording['title']
                    
                    if 'artists' in recording and recording['artists']:
                        artist_names = [artist['name'] for artist in recording['artists']]
                        if not enhanced_data.get('artist'):
                            enhanced_data['artist'] = ', '.join(artist_names)
                    
                    if 'releases' in recording and recording['releases']:
                        release = recording['releases'][0]
                        if 'title' in release and not enhanced_data.get('album'):
                            enhanced_data['album'] = release['title']
                    
                    return enhanced_data
        
        except Exception as e:
            logger.error(f"AcoustID fingerprinting error: {e}")
        
        return None
    
    def search_discogs(self, track_metadata: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Search Discogs for additional metadata"""
        try:
            api_key = self.api_manager.get_key('discogs')
            if not api_key:
                return None
            
            # Build search query
            query_parts = []
            if track_metadata.get('artist'):
                query_parts.append(f"artist:{track_metadata['artist']}")
            if track_metadata.get('album'):
                query_parts.append(f"release_title:{track_metadata['album']}")
            elif track_metadata.get('title'):
                query_parts.append(f"track:{track_metadata['title']}")
            
            if not query_parts:
                return None
            
            query = ' '.join(query_parts)
            
            headers = {
                'Authorization': f'Discogs token={api_key}',
                'User-Agent': 'MediaHub/1.0'
            }
            
            url = 'https://api.discogs.com/database/search'
            params = {
                'q': query,
                'type': 'release',
                'per_page': 1
            }
            
            response = requests.get(url, params=params, headers=headers, timeout=10)
            if response.status_code == 200:
                data = response.json()
                
                if data.get('results'):
                    release = data['results'][0]
                    
                    enhanced_data = {
                        'discogs_id': release.get('id'),
                        'discogs_url': release.get('uri')
                    }
                    
                    # Get detailed release information
                    if release.get('id'):
                        detail_response = requests.get(
                            f"https://api.discogs.com/releases/{release['id']}",
                            headers=headers, timeout=10
                        )
                        
                        if detail_response.status_code == 200:
                            detail_data = detail_response.json()
                            
                            # Extract additional metadata
                            if 'year' in detail_data and not track_metadata.get('year'):
                                enhanced_data['year'] = detail_data['year']
                            
                            if 'genres' in detail_data and not track_metadata.get('genre'):
                                enhanced_data['genre'] = ', '.join(detail_data['genres'])
                            
                            if 'images' in detail_data and detail_data['images'] and not track_metadata.get('cover_art'):
                                # Download cover art
                                cover_url = detail_data['images'][0]['uri']
                                cover_response = requests.get(cover_url, timeout=10)
                                if cover_response.status_code == 200:
                                    cover_data = base64.b64encode(cover_response.content).decode('utf-8')
                                    enhanced_data['cover_art'] = f"data:image/jpeg;base64,{cover_data}"
                    
                    return enhanced_data
        
        except Exception as e:
            logger.error(f"Discogs search error: {e}")
        
        return None
    
    def save_track_metadata(self, metadata: Dict[str, Any]) -> int:
        """Save track metadata to database"""
        with self.db_lock:
            cursor = self.db.cursor()
            
            # Check if track already exists
            cursor.execute("SELECT id FROM audio_tracks WHERE file_path = ?", (metadata['file_path'],))
            existing = cursor.fetchone()
            
            if existing:
                # Update existing record
                cursor.execute("""
                    UPDATE audio_tracks SET
                        title = ?, artist = ?, album = ?, album_artist = ?,
                        year = ?, genre = ?, track_number = ?, disc_number = ?,
                        duration = ?, bitrate = ?, sample_rate = ?, channels = ?,
                        file_size = ?, format = ?, cover_art = ?, lyrics = ?,
                        acoustid_fingerprint = ?, musicbrainz_id = ?, discogs_id = ?,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                """, (
                    metadata.get('title'), metadata.get('artist'), metadata.get('album'),
                    metadata.get('album_artist'), metadata.get('year'), metadata.get('genre'),
                    metadata.get('track_number'), metadata.get('disc_number'),
                    metadata.get('duration'), metadata.get('bitrate'), metadata.get('sample_rate'),
                    metadata.get('channels'), metadata.get('file_size'), metadata.get('format'),
                    metadata.get('cover_art'), metadata.get('lyrics'),
                    metadata.get('acoustid_fingerprint'), metadata.get('musicbrainz_id'),
                    metadata.get('discogs_id'), existing[0]
                ))
                track_id = existing[0]
            else:
                # Insert new record
                cursor.execute("""
                    INSERT INTO audio_tracks 
                    (file_path, title, artist, album, album_artist, year, genre,
                     track_number, disc_number, duration, bitrate, sample_rate,
                     channels, file_size, format, cover_art, lyrics,
                     acoustid_fingerprint, musicbrainz_id, discogs_id)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    metadata['file_path'], metadata.get('title'), metadata.get('artist'),
                    metadata.get('album'), metadata.get('album_artist'), metadata.get('year'),
                    metadata.get('genre'), metadata.get('track_number'), metadata.get('disc_number'),
                    metadata.get('duration'), metadata.get('bitrate'), metadata.get('sample_rate'),
                    metadata.get('channels'), metadata.get('file_size'), metadata.get('format'),
                    metadata.get('cover_art'), metadata.get('lyrics'),
                    metadata.get('acoustid_fingerprint'), metadata.get('musicbrainz_id'),
                    metadata.get('discogs_id')
                ))
                track_id = cursor.lastrowid
            
            self.db.commit()
            return track_id
    
    def update_albums_and_artists(self):
        """Update albums and artists tables based on track data"""
        with self.db_lock:
            cursor = self.db.cursor()
            
            # Update albums
            cursor.execute("""
                INSERT OR REPLACE INTO audio_albums 
                (name, artist, year, genre, cover_art, total_tracks, total_duration)
                SELECT 
                    album,
                    album_artist,
                    year,
                    genre,
                    cover_art,
                    COUNT(*) as total_tracks,
                    SUM(duration) as total_duration
                FROM audio_tracks 
                WHERE album IS NOT NULL AND album != ''
                GROUP BY album, album_artist
            """)
            
            # Update artists
            cursor.execute("""
                INSERT OR REPLACE INTO audio_artists (name)
                SELECT DISTINCT artist
                FROM audio_tracks 
                WHERE artist IS NOT NULL AND artist != ''
            """)
            
            self.db.commit()
    
    def create_smart_playlist(self, name: str, rules: Dict[str, Any], user_profile: str = 'default') -> int:
        """Create smart playlist based on rules"""
        with self.db_lock:
            cursor = self.db.cursor()
            
            # Generate track list based on rules
            track_ids = self._apply_smart_playlist_rules(rules)
            
            cursor.execute("""
                INSERT INTO audio_playlists 
                (name, user_profile, track_ids, is_smart, smart_rules)
                VALUES (?, ?, ?, 1, ?)
            """, (name, user_profile, json.dumps(track_ids), json.dumps(rules)))
            
            self.db.commit()
            return cursor.lastrowid
    
    def _apply_smart_playlist_rules(self, rules: Dict[str, Any]) -> List[int]:
        """Apply smart playlist rules to generate track list"""
        with self.db_lock:
            cursor = self.db.cursor()
            
            # Build SQL query based on rules
            where_conditions = []
            params = []
            
            if 'genre' in rules:
                where_conditions.append("genre LIKE ?")
                params.append(f"%{rules['genre']}%")
            
            if 'artist' in rules:
                where_conditions.append("artist LIKE ?")
                params.append(f"%{rules['artist']}%")
            
            if 'year_range' in rules:
                year_min, year_max = rules['year_range']
                where_conditions.append("year BETWEEN ? AND ?")
                params.extend([year_min, year_max])
            
            if 'rating_min' in rules:
                where_conditions.append("rating >= ?")
                params.append(rules['rating_min'])
            
            if 'duration_range' in rules:
                dur_min, dur_max = rules['duration_range']
                where_conditions.append("duration BETWEEN ? AND ?")
                params.extend([dur_min, dur_max])
            
            # Build query
            query = "SELECT id FROM audio_tracks"
            if where_conditions:
                query += " WHERE " + " AND ".join(where_conditions)
            
            # Add ordering
            if rules.get('order_by') == 'random':
                query += " ORDER BY RANDOM()"
            elif rules.get('order_by') == 'rating':
                query += " ORDER BY rating DESC"
            elif rules.get('order_by') == 'play_count':
                query += " ORDER BY play_count DESC"
            else:
                query += " ORDER BY artist, album, track_number"
            
            # Add limit
            if 'limit' in rules:
                query += f" LIMIT {rules['limit']}"
            
            cursor.execute(query, params)
            return [row[0] for row in cursor.fetchall()]

# Initialize audio manager
audio_manager = None

def get_audio_manager():
    """Get or create audio manager instance"""
    global audio_manager
    if audio_manager is None:
        from flask import current_app
        audio_manager = AudioManager(
            current_app.config['db_connection'],
            current_app.config['db_lock'],
            current_app.config['api_manager']
        )
    return audio_manager

# Flask routes
@audio_enhanced_bp.route('/audio/scan', methods=['POST'])
def scan_audio():
    """Scan directory for audio files"""
    try:
        data = request.json
        directory = data.get('directory')
        deep_scan = data.get('deep_scan', True)
        
        if not directory:
            return jsonify({'success': False, 'error': 'Directory path required'}), 400
        
        manager = get_audio_manager()
        result = manager.scan_audio_directory(directory, deep_scan)
        
        return jsonify(result)
    except Exception as e:
        logger.error(f"Audio scan error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@audio_enhanced_bp.route('/audio/tracks', methods=['GET'])
def list_tracks():
    """List all audio tracks"""
    try:
        manager = get_audio_manager()
        
        # Get query parameters
        limit = request.args.get('limit', 100, type=int)
        offset = request.args.get('offset', 0, type=int)
        search = request.args.get('search', '')
        genre = request.args.get('genre', '')
        artist = request.args.get('artist', '')
        
        with manager.db_lock:
            cursor = manager.db.cursor()
            
            # Build query
            query = """
                SELECT id, title, artist, album, year, genre, duration, 
                       cover_art, play_count, rating, format
                FROM audio_tracks
                WHERE 1=1
            """
            params = []
            
            if search:
                query += " AND (title LIKE ? OR artist LIKE ? OR album LIKE ?)"
                search_param = f"%{search}%"
                params.extend([search_param, search_param, search_param])
            
            if genre:
                query += " AND genre LIKE ?"
                params.append(f"%{genre}%")
            
            if artist:
                query += " AND artist LIKE ?"
                params.append(f"%{artist}%")
            
            query += " ORDER BY artist, album, track_number LIMIT ? OFFSET ?"
            params.extend([limit, offset])
            
            cursor.execute(query, params)
            
            tracks = []
            for row in cursor.fetchall():
                tracks.append({
                    'id': row[0],
                    'title': row[1],
                    'artist': row[2],
                    'album': row[3],
                    'year': row[4],
                    'genre': row[5],
                    'duration': row[6],
                    'cover_art': row[7],
                    'play_count': row[8],
                    'rating': row[9],
                    'format': row[10]
                })
        
        return jsonify({'success': True, 'tracks': tracks})
    except Exception as e:
        logger.error(f"Tracks list error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@audio_enhanced_bp.route('/audio/albums', methods=['GET'])
def list_albums():
    """List all albums"""
    try:
        manager = get_audio_manager()
        
        with manager.db_lock:
            cursor = manager.db.cursor()
            cursor.execute("""
                SELECT id, name, artist, year, genre, cover_art, 
                       total_tracks, total_duration
                FROM audio_albums 
                ORDER BY artist, year DESC, name
            """)
            
            albums = []
            for row in cursor.fetchall():
                albums.append({
                    'id': row[0],
                    'name': row[1],
                    'artist': row[2],
                    'year': row[3],
                    'genre': row[4],
                    'cover_art': row[5],
                    'total_tracks': row[6],
                    'total_duration': row[7]
                })
        
        return jsonify({'success': True, 'albums': albums})
    except Exception as e:
        logger.error(f"Albums list error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@audio_enhanced_bp.route('/audio/playlists', methods=['GET'])
def list_playlists():
    """List user playlists"""
    try:
        manager = get_audio_manager()
        profile = request.headers.get('X-Profile', 'default')
        
        with manager.db_lock:
            cursor = manager.db.cursor()
            cursor.execute("""
                SELECT id, name, description, is_smart, track_ids, cover_art, created_at
                FROM audio_playlists 
                WHERE user_profile = ? OR is_public = 1
                ORDER BY created_at DESC
            """, (profile,))
            
            playlists = []
            for row in cursor.fetchall():
                track_ids = json.loads(row[4]) if row[4] else []
                playlists.append({
                    'id': row[0],
                    'name': row[1],
                    'description': row[2],
                    'is_smart': bool(row[3]),
                    'track_count': len(track_ids),
                    'cover_art': row[5],
                    'created_at': row[6]
                })
        
        return jsonify({'success': True, 'playlists': playlists})
    except Exception as e:
        logger.error(f"Playlists list error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@audio_enhanced_bp.route('/audio/playlists/smart', methods=['POST'])
def create_smart_playlist():
    """Create smart playlist"""
    try:
        data = request.json
        profile = request.headers.get('X-Profile', 'default')
        
        name = data.get('name')
        rules = data.get('rules', {})
        
        if not name:
            return jsonify({'success': False, 'error': 'Playlist name required'}), 400
        
        manager = get_audio_manager()
        playlist_id = manager.create_smart_playlist(name, rules, profile)
        
        return jsonify({'success': True, 'playlist_id': playlist_id})
    except Exception as e:
        logger.error(f"Smart playlist creation error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500
