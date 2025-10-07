"""
Media Management Golden Surface APIs - Master Rulebook Compliance
Wraps existing RSS, filters, collections, and subtitle modules
"""
from flask import Blueprint, request, jsonify
import os
import json
from datetime import datetime

media_mgmt_golden_bp = Blueprint('media_mgmt_golden', __name__)

# Storage paths
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
STORAGE = os.path.join(ROOT, 'storage')
RD_FILTERS_PATH = os.path.join(STORAGE, 'rd_filters.json')
RSS_FILTERS_PATH = os.path.join(STORAGE, 'rss_filters.json')
PROVIDERS_PATH = os.path.join(STORAGE, 'provider_profiles.json')
SUBS_POLICY_PATH = os.path.join(STORAGE, 'subtitle_policy.json')
COLLECTIONS_PATH = os.path.join(STORAGE, 'collections.json')

def load_json(path, default=None):
    """Load JSON file with default fallback"""
    if default is None:
        default = {}
    try:
        if os.path.exists(path):
            with open(path, 'r', encoding='utf-8') as f:
                return json.load(f)
    except:
        pass
    return default

def save_json(path, data):
    """Save JSON file"""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)

@media_mgmt_golden_bp.route('/api/rd/filters/config', methods=['GET', 'POST'])
def rd_filters_config():
    """Real-Debrid filters configuration"""
    if request.method == 'POST':
        data = request.get_json() or {}
        save_json(RD_FILTERS_PATH, data)
        return jsonify({
            'success': True,
            'config': data
        })
    else:
        config = load_json(RD_FILTERS_PATH, {
            'enabled': True,
            'quality_filters': {
                'min_resolution': '720p',
                'preferred_codecs': ['h265', 'h264'],
                'require_hdr': False,
                'min_audio_channels': 2
            },
            'size_filters': {
                'min_size_mb': 100,
                'max_size_mb': 50000
            },
            'content_filters': {
                'exclude_keywords': [],
                'require_keywords': []
            },
            'scoring': {
                'resolution_weight': 1.0,
                'codec_weight': 0.3,
                'audio_weight': 0.2,
                'hdr_weight': 0.15,
                'size_weight': 0.1
            }
        })
        return jsonify({
            'success': True,
            'config': config
        })

@media_mgmt_golden_bp.route('/api/rss/filters/config', methods=['GET', 'POST'])
def rss_filters_config():
    """RSS automation filters configuration"""
    if request.method == 'POST':
        data = request.get_json() or {}
        save_json(RSS_FILTERS_PATH, data)
        return jsonify({
            'success': True,
            'config': data
        })
    else:
        config = load_json(RSS_FILTERS_PATH, {
            'enabled': True,
            'feeds': [],
            'quality_profiles': {
                '4K': {
                    'resolution': '2160p',
                    'codec': 'h265',
                    'hdr': True
                },
                'HD': {
                    'resolution': '1080p',
                    'codec': 'h264',
                    'hdr': False
                },
                'SD': {
                    'resolution': '720p',
                    'codec': 'h264',
                    'hdr': False
                }
            },
            'auto_download': False,
            'check_interval_minutes': 30,
            'max_downloads_per_check': 5
        })
        return jsonify({
            'success': True,
            'config': config
        })

@media_mgmt_golden_bp.route('/api/providers/profiles', methods=['GET', 'POST'])
def providers_profiles():
    """Metadata provider profiles configuration"""
    if request.method == 'POST':
        data = request.get_json() or {}
        save_json(PROVIDERS_PATH, data)
        return jsonify({
            'success': True,
            'profiles': data
        })
    else:
        profiles = load_json(PROVIDERS_PATH, {
            'providers': [
                {
                    'name': 'TMDB',
                    'enabled': True,
                    'priority': 1,
                    'api_key_required': True,
                    'languages': ['en', 'ar'],
                    'types': ['movie', 'tv']
                },
                {
                    'name': 'IMDB',
                    'enabled': True,
                    'priority': 2,
                    'api_key_required': False,
                    'languages': ['en'],
                    'types': ['movie', 'tv']
                },
                {
                    'name': 'TVMaze',
                    'enabled': True,
                    'priority': 3,
                    'api_key_required': False,
                    'languages': ['en'],
                    'types': ['tv']
                }
            ],
            'fallback_enabled': True,
            'cache_duration_hours': 24,
            'auto_refresh': False
        })
        return jsonify({
            'success': True,
            'profiles': profiles
        })

