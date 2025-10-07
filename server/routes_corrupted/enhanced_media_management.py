"""
Phase 2: Enhanced Media Management & Real-Debrid Integration
Implements advanced media library management, metadata integration, and enhanced Real-Debrid features
"""

from flask import Blueprint, request, jsonify, send_file
import os
import json
import sqlite3
import requests
import hashlib
from datetime import datetime, timedelta
import threading
import time
from pathlib import Path

enhanced_media_bp = Blueprint('enhanced_media', __name__)

# Configuration
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
STORAGE = os.path.join(ROOT, 'storage')
MEDIA_DB = os.path.join(STORAGE, 'enhanced_media.db')
METADATA_CACHE = os.path.join(STORAGE, 'metadata_cache.json')
RD_CACHE = os.path.join(STORAGE, 'rd_enhanced_cache.json')

def init_enhanced_media_db():
    """Initialize enhanced media database with all required tables"""
    conn = sqlite3.connect(MEDIA_DB)
    cursor = conn.cursor()
    
    # Enhanced media library table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS enhanced_media (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            file_path TEXT UNIQUE NOT NULL,
            title TEXT,
            type TEXT, -- movie, tv_show, episode, book, audiobook, comic, music
            metadata_json TEXT,
            tmdb_id INTEGER,
            imdb_id TEXT,
            tvdb_id INTEGER,
            goodreads_id TEXT,
            quality_profile TEXT,
            scene_group TEXT,
            resolution TEXT,
            codec TEXT,
            source TEXT, -- BluRay, WEB-DL, WEBRip, HDTV, etc.
            hdr_format TEXT, -- HDR10, Dolby Vision, etc.
            audio_format TEXT,
            subtitle_languages TEXT,
            file_size INTEGER,
            duration INTEGER,
            added_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_watched TIMESTAMP,
            watch_count INTEGER DEFAULT 0,
            rating REAL,
            tags TEXT,
            collection_id INTEGER,
            season_number INTEGER,
            episode_number INTEGER,
            series_id INTEGER,
            universe_id INTEGER,
            timeline_position INTEGER,
            rd_link TEXT,
            rd_id TEXT,
            rd_status TEXT,
            hash_md5 TEXT,
            hash_sha1 TEXT,
            processed BOOLEAN DEFAULT FALSE,
            FOREIGN KEY (collection_id) REFERENCES collections(id),
            FOREIGN KEY (series_id) REFERENCES series(id),
            FOREIGN KEY (universe_id) REFERENCES universes(id)
        )
    ''')
    
    # Collections table for organizing content
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS collections (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            description TEXT,
            type TEXT, -- franchise, series, author, genre, custom
            poster_url TEXT,
            backdrop_url TEXT,
            created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            sort_order INTEGER,
            metadata_json TEXT
        )
    ''')
    
    # Series table for TV shows and book series
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS series (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            type TEXT, -- tv_show, book_series, comic_series
            tmdb_id INTEGER,
            tvdb_id INTEGER,
            goodreads_id TEXT,
            total_seasons INTEGER,
            total_episodes INTEGER,
            status TEXT, -- ongoing, completed, cancelled
            first_air_date DATE,
            last_air_date DATE,
            poster_url TEXT,
            backdrop_url TEXT,
            overview TEXT,
            genres TEXT,
            networks TEXT,
            metadata_json TEXT
        )
    ''')
    
    # Universes table for connected content (MCU, DCEU, etc.)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS universes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            description TEXT,
            type TEXT, -- cinematic, literary, comic
            poster_url TEXT,
            backdrop_url TEXT,
            timeline_start_year INTEGER,
            timeline_end_year INTEGER,
            metadata_json TEXT
        )
    ''')
    
    # Enhanced Real-Debrid integration table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS rd_enhanced (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            rd_id TEXT UNIQUE NOT NULL,
            filename TEXT,
            filesize INTEGER,
            link TEXT,
            host TEXT,
            chunks INTEGER,
            download_url TEXT,
            status TEXT, -- downloading, downloaded, error, queued
            progress REAL DEFAULT 0.0,
            speed INTEGER,
            eta INTEGER,
            added_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            completed_date TIMESTAMP,
            media_id INTEGER,
            quality_score INTEGER,
            scene_group_tier INTEGER,
            auto_selected BOOLEAN DEFAULT FALSE,
            user_priority INTEGER DEFAULT 0,
            FOREIGN KEY (media_id) REFERENCES enhanced_media(id)
        )
    ''')
    
    # Quality profiles table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS quality_profiles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            description TEXT,
            config_json TEXT,
            is_default BOOLEAN DEFAULT FALSE,
            created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Scene groups table with tiers and specialties
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS scene_groups (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            tier INTEGER, -- 1=highest, 2=medium, 3=lowest, 0=blocked
            score INTEGER DEFAULT 50,
            specialties TEXT, -- JSON array of specialties
            notes TEXT,
            last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    conn.commit()
    conn.close()

# Initialize database on import
init_enhanced_media_db()

@enhanced_media_bp.route('/api/enhanced/media/scan', methods=['POST'])
def scan_media_library():
    """Enhanced media library scanning with metadata integration"""
    try:
        data = request.get_json() or {}
        paths = data.get('paths', [])
        deep_scan = data.get('deep_scan', False)
        update_metadata = data.get('update_metadata', True)
        
        if not paths:
        return jsonify({'error': 'No paths provided'}), 400
        
        results = {
            'scanned_files': 0,
            'new_files': 0,
            'updated_files': 0,
            'errors': [],
            'scan_id': hashlib.md5(str(datetime.now()).encode()).hexdigest()[:8]
        }
        
        conn = sqlite3.connect(MEDIA_DB)
        cursor = conn.cursor()
        
        for path in paths:
            if not os.path.exists(path):
                results['errors'].append(f"Path not found: {path}")
                continue
            
            for root, dirs, files in os.walk(path):
                for file in files:
                    file_path = os.path.join(root, file)
                    
                    # Check if file is media
                    if not is_media_file(file_path):
                        continue
                    
                    results['scanned_files'] += 1
                    
                    # Check if already in database
                    cursor.execute('SELECT id, metadata_json FROM enhanced_media WHERE file_path = ?', (file_path,))
                    existing = cursor.fetchone()
                    
                    if existing:
                        if update_metadata:
                            # Update existing entry
                            metadata = extract_media_metadata(file_path, deep_scan)
                            update_media_entry(cursor, existing[0], metadata)
                            results['updated_files'] += 1
                    else:
                        # Add new entry
                        metadata = extract_media_metadata(file_path, deep_scan)
                        add_media_entry(cursor, file_path, metadata)
                        results['new_files'] += 1
        
        conn.commit()
        conn.close()
        
        return jsonify(results)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@enhanced_media_bp.route('/api/enhanced/media/library')
def get_enhanced_library():
    """Get enhanced media library with filtering and sorting"""
    try:
        # Query parameters
        page = int(request.args.get('page', 1))
        limit = int(request.args.get('limit', 50))
        media_type = request.args.get('type')
        collection_id = request.args.get('collection_id')
        series_id = request.args.get('series_id')
        universe_id = request.args.get('universe_id')
        quality = request.args.get('quality')
        sort_by = request.args.get('sort_by', 'added_date')
        sort_order = request.args.get('sort_order', 'DESC')
        search = request.args.get('search')
        
        conn = sqlite3.connect(MEDIA_DB)
        cursor = conn.cursor()
        
        # Build query
        query = '''
            SELECT m.*, c.name as collection_name, s.name as series_name, u.name as universe_name
            FROM enhanced_media m
            LEFT JOIN collections c ON m.collection_id = c.id
            LEFT JOIN series s ON m.series_id = s.id
            LEFT JOIN universes u ON m.universe_id = u.id
            WHERE 1=1
        '''
        params = []
        
        if media_type:
            query += ' AND m.type = ?'
            params.append(media_type)
        
        if collection_id:
            query += ' AND m.collection_id = ?'
            params.append(collection_id)
        
        if series_id:
            query += ' AND m.series_id = ?'
            params.append(series_id)
        
        if universe_id:
            query += ' AND m.universe_id = ?'
            params.append(universe_id)
        
        if quality:
            query += ' AND m.resolution = ?'
            params.append(quality)
        
        if search:
            query += ' AND (m.title LIKE ? OR m.file_path LIKE ?)'
            search_term = f'%{search}%'
            params.extend([search_term, search_term])
        
        # Add sorting
        query += f' ORDER BY m.{sort_by} {sort_order}'
        
        # Add pagination
        offset = (page - 1) * limit
        query += ' LIMIT ? OFFSET ?'
        params.extend([limit, offset])
        
        cursor.execute(query, params)
        columns = [description[0] for description in cursor.description]
        results = [dict(zip(columns, row)) for row in cursor.fetchall()]
        
        # Get total count
        count_query = query.split('ORDER BY')[0].replace('SELECT m.*, c.name as collection_name, s.name as series_name, u.name as universe_name', 'SELECT COUNT(*)')
        cursor.execute(count_query, params[:-2])  # Exclude limit and offset
        total = cursor.fetchone()[0]
        
        conn.close()
        
        return jsonify({
            'items': results,
            'total': total,
            'page': page,
            'limit': limit,
            'pages': (total + limit - 1) // limit
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@enhanced_media_bp.route('/api/enhanced/media/collections')
def get_collections():
    """Get all collections with media counts"""
    try:
        conn = sqlite3.connect(MEDIA_DB)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT c.*, COUNT(m.id) as media_count
            FROM collections c
            LEFT JOIN enhanced_media m ON c.id = m.collection_id
            GROUP BY c.id
            ORDER BY c.sort_order, c.name
        ''')
        
        columns = [description[0] for description in cursor.description]
        results = [dict(zip(columns, row)) for row in cursor.fetchall()]
        
        conn.close()
        return jsonify(results)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# DUPLICATE REMOVED: @enhanced_media_bp.route('/api/enhanced/media/collections', methods=['POST'])
