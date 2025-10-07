from flask import Blueprint, jsonify, request
from .security import require_api_key
import sqlite3
import os
from typing import List, Dict, Optional

xref_bp = Blueprint('xref', __name__)

DB_PATH = os.path.join(os.path.dirname(__file__), '../storage/mediahub.db')

class CrossReferencesManager:
    """Manage cross-references between media items (franchises, universes, connections)"""
    
    @staticmethod
    def get_connection():
        """Get database connection"""
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        return conn
    
    @staticmethod
    def init_xref_tables():
        """Initialize cross-reference tables"""
        conn = CrossReferencesManager.get_connection()
        cursor = conn.cursor()
        
        # Franchises table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS franchises (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                description TEXT,
                logo_url TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Universes table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS universes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                description TEXT,
                logo_url TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Franchise-media relationship
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS franchise_media (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                franchise_id INTEGER NOT NULL,
                media_id INTEGER NOT NULL,
                media_type TEXT NOT NULL,
                order_in_franchise INTEGER,
                release_order INTEGER,
                chronological_order INTEGER,
                FOREIGN KEY (franchise_id) REFERENCES franchises(id)
            )
        ''')
        
        # Universe-media relationship
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS universe_media (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                universe_id INTEGER NOT NULL,
                media_id INTEGER NOT NULL,
                media_type TEXT NOT NULL,
                timeline_position TEXT,
                FOREIGN KEY (universe_id) REFERENCES universes(id)
            )
        ''')
        
        # Cross-references (connections between media)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS media_connections (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                media_id_1 INTEGER NOT NULL,
                media_type_1 TEXT NOT NULL,
                media_id_2 INTEGER NOT NULL,
                media_type_2 TEXT NOT NULL,
                connection_type TEXT NOT NULL,
                description TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        conn.close()
    
    # Franchise methods
    
    @staticmethod
    def create_franchise(name: str, description: str = None, logo_url: str = None) -> int:
        """Create a new franchise"""
        conn = CrossReferencesManager.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO franchises (name, description, logo_url)
            VALUES (?, ?, ?)
        ''', (name, description, logo_url))
        
        franchise_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return franchise_id
    
    @staticmethod
    def add_to_franchise(franchise_id: int, media_id: int, media_type: str, 
                        release_order: int = None, chronological_order: int = None):
        """Add media to a franchise"""
        conn = CrossReferencesManager.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO franchise_media 
            (franchise_id, media_id, media_type, release_order, chronological_order)
            VALUES (?, ?, ?, ?, ?)
        ''', (franchise_id, media_id, media_type, release_order, chronological_order))
        
        conn.commit()
        conn.close()
    
    @staticmethod
    def get_franchise_media(franchise_id: int, order_by: str = 'release') -> List[Dict]:
        """Get all media in a franchise"""
        conn = CrossReferencesManager.get_connection()
        cursor = conn.cursor()
        
        order_column = 'release_order' if order_by == 'release' else 'chronological_order'
        
        cursor.execute(f'''
            SELECT * FROM franchise_media
            WHERE franchise_id = ?
            ORDER BY {order_column} ASC, id ASC
        ''', (franchise_id,))
        
        media = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        return media
    
    @staticmethod
    def get_all_franchises() -> List[Dict]:
        """Get all franchises"""
        conn = CrossReferencesManager.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM franchises ORDER BY name ASC')
        franchises = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        return franchises
    
    # Universe methods
    
    @staticmethod
    def create_universe(name: str, description: str = None, logo_url: str = None) -> int:
        """Create a new universe"""
        conn = CrossReferencesManager.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO universes (name, description, logo_url)
            VALUES (?, ?, ?)
        ''', (name, description, logo_url))
        
        universe_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return universe_id
    
    @staticmethod
    def add_to_universe(universe_id: int, media_id: int, media_type: str, timeline_position: str = None):
        """Add media to a universe"""
        conn = CrossReferencesManager.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO universe_media 
            (universe_id, media_id, media_type, timeline_position)
            VALUES (?, ?, ?, ?)
        ''', (universe_id, media_id, media_type, timeline_position))
        
        conn.commit()
        conn.close()
    
    @staticmethod
    def get_universe_media(universe_id: int) -> List[Dict]:
        """Get all media in a universe"""
        conn = CrossReferencesManager.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM universe_media
            WHERE universe_id = ?
            ORDER BY timeline_position ASC, id ASC
        ''', (universe_id,))
        
        media = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        return media
    
    @staticmethod
    def get_all_universes() -> List[Dict]:
        """Get all universes"""
        conn = CrossReferencesManager.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM universes ORDER BY name ASC')
        universes = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        return universes
    
    # Connection methods
    
    @staticmethod
    def create_connection(media_id_1: int, media_type_1: str, media_id_2: int, media_type_2: str,
                         connection_type: str, description: str = None):
        """Create a connection between two media items"""
        conn = CrossReferencesManager.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO media_connections 
            (media_id_1, media_type_1, media_id_2, media_type_2, connection_type, description)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (media_id_1, media_type_1, media_id_2, media_type_2, connection_type, description))
        
        conn.commit()
        conn.close()
    
    @staticmethod
    def get_connections(media_id: int, media_type: str) -> List[Dict]:
        """Get all connections for a media item"""
        conn = CrossReferencesManager.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM media_connections
            WHERE (media_id_1 = ? AND media_type_1 = ?)
               OR (media_id_2 = ? AND media_type_2 = ?)
        ''', (media_id, media_type, media_id, media_type))
        
        connections = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        return connections
    
    @staticmethod
    def get_media_franchises(media_id: int, media_type: str) -> List[Dict]:
        """Get all franchises a media item belongs to"""
        conn = CrossReferencesManager.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT f.*, fm.release_order, fm.chronological_order
            FROM franchises f
            JOIN franchise_media fm ON f.id = fm.franchise_id
            WHERE fm.media_id = ? AND fm.media_type = ?
        ''', (media_id, media_type))
        
        franchises = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        return franchises
    
    @staticmethod
    def get_media_universes(media_id: int, media_type: str) -> List[Dict]:
        """Get all universes a media item belongs to"""
        conn = CrossReferencesManager.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT u.*, um.timeline_position
            FROM universes u
            JOIN universe_media um ON u.id = um.universe_id
            WHERE um.media_id = ? AND um.media_type = ?
        ''', (media_id, media_type))
        
        universes = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        return universes

