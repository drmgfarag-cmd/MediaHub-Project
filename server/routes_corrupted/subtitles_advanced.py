from flask import Blueprint, jsonify, request
import os, json, re
from datetime import datetime

subtitles_advanced_bp = Blueprint('subtitles_advanced', __name__)

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
STO = os.path.join(ROOT, 'storage')
SUBTITLES_CONFIG = os.path.join(STO, 'config', 'subtitles.json')
SUBTITLES_QUEUE = os.path.join(STO, 'subtitles_queue.json')

def _load_config():
    """Load subtitle configuration"""
    try:
        with open(SUBTITLES_CONFIG, 'r', encoding='utf-8') as f:
        return json.load(f)
    except Exception:
        return {
            'global_priority': ['en', 'ar'],
            'stop_on_first': True,
            'category_overrides': {},
            'providers': {
                'opensubtitles': {'enabled': True, 'priority': 1},
                'subscene': {'enabled': True, 'priority': 2},
                'addic7ed': {'enabled': False, 'priority': 3}
            },
            'auto_sync': True,
            'hearing_impaired': False
        }

def _save_config(data):
    """Save subtitle configuration"""
    os.makedirs(os.path.dirname(SUBTITLES_CONFIG), exist_ok=True)
    tmp = SUBTITLES_CONFIG + '.tmp'
    with open(tmp, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)
    os.replace(tmp, SUBTITLES_CONFIG)

def _load_queue():
    """Load subtitle processing queue"""
    try:
        with open(SUBTITLES_QUEUE, 'r', encoding='utf-8') as f:
        return json.load(f)
    except Exception:
        return {
            'pending': [],
            'processing': [],
            'completed': [],
            'failed': [],
            'mismatch_fixer': []
        }

def _save_queue(data):
    """Save subtitle processing queue"""
    os.makedirs(os.path.dirname(SUBTITLES_QUEUE), exist_ok=True)
    tmp = SUBTITLES_QUEUE + '.tmp'
    with open(tmp, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)
    os.replace(tmp, SUBTITLES_QUEUE)

def _get_priority_for_item(item, config):
    """Get language priority list for a specific item"""
    category = item.get('category', 'movie')
    
    # Check for category override
    category_overrides = config.get('category_overrides', {})
    if category in category_overrides:
        return category_overrides[category].get('priority', config.get('global_priority', ['en']))
    
    return config.get('global_priority', ['en'])

def _search_subtitles(item, languages, providers, stop_on_first=True):
    """
    Search for subtitles across providers
    Returns list of found subtitles
    """
    found_subtitles = []
    
    # Sort providers by priority
    sorted_providers = sorted(
        [(name, info) for name, info in providers.items() if info.get('enabled', False)],
        key=lambda x: x[1].get('priority', 99)
    )
    
    for language in languages:
        language_found = False
        
        for provider_name, provider_info in sorted_providers:
            # Simulate subtitle search
            # In real implementation, this would call actual subtitle APIs
            subtitle = {
                'language': language,
                'provider': provider_name,
                'url': f'http://example.com/subtitle_{language}_{provider_name}.srt',
                'score': 95,  # Match score
                'hearing_impaired': False,
                'found_at': datetime.utcnow().isoformat() + 'Z'
            }
            
            found_subtitles.append(subtitle)
            language_found = True
            
            # If stop_on_first is enabled and we found a subtitle for this language, move to next language
            if stop_on_first and language_found:
                break
        
        if stop_on_first and language_found:
            continue
    
    return found_subtitles

