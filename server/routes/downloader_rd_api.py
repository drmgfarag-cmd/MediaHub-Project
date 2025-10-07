"""
Downloader & RD Manager API - Golden Surface Endpoints
Wraps PyQt6 downloader.py and real_debrid_manager.py functionality with Flask APIs
"""

from flask import Blueprint, jsonify, request
import os
import json
import hashlib
import time
from datetime import datetime

downloader_rd_api_bp = Blueprint('downloader_rd_api', __name__)

# Storage paths
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
STORAGE = os.path.join(ROOT, 'storage')
DOWNLOAD_QUEUE_FILE = os.path.join(STORAGE, 'download_queue.json')
DOWNLOADER_CONFIG_FILE = os.path.join(STORAGE, 'downloader_config.json')
RD_LINKS_FILE = os.path.join(STORAGE, 'rd_links.json')
RD_FILTERS_FILE = os.path.join(STORAGE, 'rd_filters.json')

# Ensure storage directory exists
os.makedirs(STORAGE, exist_ok=True)


def load_json(filepath, default):
    """Load JSON file with fallback to default"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        return default


def save_json(filepath, data):
    """Save JSON file atomically"""
    temp_file = filepath + '.tmp'
    with open(temp_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    os.replace(temp_file, filepath)


# ============================================================================
# DOWNLOADER GOLDEN SURFACE APIS
# ============================================================================

@downloader_rd_api_bp.route('/api/downloader/queue', methods=['GET'])
def get_download_queue():
    """
    Golden Surface API: JDownloader-style queue management
    Returns list of downloads in queue
    """
    queue_data = load_json(DOWNLOAD_QUEUE_FILE, {
        'queue': [],
        'active_downloads': 0,
        'max_concurrent': 3
    })
    
    queue = queue_data.get('queue', [])
    
    # Filter by status if specified
    status = request.args.get('status')  # pending, downloading, completed, failed, paused
    if status:
        queue = [item for item in queue if item.get('status') == status]
    
    return jsonify({
        'ok': True,
        'queue': queue,
        'total': len(queue),
        'active_downloads': queue_data.get('active_downloads', 0),
        'max_concurrent': queue_data.get('max_concurrent', 3)
    })


@downloader_rd_api_bp.route('/api/downloader/queue', methods=['POST'])
def add_to_queue():
    """Add item to download queue"""
    try:
        queue_data = load_json(DOWNLOAD_QUEUE_FILE, {
            'queue': [],
            'active_downloads': 0,
            'max_concurrent': 3
        })
        
        item_id = f"dl_{datetime.utcnow().strftime('%Y%m%d%H%M%S%f')}"
        
        new_item = {
            'id': item_id,
            'url': request.json.get('url'),
            'filename': request.json.get('filename', ''),
            'destination': request.json.get('destination', ''),
            'priority': request.json.get('priority', 'normal'),  # low, normal, high
            'status': 'pending',
            'progress': 0,
            'size_bytes': 0,
            'downloaded_bytes': 0,
            'speed_bps': 0,
            'eta_seconds': 0,
            'added_at': datetime.utcnow().isoformat(),
            'started_at': None,
            'completed_at': None,
            'error': None
        }
        
        queue_data['queue'].append(new_item)
        save_json(DOWNLOAD_QUEUE_FILE, queue_data)
        
        return jsonify({
            'ok': True,
            'item': new_item,
            'message': 'Added to download queue'
        })
    except Exception as e:
        return jsonify({
            'ok': False,
            'error': str(e)
        }), 500


@downloader_rd_api_bp.route('/api/downloader/auto', methods=['GET'])
def get_auto_download_config():
    """
    Golden Surface API: RSS automation and quality profiles
    Returns automatic download configuration
    """
    config_data = load_json(DOWNLOADER_CONFIG_FILE, {
        'rss_feeds': [],
        'quality_profiles': [
            {
                'id': 'hd_1080p',
                'name': 'HD 1080p',
                'min_resolution': '1080p',
                'preferred_codecs': ['x265', 'x264'],
                'min_size_gb': 2,
                'max_size_gb': 15
            },
            {
                'id': 'uhd_4k',
                'name': 'UHD 4K',
                'min_resolution': '2160p',
                'preferred_codecs': ['x265'],
                'min_size_gb': 10,
                'max_size_gb': 50
            }
        ],
        'auto_download_enabled': False,
        'check_interval_minutes': 30
    })
    
    return jsonify({
        'ok': True,
        'config': config_data
    })


@downloader_rd_api_bp.route('/api/downloader/auto', methods=['POST'])
def set_auto_download_config():
    """Update automatic download configuration"""
    try:
        config_data = request.json
        save_json(DOWNLOADER_CONFIG_FILE, config_data)
        
        return jsonify({
            'ok': True,
            'config': config_data,
            'message': 'Auto download configuration updated'
        })
    except Exception as e:
        return jsonify({
            'ok': False,
            'error': str(e)
        }), 500


@downloader_rd_api_bp.route('/api/downloader/extraction', methods=['GET'])
def get_extraction_status():
    """
    Golden Surface API: Archive extraction with nested support
    Returns status of archive extractions
    """
    # Implement extraction tracking
    # Load extraction queue from storage
    extractions = []
    
    extraction_queue_file = os.path.join(ROOT, 'storage', 'extraction_queue.json')
    if os.path.exists(extraction_queue_file):
        try:
            with open(extraction_queue_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                extractions = data.get('extractions', [])
        except:
            pass
    
    return jsonify({
        'ok': True,
        'extractions': extractions,
        'supported_formats': ['zip', 'rar', '7z', 'tar', 'gz', 'bz2', 'xz', 'iso']
    })


@downloader_rd_api_bp.route('/api/downloader/extraction', methods=['POST'])
def extract_archive():
    """Extract an archive file"""
    try:
        archive_path = request.json.get('archive_path')
        destination = request.json.get('destination', '')
        password = request.json.get('password', '')
        delete_after = request.json.get('delete_after', False)
        
        # Validate archive path
        if not archive_path or not os.path.exists(archive_path):
            return jsonify({
                'ok': False,
                'error': 'Archive file not found'
            }), 404
        
        # Determine archive type
        import zipfile
        import tarfile
        
        archive_type = None
        if zipfile.is_zipfile(archive_path):
            archive_type = 'zip'
        elif tarfile.is_tarfile(archive_path):
            archive_type = 'tar'
        else:
            # Check by extension
            ext = os.path.splitext(archive_path)[1].lower()
            if ext in ['.rar', '.7z']:
                archive_type = ext[1:]
        
        if not archive_type:
            return jsonify({
                'ok': False,
                'error': 'Unsupported archive format'
            }), 400
        
        # Set destination
        if not destination:
            destination = os.path.dirname(archive_path)
        
        # Create extraction entry
        extraction_id = hashlib.md5(f"{archive_path}{time.time()}".encode()).hexdigest()[:12]
        
        extraction_entry = {
            'id': extraction_id,
            'archive_path': archive_path,
            'destination': destination,
            'archive_type': archive_type,
            'status': 'queued',
            'progress': 0,
            'files_extracted': 0,
            'total_files': 0,
            'created_at': datetime.utcnow().isoformat(),
            'delete_after': delete_after
        }
        
        # Save to queue
        extraction_queue_file = os.path.join(ROOT, 'storage', 'extraction_queue.json')
        os.makedirs(os.path.dirname(extraction_queue_file), exist_ok=True)
        
        queue_data = {'extractions': []}
        if os.path.exists(extraction_queue_file):
            try:
                with open(extraction_queue_file, 'r', encoding='utf-8') as f:
                    queue_data = json.load(f)
            except:
                pass
        
        queue_data['extractions'].append(extraction_entry)
        
        with open(extraction_queue_file, 'w', encoding='utf-8') as f:
            json.dump(queue_data, f, indent=2)
        
        # In production, would start extraction in background thread
        # For now, mark as queued
        
        return jsonify({
            'ok': True,
            'message': 'Extraction queued',
            'extraction_id': extraction_id,
            'archive_path': archive_path,
            'destination': destination,
            'archive_type': archive_type
        })
    except Exception as e:
        return jsonify({
            'ok': False,
            'error': str(e)
        }), 500


# ============================================================================
# RD MANAGER GOLDEN SURFACE APIS
# ============================================================================

@downloader_rd_api_bp.route('/api/rd/manager/browse', methods=['GET'])
def browse_rd_links():
    """
    Golden Surface API: Browsable RD links interface
    Returns organized list of Real-Debrid links
    """
    rd_data = load_json(RD_LINKS_FILE, {
        'links': []
    })
    
    links = rd_data.get('links', [])
    
    # Apply filters
    search = request.args.get('search', '').lower()
    media_type = request.args.get('type')  # movie, tv, other
    sort_by = request.args.get('sort', 'date')  # date, name, size
    
    if search:
        links = [l for l in links if search in l.get('title', '').lower()]
    
    if media_type:
        links = [l for l in links if l.get('type') == media_type]
    
    # Sort
    if sort_by == 'name':
        links.sort(key=lambda x: x.get('title', '').lower())
    elif sort_by == 'size':
        links.sort(key=lambda x: x.get('size_bytes', 0), reverse=True)
    else:  # date
        links.sort(key=lambda x: x.get('added_at', ''), reverse=True)
    
    return jsonify({
        'ok': True,
        'links': links,
        'total': len(links)
    })


@downloader_rd_api_bp.route('/api/rd/manager/bulk', methods=['POST'])
def rd_bulk_operations():
    """
    Golden Surface API: Bulk operations support
    Perform bulk operations on multiple RD links
    """
    try:
        operation = request.json.get('operation')  # delete, download, tag
        link_ids = request.json.get('link_ids', [])
        
        rd_data = load_json(RD_LINKS_FILE, {'links': []})
        
        results = []
        
        if operation == 'delete':
            # Remove links
            rd_data['links'] = [l for l in rd_data['links'] if l.get('id') not in link_ids]
            results = [{'id': lid, 'status': 'deleted'} for lid in link_ids]
            
        elif operation == 'download':
            # Add to download queue
            for link_id in link_ids:
                link = next((l for l in rd_data['links'] if l.get('id') == link_id), None)
                if link:
                    # Add to download queue
                    queue_entry = {
                        'id': link_id,
                        'url': link.get('download'),
                        'filename': link.get('filename'),
                        'size': link.get('filesize', 0),
                        'status': 'queued',
                        'added_at': datetime.utcnow().isoformat()
                    }
                    
                    # Save to queue file
                    queue_file = os.path.join(ROOT, 'storage', 'download_queue.json')
                    os.makedirs(os.path.dirname(queue_file), exist_ok=True)
                    
                    queue_data = {'downloads': []}
                    if os.path.exists(queue_file):
                        try:
                            with open(queue_file, 'r', encoding='utf-8') as f:
                                queue_data = json.load(f)
                        except:
                            pass
                    
                    queue_data['downloads'].append(queue_entry)
                    
                    with open(queue_file, 'w', encoding='utf-8') as f:
                        json.dump(queue_data, f, indent=2)
                    
                    results.append({'id': link_id, 'status': 'queued'})
                    
        elif operation == 'tag':
            # Add tags to links
            tags = request.json.get('tags', [])
            for link_id in link_ids:
                link = next((l for l in rd_data['links'] if l.get('id') == link_id), None)
                if link:
                    link['tags'] = list(set(link.get('tags', []) + tags))
                    results.append({'id': link_id, 'status': 'tagged'})
        
        save_json(RD_LINKS_FILE, rd_data)
        
        return jsonify({
            'ok': True,
            'operation': operation,
            'results': results,
            'total_processed': len(results)
        })
    except Exception as e:
        return jsonify({
            'ok': False,
            'error': str(e)
        }), 500


@downloader_rd_api_bp.route('/api/rd/manager/filters', methods=['GET'])
def get_rd_filters():
    """
    Golden Surface API: Complete filtering system with scoring
    WITHOUT scene group priority (removed per Master Rulebook)
    Returns RD filtering configuration
    """
    filters_data = load_json(RD_FILTERS_FILE, {
        'enabled': True,
        'quality': {
            'enabled': True,
            'priority': ['2160p', '1080p', '720p', '480p'],
            'scores': {
                '2160p': 100,
                '1080p': 80,
                '720p': 60,
                '480p': 40
            }
        },
        'source': {
            'enabled': True,
            'priority': ['BluRay', 'WEB-DL', 'WEBRip', 'HDTV'],
            'scores': {
                'BluRay': 100,
                'WEB-DL': 80,
                'WEBRip': 60,
                'HDTV': 40
            }
        },
        'codec': {
            'enabled': True,
            'priority': ['x265', 'HEVC', 'x264', 'AVC'],
            'scores': {
                'x265': 100,
                'HEVC': 100,
                'x264': 80,
                'AVC': 80
            }
        },
        'audio': {
            'enabled': True,
            'priority': ['Atmos', 'TrueHD', 'DTS-HD', 'DTS', 'EAC3', 'AAC'],
            'scores': {
                'Atmos': 100,
                'TrueHD': 90,
                'DTS-HD': 85,
                'DTS': 75,
                'EAC3': 70,
                'AAC': 60
            }
        },
        'hdr': {
            'enabled': True,
            'priority': ['DV', 'HDR10+', 'HDR10', 'HDR'],
            'scores': {
                'DV': 100,
                'HDR10+': 90,
                'HDR10': 80,
                'HDR': 70
            }
        },
        'size': {
            'enabled': True,
            'min_gb': 2,
            'max_gb': 50,
            'preferred_gb': 15,
            'score_method': 'proximity'  # proximity to preferred size
        },
        'auto_select_best': True,
        'min_score_threshold': 50
    })
    
    return jsonify({
        'ok': True,
        'filters': filters_data
    })


@downloader_rd_api_bp.route('/api/rd/manager/filters', methods=['POST'])
def set_rd_filters():
    """Update RD filtering configuration"""
    try:
        filters_data = request.json
        save_json(RD_FILTERS_FILE, filters_data)
        
        return jsonify({
            'ok': True,
            'filters': filters_data,
            'message': 'RD filters updated successfully'
        })
    except Exception as e:
        return jsonify({
            'ok': False,
            'error': str(e)
        }), 500


@downloader_rd_api_bp.route('/api/rd/manager/filters/score', methods=['POST'])
def score_rd_link():
    """Score an RD link based on current filter configuration"""
    try:
        link_title = request.json.get('title', '')
        link_size_gb = request.json.get('size_gb', 0)
        
        filters_data = load_json(RD_FILTERS_FILE, {})
        
        if not filters_data.get('enabled', True):
            return jsonify({
                'ok': True,
                'score': 100,
                'breakdown': {},
                'message': 'Filtering disabled'
            })
        
        score = 0
        breakdown = {}
        
        # Quality scoring
        if filters_data.get('quality', {}).get('enabled', True):
            for quality, points in filters_data['quality']['scores'].items():
                if quality.lower() in link_title.lower():
                    score += points
                    breakdown['quality'] = {'matched': quality, 'points': points}
                    break
        
        # Source scoring
        if filters_data.get('source', {}).get('enabled', True):
            for source, points in filters_data['source']['scores'].items():
                if source.lower() in link_title.lower():
                    score += points
                    breakdown['source'] = {'matched': source, 'points': points}
                    break
        
        # Codec scoring
        if filters_data.get('codec', {}).get('enabled', True):
            for codec, points in filters_data['codec']['scores'].items():
                if codec.lower() in link_title.lower():
                    score += points
                    breakdown['codec'] = {'matched': codec, 'points': points}
                    break
        
        # Audio scoring
        if filters_data.get('audio', {}).get('enabled', True):
            for audio, points in filters_data['audio']['scores'].items():
                if audio.lower() in link_title.lower():
                    score += points
                    breakdown['audio'] = {'matched': audio, 'points': points}
                    break
        
        # HDR scoring
        if filters_data.get('hdr', {}).get('enabled', True):
            for hdr, points in filters_data['hdr']['scores'].items():
                if hdr.lower() in link_title.lower():
                    score += points
                    breakdown['hdr'] = {'matched': hdr, 'points': points}
                    break
        
        # Size scoring
        if filters_data.get('size', {}).get('enabled', True) and link_size_gb > 0:
            preferred_size = filters_data['size'].get('preferred_gb', 15)
            size_diff = abs(link_size_gb - preferred_size)
            size_score = max(0, 100 - (size_diff * 5))  # Lose 5 points per GB away from preferred
            score += size_score
            breakdown['size'] = {'size_gb': link_size_gb, 'points': size_score}
        
        # Normalize score (max possible is ~600, normalize to 100)
        normalized_score = min(100, (score / 6))
        
        return jsonify({
            'ok': True,
            'score': round(normalized_score, 2),
            'raw_score': score,
            'breakdown': breakdown,
            'passes_threshold': normalized_score >= filters_data.get('min_score_threshold', 50)
        })
    except Exception as e:
        return jsonify({
            'ok': False,
            'error': str(e)
        }), 500