# Initialize tables
CrossReferencesManager.init_xref_tables()

# API Endpoints

# Franchise endpoints

@xref_bp.route("/api/franchises", methods=["GET"])
@require_api_key
def get_franchises():
    """Get all franchises"""
    franchises = CrossReferencesManager.get_all_franchises()
    return jsonify({'franchises': franchises})

@xref_bp.route("/api/franchises", methods=["POST"])
@require_api_key
def create_franchise():
    """Create a new franchise"""
    data = request.get_json() or {}
    name = data.get('name')
    description = data.get('description')
    logo_url = data.get('logo_url')
    
    if not name:
        return jsonify({'error': 'Name is required'}), 400
    
    franchise_id = CrossReferencesManager.create_franchise(name, description, logo_url)
    return jsonify({'franchise_id': franchise_id, 'message': 'Franchise created'})

@xref_bp.route("/api/franchises/<int:franchise_id>", methods=["GET"])
@require_api_key
def get_franchise(franchise_id):
    """Get franchise details and media"""
    order_by = request.args.get('order', 'release')  # 'release' or 'chronological'
    media = CrossReferencesManager.get_franchise_media(franchise_id, order_by)
    return jsonify({'media': media})

@xref_bp.route("/api/franchises/<int:franchise_id>/add", methods=["POST"])
@require_api_key
def add_to_franchise(franchise_id):
    """Add media to franchise"""
    data = request.get_json() or {}
    media_id = data.get('media_id')
    media_type = data.get('media_type')
    release_order = data.get('release_order')
    chronological_order = data.get('chronological_order')
    
    if not all([media_id, media_type]):
        return jsonify({'error': 'media_id and media_type are required'}), 400
    
    CrossReferencesManager.add_to_franchise(franchise_id, media_id, media_type, 
                                           release_order, chronological_order)
    return jsonify({'message': 'Media added to franchise'})

# Universe endpoints

@xref_bp.route("/api/universes", methods=["GET"])
@require_api_key
def get_universes():
    """Get all universes"""
    universes = CrossReferencesManager.get_all_universes()
    return jsonify({'universes': universes})

@xref_bp.route("/api/universes", methods=["POST"])
@require_api_key
def create_universe():
    """Create a new universe"""
    data = request.get_json() or {}
    name = data.get('name')
    description = data.get('description')
    logo_url = data.get('logo_url')
    
    if not name:
        return jsonify({'error': 'Name is required'}), 400
    
    universe_id = CrossReferencesManager.create_universe(name, description, logo_url)
    return jsonify({'universe_id': universe_id, 'message': 'Universe created'})

@xref_bp.route("/api/universes/<int:universe_id>", methods=["GET"])
@require_api_key
def get_universe(universe_id):
    """Get universe details and media"""
    media = CrossReferencesManager.get_universe_media(universe_id)
    return jsonify({'media': media})

@xref_bp.route("/api/universes/<int:universe_id>/add", methods=["POST"])
@require_api_key
def add_to_universe(universe_id):
    """Add media to universe"""
    data = request.get_json() or {}
    media_id = data.get('media_id')
    media_type = data.get('media_type')
    timeline_position = data.get('timeline_position')
    
    if not all([media_id, media_type]):
        return jsonify({'error': 'media_id and media_type are required'}), 400
    
    CrossReferencesManager.add_to_universe(universe_id, media_id, media_type, timeline_position)
    return jsonify({'message': 'Media added to universe'})

# Connection endpoints

@xref_bp.route("/api/connections", methods=["POST"])
@require_api_key
def create_connection():
    """Create a connection between media items"""
    data = request.get_json() or {}
    media_id_1 = data.get('media_id_1')
    media_type_1 = data.get('media_type_1')
    media_id_2 = data.get('media_id_2')
    media_type_2 = data.get('media_type_2')
    connection_type = data.get('connection_type')
    description = data.get('description')
    
    if not all([media_id_1, media_type_1, media_id_2, media_type_2, connection_type]):
        return jsonify({'error': 'All fields except description are required'}), 400
    
    CrossReferencesManager.create_connection(media_id_1, media_type_1, media_id_2, media_type_2,
                                            connection_type, description)
    return jsonify({'message': 'Connection created'})

@xref_bp.route("/api/media/<media_type>/<int:media_id>/connections", methods=["GET"])
@require_api_key
def get_media_connections(media_type, media_id):
    """Get all connections for a media item"""
    connections = CrossReferencesManager.get_connections(media_id, media_type)
    return jsonify({'connections': connections})

@xref_bp.route("/api/media/<media_type>/<int:media_id>/franchises", methods=["GET"])
@require_api_key
def get_media_franchises(media_type, media_id):
    """Get franchises for a media item"""
    franchises = CrossReferencesManager.get_media_franchises(media_id, media_type)
    return jsonify({'franchises': franchises})

@xref_bp.route("/api/media/<media_type>/<int:media_id>/universes", methods=["GET"])
@require_api_key
def get_media_universes(media_type, media_id):
    """Get universes for a media item"""
    universes = CrossReferencesManager.get_media_universes(media_id, media_type)
    return jsonify({'universes': universes})
