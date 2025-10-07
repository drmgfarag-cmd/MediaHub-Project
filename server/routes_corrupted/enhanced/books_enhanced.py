"""
Enhanced Books Category Implementation
Complete EPUB reader, PDF viewer, Google Books integration, and reading management
"""

from flask import Blueprint, request, jsonify, send_file, Response
import os
import json
import sqlite3
import zipfile
import xml.etree.ElementTree as ET
from pathlib import Path
import requests
import fitz  # PyMuPDF for PDF handling
import ebooklib
from ebooklib import epub
import base64
from datetime import datetime
import threading
from typing import Dict, List, Any, Optional, Tuple
import re
import logging

books_enhanced_bp = Blueprint('books_enhanced', __name__)
logger = logging.getLogger(__name__)

class BooksManager:
    """Comprehensive books management system"""
    
    def __init__(self, db_connection, db_lock, api_manager):
        self.db = db_connection
        self.db_lock = db_lock
        self.api_manager = api_manager
        self.reading_sessions = {}
        self.setup_database()
    
    def setup_database(self):
        """Initialize books-specific database tables"""
        with self.db_lock:
            cursor = self.db.cursor()
            
            # Books metadata table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS books_metadata (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    file_path TEXT UNIQUE NOT NULL,
                    title TEXT,
                    author TEXT,
                    isbn TEXT,
                    publisher TEXT,
                    published_date TEXT,
                    description TEXT,
                    cover_image TEXT,
                    page_count INTEGER,
                    language TEXT,
                    series TEXT,
                    series_number INTEGER,
                    genre TEXT,
                    google_books_id TEXT,
                    added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Reading progress table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS reading_progress (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    book_id INTEGER,
                    user_profile TEXT DEFAULT 'default',
                    current_page INTEGER DEFAULT 0,
                    total_pages INTEGER DEFAULT 0,
                    progress_percentage REAL DEFAULT 0.0,
                    reading_time_minutes INTEGER DEFAULT 0,
                    last_read TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    completed BOOLEAN DEFAULT 0,
                    FOREIGN KEY (book_id) REFERENCES books_metadata (id)
                )
            """)
            
            # Bookmarks and annotations table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS book_annotations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    book_id INTEGER,
                    user_profile TEXT DEFAULT 'default',
                    type TEXT NOT NULL, -- 'bookmark', 'highlight', 'note'
                    page_number INTEGER,
                    position_data TEXT, -- JSON with precise position info
                    content TEXT, -- highlighted text or note content
                    annotation_text TEXT, -- user's note
                    color TEXT DEFAULT '#ffff00',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (book_id) REFERENCES books_metadata (id)
                )
            """)
            
            # Reading lists table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS reading_lists (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    user_profile TEXT DEFAULT 'default',
                    description TEXT,
                    book_ids TEXT, -- JSON array of book IDs
                    is_public BOOLEAN DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            self.db.commit()
    
    def scan_books_directory(self, directory_path: str) -> Dict[str, Any]:
        """Scan directory for book files and extract metadata"""
        supported_formats = {'.epub', '.pdf', '.mobi', '.azw', '.azw3', '.txt', '.cbr', '.cbz'}
        found_books = []
        errors = []
        
        try:
            directory = Path(directory_path)
            if not directory.exists():
                return {'success': False, 'error': 'Directory does not exist'}
            
            for file_path in directory.rglob('*'):
                if file_path.suffix.lower() in supported_formats:
                    try:
                        book_info = self.extract_book_metadata(str(file_path))
                        if book_info:
                            found_books.append(book_info)
                    except Exception as e:
                        errors.append(f"Error processing {file_path.name}: {str(e)}")
            
            return {
                'success': True,
                'books_found': len(found_books),
                'books': found_books,
                'errors': errors
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def extract_book_metadata(self, file_path: str) -> Optional[Dict[str, Any]]:
        """Extract metadata from book file"""
        file_path = Path(file_path)
        
        if not file_path.exists():
            return None
        
        metadata = {
            'file_path': str(file_path),
            'filename': file_path.name,
            'format': file_path.suffix.lower(),
            'size': file_path.stat().st_size,
            'modified': datetime.fromtimestamp(file_path.stat().st_mtime).isoformat()
        }
        
        try:
            if file_path.suffix.lower() == '.epub':
                metadata.update(self._extract_epub_metadata(file_path))
            elif file_path.suffix.lower() == '.pdf':
                metadata.update(self._extract_pdf_metadata(file_path))
            elif file_path.suffix.lower() in ['.mobi', '.azw', '.azw3']:
                metadata.update(self._extract_kindle_metadata(file_path))
            elif file_path.suffix.lower() == '.txt':
                metadata.update(self._extract_text_metadata(file_path))
            elif file_path.suffix.lower() in ['.cbr', '.cbz']:
                metadata.update(self._extract_comic_metadata(file_path))
        except Exception as e:
            logger.error(f"Error extracting metadata from {file_path}: {e}")
            metadata['extraction_error'] = str(e)
        
        return metadata
    
    def _extract_epub_metadata(self, file_path: Path) -> Dict[str, Any]:
        """Extract metadata from EPUB file"""
        metadata = {}
        
        try:
            book = epub.read_epub(str(file_path))
            
            # Basic metadata
            metadata['title'] = book.get_metadata('DC', 'title')[0][0] if book.get_metadata('DC', 'title') else file_path.stem
            metadata['author'] = book.get_metadata('DC', 'creator')[0][0] if book.get_metadata('DC', 'creator') else 'Unknown'
            metadata['publisher'] = book.get_metadata('DC', 'publisher')[0][0] if book.get_metadata('DC', 'publisher') else ''
            metadata['language'] = book.get_metadata('DC', 'language')[0][0] if book.get_metadata('DC', 'language') else 'en'
            metadata['description'] = book.get_metadata('DC', 'description')[0][0] if book.get_metadata('DC', 'description') else ''
            
            # ISBN
            isbn_data = book.get_metadata('DC', 'identifier')
            for identifier in isbn_data:
                if 'isbn' in identifier[0].lower():
                    metadata['isbn'] = identifier[0]
                    break
            
            # Extract cover image
            cover_item = None
            for item in book.get_items():
                if item.get_type() == ebooklib.ITEM_COVER:
                    cover_item = item
                    break
            
            if cover_item:
                cover_data = base64.b64encode(cover_item.get_content()).decode('utf-8')
                metadata['cover_image'] = f"data:image/jpeg;base64,{cover_data}"
            
            # Count pages/chapters
            spine_items = [item for item in book.get_items() if item.get_type() == ebooklib.ITEM_DOCUMENT]
            metadata['chapter_count'] = len(spine_items)
            metadata['page_count'] = len(spine_items)  # Approximate
            
        except Exception as e:
            logger.error(f"EPUB metadata extraction error: {e}")
            metadata['title'] = file_path.stem
            metadata['author'] = 'Unknown'
        
        return metadata
    
    def _extract_pdf_metadata(self, file_path: Path) -> Dict[str, Any]:
        """Extract metadata from PDF file"""
        metadata = {}
        
        try:
            doc = fitz.open(str(file_path))
            pdf_metadata = doc.metadata
            
            metadata['title'] = pdf_metadata.get('title', file_path.stem)
            metadata['author'] = pdf_metadata.get('author', 'Unknown')
            metadata['creator'] = pdf_metadata.get('creator', '')
            metadata['producer'] = pdf_metadata.get('producer', '')
            metadata['subject'] = pdf_metadata.get('subject', '')
            metadata['page_count'] = doc.page_count
            
            # Extract first page as cover
            if doc.page_count > 0:
                page = doc[0]
                pix = page.get_pixmap(matrix=fitz.Matrix(0.5, 0.5))  # Scale down
                cover_data = base64.b64encode(pix.tobytes("png")).decode('utf-8')
                metadata['cover_image'] = f"data:image/png;base64,{cover_data}"
            
            doc.close()
            
        except Exception as e:
            logger.error(f"PDF metadata extraction error: {e}")
            metadata['title'] = file_path.stem
            metadata['author'] = 'Unknown'
        
        return metadata
    
    def _extract_kindle_metadata(self, file_path: Path) -> Dict[str, Any]:
        """Extract metadata from Kindle files (basic implementation)"""
        # This would require additional libraries like python-kindle
        return {
            'title': file_path.stem,
            'author': 'Unknown',
            'format_note': 'Kindle format - limited metadata extraction'
        }
    
    def _extract_text_metadata(self, file_path: Path) -> Dict[str, Any]:
        """Extract metadata from text file"""
        metadata = {
            'title': file_path.stem,
            'author': 'Unknown',
            'format': 'Plain Text'
        }
        
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read(1000)  # Read first 1000 chars
                lines = content.split('\n')
                metadata['line_count'] = len(lines)
                metadata['estimated_pages'] = max(1, len(content) // 2000)  # Rough estimate
        except Exception as e:
            logger.error(f"Text metadata extraction error: {e}")
        
        return metadata
    
    def _extract_comic_metadata(self, file_path: Path) -> Dict[str, Any]:
        """Extract metadata from comic book files"""
        metadata = {
            'title': file_path.stem,
            'author': 'Unknown',
            'format': 'Comic Book'
        }
        
        try:
            if file_path.suffix.lower() == '.cbz':
                with zipfile.ZipFile(file_path, 'r') as zip_file:
                    image_files = [f for f in zip_file.namelist() if f.lower().endswith(('.jpg', '.jpeg', '.png', '.gif'))]
                    metadata['page_count'] = len(image_files)
                    
                    # Try to extract first image as cover
                    if image_files:
                        first_image = sorted(image_files)[0]
                        cover_data = base64.b64encode(zip_file.read(first_image)).decode('utf-8')
                        ext = first_image.split('.')[-1].lower()
                        metadata['cover_image'] = f"data:image/{ext};base64,{cover_data}"
        except Exception as e:
            logger.error(f"Comic metadata extraction error: {e}")
        
        return metadata
    
    def enhance_metadata_with_google_books(self, book_metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Enhance book metadata using Google Books API"""
        try:
            api_key = self.api_manager.get_key('google_books')
            if not api_key:
                return book_metadata
            
            # Search by ISBN first, then title+author
            search_queries = []
            
            if book_metadata.get('isbn'):
                search_queries.append(f"isbn:{book_metadata['isbn']}")
            
            if book_metadata.get('title') and book_metadata.get('author'):
                search_queries.append(f"intitle:{book_metadata['title']}+inauthor:{book_metadata['author']}")
            elif book_metadata.get('title'):
                search_queries.append(f"intitle:{book_metadata['title']}")
            
            for query in search_queries:
                url = f"https://www.googleapis.com/books/v1/volumes"
                params = {
                    'q': query,
                    'key': api_key,
                    'maxResults': 1
                }
                
                response = requests.get(url, params=params, timeout=10)
                if response.status_code == 200:
                    data = response.json()
                    
                    if data.get('totalItems', 0) > 0:
                        volume = data['items'][0]
                        volume_info = volume.get('volumeInfo', {})
                        
                        # Enhance metadata with Google Books data
                        enhanced = book_metadata.copy()
                        enhanced.update({
                            'google_books_id': volume.get('id'),
                            'title': volume_info.get('title', book_metadata.get('title')),
                            'author': ', '.join(volume_info.get('authors', [])) or book_metadata.get('author'),
                            'publisher': volume_info.get('publisher', book_metadata.get('publisher')),
                            'published_date': volume_info.get('publishedDate', ''),
                            'description': volume_info.get('description', book_metadata.get('description')),
                            'page_count': volume_info.get('pageCount', book_metadata.get('page_count')),
                            'language': volume_info.get('language', book_metadata.get('language')),
                            'categories': volume_info.get('categories', []),
                            'average_rating': volume_info.get('averageRating'),
                            'ratings_count': volume_info.get('ratingsCount')
                        })
                        
                        # Get better cover image if available
                        image_links = volume_info.get('imageLinks', {})
                        if image_links.get('large'):
                            enhanced['cover_url'] = image_links['large']
                        elif image_links.get('medium'):
                            enhanced['cover_url'] = image_links['medium']
                        elif image_links.get('thumbnail'):
                            enhanced['cover_url'] = image_links['thumbnail']
                        
                        # Extract ISBN if not present
                        if not enhanced.get('isbn'):
                            for identifier in volume_info.get('industryIdentifiers', []):
                                if identifier.get('type') in ['ISBN_13', 'ISBN_10']:
                                    enhanced['isbn'] = identifier.get('identifier')
                                    break
                        
                        return enhanced
        
        except Exception as e:
            logger.error(f"Google Books API error: {e}")
        
        return book_metadata
    
    def save_book_metadata(self, metadata: Dict[str, Any]) -> int:
        """Save book metadata to database"""
        with self.db_lock:
            cursor = self.db.cursor()
            
            # Check if book already exists
            cursor.execute("SELECT id FROM books_metadata WHERE file_path = ?", (metadata['file_path'],))
            existing = cursor.fetchone()
            
            if existing:
                # Update existing record
                cursor.execute("""
                    UPDATE books_metadata SET
                        title = ?, author = ?, isbn = ?, publisher = ?,
                        published_date = ?, description = ?, cover_image = ?,
                        page_count = ?, language = ?, series = ?, series_number = ?,
                        genre = ?, google_books_id = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                """, (
                    metadata.get('title'), metadata.get('author'), metadata.get('isbn'),
                    metadata.get('publisher'), metadata.get('published_date'),
                    metadata.get('description'), metadata.get('cover_image'),
                    metadata.get('page_count'), metadata.get('language'),
                    metadata.get('series'), metadata.get('series_number'),
                    metadata.get('genre'), metadata.get('google_books_id'),
                    existing[0]
                ))
                book_id = existing[0]
            else:
                # Insert new record
                cursor.execute("""
                    INSERT INTO books_metadata 
                    (file_path, title, author, isbn, publisher, published_date,
                     description, cover_image, page_count, language, series,
                     series_number, genre, google_books_id)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    metadata['file_path'], metadata.get('title'), metadata.get('author'),
                    metadata.get('isbn'), metadata.get('publisher'),
                    metadata.get('published_date'), metadata.get('description'),
                    metadata.get('cover_image'), metadata.get('page_count'),
                    metadata.get('language'), metadata.get('series'),
                    metadata.get('series_number'), metadata.get('genre'),
                    metadata.get('google_books_id')
                ))
                book_id = cursor.lastrowid
            
            self.db.commit()
            return book_id
    
    def get_book_content(self, book_id: int, page: int = 0) -> Dict[str, Any]:
        """Get book content for reading"""
        with self.db_lock:
            cursor = self.db.cursor()
            cursor.execute("SELECT file_path, title FROM books_metadata WHERE id = ?", (book_id,))
            book = cursor.fetchone()
            
            if not book:
                return {'success': False, 'error': 'Book not found'}
            
            file_path = Path(book[0])
            if not file_path.exists():
                return {'success': False, 'error': 'Book file not found'}
            
            try:
                if file_path.suffix.lower() == '.epub':
                    return self._get_epub_content(file_path, page)
                elif file_path.suffix.lower() == '.pdf':
                    return self._get_pdf_content(file_path, page)
                elif file_path.suffix.lower() == '.txt':
                    return self._get_text_content(file_path, page)
                elif file_path.suffix.lower() in ['.cbr', '.cbz']:
                    return self._get_comic_content(file_path, page)
                else:
                    return {'success': False, 'error': 'Unsupported format for reading'}
            except Exception as e:
                return {'success': False, 'error': str(e)}
    
    def _get_epub_content(self, file_path: Path, chapter: int = 0) -> Dict[str, Any]:
        """Get EPUB content for reading"""
        try:
            book = epub.read_epub(str(file_path))
            spine_items = [item for item in book.get_items() if item.get_type() == ebooklib.ITEM_DOCUMENT]
            
            if chapter >= len(spine_items):
                chapter = 0
            
            if not spine_items:
                return {'success': False, 'error': 'No readable content found'}
            
            current_item = spine_items[chapter]
            content = current_item.get_content().decode('utf-8')
            
            # Extract text content and clean HTML
            import re
            text_content = re.sub(r'<[^>]+>', '', content)
            text_content = re.sub(r'\s+', ' ', text_content).strip()
            
            return {
                'success': True,
                'content': content,  # HTML content
                'text_content': text_content,  # Plain text
                'current_chapter': chapter,
                'total_chapters': len(spine_items),
                'chapter_title': current_item.get_name(),
                'format': 'epub'
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _get_pdf_content(self, file_path: Path, page: int = 0) -> Dict[str, Any]:
        """Get PDF content for reading"""
        try:
            doc = fitz.open(str(file_path))
            
            if page >= doc.page_count:
                page = 0
            
            current_page = doc[page]
            
            # Get page as image
            pix = current_page.get_pixmap(matrix=fitz.Matrix(1.5, 1.5))  # Higher resolution
            image_data = base64.b64encode(pix.tobytes("png")).decode('utf-8')
            
            # Extract text
            text_content = current_page.get_text()
            
            doc.close()
            
            return {
                'success': True,
                'image_data': f"data:image/png;base64,{image_data}",
                'text_content': text_content,
                'current_page': page,
                'total_pages': doc.page_count,
                'format': 'pdf'
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _get_text_content(self, file_path: Path, page: int = 0) -> Dict[str, Any]:
        """Get text file content for reading"""
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            # Paginate text (approximately 2000 characters per page)
            page_size = 2000
            total_pages = max(1, len(content) // page_size)
            
            if page >= total_pages:
                page = 0
            
            start = page * page_size
            end = min(start + page_size, len(content))
            page_content = content[start:end]
            
            return {
                'success': True,
                'content': page_content,
                'text_content': page_content,
                'current_page': page,
                'total_pages': total_pages,
                'format': 'text'
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _get_comic_content(self, file_path: Path, page: int = 0) -> Dict[str, Any]:
        """Get comic book content for reading"""
        try:
            if file_path.suffix.lower() == '.cbz':
                with zipfile.ZipFile(file_path, 'r') as zip_file:
                    image_files = sorted([f for f in zip_file.namelist() 
                                        if f.lower().endswith(('.jpg', '.jpeg', '.png', '.gif'))])
                    
                    if page >= len(image_files):
                        page = 0
                    
                    if not image_files:
                        return {'success': False, 'error': 'No images found in comic'}
                    
                    current_image = image_files[page]
                    image_data = base64.b64encode(zip_file.read(current_image)).decode('utf-8')
                    ext = current_image.split('.')[-1].lower()
                    
                    return {
                        'success': True,
                        'image_data': f"data:image/{ext};base64,{image_data}",
                        'current_page': page,
                        'total_pages': len(image_files),
                        'format': 'comic'
                    }
            else:
                return {'success': False, 'error': 'CBR format not yet supported'}
        except Exception as e:
            return {'success': False, 'error': str(e)}

# Initialize books manager
books_manager = None

def get_books_manager():
    """Get or create books manager instance"""
    global books_manager
    if books_manager is None:
        from flask import current_app
        books_manager = BooksManager(
            current_app.config['db_connection'],
            current_app.config['db_lock'],
            current_app.config['api_manager']
        )
    return books_manager

# Flask routes
@books_enhanced_bp.route('/books/scan', methods=['POST'])
def scan_books():
    """Scan directory for book files"""
    try:
        data = request.json
        directory = data.get('directory')
        
        if not directory:
            return jsonify({'success': False, 'error': 'Directory path required'}), 400
        
        manager = get_books_manager()
        result = manager.scan_books_directory(directory)
        
        # Enhance metadata with Google Books API for found books
        if result['success'] and 'books' in result:
            enhanced_books = []
            for book in result['books']:
                enhanced = manager.enhance_metadata_with_google_books(book)
                book_id = manager.save_book_metadata(enhanced)
                enhanced['id'] = book_id
                enhanced_books.append(enhanced)
            
            result['books'] = enhanced_books
        
        return jsonify(result)
    except Exception as e:
        logger.error(f"Books scan error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@books_enhanced_bp.route('/books/list', methods=['GET'])
def list_books():
    """List all books in library"""
    try:
        manager = get_books_manager()
        
        with manager.db_lock:
            cursor = manager.db.cursor()
            cursor.execute("""
                SELECT id, title, author, cover_image, page_count, 
                       language, series, genre, added_at
                FROM books_metadata 
                ORDER BY title
            """)
            
            books = []
            for row in cursor.fetchall():
                books.append({
                    'id': row[0],
                    'title': row[1],
                    'author': row[2],
                    'cover_image': row[3],
                    'page_count': row[4],
                    'language': row[5],
                    'series': row[6],
                    'genre': row[7],
                    'added_at': row[8]
                })
        
        return jsonify({'success': True, 'books': books})
    except Exception as e:
        logger.error(f"Books list error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@books_enhanced_bp.route('/books/<int:book_id>/read', methods=['GET'])
def read_book():
    """Get book content for reading"""
    try:
        book_id = request.view_args['book_id']
        page = request.args.get('page', 0, type=int)
        
        manager = get_books_manager()
        result = manager.get_book_content(book_id, page)
        
        return jsonify(result)
    except Exception as e:
        logger.error(f"Book read error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@books_enhanced_bp.route('/books/<int:book_id>/progress', methods=['POST'])
def update_reading_progress():
    """Update reading progress"""
    try:
        book_id = request.view_args['book_id']
        data = request.json
        profile = request.headers.get('X-Profile', 'default')
        
        manager = get_books_manager()
        
        with manager.db_lock:
            cursor = manager.db.cursor()
            
            # Update or insert progress
            cursor.execute("""
                INSERT OR REPLACE INTO reading_progress 
                (book_id, user_profile, current_page, total_pages, 
                 progress_percentage, reading_time_minutes, completed)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                book_id, profile, data.get('current_page', 0),
                data.get('total_pages', 0), data.get('progress_percentage', 0.0),
                data.get('reading_time_minutes', 0), data.get('completed', False)
            ))
            
            manager.db.commit()
        
        return jsonify({'success': True})
    except Exception as e:
        logger.error(f"Progress update error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@books_enhanced_bp.route('/books/<int:book_id>/bookmark', methods=['POST'])
def add_bookmark():
    """Add bookmark or annotation"""
    try:
        book_id = request.view_args['book_id']
        data = request.json
        profile = request.headers.get('X-Profile', 'default')
        
        manager = get_books_manager()
        
        with manager.db_lock:
            cursor = manager.db.cursor()
            cursor.execute("""
                INSERT INTO book_annotations 
                (book_id, user_profile, type, page_number, position_data,
                 content, annotation_text, color)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                book_id, profile, data.get('type', 'bookmark'),
                data.get('page_number'), json.dumps(data.get('position_data', {})),
                data.get('content', ''), data.get('annotation_text', ''),
                data.get('color', '#ffff00')
            ))
            
            manager.db.commit()
            bookmark_id = cursor.lastrowid
        
        return jsonify({'success': True, 'bookmark_id': bookmark_id})
    except Exception as e:
        logger.error(f"Bookmark error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500
