"""
Advanced Deduplication API - Master Rulebook Golden Surface
Wraps existing dedupe.py and dedupe_editor.py functionality
"""
from flask import Blueprint, request, jsonify
import os
import json
import hashlib
from datetime import datetime

advanced_dedupe_bp = Blueprint('advanced_dedupe', __name__)

# Storage paths
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
STORAGE = os.path.join(ROOT, 'storage')
HASH_INDEX_PATH = os.path.join(STORAGE, 'hash_index.json')
DEDUPE_CONFIG_PATH = os.path.join(STORAGE, 'dedupe_config.json')
DEDUPE_POLICY_PATH = os.path.join(STORAGE, 'dedupe_policy.json')

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

def calculate_file_hash(filepath):
    """Calculate SHA256 hash of file"""
    if not os.path.exists(filepath):
        return None
    try:
        sha256 = hashlib.sha256()
        with open(filepath, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b''):
                sha256.update(chunk)
        return sha256.hexdigest()
    except:
        return None

def normalize_title(title):
    """Normalize title for comparison"""
    import re
    # Remove special chars, lowercase, remove extra spaces
    title = re.sub(r'[^\w\s]', '', title.lower())
    title = re.sub(r'\s+', ' ', title).strip()
    return title

def score_quality(item):
    """Score item quality based on resolution, codec, audio"""
    score = 0
    
    # Resolution scoring
    resolution = item.get('resolution', '').lower()
    if '2160' in resolution or '4k' in resolution:
        score += 100
    elif '1080' in resolution:
        score += 80
    elif '720' in resolution:
        score += 60
    elif '480' in resolution:
        score += 40
    
    # Codec scoring
    codec = item.get('codec', '').lower()
    if 'h265' in codec or 'hevc' in codec or 'av1' in codec:
        score += 30
    elif 'h264' in codec or 'avc' in codec:
        score += 20
    elif 'xvid' in codec or 'divx' in codec:
        score += 10
    
    # Audio scoring
    audio = item.get('audio', '').lower()
    if 'atmos' in audio or 'truehd' in audio:
        score += 20
    elif 'dts' in audio or 'dd' in audio:
        score += 15
    elif 'aac' in audio:
        score += 10
    
    # HDR bonus
    if item.get('hdr', False):
        score += 15
    
    # File size (larger is usually better for same resolution)
    size = item.get('size', 0)
    if size > 10 * 1024 * 1024 * 1024:  # > 10GB
        score += 10
    elif size > 5 * 1024 * 1024 * 1024:  # > 5GB
        score += 5
    
    return score

@advanced_dedupe_bp.route('/api/dedupe/hash_index', methods=['GET', 'POST'])
def hash_index():
    """
    GET: Return grouped duplicates with hash-based analysis
    POST: Append items to hash index
    """
    if request.method == 'POST':
        # Add items to hash index
        data = request.get_json() or {}
        items = data.get('items', [])
        
        index = load_json(HASH_INDEX_PATH, {'items': [], 'groups': {}})
        
        for item in items:
            filepath = item.get('path')
            if filepath:
                file_hash = calculate_file_hash(filepath)
                if file_hash:
                    item['hash'] = file_hash
                    item['indexed_at'] = datetime.now().isoformat()
                    index['items'].append(item)
        
        # Group by hash
        groups = {}
        for item in index['items']:
            h = item.get('hash')
            if h:
                if h not in groups:
                    groups[h] = []
                groups[h].append(item)
        
        # Keep only duplicates (hash appears more than once)
        index['groups'] = {h: items for h, items in groups.items() if len(items) > 1}
        
        save_json(HASH_INDEX_PATH, index)
        
        return jsonify({
            'success': True,
            'items_added': len(items),
            'total_items': len(index['items']),
            'duplicate_groups': len(index['groups'])
        })
    
    else:
        # GET: Return grouped duplicates
        index = load_json(HASH_INDEX_PATH, {'items': [], 'groups': {}})
        
        # Add quality scores to each item
        for group_hash, items in index['groups'].items():
            for item in items:
                item['quality_score'] = score_quality(item)
            # Sort by quality score (best first)
            items.sort(key=lambda x: x.get('quality_score', 0), reverse=True)
        
        return jsonify({
            'success': True,
            'total_items': len(index['items']),
            'duplicate_groups': len(index['groups']),
            'groups': index['groups']
        })

