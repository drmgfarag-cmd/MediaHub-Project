from flask import Blueprint, jsonify, request, send_file
import os, json, re
import requests
from datetime import datetime
import xml.etree.ElementTree as ET
from xml.dom import minidom

metadata_export_bp = Blueprint('metadata_export', __name__)

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
STO = os.path.join(ROOT, 'storage')
METADATA_CACHE = os.path.join(STO, 'metadata_cache')
ARTWORK_CACHE = os.path.join(STO, 'artwork_cache')
METADATA_CONFIG = os.path.join(STO, 'config', 'metadata_export.json')

def _load_config():
    """Load metadata export configuration"""
    try:
        with open(METADATA_CONFIG, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return {
            'format': 'kodi',  # kodi, tmm, mediaelch, emby, jellyfin
            'artwork_types': ['poster', 'fanart', 'banner', 'clearlogo', 'thumb'],
            'download_artwork': True,
            'artwork_format': 'jpg',
            'artwork_quality': 95,
            'create_nfo': True,
            'offline_mode': False,
            'cache_duration_days': 30
        }

def _save_config(data):
    """Save metadata export configuration"""
    os.makedirs(os.path.dirname(METADATA_CONFIG), exist_ok=True)
    tmp = METADATA_CONFIG + '.tmp'
    with open(tmp, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)
    os.replace(tmp, METADATA_CONFIG)

def _download_artwork(url, save_path):
    """Download artwork from URL"""
    try:
        response = requests.get(url, timeout=30, stream=True)
        if response.status_code == 200:
            os.makedirs(os.path.dirname(save_path), exist_ok=True)
            with open(save_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            return True
        return False
    except Exception:
        return False

def _generate_kodi_nfo(metadata, media_type='movie'):
    """Generate Kodi-compatible NFO XML"""
    if media_type == 'movie':
        root = ET.Element('movie')
    elif media_type == 'tvshow':
        root = ET.Element('tvshow')
    elif media_type == 'episode':
        root = ET.Element('episodedetails')
    else:
        root = ET.Element('movie')
    
    # Basic info
    if metadata.get('title'):
        ET.SubElement(root, 'title').text = metadata['title']
    
    if metadata.get('original_title'):
        ET.SubElement(root, 'originaltitle').text = metadata['original_title']
    
    if metadata.get('year'):
        ET.SubElement(root, 'year').text = str(metadata['year'])
    
    if metadata.get('plot'):
        ET.SubElement(root, 'plot').text = metadata['plot']
    
    if metadata.get('tagline'):
        ET.SubElement(root, 'tagline').text = metadata['tagline']
    
    if metadata.get('rating'):
        ET.SubElement(root, 'rating').text = str(metadata['rating'])
    
    if metadata.get('votes'):
        ET.SubElement(root, 'votes').text = str(metadata['votes'])
    
    if metadata.get('runtime'):
        ET.SubElement(root, 'runtime').text = str(metadata['runtime'])
    
    if metadata.get('mpaa'):
        ET.SubElement(root, 'mpaa').text = metadata['mpaa']
    
    # IDs
    if metadata.get('imdb_id'):
        ET.SubElement(root, 'id').text = metadata['imdb_id']
        ET.SubElement(root, 'imdbid').text = metadata['imdb_id']
    
    if metadata.get('tmdb_id'):
        ET.SubElement(root, 'tmdbid').text = str(metadata['tmdb_id'])
    
    if metadata.get('tvdb_id'):
        ET.SubElement(root, 'tvdbid').text = str(metadata['tvdb_id'])
    
    # Genres
    for genre in metadata.get('genres', []):
        ET.SubElement(root, 'genre').text = genre
    
    # Studios
    for studio in metadata.get('studios', []):
        ET.SubElement(root, 'studio').text = studio
    
    # Actors
    for actor in metadata.get('actors', []):
        actor_elem = ET.SubElement(root, 'actor')
        ET.SubElement(actor_elem, 'name').text = actor.get('name', '')
        ET.SubElement(actor_elem, 'role').text = actor.get('role', '')
        if actor.get('thumb'):
            ET.SubElement(actor_elem, 'thumb').text = actor['thumb']
    
    # Directors
    for director in metadata.get('directors', []):
        ET.SubElement(root, 'director').text = director
    
    # Writers
    for writer in metadata.get('writers', []):
        ET.SubElement(root, 'credits').text = writer
    
    # Episode-specific
    if media_type == 'episode':
        if metadata.get('season'):
            ET.SubElement(root, 'season').text = str(metadata['season'])
        if metadata.get('episode'):
            ET.SubElement(root, 'episode').text = str(metadata['episode'])
        if metadata.get('aired'):
            ET.SubElement(root, 'aired').text = metadata['aired']
    
    # TV show-specific
    if media_type == 'tvshow':
        if metadata.get('premiered'):
            ET.SubElement(root, 'premiered').text = metadata['premiered']
        if metadata.get('status'):
            ET.SubElement(root, 'status').text = metadata['status']
    
    # Format XML nicely
    xml_str = ET.tostring(root, encoding='utf-8')
    dom = minidom.parseString(xml_str)
    return dom.toprettyxml(indent='  ', encoding='utf-8').decode('utf-8')

def _generate_tmm_nfo(metadata, media_type='movie'):
    """Generate TinyMediaManager-compatible NFO XML"""
    # TMM uses similar format to Kodi with some extensions
    nfo = _generate_kodi_nfo(metadata, media_type)
    
    # TMM-specific additions could go here
    # For now, TMM is largely Kodi-compatible
    
    return nfo

def _generate_mediaelch_nfo(metadata, media_type='movie'):
    """Generate MediaElch-compatible NFO XML"""
    # MediaElch also uses Kodi format with minor differences
    return _generate_kodi_nfo(metadata, media_type)

def _get_artwork_filename(artwork_type, format_type='kodi'):
    """Get the appropriate filename for artwork based on format"""
    # Kodi naming convention
    kodi_names = {
        'poster': 'poster.jpg',
        'fanart': 'fanart.jpg',
        'banner': 'banner.jpg',
        'clearlogo': 'clearlogo.png',
        'thumb': 'thumb.jpg',
        'clearart': 'clearart.png',
        'landscape': 'landscape.jpg',
        'discart': 'disc.png'
    }
    
    # TMM naming convention (similar to Kodi)
    tmm_names = kodi_names.copy()
    
    # MediaElch naming convention (similar to Kodi)
    mediaelch_names = kodi_names.copy()
    
    if format_type == 'kodi':
        return kodi_names.get(artwork_type, f'{artwork_type}.jpg')
    elif format_type == 'tmm':
        return tmm_names.get(artwork_type, f'{artwork_type}.jpg')
    elif format_type == 'mediaelch':
        return mediaelch_names.get(artwork_type, f'{artwork_type}.jpg')
    else:
        return kodi_names.get(artwork_type, f'{artwork_type}.jpg')

@metadata_export_bp.route('/api/metadata/config', methods=['GET'])
def get_config():
    """Get metadata export configuration"""
    config = _load_config()
    return jsonify({
        'ok': True,
        'config': config
    })

@metadata_export_bp.route('/api/metadata/config', methods=['POST'])
def set_config():
    """
    Update metadata export configuration
    Body: {
        "format": "kodi",
        "artwork_types": ["poster", "fanart"],
        "download_artwork": true,
        "create_nfo": true,
        "offline_mode": false
    }
    """
    req_data = request.get_json(silent=True) or {}
    
    config = _load_config()
    config.update(req_data)
    _save_config(config)
    
    return jsonify({
        'ok': True,
        'message': 'Configuration updated',
        'config': config
    })

@metadata_export_bp.route('/api/metadata/export', methods=['POST'])
def export_metadata():
    """
    Export metadata and artwork for a media item
    Body: {
        "media_type": "movie",
        "metadata": {...},
        "artwork_urls": {
            "poster": "http://...",
            "fanart": "http://..."
        },
        "output_path": "/path/to/media/folder"
    }
    """
    req_data = request.get_json(silent=True) or {}
    media_type = req_data.get('media_type', 'movie')
    metadata = req_data.get('metadata', {})
    artwork_urls = req_data.get('artwork_urls', {})
    output_path = req_data.get('output_path', '')
    
    if not output_path:
        return jsonify({'ok': False, 'error': 'output_path required'}), 400
    
    config = _load_config()
    format_type = config.get('format', 'kodi')
    
    results = {
        'nfo_created': False,
        'artwork_downloaded': [],
        'errors': []
    }
    
    # Create NFO
    if config.get('create_nfo', True):
        try:
            if format_type == 'kodi':
                nfo_content = _generate_kodi_nfo(metadata, media_type)
            elif format_type == 'tmm':
                nfo_content = _generate_tmm_nfo(metadata, media_type)
            elif format_type == 'mediaelch':
                nfo_content = _generate_mediaelch_nfo(metadata, media_type)
            else:
                nfo_content = _generate_kodi_nfo(metadata, media_type)
            
            # Determine NFO filename
            if media_type == 'movie':
                nfo_filename = 'movie.nfo'
            elif media_type == 'tvshow':
                nfo_filename = 'tvshow.nfo'
            elif media_type == 'episode':
                nfo_filename = f"{metadata.get('title', 'episode')}.nfo"
            else:
                nfo_filename = 'metadata.nfo'
            
            nfo_path = os.path.join(output_path, nfo_filename)
            os.makedirs(output_path, exist_ok=True)
            
            with open(nfo_path, 'w', encoding='utf-8') as f:
                f.write(nfo_content)
            
            results['nfo_created'] = True
            results['nfo_path'] = nfo_path
        except Exception as e:
            results['errors'].append(f'NFO creation failed: {str(e)}')
    
    # Download artwork
    if config.get('download_artwork', True) and not config.get('offline_mode', False):
        for artwork_type, url in artwork_urls.items():
            if artwork_type in config.get('artwork_types', []):
                filename = _get_artwork_filename(artwork_type, format_type)
                artwork_path = os.path.join(output_path, filename)
                
                if _download_artwork(url, artwork_path):
                    results['artwork_downloaded'].append({
                        'type': artwork_type,
                        'path': artwork_path
                    })
                else:
                    results['errors'].append(f'Failed to download {artwork_type}')
    
    return jsonify({
        'ok': True,
        'results': results
    })

@metadata_export_bp.route('/api/metadata/cache/artwork', methods=['POST'])
def cache_artwork():
    """
    Cache artwork for offline use
    Body: {
        "media_id": "tt1234567",
        "artwork_urls": {
            "poster": "http://...",
            "fanart": "http://..."
        }
    }
    """
    req_data = request.get_json(silent=True) or {}
    media_id = req_data.get('media_id', '')
    artwork_urls = req_data.get('artwork_urls', {})
    
    if not media_id:
        return jsonify({'ok': False, 'error': 'media_id required'}), 400
    
    cache_dir = os.path.join(ARTWORK_CACHE, media_id)
    os.makedirs(cache_dir, exist_ok=True)
    
    cached = []
    errors = []
    
    for artwork_type, url in artwork_urls.items():
        filename = f'{artwork_type}.jpg'
        cache_path = os.path.join(cache_dir, filename)
        
        if _download_artwork(url, cache_path):
            cached.append({
                'type': artwork_type,
                'path': cache_path
            })
        else:
            errors.append(f'Failed to cache {artwork_type}')
    
    # Save metadata about cached artwork
    cache_metadata = {
        'media_id': media_id,
        'cached_at': datetime.utcnow().isoformat() + 'Z',
        'artwork': cached
    }
    
    metadata_path = os.path.join(cache_dir, 'metadata.json')
    with open(metadata_path, 'w', encoding='utf-8') as f:
        json.dump(cache_metadata, f, indent=2)
    
    return jsonify({
        'ok': True,
        'cached_count': len(cached),
        'errors': errors
    })

@metadata_export_bp.route('/api/metadata/cache/list', methods=['GET'])
def list_cached():
    """List all cached metadata"""
    if not os.path.exists(ARTWORK_CACHE):
        return jsonify({
            'ok': True,
            'cached_items': []
        })
    
    cached_items = []
    
    for media_id in os.listdir(ARTWORK_CACHE):
        cache_dir = os.path.join(ARTWORK_CACHE, media_id)
        metadata_path = os.path.join(cache_dir, 'metadata.json')
        
        if os.path.exists(metadata_path):
            try:
                with open(metadata_path, 'r', encoding='utf-8') as f:
                    metadata = json.load(f)
                    cached_items.append(metadata)
            except Exception:
                pass
    
    return jsonify({
        'ok': True,
        'cached_items': cached_items,
        'total_count': len(cached_items)
    })

@metadata_export_bp.route('/api/metadata/offline-index', methods=['GET'])
def get_offline_index():
    """
    Get offline-safe index of all media with cached metadata
    Useful for multi-drive setups where drives may be offline
    """
    index = []
    
    # Scan metadata cache
    if os.path.exists(METADATA_CACHE):
        for filename in os.listdir(METADATA_CACHE):
            if filename.endswith('.json'):
                try:
                    with open(os.path.join(METADATA_CACHE, filename), 'r', encoding='utf-8') as f:
                        metadata = json.load(f)
                        index.append(metadata)
                except Exception:
                    pass
    
    return jsonify({
        'ok': True,
        'index': index,
        'total_items': len(index),
        'last_updated': datetime.utcnow().isoformat() + 'Z'
    })

@metadata_export_bp.route('/api/metadata/batch-export', methods=['POST'])
def batch_export():
    """
    Export metadata and artwork for multiple media items
    Body: {
        "items": [
            {
                "media_type": "movie",
                "metadata": {...},
                "artwork_urls": {...},
                "output_path": "/path/to/media/folder"
            }
        ]
    }
    """
    req_data = request.get_json(silent=True) or {}
    items = req_data.get('items', [])
    
    if not items:
        return jsonify({'ok': False, 'error': 'items array required'}), 400
    
    results = []
    
    for item in items:
        # Call export_metadata for each item
        media_type = item.get('media_type', 'movie')
        metadata = item.get('metadata', {})
        artwork_urls = item.get('artwork_urls', {})
        output_path = item.get('output_path', '')
        
        if not output_path:
            results.append({
                'success': False,
                'error': 'output_path missing'
            })
            continue
        
        config = _load_config()
        format_type = config.get('format', 'kodi')
        
        item_result = {
            'success': False,
            'nfo_created': False,
            'artwork_downloaded': [],
            'errors': []
        }
        
        # Create NFO
        if config.get('create_nfo', True):
            try:
                if format_type == 'kodi':
                    nfo_content = _generate_kodi_nfo(metadata, media_type)
                else:
                    nfo_content = _generate_kodi_nfo(metadata, media_type)
                
                nfo_filename = 'movie.nfo' if media_type == 'movie' else 'tvshow.nfo'
                nfo_path = os.path.join(output_path, nfo_filename)
                os.makedirs(output_path, exist_ok=True)
                
                with open(nfo_path, 'w', encoding='utf-8') as f:
                    f.write(nfo_content)
                
                item_result['nfo_created'] = True
            except Exception as e:
                item_result['errors'].append(f'NFO: {str(e)}')
        
        # Download artwork
        if config.get('download_artwork', True):
            for artwork_type, url in artwork_urls.items():
                filename = _get_artwork_filename(artwork_type, format_type)
                artwork_path = os.path.join(output_path, filename)
                
                if _download_artwork(url, artwork_path):
                    item_result['artwork_downloaded'].append(artwork_type)
        
        item_result['success'] = item_result['nfo_created'] or len(item_result['artwork_downloaded']) > 0
        results.append(item_result)
    
    success_count = sum(1 for r in results if r['success'])
    
    return jsonify({
        'ok': True,
        'total_items': len(items),
        'success_count': success_count,
        'failed_count': len(items) - success_count,
        'results': results
    })
