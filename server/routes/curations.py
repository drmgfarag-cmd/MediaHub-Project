from flask import Blueprint, jsonify, request
import os, json, re
from datetime import datetime, timedelta

curations_bp = Blueprint('curations', __name__)

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
STO = os.path.join(ROOT, 'storage')
CURATIONS_FILE = os.path.join(STO, 'curations.json')

def _load_curations():
    """Load curations data"""
    try:
        with open(CURATIONS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return {'curations': []}

def _save_curations(data):
    """Save curations data"""
    os.makedirs(os.path.dirname(CURATIONS_FILE), exist_ok=True)
    tmp = CURATIONS_FILE + '.tmp'
    with open(tmp, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)
    os.replace(tmp, CURATIONS_FILE)

def _should_refresh(curation):
    """Check if a curation should be refreshed"""
    if not curation.get('auto_refresh'):
        return False
    
    last_refreshed = curation.get('last_refreshed')
    if not last_refreshed:
        return True
    
    try:
        last_refreshed_dt = datetime.fromisoformat(last_refreshed.replace('Z', '+00:00'))
        refresh_interval_hours = curation.get('refresh_interval_hours', 24)
        next_refresh = last_refreshed_dt.replace(tzinfo=None) + timedelta(hours=refresh_interval_hours)
        
        return datetime.utcnow() >= next_refresh
    except Exception:
        return True

@curations_bp.route('/api/curations', methods=['GET'])
def get_curations():
    """Get all curations"""
    data = _load_curations()
    curations = data.get('curations', [])
    
    return jsonify({
        'ok': True,
        'curations': curations,
        'total': len(curations)
    })

@curations_bp.route('/api/curations/<curation_id>', methods=['GET'])
def get_curation(curation_id):
    """Get a specific curation"""
    data = _load_curations()
    curations = data.get('curations', [])
    
    curation = next((c for c in curations if c.get('id') == curation_id), None)
    
    if not curation:
        return jsonify({'ok': False, 'error': 'Curation not found'}), 404
    
    # Check if refresh is needed
    needs_refresh = _should_refresh(curation)
    
    return jsonify({
        'ok': True,
        'curation': curation,
        'needs_refresh': needs_refresh
    })

@curations_bp.route('/api/curations', methods=['POST'])
def create_curation():
    """
    Create a new curation
    Body: {
        "name": "Marvel Cinematic Universe",
        "description": "All MCU movies in chronological order",
        "type": "franchise",
        "items": [
            {
                "id": "tmdb_1771",
                "title": "Captain America: The First Avenger",
                "order": 1
            }
        ],
        "auto_refresh": true,
        "refresh_interval_hours": 24,
        "source_type": "manual"
    }
    """
    req_data = request.get_json(silent=True) or {}
    
    if not req_data.get('name'):
        return jsonify({'ok': False, 'error': 'name required'}), 400
    
    data = _load_curations()
    curations = data.get('curations', [])
    
    curation = {
        'id': f"curation_{datetime.utcnow().timestamp()}",
        'name': req_data.get('name'),
        'description': req_data.get('description', ''),
        'type': req_data.get('type', 'custom'),  # franchise, awards, universe, custom
        'items': req_data.get('items', []),
        'auto_refresh': req_data.get('auto_refresh', False),
        'refresh_interval_hours': req_data.get('refresh_interval_hours', 24),
        'source_type': req_data.get('source_type', 'manual'),  # manual, tmdb_list, imdb_list
        'source_id': req_data.get('source_id', ''),
        'created_at': datetime.utcnow().isoformat() + 'Z',
        'last_refreshed': datetime.utcnow().isoformat() + 'Z',
        'item_count': len(req_data.get('items', []))
    }
    
    curations.append(curation)
    data['curations'] = curations
    _save_curations(data)
    
    return jsonify({
        'ok': True,
        'message': 'Curation created',
        'curation': curation
    })

@curations_bp.route('/api/curations/<curation_id>', methods=['PUT'])
def update_curation(curation_id):
    """
    Update a curation
    Body: {
        "name": "Updated Name",
        "items": [...]
    }
    """
    req_data = request.get_json(silent=True) or {}
    
    data = _load_curations()
    curations = data.get('curations', [])
    
    curation = next((c for c in curations if c.get('id') == curation_id), None)
    
    if not curation:
        return jsonify({'ok': False, 'error': 'Curation not found'}), 404
    
    # Update fields
    if 'name' in req_data:
        curation['name'] = req_data['name']
    if 'description' in req_data:
        curation['description'] = req_data['description']
    if 'type' in req_data:
        curation['type'] = req_data['type']
    if 'items' in req_data:
        curation['items'] = req_data['items']
        curation['item_count'] = len(req_data['items'])
    if 'auto_refresh' in req_data:
        curation['auto_refresh'] = req_data['auto_refresh']
    if 'refresh_interval_hours' in req_data:
        curation['refresh_interval_hours'] = req_data['refresh_interval_hours']
    
    curation['updated_at'] = datetime.utcnow().isoformat() + 'Z'
    
    _save_curations(data)
    
    return jsonify({
        'ok': True,
        'message': 'Curation updated',
        'curation': curation
    })

@curations_bp.route('/api/curations/<curation_id>', methods=['DELETE'])
def delete_curation(curation_id):
    """Delete a curation"""
    data = _load_curations()
    curations = data.get('curations', [])
    
    original_count = len(curations)
    curations = [c for c in curations if c.get('id') != curation_id]
    
    if len(curations) == original_count:
        return jsonify({'ok': False, 'error': 'Curation not found'}), 404
    
    data['curations'] = curations
    _save_curations(data)
    
    return jsonify({
        'ok': True,
        'message': 'Curation deleted'
    })

@curations_bp.route('/api/curations/<curation_id>/items', methods=['POST'])
def add_item_to_curation(curation_id):
    """
    Add an item to a curation
    Body: {
        "id": "tmdb_1771",
        "title": "Captain America",
        "order": 5
    }
    """
    req_data = request.get_json(silent=True) or {}
    
    if not req_data.get('id'):
        return jsonify({'ok': False, 'error': 'item id required'}), 400
    
    data = _load_curations()
    curations = data.get('curations', [])
    
    curation = next((c for c in curations if c.get('id') == curation_id), None)
    
    if not curation:
        return jsonify({'ok': False, 'error': 'Curation not found'}), 404
    
    items = curation.get('items', [])
    
    # Check if item already exists
    existing_item = next((item for item in items if item.get('id') == req_data['id']), None)
    if existing_item:
        return jsonify({'ok': False, 'error': 'Item already in curation'}), 400
    
    item = {
        'id': req_data['id'],
        'title': req_data.get('title', 'Unknown'),
        'order': req_data.get('order', len(items) + 1),
        'added_at': datetime.utcnow().isoformat() + 'Z'
    }
    
    items.append(item)
    curation['items'] = items
    curation['item_count'] = len(items)
    curation['updated_at'] = datetime.utcnow().isoformat() + 'Z'
    
    _save_curations(data)
    
    return jsonify({
        'ok': True,
        'message': 'Item added to curation',
        'item': item
    })

@curations_bp.route('/api/curations/<curation_id>/items/<item_id>', methods=['DELETE'])
def remove_item_from_curation(curation_id, item_id):
    """Remove an item from a curation"""
    data = _load_curations()
    curations = data.get('curations', [])
    
    curation = next((c for c in curations if c.get('id') == curation_id), None)
    
    if not curation:
        return jsonify({'ok': False, 'error': 'Curation not found'}), 404
    
    items = curation.get('items', [])
    original_count = len(items)
    items = [item for item in items if item.get('id') != item_id]
    
    if len(items) == original_count:
        return jsonify({'ok': False, 'error': 'Item not found'}), 404
    
    curation['items'] = items
    curation['item_count'] = len(items)
    curation['updated_at'] = datetime.utcnow().isoformat() + 'Z'
    
    _save_curations(data)
    
    return jsonify({
        'ok': True,
        'message': 'Item removed from curation'
    })

@curations_bp.route('/api/curations/<curation_id>/refresh', methods=['POST'])
def refresh_curation(curation_id):
    """
    Manually refresh a curation
    If source_type is tmdb_list or imdb_list, fetch latest items
    """
    data = _load_curations()
    curations = data.get('curations', [])
    
    curation = next((c for c in curations if c.get('id') == curation_id), None)
    
    if not curation:
        return jsonify({'ok': False, 'error': 'Curation not found'}), 404
    
    source_type = curation.get('source_type', 'manual')
    
    if source_type == 'manual':
        return jsonify({'ok': False, 'error': 'Manual curations cannot be auto-refreshed'}), 400
    
    # In a real implementation, this would fetch from TMDB/IMDb
    # For now, just update the timestamp
    curation['last_refreshed'] = datetime.utcnow().isoformat() + 'Z'
    
    _save_curations(data)
    
    return jsonify({
        'ok': True,
        'message': 'Curation refreshed',
        'last_refreshed': curation['last_refreshed']
    })

@curations_bp.route('/api/curations/check-refresh', methods=['POST'])
def check_refresh_all():
    """Check all curations and refresh those that need it"""
    data = _load_curations()
    curations = data.get('curations', [])
    
    refreshed = []
    
    for curation in curations:
        if _should_refresh(curation) and curation.get('source_type') != 'manual':
            # Refresh the curation
            curation['last_refreshed'] = datetime.utcnow().isoformat() + 'Z'
            refreshed.append(curation['id'])
    
    _save_curations(data)
    
    return jsonify({
        'ok': True,
        'message': f'Refreshed {len(refreshed)} curations',
        'refreshed_ids': refreshed
    })

@curations_bp.route('/api/curations/templates', methods=['GET'])
def get_templates():
    """Get pre-defined curation templates"""
    templates = [
        {
            'id': 'mcu',
            'name': 'Marvel Cinematic Universe',
            'type': 'franchise',
            'description': 'All MCU movies in chronological order'
        },
        {
            'id': 'dceu',
            'name': 'DC Extended Universe',
            'type': 'franchise',
            'description': 'All DCEU movies'
        },
        {
            'id': 'star_wars',
            'name': 'Star Wars Saga',
            'type': 'franchise',
            'description': 'Star Wars movies in release order'
        },
        {
            'id': 'oscar_best_picture',
            'name': 'Oscar Best Picture Winners',
            'type': 'awards',
            'description': 'Academy Award Best Picture winners'
        },
        {
            'id': 'studio_ghibli',
            'name': 'Studio Ghibli Collection',
            'type': 'universe',
            'description': 'All Studio Ghibli films'
        }
    ]
    
    return jsonify({
        'ok': True,
        'templates': templates
    })

@curations_bp.route('/api/curations/from-template/<template_id>', methods=['POST'])
def create_from_template(template_id):
    """Create a curation from a template"""
    # In a real implementation, this would fetch the actual items
    # For now, create an empty curation with the template metadata
    
    templates = {
        'mcu': {'name': 'Marvel Cinematic Universe', 'type': 'franchise'},
        'dceu': {'name': 'DC Extended Universe', 'type': 'franchise'},
        'star_wars': {'name': 'Star Wars Saga', 'type': 'franchise'},
        'oscar_best_picture': {'name': 'Oscar Best Picture Winners', 'type': 'awards'},
        'studio_ghibli': {'name': 'Studio Ghibli Collection', 'type': 'universe'}
    }
    
    if template_id not in templates:
        return jsonify({'ok': False, 'error': 'Template not found'}), 404
    
    template = templates[template_id]
    
    data = _load_curations()
    curations = data.get('curations', [])
    
    curation = {
        'id': f"curation_{datetime.utcnow().timestamp()}",
        'name': template['name'],
        'type': template['type'],
        'items': [],
        'auto_refresh': False,
        'source_type': 'manual',
        'created_at': datetime.utcnow().isoformat() + 'Z',
        'item_count': 0
    }
    
    curations.append(curation)
    data['curations'] = curations
    _save_curations(data)
    
    return jsonify({
        'ok': True,
        'message': 'Curation created from template',
        'curation': curation
    })