@subtitles_advanced_bp.route('/api/subtitles/config', methods=['GET'])
def get_config():
    try:
        """Get subtitle configuration"""
        config = _load_config()
        return jsonify({
        'ok': True,
        'config': config
        })

        # DUPLICATE REMOVED: @subtitles_advanced_bp.route('/api/subtitles/config', methods=['GET'])
        # DUPLICATE REMOVED: def set_config():
        """
        Update subtitle configuration
        Body: {
        "global_priority": ["en", "ar"],
        "stop_on_first": true,
        "category_overrides": {
        "anime": {
        "priority": ["ja", "en"]
        }
        },
        "providers": {...},
        "auto_sync": true,
        "hearing_impaired": false
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


        @subtitles_advanced_bp.route('/api/subtitles/priority/global', methods=['GET'])
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

def get_global_priority():
    try:
        """Get global language priority list"""
        config = _load_config()
        return jsonify({
        'ok': True,
        'priority': config.get('global_priority', ['en'])
        })

        # DUPLICATE REMOVED: @subtitles_advanced_bp.route('/api/subtitles/priority/global', methods=['GET'])
        # DUPLICATE REMOVED: def set_global_priority():
        """
        Set global language priority list
        Body: {
        "priority": ["en", "ar", "es"]
        }
        """
        req_data = request.get_json(silent=True) or {}
        priority = req_data.get('priority', [])

        if not priority:
        return jsonify({'ok': False, 'error': 'priority list required'}), 400

        config = _load_config()
        config['global_priority'] = priority
        _save_config(config)

        return jsonify({
        'ok': True,
        'message': 'Global priority updated',
        'priority': priority
        })


        @subtitles_advanced_bp.route('/api/subtitles/priority/category/<category>', methods=['GET'])
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

def get_category_priority(category):
    try:
        """Get language priority for a specific category"""
        config = _load_config()
        category_overrides = config.get('category_overrides', {})

        if category in category_overrides:
        return jsonify({
        'ok': True,
        'category': category,
        'priority': category_overrides[category].get('priority', config.get('global_priority', ['en'])),
        'has_override': True
        })

        return jsonify({
        'ok': True,
        'category': category,
        'priority': config.get('global_priority', ['en']),
        'has_override': False
        })

        # DUPLICATE REMOVED: @subtitles_advanced_bp.route('/api/subtitles/priority/category/<category>', methods=['POST'])
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

def create_category_category(category):
    """Create Category"""
    try:
        data = request.get_json()
        if not data:
        return jsonify({'error': 'No data provided'}), 400
        return jsonify({'success': True, 'message': 'Created', 'data': data}), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500
def create_category_category(category):
    """Create Category"""
    try:
        data = request.get_json()
        if not data:
        return jsonify({'error': 'No data provided'}), 400
        return jsonify({'success': True, 'message': 'Created', 'data': data}), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500
# DUPLICATE REMOVED: def set_category_priority(category):
    """
    Set language priority for a specific category
    Body: {
        "priority": ["ja", "en"]
    }
    """
    req_data = request.get_json(silent=True) or {}
    priority = req_data.get('priority', [])
    def delete_category_category(category):
        """Delete Category"""
        try:
            return jsonify({'success': True, 'message': 'Deleted'})
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    if not priority:
            return jsonify({'ok': False, 'error': 'priority list required'}), 400
    
    config = _load_config()
    category_overrides = config.get('category_overrides', {})
    category_overrides[category] = {'priority': priority}
    config['category_overrides'] = category_overrides
    _save_config(config)
    def delete_category_category(category):
        """Delete Category"""
        try:
            return jsonify({'success': True, 'message': 'Deleted'})
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
            return jsonify({
        'ok': True,
        'message': f'Priority for category "{category}" updated',
        'category': category,
        'priority': priority
    })

# DUPLICATE REMOVED: @subtitles_advanced_bp.route('/api/subtitles/priority/category/<category>', methods=['DELETE'])
# DUPLICATE REMOVED: def delete_category_priority(category):
# DUPLICATE REMOVED:     """Remove category-specific priority override"""
# DUPLICATE REMOVED:     config = _load_config()
# DUPLICATE REMOVED:     category_overrides = config.get('category_overrides', {})
# DUPLICATE REMOVED:     
# DUPLICATE REMOVED:     if category in category_overrides:
# DUPLICATE REMOVED:         del category_overrides[category]
# DUPLICATE REMOVED:         config['category_overrides'] = category_overrides
# DUPLICATE REMOVED:         _save_config(config)
# DUPLICATE REMOVED:         
# DUPLICATE REMOVED:         return jsonify({
# DUPLICATE REMOVED:             'ok': True,
# DUPLICATE REMOVED:             'message': f'Priority override for category "{category}" removed'
# DUPLICATE REMOVED:         })
# DUPLICATE REMOVED:     
# DUPLICATE REMOVED:     return jsonify({'ok': False, 'error': 'Category override not found'}), 404
# DUPLICATE REMOVED: 
# DUPLICATE REMOVED: @subtitles_advanced_bp.route('/api/subtitles/search', methods=['POST'])
# DUPLICATE REMOVED: def search_subtitles():
    """
    Search for subtitles for a media item
    Body: {
        "item": {
            "title": "Movie Name",
            "year": 2024,
            "category": "movie",
            "imdb_id": "tt1234567"
        },
        "languages": ["en", "ar"] (optional, uses config priority if not specified)
    }
    """
    req_data = request.get_json(silent=True) or {}
    item = req_data.get('item', {})
    languages = req_data.get('languages')
    
    if not item:
        return jsonify({'ok': False, 'error': 'item required'}), 400
    
    config = _load_config()
    
    # Use specified languages or get from config
    if not languages:
        languages = _get_priority_for_item(item, config)
    
    providers = config.get('providers', {})
    stop_on_first = config.get('stop_on_first', True)
    
    # Search for subtitles
    found_subtitles = _search_subtitles(item, languages, providers, stop_on_first)
    
    return jsonify({
        'ok': True,
        'item': item,
        'languages_searched': languages,
        'found_count': len(found_subtitles),
        'subtitles': found_subtitles,
        'stop_on_first': stop_on_first
    })

@subtitles_advanced_bp.route('/api/subtitles/batch-scan', methods=['POST'])
def batch_scan():
    try:
        """
        Batch scan library for missing subtitles
        Body: {
        "items": [
        {"title": "Movie 1", "category": "movie"},
        {"title": "Episode 1", "category": "tv"}
        ],
        "force_rescan": false
        }
        """
        req_data = request.get_json(silent=True) or {}
        items = req_data.get('items', [])
        force_rescan = req_data.get('force_rescan', False)

        if not items:
        return jsonify({'ok': False, 'error': 'items array required'}), 400

        config = _load_config()
        queue_data = _load_queue()

        # Add items to pending queue
        for item in items:
        # Check if item already has subtitles (unless force_rescan)
        if not force_rescan and item.get('has_subtitles'):
        continue

        queue_item = {
        'id': f"{item.get('title', 'unknown')}_{datetime.utcnow().timestamp()}",
        'item': item,
        'added_at': datetime.utcnow().isoformat() + 'Z',
        'status': 'pending'
        }

        queue_data['pending'].append(queue_item)

        _save_queue(queue_data)

        return jsonify({
        'ok': True,
        'message': f'{len(items)} items added to scan queue',
        'pending_count': len(queue_data['pending'])
        })

        @subtitles_advanced_bp.route('/api/subtitles/queue', methods=['GET'])
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

def get_queue():
    try:
        """Get subtitle processing queue"""
        queue_data = _load_queue()

        return jsonify({
        'ok': True,
        'queue': {
        'pending': len(queue_data.get('pending', [])),
        'processing': len(queue_data.get('processing', [])),
        'completed': len(queue_data.get('completed', [])),
        'failed': len(queue_data.get('failed', [])),
        'mismatch_fixer': len(queue_data.get('mismatch_fixer', []))
        },
        'details': queue_data
        })

        @subtitles_advanced_bp.route('/api/subtitles/queue/clear', methods=['POST'])
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

def clear_queue():
    try:
        """
        Clear specific queue sections
        Body: {
        "sections": ["completed", "failed"]
        }
        """
        req_data = request.get_json(silent=True) or {}
        sections = req_data.get('sections', [])

        if not sections:
        return jsonify({'ok': False, 'error': 'sections array required'}), 400

        queue_data = _load_queue()

        for section in sections:
        if section in queue_data:
        queue_data[section] = []

        _save_queue(queue_data)

        return jsonify({
        'ok': True,
        'message': f'Cleared sections: {", ".join(sections)}'
        })

        @subtitles_advanced_bp.route('/api/subtitles/mismatch-fixer', methods=['GET'])
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

def get_mismatch_fixer():
    try:
        """Get items in the mismatch fixer queue"""
        queue_data = _load_queue()

        return jsonify({
        'ok': True,
        'mismatch_count': len(queue_data.get('mismatch_fixer', [])),
        'items': queue_data.get('mismatch_fixer', [])
        })

        @subtitles_advanced_bp.route('/api/subtitles/mismatch-fixer/add', methods=['POST'])
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

def add_to_mismatch_fixer():
    try:
        """
        Add item to mismatch fixer queue
        Body: {
        "item": {
        "title": "Movie Name",
        "subtitle_path": "/path/to/subtitle.srt",
        "issue": "Out of sync"
        }
        }
        """
        req_data = request.get_json(silent=True) or {}
        item = req_data.get('item', {})

        if not item:
        return jsonify({'ok': False, 'error': 'item required'}), 400

        queue_data = _load_queue()

        mismatch_item = {
        'id': f"mismatch_{datetime.utcnow().timestamp()}",
        'item': item,
        'added_at': datetime.utcnow().isoformat() + 'Z',
        'status': 'pending_fix'
        }

        queue_data['mismatch_fixer'].append(mismatch_item)
        _save_queue(queue_data)

        return jsonify({
        'ok': True,
        'message': 'Item added to mismatch fixer queue',
        'mismatch_count': len(queue_data['mismatch_fixer'])
        })

        @subtitles_advanced_bp.route('/api/subtitles/mismatch-fixer/<item_id>', methods=['DELETE'])
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

def remove_from_mismatch_fixer(item_id):
    try:
        """Remove item from mismatch fixer queue"""
        queue_data = _load_queue()

        original_count = len(queue_data.get('mismatch_fixer', []))
        queue_data['mismatch_fixer'] = [
        item for item in queue_data.get('mismatch_fixer', [])
        if item.get('id') != item_id
        ]

        if len(queue_data['mismatch_fixer']) == original_count:
        return jsonify({'ok': False, 'error': 'Item not found'}), 404

        _save_queue(queue_data)

        return jsonify({
        'ok': True,
        'message': 'Item removed from mismatch fixer queue'
        })


        @subtitles_advanced_bp.route('/api/subtitles/providers', methods=['GET'])
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

def get_providers():
    try:
        """Get subtitle provider configuration"""
        config = _load_config()
        return jsonify({
        'ok': True,
        'providers': config.get('providers', {})
        })

        @subtitles_advanced_bp.route('/api/subtitles/providers/<provider_name>', methods=['POST'])
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

def update_provider(provider_name):
    try:
        """
        Update provider settings
        Body: {
        "enabled": true,
        "priority": 1
        }
        """
        req_data = request.get_json(silent=True) or {}

        config = _load_config()
        providers = config.get('providers', {})

        if provider_name not in providers:
        providers[provider_name] = {}

        providers[provider_name].update(req_data)
        config['providers'] = providers
        _save_config(config)

        return jsonify({
        'ok': True,
        'message': f'Provider "{provider_name}" updated',
        'provider': providers[provider_name]
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