@advanced_dedupe_bp.route('/api/dedupe/criteria_analysis', methods=['POST'])
def criteria_analysis():
    """Analyze and score content by multiple criteria"""
    data = request.get_json() or {}
    items = data.get('items', [])
    criteria = data.get('criteria', ['resolution', 'codec', 'audio', 'hdr', 'size'])
    
    results = []
    for item in items:
        analysis = {
            'item': item,
            'scores': {},
            'total_score': 0
        }
        
        # Score each criterion
        if 'resolution' in criteria:
            res_score = 0
            resolution = item.get('resolution', '').lower()
            if '2160' in resolution or '4k' in resolution:
                res_score = 100
            elif '1080' in resolution:
                res_score = 80
            elif '720' in resolution:
                res_score = 60
            elif '480' in resolution:
                res_score = 40
            analysis['scores']['resolution'] = res_score
            analysis['total_score'] += res_score
        
        if 'codec' in criteria:
            codec_score = 0
            codec = item.get('codec', '').lower()
            if 'h265' in codec or 'hevc' in codec or 'av1' in codec:
                codec_score = 30
            elif 'h264' in codec or 'avc' in codec:
                codec_score = 20
            elif 'xvid' in codec or 'divx' in codec:
                codec_score = 10
            analysis['scores']['codec'] = codec_score
            analysis['total_score'] += codec_score
        
        if 'audio' in criteria:
            audio_score = 0
            audio = item.get('audio', '').lower()
            if 'atmos' in audio or 'truehd' in audio:
                audio_score = 20
            elif 'dts' in audio or 'dd' in audio:
                audio_score = 15
            elif 'aac' in audio:
                audio_score = 10
            analysis['scores']['audio'] = audio_score
            analysis['total_score'] += audio_score
        
        if 'hdr' in criteria:
            hdr_score = 15 if item.get('hdr', False) else 0
            analysis['scores']['hdr'] = hdr_score
            analysis['total_score'] += hdr_score
        
        if 'size' in criteria:
            size_score = 0
            size = item.get('size', 0)
            if size > 10 * 1024 * 1024 * 1024:
                size_score = 10
            elif size > 5 * 1024 * 1024 * 1024:
                size_score = 5
            analysis['scores']['size'] = size_score
            analysis['total_score'] += size_score
        
        results.append(analysis)
    
    # Sort by total score (best first)
    results.sort(key=lambda x: x['total_score'], reverse=True)
    
    return jsonify({
        'success': True,
        'criteria': criteria,
        'results': results,
        'best_item': results[0] if results else None
    })

@advanced_dedupe_bp.route('/api/dedupe/bulk_action', methods=['POST'])
def bulk_action():
    """Execute bulk deduplication action"""
    data = request.get_json() or {}
    action = data.get('action')  # 'delete', 'keep_best', 'mark'
    groups = data.get('groups', [])
    
    results = {
        'success': True,
        'action': action,
        'groups_processed': 0,
        'items_affected': 0,
        'errors': []
    }
    
    for group in groups:
        items = group.get('items', [])
        if not items:
            continue
        
        try:
            if action == 'keep_best':
                # Score all items
                for item in items:
                    item['quality_score'] = score_quality(item)
                
                # Sort by quality (best first)
                items.sort(key=lambda x: x.get('quality_score', 0), reverse=True)
                
                # Keep first (best), delete rest
                best = items[0]
                to_delete = items[1:]
                
                for item in to_delete:
                    filepath = item.get('path')
                    if filepath and os.path.exists(filepath):
                        try:
                            os.remove(filepath)
                            results['items_affected'] += 1
                        except Exception as e:
                            results['errors'].append(f"Failed to delete {filepath}: {str(e)}")
                
                results['groups_processed'] += 1
            
            elif action == 'delete':
                # Delete all items in group
                for item in items:
                    filepath = item.get('path')
                    if filepath and os.path.exists(filepath):
                        try:
                            os.remove(filepath)
                            results['items_affected'] += 1
                        except Exception as e:
                            results['errors'].append(f"Failed to delete {filepath}: {str(e)}")
                
                results['groups_processed'] += 1
            
            elif action == 'mark':
                # Just mark items (don't delete)
                for item in items:
                    item['marked_for_review'] = True
                results['groups_processed'] += 1
                results['items_affected'] += len(items)
        
        except Exception as e:
            results['errors'].append(f"Error processing group: {str(e)}")
    
    return jsonify(results)

