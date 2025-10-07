"""
Phase 3: Faceted Database & Timeline Visualization
Implements cross-category search, clickable tags, timeline views, and detail pages
"""

from flask import Blueprint, request, jsonify, render_template_string
import os
import json
import sqlite3
from datetime import datetime, timedelta
import re
from collections import defaultdict, Counter

faceted_db_bp = Blueprint('faceted_db', __name__)

# Configuration
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
STORAGE = os.path.join(ROOT, 'storage')
FACETED_DB = os.path.join(STORAGE, 'faceted_search.db')
TIMELINE_CACHE = os.path.join(STORAGE, 'timeline_cache.json')

def init_faceted_db():
    """Initialize faceted search database"""
    conn = sqlite3.connect(FACETED_DB)
    cursor = conn.cursor()
    
    # Faceted search index table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS faceted_index (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            item_id TEXT NOT NULL,
            item_type TEXT NOT NULL, -- movie, tv_show, book, comic, music, etc.
            title TEXT NOT NULL,
            description TEXT,
            year INTEGER,
            genre TEXT,
            tags TEXT, -- JSON array
            metadata_json TEXT,
            file_path TEXT,
            thumbnail_url TEXT,
            backdrop_url TEXT,
            rating REAL,
            popularity_score INTEGER DEFAULT 0,
            last_accessed TIMESTAMP,
            created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Tags table for clickable tag system
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS tags (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            category TEXT, -- genre, actor, director, author, publisher, etc.
            color TEXT, -- hex color for UI
            usage_count INTEGER DEFAULT 0,
            created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Item-tag relationships
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS item_tags (
            item_id TEXT NOT NULL,
            tag_id INTEGER NOT NULL,
            relevance_score REAL DEFAULT 1.0,
            PRIMARY KEY (item_id, tag_id),
            FOREIGN KEY (tag_id) REFERENCES tags(id)
        )
    ''')
    
    # Timeline events for universe/franchise visualization
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS timeline_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            item_id TEXT NOT NULL,
            universe_name TEXT,
            event_date DATE,
            event_year INTEGER,
            event_title TEXT,
            event_description TEXT,
            event_type TEXT, -- release, story_event, production
            timeline_position INTEGER,
            is_canonical BOOLEAN DEFAULT TRUE,
            metadata_json TEXT,
            created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Detail pages content
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS detail_pages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            item_id TEXT UNIQUE NOT NULL,
            item_type TEXT NOT NULL,
            title TEXT NOT NULL,
            synopsis TEXT,
            cast_crew TEXT, -- JSON
            technical_specs TEXT, -- JSON
            reviews TEXT, -- JSON
            related_items TEXT, -- JSON
            trailer_urls TEXT, -- JSON
            image_gallery TEXT, -- JSON
            trivia TEXT, -- JSON
            awards TEXT, -- JSON
            box_office TEXT, -- JSON for movies
            publication_info TEXT, -- JSON for books
            series_info TEXT, -- JSON for TV shows
            last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Search analytics
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS search_analytics (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            query TEXT NOT NULL,
            filters_json TEXT,
            results_count INTEGER,
            clicked_item_id TEXT,
            search_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            user_session TEXT
        )
    ''')
    
    # Create indexes for performance
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_faceted_type ON faceted_index(item_type)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_faceted_year ON faceted_index(year)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_faceted_rating ON faceted_index(rating)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_faceted_title ON faceted_index(title)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_tags_category ON tags(category)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_timeline_universe ON timeline_events(universe_name)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_timeline_year ON timeline_events(event_year)')
    
    conn.commit()
    conn.close()

# Initialize database on import
init_faceted_db()