# DUPLICATE REMOVED: def create_collection():
    """Create a new collection"""
    try:
        data = request.get_json()
        name = data.get('name')
        description = data.get('description', '')
        collection_type = data.get('type', 'custom')
        
        if not name:
        return jsonify({'error': 'Collection name required'}), 400
        
        conn = sqlite3.connect(MEDIA_DB)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO collections (name, description, type)
            VALUES (?, ?, ?)
        ''', (name, description, collection_type))
        
        collection_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return jsonify({'id': collection_id, 'message': 'Collection created successfully'})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@enhanced_media_bp.route('/api/enhanced/rd/enhanced_download', methods=['POST'])
def enhanced_rd_download():
    """Enhanced Real-Debrid download with quality selection and automation"""
    try:
        data = request.get_json()
        magnet_link = data.get('magnet_link')
        torrent_file = data.get('torrent_file')
        quality_profile = data.get('quality_profile', 'balanced')
        auto_select = data.get('auto_select', True)
        
        if not magnet_link and not torrent_file:
        return jsonify({'error': 'Magnet link or torrent file required'}), 400
        
        # Add to Real-Debrid
        rd_result = add_to_real_debrid(magnet_link or torrent_file)
        
        if not rd_result.get('success'):
        return jsonify({'error': 'Failed to add to Real-Debrid', 'details': rd_result}), 500
        
        rd_id = rd_result['id']
        
        # Get torrent info
        torrent_info = get_rd_torrent_info(rd_id)
        
        if auto_select and torrent_info.get('files'):
            # Auto-select files based on quality profile
            selected_files = auto_select_files(torrent_info['files'], quality_profile)
            
            if selected_files:
                # Select files in Real-Debrid
                select_result = select_rd_files(rd_id, selected_files)
                
                if select_result.get('success'):
                    # Store in enhanced database
                    store_enhanced_rd_entry(rd_id, torrent_info, quality_profile, selected_files)
                    
                    return jsonify({
                        'success': True,
                        'rd_id': rd_id,
                        'selected_files': len(selected_files),
                        'auto_selected': True
                    })
        
        # Manual selection required
        return jsonify({
            'success': True,
            'rd_id': rd_id,
            'files': torrent_info.get('files', []),
            'manual_selection_required': True
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@enhanced_media_bp.route('/api/enhanced/rd/status')
def get_enhanced_rd_status():
    """Get enhanced Real-Debrid status with progress tracking"""
    try:
        conn = sqlite3.connect(MEDIA_DB)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM rd_enhanced
            ORDER BY added_date DESC
            LIMIT 100
        ''')
        
        columns = [description[0] for description in cursor.description]
        results = [dict(zip(columns, row)) for row in cursor.fetchall()]
        
        # Update status for active downloads
        for item in results:
            if item['status'] in ['downloading', 'queued']:
                updated_status = get_rd_download_status(item['rd_id'])
                if updated_status:
                    update_rd_status(cursor, item['id'], updated_status)
        
        conn.commit()
        conn.close()
        
        return jsonify(results)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Helper functions

