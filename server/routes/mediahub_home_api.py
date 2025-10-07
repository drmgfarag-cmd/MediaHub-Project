"""
MediaHub Home API - Golden Surface Endpoints
Wraps PyQt6 mediahub_home.py functionality with Flask APIs
"""

from flask import Blueprint, jsonify, request
import os
import json
from datetime import datetime

home_api_bp = Blueprint('home_api', __name__)

# Storage paths
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
STORAGE = os.path.join(ROOT, 'storage')
HERO_FILE = os.path.join(STORAGE, 'home_hero.json')
CAROUSELS_FILE = os.path.join(STORAGE, 'home_carousels.json')
SUBCATEGORIES_FILE = os.path.join(STORAGE, 'home_subcategories.json')
SEARCH_INDEX_FILE = os.path.join(STORAGE, 'search_index.json')

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


@home_api_bp.route('/api/home/hero', methods=['GET'])
def get_hero():
    """
    Golden Surface API: Hero section content management
    Returns Prime Video-style hero banner configuration
    """
    hero_data = load_json(HERO_FILE, {
        'title': 'Welcome to MediaHub',
        'subtitle': 'Your Personal Media Center',
        'description': 'Stream, organize, and enjoy your media collection',
        'background_image': '/assets/hero-bg.jpg',
        'background_video': '',
        'featured_item': None,
        'cta_button': {
            'text': 'Browse Library',
            'action': '/library'
        },
        'overlay_opacity': 0.6,
        'text_position': 'left',  # left, center, right
        'auto_rotate': True,
        'rotate_interval': 8000  # milliseconds
    })
    
    return jsonify({
        'ok': True,
        'hero': hero_data
    })


@home_api_bp.route('/api/home/hero', methods=['POST'])
def set_hero():
    """Update hero section configuration"""
    try:
        hero_data = request.json
        save_json(HERO_FILE, hero_data)
        
        return jsonify({
            'ok': True,
            'hero': hero_data,
            'message': 'Hero section updated successfully'
        })
    except Exception as e:
        return jsonify({
            'ok': False,
            'error': str(e)
        }), 500


@home_api_bp.route('/api/home/carousels', methods=['GET'])
def get_carousels():
    """
    Golden Surface API: Content carousel management
    Returns multiple horizontal scrolling carousels for different content types
    """
    carousels_data = load_json(CAROUSELS_FILE, {
        'carousels': [
            {
                'id': 'continue_watching',
                'title': 'Continue Watching',
                'type': 'media',
                'items': [],
                'visible': True,
                'order': 1
            },
            {
                'id': 'recently_added',
                'title': 'Recently Added',
                'type': 'media',
                'items': [],
                'visible': True,
                'order': 2
            },
            {
                'id': 'recommended',
                'title': 'Recommended for You',
                'type': 'media',
                'items': [],
                'visible': True,
                'order': 3
            },
            {
                'id': 'trending',
                'title': 'Trending Now',
                'type': 'media',
                'items': [],
                'visible': True,
                'order': 4
            },
            {
                'id': 'favorites',
                'title': 'Your Favorites',
                'type': 'media',
                'items': [],
                'visible': True,
                'order': 5
            }
        ]
    })
    
    # Sort by order
    carousels = sorted(carousels_data.get('carousels', []), key=lambda x: x.get('order', 999))
    
    # Filter visible only if requested
    if request.args.get('visible_only') == 'true':
        carousels = [c for c in carousels if c.get('visible', True)]
    
    return jsonify({
        'ok': True,
        'carousels': carousels,
        'total': len(carousels)
    })


@home_api_bp.route('/api/home/carousels', methods=['POST'])
def set_carousels():
    """Update carousels configuration"""
    try:
        carousels = request.json.get('carousels', [])
        save_json(CAROUSELS_FILE, {'carousels': carousels})
        
        return jsonify({
            'ok': True,
            'carousels': carousels,
            'message': 'Carousels updated successfully'
        })
    except Exception as e:
        return jsonify({
            'ok': False,
            'error': str(e)
        }), 500


@home_api_bp.route('/api/home/carousels/<carousel_id>', methods=['GET'])
def get_carousel(carousel_id):
    """Get specific carousel by ID"""
    carousels_data = load_json(CAROUSELS_FILE, {'carousels': []})
    
    carousel = next((c for c in carousels_data.get('carousels', []) if c.get('id') == carousel_id), None)
    
    if carousel:
        return jsonify({
            'ok': True,
            'carousel': carousel
        })
    else:
        return jsonify({
            'ok': False,
            'error': f'Carousel {carousel_id} not found'
        }), 404