@faceted_db_bp.route('/api/faceted/search')
def faceted_search():
    """Advanced faceted search across all content types"""
    try:
        # Query parameters
        query = request.args.get('q', '').strip()
        item_types = request.args.getlist('type')
        genres = request.args.getlist('genre')
        tags = request.args.getlist('tag')
        year_min = request.args.get('year_min', type=int)
        year_max = request.args.get('year_max', type=int)
        rating_min = request.args.get('rating_min', type=float)
        rating_max = request.args.get('rating_max', type=float)
        sort_by = request.args.get('sort_by', 'relevance')
        sort_order = request.args.get('sort_order', 'DESC')
        page = int(request.args.get('page', 1))
        limit = int(request.args.get('limit', 20))
        
        conn = sqlite3.connect(FACETED_DB)
        cursor = conn.cursor()
        
        # Build dynamic query
        base_query = '''
            SELECT DISTINCT f.*, 
                   GROUP_CONCAT(t.name) as tag_names,
                   GROUP_CONCAT(t.category) as tag_categories
            FROM faceted_index f
            LEFT JOIN item_tags it ON f.item_id = it.item_id
            LEFT JOIN tags t ON it.tag_id = t.id
            WHERE 1=1
        '''
        params = []
        
        # Text search
        if query:
            base_query += ' AND (f.title LIKE ? OR f.description LIKE ? OR t.name LIKE ?)'
            search_term = f'%{query}%'
            params.extend([search_term, search_term, search_term])
        
        # Type filter
        if item_types:
            placeholders = ','.join(['?' for _ in item_types])
            base_query += f' AND f.item_type IN ({placeholders})'
            params.extend(item_types)
        
        # Genre filter (stored in tags)
        if genres:
            genre_placeholders = ','.join(['?' for _ in genres])
            base_query += f' AND EXISTS (SELECT 1 FROM item_tags it2 JOIN tags t2 ON it2.tag_id = t2.id WHERE it2.item_id = f.item_id AND t2.category = "genre" AND t2.name IN ({genre_placeholders}))'
            params.extend(genres)
        
        # Tag filter
        if tags:
            tag_placeholders = ','.join(['?' for _ in tags])
            base_query += f' AND EXISTS (SELECT 1 FROM item_tags it3 JOIN tags t3 ON it3.tag_id = t3.id WHERE it3.item_id = f.item_id AND t3.name IN ({tag_placeholders}))'
            params.extend(tags)
        
        # Year range
        if year_min:
            base_query += ' AND f.year >= ?'
            params.append(year_min)
        if year_max:
            base_query += ' AND f.year <= ?'
            params.append(year_max)
        
        # Rating range
        if rating_min:
            base_query += ' AND f.rating >= ?'
            params.append(rating_min)
        if rating_max:
            base_query += ' AND f.rating <= ?'
            params.append(rating_max)
        
        # Group by item
        base_query += ' GROUP BY f.item_id'
        
        # Sorting
        if sort_by == 'relevance':
            base_query += ' ORDER BY f.popularity_score DESC, f.rating DESC'
        elif sort_by == 'title':
            base_query += f' ORDER BY f.title {sort_order}'
        elif sort_by == 'year':
            base_query += f' ORDER BY f.year {sort_order}'
        elif sort_by == 'rating':
            base_query += f' ORDER BY f.rating {sort_order}'
        elif sort_by == 'date_added':
            base_query += f' ORDER BY f.created_date {sort_order}'
        
        # Get total count
        count_query = f'SELECT COUNT(DISTINCT f.item_id) FROM ({base_query}) f'
        cursor.execute(count_query, params)
        total = cursor.fetchone()[0]
        
        # Add pagination
        offset = (page - 1) * limit
        base_query += ' LIMIT ? OFFSET ?'
        params.extend([limit, offset])
        
        # Execute main query
        cursor.execute(base_query, params)
        columns = [description[0] for description in cursor.description]
        results = [dict(zip(columns, row)) for row in cursor.fetchall()]
        
        # Process results
        for result in results:
            if result['tags']:
                result['tags'] = result['tags'].split(',') if result['tags'] else []
            if result['metadata_json']:
                result['metadata'] = json.loads(result['metadata_json'])
        
        # Log search analytics
        log_search_analytics(cursor, query, {
            'types': item_types,
            'genres': genres,
            'tags': tags,
            'year_range': [year_min, year_max],
            'rating_range': [rating_min, rating_max]
        }, total)
        
        conn.commit()
        conn.close()
        
        return jsonify({
            'results': results,
            'total': total,
            'page': page,
            'limit': limit,
            'pages': (total + limit - 1) // limit,
            'facets': get_search_facets(item_types, genres, tags)
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@faceted_db_bp.route('/api/faceted/tags')
def get_all_tags():
    """Get all available tags with usage counts"""
    try:
        category = request.args.get('category')
        min_usage = int(request.args.get('min_usage', 1))
        
        conn = sqlite3.connect(FACETED_DB)
        cursor = conn.cursor()
        
        query = 'SELECT * FROM tags WHERE usage_count >= ?'
        params = [min_usage]
        
        if category:
            query += ' AND category = ?'
            params.append(category)
        
        query += ' ORDER BY usage_count DESC, name ASC'
        
        cursor.execute(query, params)
        columns = [description[0] for description in cursor.description]
        results = [dict(zip(columns, row)) for row in cursor.fetchall()]
        
        conn.close()
        return jsonify(results)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@faceted_db_bp.route('/api/faceted/tags/categories')
def get_tag_categories():
    """Get all tag categories with counts"""
    try:
        conn = sqlite3.connect(FACETED_DB)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT category, COUNT(*) as tag_count, SUM(usage_count) as total_usage
            FROM tags
            GROUP BY category
            ORDER BY total_usage DESC
        ''')
        
        columns = [description[0] for description in cursor.description]
        results = [dict(zip(columns, row)) for row in cursor.fetchall()]
        
        conn.close()
        return jsonify(results)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@faceted_db_bp.route('/api/faceted/timeline/<universe_name>')
def get_timeline(universe_name):
    """Get timeline visualization for a universe/franchise"""
    try:
        view_type = request.args.get('view', 'chronological')  # chronological, release_order
        include_non_canonical = request.args.get('include_non_canonical', 'false').lower() == 'true'
        
        conn = sqlite3.connect(FACETED_DB)
        cursor = conn.cursor()
        
        query = '''
            SELECT te.*, f.title, f.item_type, f.thumbnail_url, f.rating
            FROM timeline_events te
            JOIN faceted_index f ON te.item_id = f.item_id
            WHERE te.universe_name = ?
        '''
        params = [universe_name]
        
        if not include_non_canonical:
            query += ' AND te.is_canonical = TRUE'
        
        if view_type == 'chronological':
            query += ' ORDER BY te.event_year, te.timeline_position'
        else:  # release_order
            query += ' ORDER BY f.year, te.timeline_position'
        
        cursor.execute(query, params)
        columns = [description[0] for description in cursor.description]
        events = [dict(zip(columns, row)) for row in cursor.fetchall()]
        
        # Group events by year/decade for visualization
        timeline_data = defaultdict(list)
        
        for event in events:
            year_key = event['event_year'] if event['event_year'] else 'Unknown'
            timeline_data[year_key].append(event)
        
        # Create timeline structure
        timeline = {
            'universe': universe_name,
            'view_type': view_type,
            'total_events': len(events),
            'timeline': dict(timeline_data),
            'year_range': [
                min(e['event_year'] for e in events if e['event_year']),
                max(e['event_year'] for e in events if e['event_year'])
            ] if events else [None, None]
        }
        
        conn.close()
        return jsonify(timeline)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@faceted_db_bp.route('/api/faceted/detail/<item_id>')
def get_detail_page(item_id):
    """Get detailed information page for an item"""
    try:
        conn = sqlite3.connect(FACETED_DB)
        cursor = conn.cursor()
        
        # Get main item info
        cursor.execute('''
            SELECT f.*, dp.*
            FROM faceted_index f
            LEFT JOIN detail_pages dp ON f.item_id = dp.item_id
            WHERE f.item_id = ?
        ''', (item_id,))
        
        result = cursor.fetchone()
        if not result:
            return jsonify({'error': 'Item not found'}), 404
        
        columns = [description[0] for description in cursor.description]
        item_data = dict(zip(columns, result))
        
        # Get tags
        cursor.execute('''
            SELECT t.name, t.category, t.color
            FROM item_tags it
            JOIN tags t ON it.tag_id = t.id
            WHERE it.item_id = ?
            ORDER BY t.category, t.name
        ''', (item_id,))
        
        tags = [dict(zip(['name', 'category', 'color'], row)) for row in cursor.fetchall()]
        
        # Get related items (same universe, genre, or tags)
        cursor.execute('''
            SELECT DISTINCT f2.item_id, f2.title, f2.item_type, f2.thumbnail_url, f2.rating
            FROM faceted_index f2
            JOIN item_tags it2 ON f2.item_id = it2.item_id
            WHERE it2.tag_id IN (
                SELECT it.tag_id FROM item_tags it WHERE it.item_id = ?
            )
            AND f2.item_id != ?
            ORDER BY f2.rating DESC
            LIMIT 10
        ''', (item_id, item_id))
        
        related_items = [dict(zip(['item_id', 'title', 'item_type', 'thumbnail_url', 'rating'], row)) 
                        for row in cursor.fetchall()]
        
        # Update last accessed
        cursor.execute('''
            UPDATE faceted_index SET last_accessed = CURRENT_TIMESTAMP
            WHERE item_id = ?
        ''', (item_id,))
        
        conn.commit()
        conn.close()
        
        # Process JSON fields
        for field in ['metadata_json', 'cast_crew', 'technical_specs', 'reviews', 'related_items', 
                     'trailer_urls', 'image_gallery', 'trivia', 'awards', 'box_office', 
                     'publication_info', 'series_info']:
            if item_data.get(field):
                try:
                    item_data[field] = json.loads(item_data[field])
                except:
                    pass
        
        item_data['tags'] = tags
        item_data['related_items'] = related_items
        
        return jsonify(item_data)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@faceted_db_bp.route('/api/faceted/universes')
def get_universes():
    """Get all available universes/franchises"""
    try:
        conn = sqlite3.connect(FACETED_DB)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT universe_name, 
                   COUNT(*) as item_count,
                   MIN(event_year) as start_year,
                   MAX(event_year) as end_year,
                   GROUP_CONCAT(DISTINCT f.item_type) as content_types
            FROM timeline_events te
            JOIN faceted_index f ON te.item_id = f.item_id
            GROUP BY universe_name
            ORDER BY item_count DESC
        ''')
        
        columns = [description[0] for description in cursor.description]
        results = [dict(zip(columns, row)) for row in cursor.fetchall()]
        
        for result in results:
            if result['content_types']:
                result['content_types'] = result['content_types'].split(',')
        
        conn.close()
        return jsonify(results)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@faceted_db_bp.route('/api/faceted/index/rebuild', methods=['POST'])
def rebuild_faceted_index():
    """Rebuild the faceted search index from media library"""
    try:
        # This would integrate with the enhanced media management system
        # to rebuild the faceted index from the main media database
        
        conn = sqlite3.connect(FACETED_DB)
        cursor = conn.cursor()
        
        # Clear existing index
        cursor.execute('DELETE FROM faceted_index')
        cursor.execute('DELETE FROM item_tags')
        cursor.execute('DELETE FROM tags')
        cursor.execute('DELETE FROM timeline_events')
        cursor.execute('DELETE FROM detail_pages')
        
        # Rebuild from enhanced media database
        media_conn = sqlite3.connect(os.path.join(STORAGE, 'enhanced_media.db'))
        media_cursor = media_conn.cursor()
        
        media_cursor.execute('SELECT * FROM enhanced_media')
        media_items = media_cursor.fetchall()
        
        processed_count = 0
        
        for item in media_items:
            # Extract data (assuming column order)
            item_id = f"media_{item[0]}"
            title = item[2] or "Unknown Title"
            item_type = item[3] or "unknown"
            metadata = json.loads(item[4]) if item[4] else {}
            
            # Add to faceted index
            cursor.execute('''
                INSERT INTO faceted_index (
                    item_id, item_type, title, description, year, 
                    metadata_json, file_path, rating
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                item_id, item_type, title, 
                metadata.get('description', ''),
                extract_year_from_metadata(metadata),
                json.dumps(metadata),
                item[1],  # file_path
                item[19] or 0  # rating
            ))
            
            # Extract and add tags
            tags = extract_tags_from_metadata(metadata, item_type)
            for tag_name, category in tags:
                add_tag_to_item(cursor, item_id, tag_name, category)
            
            # Add timeline events for franchises
            if metadata.get('universe') or metadata.get('franchise'):
                add_timeline_event(cursor, item_id, metadata)
            
            processed_count += 1
        
        media_conn.close()
        
        # Update tag usage counts
        cursor.execute('''
            UPDATE tags SET usage_count = (
                SELECT COUNT(*) FROM item_tags WHERE tag_id = tags.id
            )
        ''')
        
        conn.commit()
        conn.close()
        
        return jsonify({
            'success': True,
            'processed_items': processed_count,
            'message': 'Faceted index rebuilt successfully'
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Helper functions

def get_search_facets(selected_types, selected_genres, selected_tags):
    """Get available facets for current search"""
    conn = sqlite3.connect(FACETED_DB)
    cursor = conn.cursor()
    
    facets = {}
    
    # Content types
    cursor.execute('''
        SELECT item_type, COUNT(*) as count
        FROM faceted_index
        GROUP BY item_type
        ORDER BY count DESC
    ''')
    facets['types'] = [{'name': row[0], 'count': row[1], 'selected': row[0] in selected_types} 
                      for row in cursor.fetchall()]
    
    # Genres (from tags)
    cursor.execute('''
        SELECT t.name, COUNT(*) as count
        FROM tags t
        JOIN item_tags it ON t.id = it.tag_id
        WHERE t.category = 'genre'
        GROUP BY t.name
        ORDER BY count DESC
        LIMIT 20
    ''')
    facets['genres'] = [{'name': row[0], 'count': row[1], 'selected': row[0] in selected_genres} 
                       for row in cursor.fetchall()]
    
    # Popular tags
    cursor.execute('''
        SELECT t.name, t.category, COUNT(*) as count
        FROM tags t
        JOIN item_tags it ON t.id = it.tag_id
        WHERE t.category != 'genre'
        GROUP BY t.name, t.category
        ORDER BY count DESC
        LIMIT 30
    ''')
    facets['tags'] = [{'name': row[0], 'category': row[1], 'count': row[2], 'selected': row[0] in selected_tags} 
                     for row in cursor.fetchall()]
    
    # Year ranges
    cursor.execute('SELECT MIN(year), MAX(year) FROM faceted_index WHERE year IS NOT NULL')
    year_range = cursor.fetchone()
    facets['year_range'] = {'min': year_range[0], 'max': year_range[1]} if year_range[0] else {'min': 1900, 'max': 2024}
    
    conn.close()
    return facets

def log_search_analytics(cursor, query, filters, results_count):
    """Log search analytics"""
    cursor.execute('''
        INSERT INTO search_analytics (query, filters_json, results_count)
        VALUES (?, ?, ?)
    ''', (query, json.dumps(filters), results_count))

def extract_year_from_metadata(metadata):
    """Extract year from metadata"""
    # Try various year fields
    for field in ['year', 'release_year', 'publication_year', 'date']:
        if field in metadata:
            year_value = metadata[field]
            if isinstance(year_value, int):
                return year_value
            elif isinstance(year_value, str):
                # Extract year from date string
                import re
                year_match = re.search(r'\b(19|20)\d{2}\b', year_value)
                if year_match:
                    return int(year_match.group())
    return None

def extract_tags_from_metadata(metadata, item_type):
    """Extract tags from metadata"""
    tags = []
    
    # Genre tags
    if 'genre' in metadata:
        genres = metadata['genre']
        if isinstance(genres, str):
            genres = [genres]
        elif isinstance(genres, list):
            pass
        else:
            genres = []
        
        for genre in genres:
            tags.append((genre.strip(), 'genre'))
    
    # Actor tags
    if 'actors' in metadata or 'cast' in metadata:
        actors = metadata.get('actors', metadata.get('cast', []))
        if isinstance(actors, list):
            for actor in actors[:10]:  # Limit to top 10
                if isinstance(actor, dict):
                    name = actor.get('name', '')
                else:
                    name = str(actor)
                if name:
                    tags.append((name.strip(), 'actor'))
    
    # Director tags
    if 'director' in metadata:
        directors = metadata['director']
        if isinstance(directors, str):
            directors = [directors]
        elif isinstance(directors, list):
            pass
        else:
            directors = []
        
        for director in directors:
            tags.append((director.strip(), 'director'))
    
    # Author tags (for books)
    if item_type in ['book', 'audiobook'] and 'author' in metadata:
        authors = metadata['author']
        if isinstance(authors, str):
            authors = [authors]
        elif isinstance(authors, list):
            pass
        else:
            authors = []
        
        for author in authors:
            tags.append((author.strip(), 'author'))
    
    # Publisher tags (for books/comics)
    if item_type in ['book', 'comic'] and 'publisher' in metadata:
        publisher = metadata['publisher']
        if publisher:
            tags.append((publisher.strip(), 'publisher'))
    
    # Network tags (for TV shows)
    if item_type == 'tv_show' and 'network' in metadata:
        networks = metadata['network']
        if isinstance(networks, str):
            networks = [networks]
        elif isinstance(networks, list):
            pass
        else:
            networks = []
        
        for network in networks:
            tags.append((network.strip(), 'network'))
    
    # Studio tags (for movies)
    if item_type == 'movie' and 'studio' in metadata:
        studios = metadata['studio']
        if isinstance(studios, str):
            studios = [studios]
        elif isinstance(studios, list):
            pass
        else:
            studios = []
        
        for studio in studios:
            tags.append((studio.strip(), 'studio'))
    
    return tags

def add_tag_to_item(cursor, item_id, tag_name, category):
    """Add tag to item with automatic tag creation"""
    # Get or create tag
    cursor.execute('SELECT id FROM tags WHERE name = ? AND category = ?', (tag_name, category))
    tag_row = cursor.fetchone()
    
    if tag_row:
        tag_id = tag_row[0]
    else:
        # Create new tag
        cursor.execute('''
            INSERT INTO tags (name, category, color)
            VALUES (?, ?, ?)
        ''', (tag_name, category, generate_tag_color(category)))
        tag_id = cursor.lastrowid
    
    # Link tag to item
    cursor.execute('''
        INSERT OR IGNORE INTO item_tags (item_id, tag_id)
        VALUES (?, ?)
    ''', (item_id, tag_id))

def add_timeline_event(cursor, item_id, metadata):
    """Add timeline event for universe/franchise content"""
    universe = metadata.get('universe') or metadata.get('franchise')
    if not universe:
        return
    
    event_year = extract_year_from_metadata(metadata)
    if not event_year:
        return
    
    cursor.execute('''
        INSERT INTO timeline_events (
            item_id, universe_name, event_year, event_title, 
            event_description, event_type, timeline_position
        ) VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (
        item_id,
        universe,
        event_year,
        metadata.get('title', 'Unknown'),
        metadata.get('description', ''),
        'release',
        metadata.get('timeline_position', event_year)
    ))

def generate_tag_color(category):
    """Generate color for tag category"""
    colors = {
        'genre': '#3B82F6',      # Blue
        'actor': '#10B981',      # Green
        'director': '#F59E0B',   # Yellow
        'author': '#8B5CF6',     # Purple
        'publisher': '#EF4444',  # Red
        'network': '#06B6D4',    # Cyan
        'studio': '#F97316',     # Orange
        'year': '#6B7280',       # Gray
        'quality': '#84CC16',    # Lime
        'source': '#EC4899'      # Pink
    }
    return colors.get(category, '#6B7280')
