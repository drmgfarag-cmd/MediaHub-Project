from flask import Blueprint, jsonify, request
from .security import require_api_key
import sqlite3
import os
from typing import List, Dict

tags_bp = Blueprint('tags', __name__)

DB_PATH = os.path.join(os.path.dirname(__file__), '../storage/mediahub.db')

class TagsManager:
    """Manage clickable tags for genres, directors, actors, franchises"""
    
    @staticmethod
    def get_connection():
        """Get database connection"""
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        return conn
    
    @staticmethod
    def init_tags_tables():
        """Initialize tags tables"""
        conn = TagsManager.get_connection()
        cursor = conn.cursor()
        
        # Tags table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS tags (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                type TEXT NOT NULL,
                tmdb_id INTEGER,
                description TEXT,
                image_url TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Media-tags relationship
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS media_tags (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                media_id INTEGER NOT NULL,
                media_type TEXT NOT NULL,
                tag_id INTEGER NOT NULL,
                FOREIGN KEY (tag_id) REFERENCES tags(id)
            )
        ''')
        
        # Tag clicks/usage tracking
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS tag_stats (
                tag_id INTEGER PRIMARY KEY,
                click_count INTEGER DEFAULT 0,
                last_clicked TIMESTAMP,
                FOREIGN KEY (tag_id) REFERENCES tags(id)
            )
        ''')
        
        conn.commit()
        conn.close()
    
    @staticmethod
    def add_tag(name: str, tag_type: str, tmdb_id: int = None, description: str = None, image_url: str = None) -> int:
        """Add a new tag"""
        conn = TagsManager.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO tags (name, type, tmdb_id, description, image_url)
            VALUES (?, ?, ?, ?, ?)
        ''', (name, tag_type, tmdb_id, description, image_url))
        
        tag_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return tag_id
    
    @staticmethod
    def link_tag_to_media(media_id: int, media_type: str, tag_id: int):
        """Link a tag to a media item"""
        conn = TagsManager.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT OR IGNORE INTO media_tags (media_id, media_type, tag_id)
            VALUES (?, ?, ?)
        ''', (media_id, media_type, tag_id))
        
        conn.commit()
        conn.close()
    
    @staticmethod
    def get_tags_by_type(tag_type: str, limit: int = 100) -> List[Dict]:
        """Get all tags of a specific type"""
        conn = TagsManager.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT t.*, COALESCE(ts.click_count, 0) as click_count
            FROM tags t
            LEFT JOIN tag_stats ts ON t.id = ts.tag_id
            WHERE t.type = ?
            ORDER BY ts.click_count DESC, t.name ASC
            LIMIT ?
        ''', (tag_type, limit))
        
        tags = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        return tags
    
    @staticmethod
    def get_media_by_tag(tag_id: int, limit: int = 50) -> List[Dict]:
        """Get all media items with a specific tag"""
        conn = TagsManager.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT media_id, media_type
            FROM media_tags
            WHERE tag_id = ?
            LIMIT ?
        ''', (tag_id, limit))
        
        media = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        return media
    
    @staticmethod
    def get_tags_for_media(media_id: int, media_type: str) -> List[Dict]:
        """Get all tags for a specific media item"""
        conn = TagsManager.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT t.*
            FROM tags t
            JOIN media_tags mt ON t.id = mt.tag_id
            WHERE mt.media_id = ? AND mt.media_type = ?
        ''', (media_id, media_type))
        
        tags = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        return tags
    
    @staticmethod
    def record_tag_click(tag_id: int):
        """Record a tag click for analytics"""
        conn = TagsManager.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO tag_stats (tag_id, click_count, last_clicked)
            VALUES (?, 1, CURRENT_TIMESTAMP)
            ON CONFLICT(tag_id) DO UPDATE SET
                click_count = click_count + 1,
                last_clicked = CURRENT_TIMESTAMP
        ''')
        
        conn.commit()
        conn.close()
    
    @staticmethod
    def get_popular_tags(tag_type: str = None, limit: int = 20) -> List[Dict]:
        """Get most popular tags"""
        conn = TagsManager.get_connection()
        cursor = conn.cursor()
        
        if tag_type:
            cursor.execute('''
                SELECT t.*, ts.click_count
                FROM tags t
                JOIN tag_stats ts ON t.id = ts.tag_id
                WHERE t.type = ?
                ORDER BY ts.click_count DESC
                LIMIT ?
            ''', (tag_type, limit))
        else:
            cursor.execute('''
                SELECT t.*, ts.click_count
                FROM tags t
                JOIN tag_stats ts ON t.id = ts.tag_id
                ORDER BY ts.click_count DESC
                LIMIT ?
            ''', (limit,))
        
        tags = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        return tags
    
    @staticmethod
    def search_tags(query: str, tag_type: str = None) -> List[Dict]:
        """Search tags by name"""
        conn = TagsManager.get_connection()
        cursor = conn.cursor()
        
        if tag_type:
            cursor.execute('''
                SELECT t.*, COALESCE(ts.click_count, 0) as click_count
                FROM tags t
                LEFT JOIN tag_stats ts ON t.id = ts.tag_id
                WHERE t.name LIKE ? AND t.type = ?
                ORDER BY ts.click_count DESC
                LIMIT 50
            ''', (f'%{query}%', tag_type))
        else:
            cursor.execute('''
                SELECT t.*, COALESCE(ts.click_count, 0) as click_count
                FROM tags t
                LEFT JOIN tag_stats ts ON t.id = ts.tag_id
                WHERE t.name LIKE ?
                ORDER BY ts.click_count DESC
                LIMIT 50
            ''', (f'%{query}%',))
        
        tags = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        return tags