@advanced_dedupe_bp.route('/api/dedupe/criteria_config', methods=['GET', 'POST'])
def criteria_config():
    """Get or update deduplication criteria configuration"""
    if request.method == 'POST':
        data = request.get_json() or {}
        save_json(DEDUPE_CONFIG_PATH, data)
        return jsonify({
            'success': True,
            'config': data
        })
    else:
        config = load_json(DEDUPE_CONFIG_PATH, {
            'criteria': ['resolution', 'codec', 'audio', 'hdr', 'size'],
            'weights': {
                'resolution': 1.0,
                'codec': 0.3,
                'audio': 0.2,
                'hdr': 0.15,
                'size': 0.1
            },
            'auto_action': 'mark',  # 'mark', 'keep_best', 'delete'
            'min_confidence': 0.8
        })
        return jsonify({
            'success': True,
            'config': config
        })

@advanced_dedupe_bp.route('/api/dedupe/policy', methods=['GET', 'POST'])
def dedupe_policy():
    """Get or update deduplication policy"""
    if request.method == 'POST':
        data = request.get_json() or {}
        save_json(DEDUPE_POLICY_PATH, data)
        return jsonify({
            'success': True,
            'policy': data
        })
    else:
        policy = load_json(DEDUPE_POLICY_PATH, {
            'enabled': True,
            'auto_scan': False,
            'scan_interval_hours': 24,
            'auto_resolve': False,
            'keep_strategy': 'best_quality',  # 'best_quality', 'newest', 'largest', 'manual'
            'delete_confirmation': True,
            'backup_before_delete': True
        })
        return jsonify({
            'success': True,
            'policy': policy
        })

@advanced_dedupe_bp.route('/api/dedupe/movie_list_resolve', methods=['POST'])
def movie_list_resolve():
    """Resolve duplicates in a movie list"""
    data = request.get_json() or {}
    movies = data.get('movies', [])
    strategy = data.get('strategy', 'best_quality')
    
    # Group movies by normalized title
    groups = {}
    for movie in movies:
        title = normalize_title(movie.get('title', ''))
        if title:
            if title not in groups:
                groups[title] = []
            groups[title].append(movie)
    
    # Find duplicates (groups with more than one movie)
    duplicates = {title: items for title, items in groups.items() if len(items) > 1}
    
    resolved = []
    for title, items in duplicates.items():
        if strategy == 'best_quality':
            # Score by quality
            for item in items:
                item['quality_score'] = score_quality(item)
            items.sort(key=lambda x: x.get('quality_score', 0), reverse=True)
            resolved.append({
                'title': title,
                'kept': items[0],
                'removed': items[1:],
                'reason': 'best_quality'
            })
        
        elif strategy == 'newest':
            # Keep newest
            items.sort(key=lambda x: x.get('added_date', ''), reverse=True)
            resolved.append({
                'title': title,
                'kept': items[0],
                'removed': items[1:],
                'reason': 'newest'
            })
        
        elif strategy == 'largest':
            # Keep largest file
            items.sort(key=lambda x: x.get('size', 0), reverse=True)
            resolved.append({
                'title': title,
                'kept': items[0],
                'removed': items[1:],
                'reason': 'largest'
            })
    
    return jsonify({
        'success': True,
        'total_movies': len(movies),
        'duplicate_groups': len(duplicates),
        'resolved': resolved,
        'strategy': strategy
    })