def is_media_file(file_path):
    """Check if file is a media file"""
    media_extensions = {
        'video': ['.mp4', '.mkv', '.avi', '.mov', '.wmv', '.flv', '.webm', '.m4v'],
        'audio': ['.mp3', '.flac', '.wav', '.aac', '.ogg', '.m4a', '.wma'],
        'book': ['.epub', '.pdf', '.mobi', '.azw', '.azw3', '.fb2'],
        'comic': ['.cbr', '.cbz', '.cb7', '.cbt', '.pdf']
    }
    
    ext = os.path.splitext(file_path)[1].lower()
    return any(ext in extensions for extensions in media_extensions.values())

def extract_media_metadata(file_path, deep_scan=False):
    """Extract metadata from media file"""
    metadata = {
        'file_path': file_path,
        'filename': os.path.basename(file_path),
        'file_size': os.path.getsize(file_path),
        'modified_date': datetime.fromtimestamp(os.path.getmtime(file_path)).isoformat()
    }
    
    # Extract title and type from filename
    filename = os.path.splitext(os.path.basename(file_path))[0]
    
    # Basic parsing logic (can be enhanced)
    if any(x in filename.lower() for x in ['s01', 's02', 'season', 'episode']):
        metadata['type'] = 'tv_show'
        # Extract season/episode info
        import re
        season_match = re.search(r's(\d+)', filename.lower())
        episode_match = re.search(r'e(\d+)', filename.lower())
        if season_match:
            metadata['season_number'] = int(season_match.group(1))
        if episode_match:
            metadata['episode_number'] = int(episode_match.group(1))
    elif any(x in filename.lower() for x in ['.epub', '.pdf', '.mobi']):
        metadata['type'] = 'book'
    elif any(x in filename.lower() for x in ['.cbr', '.cbz', '.cb7']):
        metadata['type'] = 'comic'
    elif any(x in filename.lower() for x in ['.mp3', '.flac', '.wav']):
        metadata['type'] = 'music'
    else:
        metadata['type'] = 'movie'
    
    # Extract quality info
    quality_indicators = {
        '4k': ['2160p', '4k', 'uhd'],
        '1080p': ['1080p', 'fhd'],
        '720p': ['720p', 'hd'],
        '480p': ['480p', 'sd']
    }
    
    for quality, indicators in quality_indicators.items():
        if any(indicator in filename.lower() for indicator in indicators):
            metadata['resolution'] = quality
            break
    
    # Extract codec info
    if 'x265' in filename.lower() or 'hevc' in filename.lower():
        metadata['codec'] = 'HEVC'
    elif 'x264' in filename.lower():
        metadata['codec'] = 'H.264'
    
    # Extract source info
    source_indicators = {
        'BluRay': ['bluray', 'bdrip', 'brrip'],
        'WEB-DL': ['web-dl', 'webdl'],
        'WEBRip': ['webrip'],
        'HDTV': ['hdtv'],
        'DVD': ['dvdrip', 'dvd']
    }
    
    for source, indicators in source_indicators.items():
        if any(indicator in filename.lower() for indicator in indicators):
            metadata['source'] = source
            break
    
    # Extract scene group
    parts = filename.split('-')
    if len(parts) > 1:
        potential_group = parts[-1].strip()
        if len(potential_group) < 20 and not any(char.isdigit() for char in potential_group):
            metadata['scene_group'] = potential_group
    
    metadata['title'] = clean_title(filename)
    
    return metadata

