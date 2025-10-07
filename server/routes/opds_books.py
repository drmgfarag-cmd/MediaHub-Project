from flask import Blueprint, jsonify, request, Response, send_file
import os, json, re
from datetime import datetime
import xml.etree.ElementTree as ET
from xml.dom import minidom
import requests

opds_books_bp = Blueprint('opds_books', __name__)

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
STO = os.path.join(ROOT, 'storage')
BOOKS_DIR = os.path.join(STO, 'books')
BOOKS_INDEX = os.path.join(STO, 'books_index.json')
OPDS_CONFIG = os.path.join(STO, 'config', 'opds.json')

def _load_config():
    """Load OPDS configuration"""
    try:
        with open(OPDS_CONFIG, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return {
            'title': 'MediaHub Books',
            'author': 'MediaHub',
            'calibre_server': {
                'enabled': False,
                'url': 'http://localhost:8080',
                'fts_passthrough': False
            },
            'items_per_page': 50
        }

def _save_config(data):
    """Save OPDS configuration"""
    os.makedirs(os.path.dirname(OPDS_CONFIG), exist_ok=True)
    tmp = OPDS_CONFIG + '.tmp'
    with open(tmp, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)
    os.replace(tmp, OPDS_CONFIG)

def _load_books_index():
    """Load books index"""
    try:
        with open(BOOKS_INDEX, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return {'books': []}

def _save_books_index(data):
    """Save books index"""
    os.makedirs(os.path.dirname(BOOKS_INDEX), exist_ok=True)
    tmp = BOOKS_INDEX + '.tmp'
    with open(tmp, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)
    os.replace(tmp, BOOKS_INDEX)

def _generate_opds_feed(title, books, self_url, config):
    """Generate OPDS Atom feed"""
    # Create feed
    feed = ET.Element('feed', xmlns='http://www.w3.org/2005/Atom')
    feed.set('xmlns:dc', 'http://purl.org/dc/terms/')
    feed.set('xmlns:opds', 'http://opds-spec.org/2010/catalog')
    
    # Feed metadata
    ET.SubElement(feed, 'id').text = self_url
    ET.SubElement(feed, 'title').text = title
    ET.SubElement(feed, 'updated').text = datetime.utcnow().isoformat() + 'Z'
    
    author = ET.SubElement(feed, 'author')
    ET.SubElement(author, 'name').text = config.get('author', 'MediaHub')
    
    # Self link
    link_self = ET.SubElement(feed, 'link')
    link_self.set('rel', 'self')
    link_self.set('href', self_url)
    link_self.set('type', 'application/atom+xml;profile=opds-catalog;kind=acquisition')
    
    # Add books as entries
    for book in books:
        entry = ET.SubElement(feed, 'entry')
        
        ET.SubElement(entry, 'id').text = f"urn:uuid:{book.get('id', 'unknown')}"
        ET.SubElement(entry, 'title').text = book.get('title', 'Unknown')
        ET.SubElement(entry, 'updated').text = book.get('updated', datetime.utcnow().isoformat() + 'Z')
        
        # Author
        if book.get('author'):
            author_elem = ET.SubElement(entry, 'author')
            ET.SubElement(author_elem, 'name').text = book['author']
        
        # Summary
        if book.get('summary'):
            ET.SubElement(entry, 'summary').text = book['summary']
        
        # Cover link
        if book.get('cover_url'):
            link_cover = ET.SubElement(entry, 'link')
            link_cover.set('rel', 'http://opds-spec.org/image')
            link_cover.set('href', book['cover_url'])
            link_cover.set('type', 'image/jpeg')
        
        # Download links
        if book.get('download_url'):
            link_download = ET.SubElement(entry, 'link')
            link_download.set('rel', 'http://opds-spec.org/acquisition')
            link_download.set('href', book['download_url'])
            link_download.set('type', book.get('format', 'application/epub+zip'))
    
    # Format XML nicely
    xml_str = ET.tostring(feed, encoding='utf-8')
    dom = minidom.parseString(xml_str)
    return dom.toprettyxml(indent='  ', encoding='utf-8').decode('utf-8')

@opds_books_bp.route('/opds', methods=['GET'])
def opds_root():
    """OPDS root catalog"""
    config = _load_config()
    
    feed = ET.Element('feed', xmlns='http://www.w3.org/2005/Atom')
    feed.set('xmlns:opds', 'http://opds-spec.org/2010/catalog')
    
    ET.SubElement(feed, 'id').text = 'urn:uuid:mediahub-opds-root'
    ET.SubElement(feed, 'title').text = config.get('title', 'MediaHub Books')
    ET.SubElement(feed, 'updated').text = datetime.utcnow().isoformat() + 'Z'
    
    author = ET.SubElement(feed, 'author')
    ET.SubElement(author, 'name').text = config.get('author', 'MediaHub')
    
    # Self link
    link_self = ET.SubElement(feed, 'link')
    link_self.set('rel', 'self')
    link_self.set('href', '/opds')
    link_self.set('type', 'application/atom+xml;profile=opds-catalog;kind=navigation')
    
    # All books entry
    entry_all = ET.SubElement(feed, 'entry')
    ET.SubElement(entry_all, 'id').text = 'urn:uuid:mediahub-opds-all'
    ET.SubElement(entry_all, 'title').text = 'All Books'
    ET.SubElement(entry_all, 'updated').text = datetime.utcnow().isoformat() + 'Z'
    link_all = ET.SubElement(entry_all, 'link')
    link_all.set('rel', 'subsection')
    link_all.set('href', '/opds/all')
    link_all.set('type', 'application/atom+xml;profile=opds-catalog;kind=acquisition')
    
    # Recent books entry
    entry_recent = ET.SubElement(feed, 'entry')
    ET.SubElement(entry_recent, 'id').text = 'urn:uuid:mediahub-opds-recent'
    ET.SubElement(entry_recent, 'title').text = 'Recent Additions'
    ET.SubElement(entry_recent, 'updated').text = datetime.utcnow().isoformat() + 'Z'
    link_recent = ET.SubElement(entry_recent, 'link')
    link_recent.set('rel', 'subsection')
    link_recent.set('href', '/opds/recent')
    link_recent.set('type', 'application/atom+xml;profile=opds-catalog;kind=acquisition')
    
    # Search entry
    entry_search = ET.SubElement(feed, 'entry')
    ET.SubElement(entry_search, 'id').text = 'urn:uuid:mediahub-opds-search'
    ET.SubElement(entry_search, 'title').text = 'Search'
    ET.SubElement(entry_search, 'updated').text = datetime.utcnow().isoformat() + 'Z'
    link_search = ET.SubElement(entry_search, 'link')
    link_search.set('rel', 'search')
    link_search.set('href', '/opds/search?q={searchTerms}')
    link_search.set('type', 'application/atom+xml;profile=opds-catalog;kind=acquisition')
    
    xml_str = ET.tostring(feed, encoding='utf-8')
    dom = minidom.parseString(xml_str)
    xml_output = dom.toprettyxml(indent='  ', encoding='utf-8').decode('utf-8')
    
    return Response(xml_output, mimetype='application/atom+xml;profile=opds-catalog')

@opds_books_bp.route('/opds/all', methods=['GET'])
def opds_all_books():
    """OPDS feed of all books"""
    config = _load_config()
    index = _load_books_index()
    books = index.get('books', [])
    
    # Pagination
    page = int(request.args.get('page', 1))
    per_page = config.get('items_per_page', 50)
    start = (page - 1) * per_page
    end = start + per_page
    
    paginated_books = books[start:end]
    
    feed_xml = _generate_opds_feed(
        'All Books',
        paginated_books,
        f'/opds/all?page={page}',
        config
    )
    
    return Response(feed_xml, mimetype='application/atom+xml;profile=opds-catalog')

@opds_books_bp.route('/opds/recent', methods=['GET'])
def opds_recent_books():
    """OPDS feed of recent books"""
    config = _load_config()
    index = _load_books_index()
    books = index.get('books', [])
    
    # Sort by updated date
    sorted_books = sorted(
        books,
        key=lambda x: x.get('updated', ''),
        reverse=True
    )
    
    # Get recent (last 50)
    recent_books = sorted_books[:50]
    
    feed_xml = _generate_opds_feed(
        'Recent Additions',
        recent_books,
        '/opds/recent',
        config
    )
    
    return Response(feed_xml, mimetype='application/atom+xml;profile=opds-catalog')

@opds_books_bp.route('/opds/search', methods=['GET'])
def opds_search():
    """
    OPDS search
    Query param: q (search term)
    """
    query = request.args.get('q', '').lower()
    
    if not query:
        return Response('<?xml version="1.0"?><feed></feed>', mimetype='application/atom+xml')
    
    config = _load_config()
    
    # Check if Calibre FTS pass-through is enabled
    if config.get('calibre_server', {}).get('enabled') and config.get('calibre_server', {}).get('fts_passthrough'):
        # Pass-through to Calibre server
        calibre_url = config['calibre_server']['url']
        try:
            response = requests.get(f"{calibre_url}/opds/search?q={query}", timeout=10)
            if response.status_code == 200:
                return Response(response.content, mimetype='application/atom+xml;profile=opds-catalog')
        except Exception:
            pass
    
    # Local search
    index = _load_books_index()
    books = index.get('books', [])
    
    # Simple search in title and author
    results = []
    for book in books:
        title = book.get('title', '').lower()
        author = book.get('author', '').lower()
        
        if query in title or query in author:
            results.append(book)
    
    feed_xml = _generate_opds_feed(
        f'Search Results for "{query}"',
        results,
        f'/opds/search?q={query}',
        config
    )
    
    return Response(feed_xml, mimetype='application/atom+xml;profile=opds-catalog')

@opds_books_bp.route('/api/books/config', methods=['GET'])
def get_config():
    """Get OPDS configuration"""
    config = _load_config()
    return jsonify({
        'ok': True,
        'config': config
    })

@opds_books_bp.route('/api/books/config', methods=['POST'])
def set_config():
    """
    Update OPDS configuration
    Body: {
        "title": "My Books",
        "calibre_server": {
            "enabled": true,
            "url": "http://localhost:8080",
            "fts_passthrough": true
        }
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

@opds_books_bp.route('/api/books/index', methods=['GET'])
def get_books_index():
    """Get books index"""
    index = _load_books_index()
    return jsonify({
        'ok': True,
        'total_books': len(index.get('books', [])),
        'books': index.get('books', [])
    })

@opds_books_bp.route('/api/books/add', methods=['POST'])
def add_book():
    """
    Add a book to the index
    Body: {
        "title": "Book Title",
        "author": "Author Name",
        "summary": "Book description",
        "cover_url": "http://...",
        "download_url": "/books/file.epub",
        "format": "application/epub+zip"
    }
    """
    req_data = request.get_json(silent=True) or {}
    
    if not req_data.get('title'):
        return jsonify({'ok': False, 'error': 'title required'}), 400
    
    index = _load_books_index()
    books = index.get('books', [])
    
    book = {
        'id': f"book_{datetime.utcnow().timestamp()}",
        'title': req_data.get('title'),
        'author': req_data.get('author', 'Unknown'),
        'summary': req_data.get('summary', ''),
        'cover_url': req_data.get('cover_url', ''),
        'download_url': req_data.get('download_url', ''),
        'format': req_data.get('format', 'application/epub+zip'),
        'updated': datetime.utcnow().isoformat() + 'Z'
    }
    
    books.append(book)
    index['books'] = books
    _save_books_index(index)
    
    return jsonify({
        'ok': True,
        'message': 'Book added',
        'book': book
    })

@opds_books_bp.route('/api/books/<book_id>', methods=['DELETE'])
def delete_book(book_id):
    """Delete a book from the index"""
    index = _load_books_index()
    books = index.get('books', [])
    
    original_count = len(books)
    books = [b for b in books if b.get('id') != book_id]
    
    if len(books) == original_count:
        return jsonify({'ok': False, 'error': 'Book not found'}), 404
    
    index['books'] = books
    _save_books_index(index)
    
    return jsonify({
        'ok': True,
        'message': 'Book deleted'
    })

@opds_books_bp.route('/api/books/calibre/test', methods=['GET'])
def test_calibre_connection():
    """Test connection to Calibre server"""
    config = _load_config()
    calibre_config = config.get('calibre_server', {})
    
    if not calibre_config.get('enabled'):
        return jsonify({
            'ok': False,
            'error': 'Calibre server not enabled'
        }), 400
    
    calibre_url = calibre_config.get('url')
    
    try:
        response = requests.get(f"{calibre_url}/opds", timeout=10)
        if response.status_code == 200:
            return jsonify({
                'ok': True,
                'message': 'Calibre server connection successful',
                'calibre_url': calibre_url
            })
        else:
            return jsonify({
                'ok': False,
                'error': f'Calibre server returned status {response.status_code}'
            }), 500
    except Exception as e:
        return jsonify({
            'ok': False,
            'error': f'Failed to connect to Calibre server: {str(e)}'
        }), 500