# Initialize tables on import
TagsManager.init_tags_tables()

# API Endpoints

@tags_bp.route("/api/tags/types", methods=["GET"])
@require_api_key
def get_tag_types():
    """Get available tag types"""
    return jsonify({
        'types': ['genre', 'director', 'actor', 'writer', 'franchise', 'universe', 'studio', 'network']
    })

@tags_bp.route("/api/tags/<tag_type>", methods=["GET"])
@require_api_key
def get_tags(tag_type):
    """Get all tags of a specific type"""
    limit = request.args.get('limit', 100, type=int)
    tags = TagsManager.get_tags_by_type(tag_type, limit)
    return jsonify({'tags': tags})

@tags_bp.route("/api/tags/add", methods=["POST"])
@require_api_key
def add_tag():
    """Add a new tag"""
    data = request.get_json() or {}
    
    name = data.get('name')
    tag_type = data.get('type')
    tmdb_id = data.get('tmdb_id')
    description = data.get('description')
    image_url = data.get('image_url')
    
    if not name or not tag_type:
        return jsonify({'error': 'Name and type are required'}), 400
    
    tag_id = TagsManager.add_tag(name, tag_type, tmdb_id, description, image_url)
    return jsonify({'tag_id': tag_id, 'message': 'Tag added successfully'})

@tags_bp.route("/api/tags/link", methods=["POST"])
@require_api_key
def link_tag():
    """Link a tag to a media item"""
    data = request.get_json() or {}
    
    media_id = data.get('media_id')
    media_type = data.get('media_type')
    tag_id = data.get('tag_id')
    
    if not all([media_id, media_type, tag_id]):
        return jsonify({'error': 'media_id, media_type, and tag_id are required'}), 400
    
    TagsManager.link_tag_to_media(media_id, media_type, tag_id)
    return jsonify({'message': 'Tag linked successfully'})

@tags_bp.route("/api/tags/<int:tag_id>/media", methods=["GET"])
@require_api_key
def get_tag_media(tag_id):
    """Get all media items with a specific tag"""
    limit = request.args.get('limit', 50, type=int)
    media = TagsManager.get_media_by_tag(tag_id, limit)
    return jsonify({'media': media})

@tags_bp.route("/api/media/<media_type>/<int:media_id>/tags", methods=["GET"])
@require_api_key
def get_media_tags(media_type, media_id):
    """Get all tags for a specific media item"""
    tags = TagsManager.get_tags_for_media(media_id, media_type)
    return jsonify({'tags': tags})

@tags_bp.route("/api/tags/<int:tag_id>/click", methods=["POST"])
@require_api_key
def record_click(tag_id):
    """Record a tag click"""
    TagsManager.record_tag_click(tag_id)
    return jsonify({'message': 'Click recorded'})

@tags_bp.route("/api/tags/popular", methods=["GET"])
@require_api_key
def get_popular():
    """Get popular tags"""
    tag_type = request.args.get('type')
    limit = request.args.get('limit', 20, type=int)
    tags = TagsManager.get_popular_tags(tag_type, limit)
    return jsonify({'tags': tags})

@tags_bp.route("/api/tags/search", methods=["GET"])
@require_api_key
def search():
    """Search tags"""
    query = request.args.get('q', '')
    tag_type = request.args.get('type')
    
    if not query:
        return jsonify({'error': 'Query parameter q is required'}), 400
    
    tags = TagsManager.search_tags(query, tag_type)
    return jsonify({'tags': tags})