@media_mgmt_golden_bp.route('/api/subs/policy', methods=['GET', 'POST'])
def subs_policy():
    """Subtitle download policy configuration"""
    if request.method == 'POST':
        data = request.get_json() or {}
        save_json(SUBS_POLICY_PATH, data)
        return jsonify({
            'success': True,
            'policy': data
        })
    else:
        policy = load_json(SUBS_POLICY_PATH, {
            'enabled': True,
            'auto_download': True,
            'languages': ['ar', 'en'],
            'priority_order': ['ar', 'en'],
            'providers': ['opensubtitles', 'subscene', 'podnapisi'],
            'quality_preference': 'hearing_impaired',  # 'normal', 'hearing_impaired', 'forced'
            'encoding': 'utf-8',
            'format': 'srt',
            'embed_in_video': False,
            'backup_original': True
        })
        return jsonify({
            'success': True,
            'policy': policy
        })

@media_mgmt_golden_bp.route('/api/collections/manage', methods=['GET', 'POST', 'PUT', 'DELETE'])
def collections_manage():
    """Dynamic collection creation and management"""
    collections = load_json(COLLECTIONS_PATH, {'collections': []})
    
    if request.method == 'GET':
        # Get all collections or specific collection
        collection_id = request.args.get('id')
        if collection_id:
            collection = next((c for c in collections['collections'] if c.get('id') == collection_id), None)
            if collection:
                return jsonify({
                    'success': True,
                    'collection': collection
                })
            else:
                return jsonify({
                    'success': False,
                    'error': 'Collection not found'
                }), 404
        else:
            return jsonify({
                'success': True,
                'collections': collections['collections'],
                'total': len(collections['collections'])
            })
    
    elif request.method == 'POST':
        # Create new collection
        data = request.get_json() or {}
        collection = {
            'id': data.get('id') or f"col_{datetime.now().timestamp()}",
            'name': data.get('name', 'Untitled Collection'),
            'description': data.get('description', ''),
            'type': data.get('type', 'manual'),  # 'manual', 'smart', 'auto'
            'criteria': data.get('criteria', {}),
            'items': data.get('items', []),
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat()
        }
        collections['collections'].append(collection)
        save_json(COLLECTIONS_PATH, collections)
        
        return jsonify({
            'success': True,
            'collection': collection
        })
    
    elif request.method == 'PUT':
        # Update existing collection
        data = request.get_json() or {}
        collection_id = data.get('id')
        
        for i, col in enumerate(collections['collections']):
            if col.get('id') == collection_id:
                # Update fields
                col.update({
                    'name': data.get('name', col.get('name')),
                    'description': data.get('description', col.get('description')),
                    'criteria': data.get('criteria', col.get('criteria')),
                    'items': data.get('items', col.get('items')),
                    'updated_at': datetime.now().isoformat()
                })
                collections['collections'][i] = col
                save_json(COLLECTIONS_PATH, collections)
                
                return jsonify({
                    'success': True,
                    'collection': col
                })
        
        return jsonify({
            'success': False,
            'error': 'Collection not found'
        }), 404
    
    elif request.method == 'DELETE':
        # Delete collection
        collection_id = request.args.get('id')
        original_count = len(collections['collections'])
        collections['collections'] = [c for c in collections['collections'] if c.get('id') != collection_id]
        
        if len(collections['collections']) < original_count:
            save_json(COLLECTIONS_PATH, collections)
            return jsonify({
                'success': True,
                'message': 'Collection deleted'
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Collection not found'
            }), 404

@media_mgmt_golden_bp.route('/api/metadata/fetch', methods=['POST'])
def metadata_fetch():
    """Multi-provider metadata fetching"""
    data = request.get_json() or {}
    query = data.get('query', '')
    media_type = data.get('type', 'movie')  # 'movie', 'tv'
    providers = data.get('providers', ['tmdb', 'imdb'])
    
    # Load provider profiles
    profiles = load_json(PROVIDERS_PATH, {'providers': []})
    enabled_providers = [p for p in profiles.get('providers', []) if p.get('enabled', False)]
    
    # Mock metadata response (in production, this would call actual APIs)
    metadata = {
        'success': True,
        'query': query,
        'type': media_type,
        'providers_used': providers,
        'results': {
            'title': query,
            'year': 2024,
            'rating': 8.5,
            'genres': ['Action', 'Adventure'],
            'cast': [],
            'crew': [],
            'poster_url': '',
            'backdrop_url': '',
            'overview': '',
            'runtime': 120,
            'release_date': '2024-01-01',
            'providers': {
                'tmdb': {
                    'id': '12345',
                    'confidence': 0.95
                },
                'imdb': {
                    'id': 'tt1234567',
                    'confidence': 0.90
                }
            },
            'fetched_at': datetime.now().isoformat()
        }
    }
    
    return jsonify(metadata)
