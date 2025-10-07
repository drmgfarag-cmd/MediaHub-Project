from flask import Blueprint, jsonify, request, send_file
import os, json, zipfile, rarfile
from datetime import datetime
import io
from PIL import Image

comics_enhanced_bp = Blueprint('comics_enhanced', __name__)

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
STO = os.path.join(ROOT, 'storage')
COMICS_DIR = os.path.join(STO, 'comics')
COMICS_DB = os.path.join(STO, 'comics_database.json')
COMICS_CONFIG = os.path.join(STO, 'config', 'comics_config.json')

def _load_config():
    """Load comics configuration"""
    try:
        with open(COMICS_CONFIG, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return {
            'reading_mode': 'single_page',  # single_page, double_page, continuous
            'reading_direction': 'ltr',  # ltr (left-to-right), rtl (right-to-left for manga)
            'fit_mode': 'fit_width',  # fit_width, fit_height, fit_screen, original
            'background_color': '#1a1a1a',
            'manga_mode': False,
            'auto_detect_manga': True
        }

def _save_config(data):
    """Save comics configuration"""
    os.makedirs(os.path.dirname(COMICS_CONFIG), exist_ok=True)
    tmp = COMICS_CONFIG + '.tmp'
    with open(tmp, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)
    os.replace(tmp, COMICS_CONFIG)

def _load_comics_db():
    """Load comics database"""
    try:
        with open(COMICS_DB, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return {'comics': [], 'series': [], 'reading_progress': {}}

def _save_comics_db(data):
    """Save comics database"""
    os.makedirs(os.path.dirname(COMICS_DB), exist_ok=True)
    tmp = COMICS_DB + '.tmp'
    with open(tmp, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)
    os.replace(tmp, COMICS_DB)

def _extract_comic_pages(file_path):
    """Extract pages from CBZ/CBR file"""
    pages = []
    file_ext = os.path.splitext(file_path)[1].lower()
    
    try:
        if file_ext == '.cbz' or file_ext == '.zip':
            with zipfile.ZipFile(file_path, 'r') as zf:
                for name in sorted(zf.namelist()):
                    if name.lower().endswith(('.jpg', '.jpeg', '.png', '.gif', '.webp')):
                        pages.append(name)
        
        elif file_ext == '.cbr' or file_ext == '.rar':
            with rarfile.RarFile(file_path, 'r') as rf:
                for name in sorted(rf.namelist()):
                    if name.lower().endswith(('.jpg', '.jpeg', '.png', '.gif', '.webp')):
                        pages.append(name)
    except Exception as e:
        print(f"Error extracting comic pages: {e}")
    
    return pages

def _get_comic_page(file_path, page_name):
    """Get a specific page from comic file"""
    file_ext = os.path.splitext(file_path)[1].lower()
    
    try:
        if file_ext == '.cbz' or file_ext == '.zip':
            with zipfile.ZipFile(file_path, 'r') as zf:
                return zf.read(page_name)
        
        elif file_ext == '.cbr' or file_ext == '.rar':
            with rarfile.RarFile(file_path, 'r') as rf:
                return rf.read(page_name)
    except Exception as e:
        print(f"Error reading comic page: {e}")
    
    return None

def _detect_manga(title, file_path):
    """Auto-detect if comic is manga based on title and metadata"""
    manga_keywords = ['manga', '漫画', 'マンガ', 'japanese', 'jp', 'raw']
    title_lower = title.lower()
    
    for keyword in manga_keywords:
        if keyword in title_lower:
            return True
    
    return False

@comics_enhanced_bp.route('/api/comics/config', methods=['GET'])
def get_config():
    """Get comics configuration"""
    config = _load_config()
    return jsonify({
        'ok': True,
        'config': config
    })

@comics_enhanced_bp.route('/api/comics/config', methods=['POST'])
def update_config():
    """Update comics configuration"""
    req_data = request.get_json(silent=True) or {}
    
    config = _load_config()
    config.update(req_data)
    _save_config(config)
    
    return jsonify({
        'ok': True,
        'message': 'Configuration updated',
        'config': config
    })

@comics_enhanced_bp.route('/api/comics/library', methods=['GET'])
def get_library():
    """Get all comics in library"""
    db = _load_comics_db()
    comics = db.get('comics', [])
    
    # Apply filters
    series = request.args.get('series')
    publisher = request.args.get('publisher')
    genre = request.args.get('genre')
    
    if series:
        comics = [c for c in comics if c.get('series_id') == series]
    if publisher:
        comics = [c for c in comics if publisher.lower() in c.get('publisher', '').lower()]
    if genre:
        comics = [c for c in comics if genre.lower() in ' '.join(c.get('genres', [])).lower()]
    
    return jsonify({
        'ok': True,
        'comics': comics,
        'total': len(comics)
    })

@comics_enhanced_bp.route('/api/comics/add', methods=['POST'])
def add_comic():
    """Add a comic to library"""
    req_data = request.get_json(silent=True) or {}
    
    if not req_data.get('title') or not req_data.get('file_path'):
        return jsonify({'ok': False, 'error': 'Title and file_path required'}), 400
    
    db = _load_comics_db()
    comics = db.get('comics', [])
    
    file_path = req_data.get('file_path')
    title = req_data.get('title')
    
    # Extract pages
    pages = _extract_comic_pages(file_path)
    
    # Auto-detect manga
    config = _load_config()
    is_manga = False
    if config.get('auto_detect_manga'):
        is_manga = _detect_manga(title, file_path)
    
    comic = {
        'id': f"comic_{datetime.utcnow().timestamp()}",
        'title': title,
        'series_id': req_data.get('series_id', ''),
        'issue_number': req_data.get('issue_number', ''),
        'publisher': req_data.get('publisher', ''),
        'publish_date': req_data.get('publish_date', ''),
        'writers': req_data.get('writers', []),
        'artists': req_data.get('artists', []),
        'genres': req_data.get('genres', []),
        'description': req_data.get('description', ''),
        'cover_image': req_data.get('cover_image', ''),
        'file_path': file_path,
        'file_format': os.path.splitext(file_path)[1].lower(),
        'page_count': len(pages),
        'pages': pages,
        'is_manga': is_manga,
        'added_at': datetime.utcnow().isoformat() + 'Z',
        'rating': 0,
        'tags': []
    }
    
    comics.append(comic)
    db['comics'] = comics
    _save_comics_db(db)
    
    return jsonify({
        'ok': True,
        'message': 'Comic added to library',
        'comic': comic
    })

@comics_enhanced_bp.route('/api/comics/<comic_id>', methods=['GET'])
def get_comic(comic_id):
    """Get comic details"""
    db = _load_comics_db()
    comics = db.get('comics', [])
    
    comic = next((c for c in comics if c.get('id') == comic_id), None)
    
    if not comic:
        return jsonify({'ok': False, 'error': 'Comic not found'}), 404
    
    # Get reading progress
    progress = db.get('reading_progress', {}).get(comic_id, {})
    
    return jsonify({
        'ok': True,
        'comic': comic,
        'progress': progress
    })

@comics_enhanced_bp.route('/api/comics/<comic_id>/page/<int:page_number>', methods=['GET'])
def get_comic_page(comic_id, page_number):
    """Get a specific page from a comic"""
    db = _load_comics_db()
    comics = db.get('comics', [])
    
    comic = next((c for c in comics if c.get('id') == comic_id), None)
    
    if not comic:
        return jsonify({'ok': False, 'error': 'Comic not found'}), 404
    
    pages = comic.get('pages', [])
    if page_number < 0 or page_number >= len(pages):
        return jsonify({'ok': False, 'error': 'Invalid page number'}), 400
    
    page_name = pages[page_number]
    file_path = comic.get('file_path')
    
    page_data = _get_comic_page(file_path, page_name)
    
    if not page_data:
        return jsonify({'ok': False, 'error': 'Failed to read page'}), 500
    
    # Return image
    return send_file(
        io.BytesIO(page_data),
        mimetype='image/jpeg'
    )

@comics_enhanced_bp.route('/api/comics/<comic_id>/progress', methods=['POST'])
def update_reading_progress(comic_id):
    """Update reading progress"""
    req_data = request.get_json(silent=True) or {}
    
    db = _load_comics_db()
    
    # Verify comic exists
    comics = db.get('comics', [])
    comic = next((c for c in comics if c.get('id') == comic_id), None)
    
    if not comic:
        return jsonify({'ok': False, 'error': 'Comic not found'}), 404
    
    if 'reading_progress' not in db:
        db['reading_progress'] = {}
    
    progress = db['reading_progress'].get(comic_id, {})
    
    # Update progress fields
    if 'current_page' in req_data:
        progress['current_page'] = req_data['current_page']
    if 'total_pages' in req_data:
        progress['total_pages'] = req_data['total_pages']
    if 'percentage' in req_data:
        progress['percentage'] = req_data['percentage']
    if 'bookmarks' in req_data:
        progress['bookmarks'] = req_data['bookmarks']
    
    progress['last_read'] = datetime.utcnow().isoformat() + 'Z'
    
    db['reading_progress'][comic_id] = progress
    _save_comics_db(db)
    
    return jsonify({
        'ok': True,
        'message': 'Reading progress updated',
        'progress': progress
    })

@comics_enhanced_bp.route('/api/comics/series', methods=['GET'])
def get_series():
    """Get all comic series"""
    db = _load_comics_db()
    series = db.get('series', [])
    
    return jsonify({
        'ok': True,
        'series': series,
        'total': len(series)
    })

@comics_enhanced_bp.route('/api/comics/series', methods=['POST'])
def create_series():
    """Create a new comic series"""
    req_data = request.get_json(silent=True) or {}
    
    if not req_data.get('name'):
        return jsonify({'ok': False, 'error': 'Series name required'}), 400
    
    db = _load_comics_db()
    series = db.get('series', [])
    
    series_obj = {
        'id': f"series_{datetime.utcnow().timestamp()}",
        'name': req_data.get('name'),
        'publisher': req_data.get('publisher', ''),
        'description': req_data.get('description', ''),
        'start_year': req_data.get('start_year', ''),
        'end_year': req_data.get('end_year', ''),
        'created_at': datetime.utcnow().isoformat() + 'Z'
    }
    
    series.append(series_obj)
    db['series'] = series
    _save_comics_db(db)
    
    return jsonify({
        'ok': True,
        'message': 'Series created',
        'series': series_obj
    })

@comics_enhanced_bp.route('/api/comics/stats', methods=['GET'])
def get_reading_stats():
    """Get reading statistics"""
    db = _load_comics_db()
    comics = db.get('comics', [])
    reading_progress = db.get('reading_progress', {})
    
    total_comics = len(comics)
    comics_read = len([p for p in reading_progress.values() if p.get('percentage', 0) >= 100])
    comics_in_progress = len([p for p in reading_progress.values() if 0 < p.get('percentage', 0) < 100])
    
    # Calculate total pages read
    total_pages_read = sum(p.get('current_page', 0) for p in reading_progress.values())
    
    # Get favorite genres
    genre_counts = {}
    for comic in comics:
        for genre in comic.get('genres', []):
            genre_counts[genre] = genre_counts.get(genre, 0) + 1
    
    favorite_genres = sorted(genre_counts.items(), key=lambda x: x[1], reverse=True)[:5]
    
    return jsonify({
        'ok': True,
        'stats': {
            'total_comics': total_comics,
            'comics_read': comics_read,
            'comics_in_progress': comics_in_progress,
            'total_pages_read': total_pages_read,
            'favorite_genres': [{'genre': g[0], 'count': g[1]} for g in favorite_genres]
        }
    })
