from flask import Blueprint, jsonify, request
import os, json, re
import requests
from datetime import datetime
from urllib.parse import urlparse

link_grabber_bp = Blueprint('link_grabber', __name__)

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
STO = os.path.join(ROOT, 'storage')
LINK_GRABBER_QUEUE = os.path.join(STO, 'link_grabber_queue.json')

def _load_queue():
    """Load link grabber queue"""
    try:
        with open(LINK_GRABBER_QUEUE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return {
            'items': [],
            'filters': {
                'allowed_hosts': [],
                'blocked_hosts': [],
                'allowed_extensions': [],
                'blocked_extensions': [],
                'exclude_samples': True,
                'exclude_trailers': True,
                'min_size_mb': 0,
                'max_size_mb': 0
            }
        }

def _save_queue(data):
    """Save link grabber queue"""
    os.makedirs(os.path.dirname(LINK_GRABBER_QUEUE), exist_ok=True)
    tmp = LINK_GRABBER_QUEUE + '.tmp'
    with open(tmp, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)
    os.replace(tmp, LINK_GRABBER_QUEUE)

def _probe_availability(url):
    """
    Probe URL availability without downloading
    Returns dict with: available, size, content_type, error
    """
    try:
        response = requests.head(url, timeout=10, allow_redirects=True)
        
        if response.status_code == 200:
            size = response.headers.get('Content-Length', 0)
            content_type = response.headers.get('Content-Type', 'unknown')
            
            return {
                'available': True,
                'size_bytes': int(size) if size else 0,
                'size_mb': round(int(size) / (1024 * 1024), 2) if size else 0,
                'content_type': content_type,
                'error': None
            }
        else:
            return {
                'available': False,
                'size_bytes': 0,
                'size_mb': 0,
                'content_type': 'unknown',
                'error': f'HTTP {response.status_code}'
            }
    except Exception as e:
        return {
            'available': False,
            'size_bytes': 0,
            'size_mb': 0,
            'content_type': 'unknown',
            'error': str(e)
        }

def _guess_media_type(filename, content_type=''):
    """
    Guess media type from filename and content type
    Returns: video, audio, image, archive, document, other
    """
    filename_lower = filename.lower()
    content_type_lower = content_type.lower()
    
    video_exts = ['.mp4', '.mkv', '.avi', '.mov', '.wmv', '.flv', '.webm', '.m4v', '.mpg', '.mpeg']
    audio_exts = ['.mp3', '.flac', '.aac', '.wav', '.ogg', '.m4a', '.wma']
    image_exts = ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp', '.svg']
    archive_exts = ['.zip', '.rar', '.7z', '.tar', '.gz', '.bz2']
    document_exts = ['.pdf', '.doc', '.docx', '.txt', '.epub', '.mobi']
    
    for ext in video_exts:
        if filename_lower.endswith(ext) or ext[1:] in content_type_lower:
            return 'video'
    
    for ext in audio_exts:
        if filename_lower.endswith(ext) or ext[1:] in content_type_lower:
            return 'audio'
    
    for ext in image_exts:
        if filename_lower.endswith(ext) or ext[1:] in content_type_lower:
            return 'image'
    
    for ext in archive_exts:
        if filename_lower.endswith(ext) or ext[1:] in content_type_lower:
            return 'archive'
    
    for ext in document_exts:
        if filename_lower.endswith(ext) or ext[1:] in content_type_lower:
            return 'document'
    
    return 'other'

def _extract_filename_from_url(url):
    """Extract filename from URL"""
    parsed = urlparse(url)
    path = parsed.path
    
    if path:
        filename = os.path.basename(path)
        if filename:
            return filename
    
    return 'unknown'

def _apply_filters(item, filters):
    """
    Apply filters to an item
    Returns dict with: passed, reasons
    """
    reasons = []
    passed = True
    
    # Check host filters
    parsed_url = urlparse(item.get('url', ''))
    host = parsed_url.netloc
    
    if filters.get('allowed_hosts') and host:
        if not any(allowed in host for allowed in filters['allowed_hosts']):
            passed = False
            reasons.append(f'Host "{host}" not in allowed list')
    
    if filters.get('blocked_hosts') and host:
        if any(blocked in host for blocked in filters['blocked_hosts']):
            passed = False
            reasons.append(f'Host "{host}" is blocked')
    
    # Check extension filters
    filename = item.get('filename', '')
    file_ext = os.path.splitext(filename)[1].lower()
    
    if filters.get('allowed_extensions'):
        if file_ext and file_ext not in filters['allowed_extensions']:
            passed = False
            reasons.append(f'Extension "{file_ext}" not in allowed list')
    
    if filters.get('blocked_extensions'):
        if file_ext and file_ext in filters['blocked_extensions']:
            passed = False
            reasons.append(f'Extension "{file_ext}" is blocked')
    
    # Check sample/trailer exclusion
    if filters.get('exclude_samples', True):
        if re.search(r'\bsample\b', filename, re.IGNORECASE):
            passed = False
            reasons.append('Filename contains "sample"')
    
    if filters.get('exclude_trailers', True):
        if re.search(r'\btrailer\b', filename, re.IGNORECASE):
            passed = False
            reasons.append('Filename contains "trailer"')
    
    # Check size filters
    size_mb = item.get('size_mb', 0)
    min_size = filters.get('min_size_mb', 0)
    max_size = filters.get('max_size_mb', 0)
    
    if min_size > 0 and size_mb < min_size:
        passed = False
        reasons.append(f'Size {size_mb}MB below minimum {min_size}MB')
    
    if max_size > 0 and size_mb > max_size:
        passed = False
        reasons.append(f'Size {size_mb}MB above maximum {max_size}MB')
    
    return {
        'passed': passed,
        'reasons': reasons if not passed else ['All filters passed']
    }

@link_grabber_bp.route('/api/link-grabber/add', methods=['POST'])
def add_links():
    """
    Add links to the link grabber queue
    Body: {
        "urls": ["http://example.com/file1.mkv", "http://example.com/file2.mp4"],
        "probe": true (optional, default true - probe availability and size)
    }
    """
    req_data = request.get_json(silent=True) or {}
    urls = req_data.get('urls', [])
    probe = req_data.get('probe', True)
    
    if not urls:
        return jsonify({'ok': False, 'error': 'urls array required'}), 400
    
    # Ensure urls is a list
    if isinstance(urls, str):
        urls = [urls]
    
    queue_data = _load_queue()
    items = queue_data.get('items', [])
    filters = queue_data.get('filters', {})
    
    added_items = []
    
    for url in urls:
        # Check if URL already in queue
        if any(item['url'] == url for item in items):
            continue
        
        # Extract filename
        filename = _extract_filename_from_url(url)
        
        # Probe availability if requested
        probe_result = {}
        if probe:
            probe_result = _probe_availability(url)
        else:
            probe_result = {
                'available': None,
                'size_bytes': 0,
                'size_mb': 0,
                'content_type': 'unknown',
                'error': None
            }
        
        # Guess media type
        media_type = _guess_media_type(filename, probe_result.get('content_type', ''))
        
        # Create item
        item = {
            'id': f"{datetime.utcnow().timestamp()}_{len(items)}",
            'url': url,
            'filename': filename,
            'media_type': media_type,
            'available': probe_result.get('available'),
            'size_bytes': probe_result.get('size_bytes', 0),
            'size_mb': probe_result.get('size_mb', 0),
            'content_type': probe_result.get('content_type', 'unknown'),
            'probe_error': probe_result.get('error'),
            'added_at': datetime.utcnow().isoformat() + 'Z',
            'selected': True,
            'filter_status': None
        }
        
        # Apply filters
        filter_result = _apply_filters(item, filters)
        item['filter_status'] = filter_result
        
        items.append(item)
        added_items.append(item)
    
    queue_data['items'] = items
    _save_queue(queue_data)
    
    return jsonify({
        'ok': True,
        'added_count': len(added_items),
        'total_items': len(items),
        'items': added_items
    })

@link_grabber_bp.route('/api/link-grabber/queue', methods=['GET'])
def get_queue():
    """Get the current link grabber queue"""
    queue_data = _load_queue()
    
    # Optional filtering by media type
    media_type_filter = request.args.get('media_type')
    filter_passed = request.args.get('filter_passed')
    
    items = queue_data.get('items', [])
    
    if media_type_filter:
        items = [item for item in items if item.get('media_type') == media_type_filter]
    
    if filter_passed is not None:
        filter_passed_bool = filter_passed.lower() == 'true'
        items = [item for item in items if item.get('filter_status', {}).get('passed') == filter_passed_bool]
    
    return jsonify({
        'ok': True,
        'total_items': len(items),
        'filters': queue_data.get('filters', {}),
        'items': items
    })

@link_grabber_bp.route('/api/link-grabber/queue/<item_id>', methods=['DELETE'])
def remove_item(item_id):
    """Remove an item from the queue"""
    queue_data = _load_queue()
    items = queue_data.get('items', [])
    
    original_count = len(items)
    items = [item for item in items if item['id'] != item_id]
    
    if len(items) == original_count:
        return jsonify({'ok': False, 'error': 'Item not found'}), 404
    
    queue_data['items'] = items
    _save_queue(queue_data)
    
    return jsonify({
        'ok': True,
        'message': 'Item removed from queue'
    })

@link_grabber_bp.route('/api/link-grabber/queue/clear', methods=['POST'])
def clear_queue():
    """Clear the entire queue or filtered items"""
    req_data = request.get_json(silent=True) or {}
    clear_all = req_data.get('clear_all', False)
    clear_filtered = req_data.get('clear_filtered', False)
    
    queue_data = _load_queue()
    items = queue_data.get('items', [])
    
    if clear_all:
        queue_data['items'] = []
    elif clear_filtered:
        # Remove items that didn't pass filters
        queue_data['items'] = [item for item in items if item.get('filter_status', {}).get('passed', True)]
    
    _save_queue(queue_data)
    
    return jsonify({
        'ok': True,
        'message': 'Queue cleared',
        'remaining_items': len(queue_data['items'])
    })

@link_grabber_bp.route('/api/link-grabber/filters', methods=['GET'])
def get_filters():
    """Get current filters"""
    queue_data = _load_queue()
    return jsonify({
        'ok': True,
        'filters': queue_data.get('filters', {})
    })

@link_grabber_bp.route('/api/link-grabber/filters', methods=['POST'])
def set_filters():
    """
    Update filters
    Body: {
        "allowed_hosts": ["example.com"],
        "blocked_hosts": ["spam.com"],
        "allowed_extensions": [".mkv", ".mp4"],
        "blocked_extensions": [".exe"],
        "exclude_samples": true,
        "exclude_trailers": true,
        "min_size_mb": 100,
        "max_size_mb": 50000
    }
    """
    req_data = request.get_json(silent=True) or {}
    
    queue_data = _load_queue()
    current_filters = queue_data.get('filters', {})
    current_filters.update(req_data)
    queue_data['filters'] = current_filters
    _save_queue(queue_data)
    
    return jsonify({
        'ok': True,
        'message': 'Filters updated',
        'filters': current_filters
    })

@link_grabber_bp.route('/api/link-grabber/apply-filters', methods=['POST'])
def apply_filters_to_queue():
    """Re-apply filters to all items in the queue"""
    queue_data = _load_queue()
    items = queue_data.get('items', [])
    filters = queue_data.get('filters', {})
    
    for item in items:
        filter_result = _apply_filters(item, filters)
        item['filter_status'] = filter_result
    
    _save_queue(queue_data)
    
    passed_count = sum(1 for item in items if item.get('filter_status', {}).get('passed', False))
    
    return jsonify({
        'ok': True,
        'message': 'Filters applied to all items',
        'total_items': len(items),
        'passed_items': passed_count,
        'filtered_items': len(items) - passed_count
    })

@link_grabber_bp.route('/api/link-grabber/select', methods=['POST'])
def select_items():
    """
    Select/deselect items for download
    Body: {
        "item_ids": ["id1", "id2"],
        "selected": true
    }
    """
    req_data = request.get_json(silent=True) or {}
    item_ids = req_data.get('item_ids', [])
    selected = req_data.get('selected', True)
    
    if not item_ids:
        return jsonify({'ok': False, 'error': 'item_ids required'}), 400
    
    queue_data = _load_queue()
    items = queue_data.get('items', [])
    
    updated_count = 0
    for item in items:
        if item['id'] in item_ids:
            item['selected'] = selected
            updated_count += 1
    
    _save_queue(queue_data)
    
    return jsonify({
        'ok': True,
        'message': f'{updated_count} items {"selected" if selected else "deselected"}',
        'updated_count': updated_count
    })

@link_grabber_bp.route('/api/link-grabber/enqueue', methods=['POST'])
def enqueue_selected():
    """
    Move selected items to the download queue
    Body: {
        "only_passed": true (optional, only enqueue items that passed filters)
    }
    """
    req_data = request.get_json(silent=True) or {}
    only_passed = req_data.get('only_passed', True)
    
    queue_data = _load_queue()
    items = queue_data.get('items', [])
    
    # Filter items to enqueue
    items_to_enqueue = []
    remaining_items = []
    
    for item in items:
        if item.get('selected', False):
            if only_passed:
                if item.get('filter_status', {}).get('passed', False):
                    items_to_enqueue.append(item)
                else:
                    remaining_items.append(item)
            else:
                items_to_enqueue.append(item)
        else:
            remaining_items.append(item)
    
    # Update queue (remove enqueued items)
    queue_data['items'] = remaining_items
    _save_queue(queue_data)
    
    # TODO: Actually add to download queue (integrate with existing downloader)
    # For now, just return the items that would be enqueued
    
    return jsonify({
        'ok': True,
        'message': f'{len(items_to_enqueue)} items enqueued for download',
        'enqueued_count': len(items_to_enqueue),
        'remaining_count': len(remaining_items),
        'enqueued_items': items_to_enqueue
    })