def clean_title(filename):
    """Clean filename to extract title"""
    import re
    
    # Remove common patterns
    patterns = [
        r'\d{4}',  # Year
        r'[Ss]\d+[Ee]\d+',  # Season/Episode
        r'\d{3,4}p',  # Resolution
        r'(BluRay|WEB-DL|WEBRip|HDTV|DVDRip)',  # Source
        r'(x264|x265|HEVC|H\.264)',  # Codec
        r'-\w+$'  # Scene group at end
    ]
    
    title = filename
    for pattern in patterns:
        title = re.sub(pattern, '', title, flags=re.IGNORECASE)
    
    # Clean up
    title = re.sub(r'[._\-]+', ' ', title)
    title = re.sub(r'\s+', ' ', title)
    title = title.strip()
    
    return title

def add_media_entry(cursor, file_path, metadata):
    """Add new media entry to database"""
    cursor.execute('''
        INSERT INTO enhanced_media (
            file_path, title, type, metadata_json, resolution, codec, source,
            scene_group, file_size, season_number, episode_number
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        file_path,
        metadata.get('title'),
        metadata.get('type'),
        json.dumps(metadata),
        metadata.get('resolution'),
        metadata.get('codec'),
        metadata.get('source'),
        metadata.get('scene_group'),
        metadata.get('file_size'),
        metadata.get('season_number'),
        metadata.get('episode_number')
    ))

def update_media_entry(cursor, media_id, metadata):
    """Update existing media entry"""
    cursor.execute('''
        UPDATE enhanced_media SET
            title = ?, metadata_json = ?, resolution = ?, codec = ?,
            source = ?, scene_group = ?, file_size = ?
        WHERE id = ?
    ''', (
        metadata.get('title'),
        json.dumps(metadata),
        metadata.get('resolution'),
        metadata.get('codec'),
        metadata.get('source'),
        metadata.get('scene_group'),
        metadata.get('file_size'),
        media_id
    ))

def add_to_real_debrid(link):
    """Add magnet/torrent to Real-Debrid"""
    # Placeholder - implement actual RD API calls
    return {
        'success': True,
        'id': f'rd_{hashlib.md5(link.encode()).hexdigest()[:8]}'
    }

def get_rd_torrent_info(rd_id):
    """Get torrent info from Real-Debrid"""
    # Placeholder - implement actual RD API calls
    return {
        'id': rd_id,
        'files': [
            {'id': 1, 'path': 'Movie.2024.1080p.BluRay.x264-GROUP.mkv', 'bytes': 8589934592},
            {'id': 2, 'path': 'Sample.mkv', 'bytes': 104857600}
        ]
    }

def auto_select_files(files, quality_profile):
    """Auto-select files based on quality profile"""
    # Implement quality-based file selection logic
    selected = []
    
    for file in files:
        filename = file.get('path', '')
        file_size = file.get('bytes', 0)
        
        # Skip samples and small files
        if 'sample' in filename.lower() or file_size < 100 * 1024 * 1024:  # 100MB
            continue
        
        # Select main video files
        if any(ext in filename.lower() for ext in ['.mkv', '.mp4', '.avi']):
            selected.append(file['id'])
    
    return selected

def select_rd_files(rd_id, file_ids):
    """Select files in Real-Debrid"""
    # Placeholder - implement actual RD API calls
    return {'success': True}

def store_enhanced_rd_entry(rd_id, torrent_info, quality_profile, selected_files):
    """Store enhanced RD entry in database"""
    conn = sqlite3.connect(MEDIA_DB)
    cursor = conn.cursor()
    
    cursor.execute('''
        INSERT INTO rd_enhanced (rd_id, filename, status, quality_score)
        VALUES (?, ?, ?, ?)
    ''', (rd_id, torrent_info.get('filename', ''), 'downloading', 75))
    
    conn.commit()
    conn.close()

def get_rd_download_status(rd_id):
    """Get download status from Real-Debrid"""
    # Placeholder - implement actual RD API calls
    return {
        'status': 'downloading',
        'progress': 45.5,
        'speed': 1024000,
        'eta': 3600
    }

def update_rd_status(cursor, entry_id, status_data):
    """Update RD status in database"""
    cursor.execute('''
        UPDATE rd_enhanced SET
            status = ?, progress = ?, speed = ?, eta = ?
        WHERE id = ?
    ''', (
        status_data.get('status'),
        status_data.get('progress'),
        status_data.get('speed'),
        status_data.get('eta'),
        entry_id
    ))