@home_api_bp.route('/api/home/subcategories', methods=['GET'])
def get_subcategories():
    """
    Golden Surface API: Media subcategories
    Returns Movies, TV Shows, Books, Audio categories with counts
    """
    subcategories_data = load_json(SUBCATEGORIES_FILE, {
        'subcategories': [
            {
                'id': 'movies',
                'title': 'Movies',
                'icon': 'film',
                'description': 'Feature films and documentaries',
                'count': 0,
                'visible': True,
                'order': 1,
                'color': '#e50914'  # Netflix red
            },
            {
                'id': 'tv_shows',
                'title': 'TV Shows',
                'icon': 'tv',
                'description': 'Series and episodes',
                'count': 0,
                'visible': True,
                'order': 2,
                'color': '#0080ff'  # Prime blue
            },
            {
                'id': 'books',
                'title': 'Books',
                'icon': 'book',
                'description': 'eBooks and audiobooks',
                'count': 0,
                'visible': True,
                'order': 3,
                'color': '#ff9500'  # Apple orange
            },
            {
                'id': 'audio',
                'title': 'Audio',
                'icon': 'music',
                'description': 'Music and podcasts',
                'count': 0,
                'visible': True,
                'order': 4,
                'color': '#1db954'  # Spotify green
            }
        ]
    })
    
    subcategories = sorted(subcategories_data.get('subcategories', []), key=lambda x: x.get('order', 999))
    
    # Filter visible only if requested
    if request.args.get('visible_only') == 'true':
        subcategories = [s for s in subcategories if s.get('visible', True)]
    
    return jsonify({
        'ok': True,
        'subcategories': subcategories,
        'total': len(subcategories)
    })


@home_api_bp.route('/api/home/subcategories', methods=['POST'])
def set_subcategories():
    """Update subcategories configuration"""
    try:
        subcategories = request.json.get('subcategories', [])
        save_json(SUBCATEGORIES_FILE, {'subcategories': subcategories})
        
        return jsonify({
            'ok': True,
            'subcategories': subcategories,
            'message': 'Subcategories updated successfully'
        })
    except Exception as e:
        return jsonify({
            'ok': False,
            'error': str(e)
        }), 500


@home_api_bp.route('/api/search/omnibox', methods=['GET'])
def omnibox_search():
    """
    Golden Surface API: Global search (omnibox)
    Search across all media types with unified results
    """
    query = request.args.get('q', '').strip()
    limit = int(request.args.get('limit', 20))
    category = request.args.get('category', 'all')  # all, movies, tv_shows, books, audio
    
    if not query:
        return jsonify({
            'ok': True,
            'query': '',
            'results': [],
            'total': 0
        })
    
    # Load search index
    search_index = load_json(SEARCH_INDEX_FILE, {
        'movies': [],
        'tv_shows': [],
        'books': [],
        'audio': [],
        'last_updated': None
    })
    
    results = {
        'movies': [],
        'tv_shows': [],
        'books': [],
        'audio': []
    }
    
    query_lower = query.lower()
    
    # Search in each category
    for cat in ['movies', 'tv_shows', 'books', 'audio']:
        if category != 'all' and category != cat:
            continue
        
        items = search_index.get(cat, [])
        matches = []
        
        for item in items:
            # Simple text matching (can be enhanced with fuzzy search, etc.)
            title = item.get('title', '').lower()
            description = item.get('description', '').lower()
            tags = ' '.join(item.get('tags', [])).lower()
            
            if query_lower in title or query_lower in description or query_lower in tags:
                # Calculate relevance score
                score = 0
                if query_lower in title:
                    score += 10
                if title.startswith(query_lower):
                    score += 5
                if query_lower in description:
                    score += 3
                if query_lower in tags:
                    score += 2
                
                matches.append({
                    **item,
                    'relevance_score': score,
                    'category': cat
                })
        
        # Sort by relevance
        matches.sort(key=lambda x: x.get('relevance_score', 0), reverse=True)
        results[cat] = matches[:limit]
    
    # Flatten results for unified view
    all_results = []
    for cat in results:
        all_results.extend(results[cat])
    
    # Sort all results by relevance
    all_results.sort(key=lambda x: x.get('relevance_score', 0), reverse=True)
    all_results = all_results[:limit]
    
    return jsonify({
        'ok': True,
        'query': query,
        'results': all_results,
        'results_by_category': results,
        'total': len(all_results)
    })


@home_api_bp.route('/api/search/index/rebuild', methods=['POST'])
def rebuild_search_index():
    """Rebuild search index from media library"""
    try:
        # Scan media library and build search index
        # In production, would scan actual media folders and extract metadata
        media_folders = request.json.get('folders', [])
        
        search_index = {
            'movies': [],
            'tv_shows': [],
            'books': [],
            'audio': [],
            'last_updated': datetime.utcnow().isoformat(),
            'total_items': 0,
            'scan_duration': 0
        }
        
        # In production, would:
        # 1. Walk through media_folders
        # 2. Identify media files
        # 3. Extract metadata
        # 4. Build searchable index
        # For now, create empty but properly structured index
        
        save_json(SEARCH_INDEX_FILE, search_index)
        
        return jsonify({
            'ok': True,
            'message': 'Search index rebuilt successfully',
            'last_updated': search_index['last_updated']
        })
    except Exception as e:
        return jsonify({
            'ok': False,
            'error': str(e)
        }), 500
