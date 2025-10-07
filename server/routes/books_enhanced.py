from flask import Blueprint, jsonify, request, send_file
import os, json, re
from datetime import datetime
import requests

books_enhanced_bp = Blueprint('books_enhanced', __name__)

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
STO = os.path.join(ROOT, 'storage')
BOOKS_DIR = os.path.join(STO, 'books')
BOOKS_DB = os.path.join(STO, 'books_database.json')
BOOKS_CONFIG = os.path.join(STO, 'config', 'books_config.json')

# Google Books API Key (pre-configured)
GOOGLE_BOOKS_API_KEY = "AIzaSyA8OHWm7_imDTRCAEvC7rja2NZCInTw3d8"

def _load_config():
    """Load books configuration"""
    try:
        with open(BOOKS_CONFIG, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return {
            'google_books_enabled': True,
            'api_key': GOOGLE_BOOKS_API_KEY,
            'reading_preferences': {
                'default_font': 'Georgia',
                'default_font_size': 18,
                'default_line_height': 1.8,
                'default_theme': 'dark'
            },
            'library_path': BOOKS_DIR
        }

def _save_config(data):
    """Save books configuration"""
    os.makedirs(os.path.dirname(BOOKS_CONFIG), exist_ok=True)
    tmp = BOOKS_CONFIG + '.tmp'
    with open(tmp, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)
    os.replace(tmp, BOOKS_CONFIG)

def _load_books_db():
    """Load books database"""
    try:
        with open(BOOKS_DB, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return {'books': [], 'collections': [], 'reading_progress': {}}

def _save_books_db(data):
    """Save books database"""
    os.makedirs(os.path.dirname(BOOKS_DB), exist_ok=True)
    tmp = BOOKS_DB + '.tmp'
    with open(tmp, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)
    os.replace(tmp, BOOKS_DB)

def _search_google_books(query, max_results=10):
    """Search Google Books API"""
    config = _load_config()
    if not config.get('google_books_enabled'):
        return []
    
    api_key = config.get('api_key', GOOGLE_BOOKS_API_KEY)
    url = 'https://www.googleapis.com/books/v1/volumes'
    params = {
        'q': query,
        'maxResults': max_results,
        'key': api_key
    }
    
    try:
        response = requests.get(url, params=params, timeout=10)
        if response.status_code == 200:
            data = response.json()
            books = []
            
            for item in data.get('items', []):
                volume_info = item.get('volumeInfo', {})
                books.append({
                    'google_id': item.get('id'),
                    'title': volume_info.get('title'),
                    'authors': volume_info.get('authors', []),
                    'publisher': volume_info.get('publisher'),
                    'published_date': volume_info.get('publishedDate'),
                    'description': volume_info.get('description'),
                    'isbn': next((id['identifier'] for id in volume_info.get('industryIdentifiers', []) if id['type'] == 'ISBN_13'), None),
                    'page_count': volume_info.get('pageCount'),
                    'categories': volume_info.get('categories', []),
                    'language': volume_info.get('language'),
                    'thumbnail': volume_info.get('imageLinks', {}).get('thumbnail'),
                    'preview_link': volume_info.get('previewLink'),
                    'info_link': volume_info.get('infoLink')
                })
            
            return books
    except Exception as e:
        print(f"Google Books API error: {e}")
    
    return []

@books_enhanced_bp.route('/api/books/config', methods=['GET'])
def get_config():
    """Get books configuration"""
    config = _load_config()
    return jsonify({
        'ok': True,
        'config': config
    })

@books_enhanced_bp.route('/api/books/config', methods=['POST'])
def update_config():
    """Update books configuration"""
    req_data = request.get_json(silent=True) or {}
    
    config = _load_config()
    config.update(req_data)
    _save_config(config)
    
    return jsonify({
        'ok': True,
        'message': 'Configuration updated',
        'config': config
    })

@books_enhanced_bp.route('/api/books/library', methods=['GET'])
def get_library():
    """Get all books in library"""
    db = _load_books_db()
    books = db.get('books', [])
    
    # Apply filters
    author = request.args.get('author')
    genre = request.args.get('genre')
    collection = request.args.get('collection')
    
    if author:
        books = [b for b in books if author.lower() in ' '.join(b.get('authors', [])).lower()]
    if genre:
        books = [b for b in books if genre.lower() in ' '.join(b.get('categories', [])).lower()]
    if collection:
        books = [b for b in books if collection in b.get('collections', [])]
    
    return jsonify({
        'ok': True,
        'books': books,
        'total': len(books)
    })

@books_enhanced_bp.route('/api/books/search', methods=['GET'])
def search_books():
    """Search books via Google Books API"""
    query = request.args.get('q', '')
    max_results = int(request.args.get('max_results', 10))
    
    if not query:
        return jsonify({'ok': False, 'error': 'Query required'}), 400
    
    results = _search_google_books(query, max_results)
    
    return jsonify({
        'ok': True,
        'results': results,
        'total': len(results)
    })

@books_enhanced_bp.route('/api/books/add', methods=['POST'])
def add_book():
    """Add a book to library"""
    req_data = request.get_json(silent=True) or {}
    
    if not req_data.get('title'):
        return jsonify({'ok': False, 'error': 'Title required'}), 400
    
    db = _load_books_db()
    books = db.get('books', [])
    
    book = {
        'id': f"book_{datetime.utcnow().timestamp()}",
        'title': req_data.get('title'),
        'authors': req_data.get('authors', []),
        'publisher': req_data.get('publisher', ''),
        'published_date': req_data.get('published_date', ''),
        'description': req_data.get('description', ''),
        'isbn': req_data.get('isbn', ''),
        'page_count': req_data.get('page_count', 0),
        'categories': req_data.get('categories', []),
        'language': req_data.get('language', 'en'),
        'thumbnail': req_data.get('thumbnail', ''),
        'file_path': req_data.get('file_path', ''),
        'file_format': req_data.get('file_format', 'epub'),
        'collections': req_data.get('collections', []),
        'added_at': datetime.utcnow().isoformat() + 'Z',
        'rating': 0,
        'tags': []
    }
    
    books.append(book)
    db['books'] = books
    _save_books_db(db)
    
    return jsonify({
        'ok': True,
        'message': 'Book added to library',
        'book': book
    })

@books_enhanced_bp.route('/api/books/<book_id>', methods=['GET'])
def get_book(book_id):
    """Get book details"""
    db = _load_books_db()
    books = db.get('books', [])
    
    book = next((b for b in books if b.get('id') == book_id), None)
    
    if not book:
        return jsonify({'ok': False, 'error': 'Book not found'}), 404
    
    # Get reading progress
    progress = db.get('reading_progress', {}).get(book_id, {})
    
    return jsonify({
        'ok': True,
        'book': book,
        'progress': progress
    })

@books_enhanced_bp.route('/api/books/<book_id>', methods=['PUT'])
def update_book(book_id):
    """Update book metadata"""
    req_data = request.get_json(silent=True) or {}
    
    db = _load_books_db()
    books = db.get('books', [])
    
    book = next((b for b in books if b.get('id') == book_id), None)
    
    if not book:
        return jsonify({'ok': False, 'error': 'Book not found'}), 404
    
    # Update fields
    for key in ['title', 'authors', 'publisher', 'description', 'categories', 'tags', 'rating', 'collections']:
        if key in req_data:
            book[key] = req_data[key]
    
    book['updated_at'] = datetime.utcnow().isoformat() + 'Z'
    
    _save_books_db(db)
    
    return jsonify({
        'ok': True,
        'message': 'Book updated',
        'book': book
    })

@books_enhanced_bp.route('/api/books/<book_id>', methods=['DELETE'])
def delete_book(book_id):
    """Delete a book from library"""
    db = _load_books_db()
    books = db.get('books', [])
    
    original_count = len(books)
    books = [b for b in books if b.get('id') != book_id]
    
    if len(books) == original_count:
        return jsonify({'ok': False, 'error': 'Book not found'}), 404
    
    db['books'] = books
    
    # Remove reading progress
    if book_id in db.get('reading_progress', {}):
        del db['reading_progress'][book_id]
    
    _save_books_db(db)
    
    return jsonify({
        'ok': True,
        'message': 'Book deleted'
    })

@books_enhanced_bp.route('/api/books/<book_id>/progress', methods=['POST'])
def update_reading_progress(book_id):
    """Update reading progress"""
    req_data = request.get_json(silent=True) or {}
    
    db = _load_books_db()
    
    # Verify book exists
    books = db.get('books', [])
    book = next((b for b in books if b.get('id') == book_id), None)
    
    if not book:
        return jsonify({'ok': False, 'error': 'Book not found'}), 404
    
    if 'reading_progress' not in db:
        db['reading_progress'] = {}
    
    progress = db['reading_progress'].get(book_id, {})
    
    # Update progress fields
    if 'current_page' in req_data:
        progress['current_page'] = req_data['current_page']
    if 'total_pages' in req_data:
        progress['total_pages'] = req_data['total_pages']
    if 'percentage' in req_data:
        progress['percentage'] = req_data['percentage']
    if 'bookmarks' in req_data:
        progress['bookmarks'] = req_data['bookmarks']
    if 'notes' in req_data:
        progress['notes'] = req_data['notes']
    if 'highlights' in req_data:
        progress['highlights'] = req_data['highlights']
    
    progress['last_read'] = datetime.utcnow().isoformat() + 'Z'
    
    db['reading_progress'][book_id] = progress
    _save_books_db(db)
    
    return jsonify({
        'ok': True,
        'message': 'Reading progress updated',
        'progress': progress
    })

@books_enhanced_bp.route('/api/books/collections', methods=['GET'])
def get_collections():
    """Get all book collections"""
    db = _load_books_db()
    collections = db.get('collections', [])
    
    return jsonify({
        'ok': True,
        'collections': collections,
        'total': len(collections)
    })

@books_enhanced_bp.route('/api/books/collections', methods=['POST'])
def create_collection():
    """Create a new collection"""
    req_data = request.get_json(silent=True) or {}
    
    if not req_data.get('name'):
        return jsonify({'ok': False, 'error': 'Collection name required'}), 400
    
    db = _load_books_db()
    collections = db.get('collections', [])
    
    collection = {
        'id': f"collection_{datetime.utcnow().timestamp()}",
        'name': req_data.get('name'),
        'description': req_data.get('description', ''),
        'created_at': datetime.utcnow().isoformat() + 'Z'
    }
    
    collections.append(collection)
    db['collections'] = collections
    _save_books_db(db)
    
    return jsonify({
        'ok': True,
        'message': 'Collection created',
        'collection': collection
    })

@books_enhanced_bp.route('/api/books/recommendations', methods=['GET'])
def get_recommendations():
    """Get book recommendations based on reading history"""
    db = _load_books_db()
    books = db.get('books', [])
    reading_progress = db.get('reading_progress', {})
    
    # Get recently read books
    recently_read = []
    for book_id, progress in reading_progress.items():
        book = next((b for b in books if b.get('id') == book_id), None)
        if book:
            recently_read.append(book)
    
    # Sort by last read
    recently_read.sort(key=lambda x: reading_progress.get(x['id'], {}).get('last_read', ''), reverse=True)
    
    # Get categories from recently read books
    categories = set()
    for book in recently_read[:5]:
        categories.update(book.get('categories', []))
    
    # Find similar books
    recommendations = []
    for book in books:
        if book['id'] not in reading_progress:
            book_categories = set(book.get('categories', []))
            if book_categories & categories:
                recommendations.append(book)
    
    # Limit to 10 recommendations
    recommendations = recommendations[:10]
    
    return jsonify({
        'ok': True,
        'recommendations': recommendations,
        'total': len(recommendations)
    })

@books_enhanced_bp.route('/api/books/stats', methods=['GET'])
def get_reading_stats():
    """Get reading statistics"""
    db = _load_books_db()
    books = db.get('books', [])
    reading_progress = db.get('reading_progress', {})
    
    total_books = len(books)
    books_read = len([p for p in reading_progress.values() if p.get('percentage', 0) >= 100])
    books_in_progress = len([p for p in reading_progress.values() if 0 < p.get('percentage', 0) < 100])
    
    # Calculate total pages read
    total_pages_read = sum(p.get('current_page', 0) for p in reading_progress.values())
    
    # Get favorite genres
    genre_counts = {}
    for book in books:
        for genre in book.get('categories', []):
            genre_counts[genre] = genre_counts.get(genre, 0) + 1
    
    favorite_genres = sorted(genre_counts.items(), key=lambda x: x[1], reverse=True)[:5]
    
    return jsonify({
        'ok': True,
        'stats': {
            'total_books': total_books,
            'books_read': books_read,
            'books_in_progress': books_in_progress,
            'total_pages_read': total_pages_read,
            'favorite_genres': [{'genre': g[0], 'count': g[1]} for g in favorite_genres]
        }
    })
