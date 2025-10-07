"""
Mobile Smart Rails API - Optimized endpoints for mobile interface
Provides mobile-optimized data for touch-friendly smart rails interface
"""

from flask import Blueprint, jsonify, request
import os
import json
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional
# from utils.advanced_smart_rails import advanced_smart_rails_engine

mobile_rails_bp = Blueprint('mobile_smart_rails', __name__)
logger = logging.getLogger(__name__)

@mobile_rails_bp.route('/api/smart_rails/mobile/<rail_type>')
def get_mobile_rail(rail_type):
    """Get mobile-optimized smart rail data"""
    try:
        # Get limit from query params (default to mobile-friendly count)
        limit = min(int(request.args.get('limit', 20)), 50)  # Max 50 for mobile
        
        # Mock library data for demonstration
        # In real implementation, this would come from the actual library
        mock_library_items = generate_mock_library_data()
        
        # Generate smart rails based on type
        if rail_type == 'recommended':
            items = get_recommended_rail(mock_library_items, limit)
        elif rail_type == 'premium':
            items = get_premium_rail(mock_library_items, limit)
        elif rail_type == 'trending':
            items = get_trending_rail(mock_library_items, limit)
        elif rail_type == 'discovery':
            items = get_discovery_rail(mock_library_items, limit)
        elif rail_type == 'collections':
            items = get_collections_rail(limit)
        else:
            return jsonify({
                'success': False,
                'error': f'Unknown rail type: {rail_type}'
            }), 400
        
        # Optimize data for mobile
        mobile_optimized_items = optimize_for_mobile(items, rail_type)
        
        return jsonify({
            'success': True,
            'rail_type': rail_type,
            'items': mobile_optimized_items,
            'count': len(mobile_optimized_items),
            'generated_at': datetime.now().isoformat(),
            'mobile_optimized': True
        })
        
    except Exception as e:
        logger.error(f"Error getting mobile rail {rail_type}: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@mobile_rails_bp.route('/api/smart_rails/mobile/refresh/<rail_type>', methods=['POST'])
def refresh_mobile_rail(rail_type):
    """Refresh a specific mobile rail"""
    try:
        # Force refresh by clearing any cached data
        # In real implementation, this would clear the specific rail cache
        
        # Get fresh data
        response_data = get_mobile_rail(rail_type)
        
        if response_data[1] == 200:  # Success
            data = response_data[0].get_json()
            return jsonify({
                'success': True,
                'message': f'Rail {rail_type} refreshed successfully',
                'rail_type': rail_type,
                'item_count': data.get('count', 0),
                'refreshed_at': datetime.now().isoformat()
            })
        else:
            return response_data
            
    except Exception as e:
        logger.error(f"Error refreshing mobile rail {rail_type}: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@mobile_rails_bp.route('/api/smart_rails/mobile/all')
def get_all_mobile_rails():
    """Get all mobile rails data in one request"""
    try:
        rail_types = ['recommended', 'premium', 'trending', 'discovery', 'collections']
        all_rails = {}
        
        for rail_type in rail_types:
            try:
                response_data = get_mobile_rail(rail_type)
                if response_data[1] == 200:
                    data = response_data[0].get_json()
                    all_rails[rail_type] = {
                        'items': data.get('items', []),
                        'count': data.get('count', 0)
                    }
                else:
                    all_rails[rail_type] = {
                        'items': [],
                        'count': 0,
                        'error': 'Failed to load'
                    }
            except Exception as e:
                logger.error(f"Error loading rail {rail_type}: {e}")
                all_rails[rail_type] = {
                    'items': [],
                    'count': 0,
                    'error': str(e)
                }
        
        return jsonify({
            'success': True,
            'rails': all_rails,
            'total_rails': len(rail_types),
            'generated_at': datetime.now().isoformat(),
            'mobile_optimized': True
        })
        
    except Exception as e:
        logger.error(f"Error getting all mobile rails: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@mobile_rails_bp.route('/api/smart_rails/mobile/item/<item_id>')
def get_mobile_item_details(item_id):
    """Get mobile-optimized item details"""
    try:
        # In real implementation, this would fetch from the actual library
        item = find_item_by_id(item_id)
        
        if not item:
            return jsonify({
                'success': False,
                'error': 'Item not found'
            }), 404
        
        # Optimize for mobile display
        mobile_item = {
            'id': item.get('id'),
            'title': item.get('title', ''),
            'type': item.get('type', ''),
            'year': item.get('year'),
            'rating': item.get('rating'),
            'overview': item.get('overview', '')[:200] + '...' if len(item.get('overview', '')) > 200 else item.get('overview', ''),
            'poster': item.get('poster'),
            'backdrop': item.get('backdrop'),
            'quality_features': item.get('quality_features', {}),
            'genres': item.get('genres', []),
            'duration': item.get('duration'),
            'file_size': item.get('file_size'),
            'path': item.get('path'),
            'available_actions': get_available_actions(item),
            'mobile_optimized': True
        }
        
        return jsonify({
            'success': True,
            'item': mobile_item
        })
        
    except Exception as e:
        logger.error(f"Error getting mobile item details for {item_id}: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@mobile_rails_bp.route('/api/smart_rails/mobile/search')
def mobile_search():
    """Mobile-optimized search across smart rails"""
    try:
        query = request.args.get('q', '').strip()
        limit = min(int(request.args.get('limit', 15)), 30)  # Mobile-friendly limit
        
        if not query:
            return jsonify({
                'success': False,
                'error': 'Search query is required'
            }), 400
        
        # Search across all rails
        all_items = []
        mock_library_items = generate_mock_library_data()
        
        # Simple search implementation
        for item in mock_library_items:
            if (query.lower() in item.get('title', '').lower() or 
                query.lower() in item.get('overview', '').lower() or
                any(query.lower() in genre.lower() for genre in item.get('genres', []))):
                all_items.append(item)
        
        # Sort by relevance (simple implementation)
        all_items.sort(key=lambda x: x.get('rating', 0), reverse=True)
        
        # Limit results and optimize for mobile
        results = optimize_for_mobile(all_items[:limit], 'search')
        
        return jsonify({
            'success': True,
            'query': query,
            'results': results,
            'count': len(results),
            'total_found': len(all_items),
            'mobile_optimized': True
        })
        
    except Exception as e:
        logger.error(f"Error in mobile search: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

def generate_mock_library_data() -> List[Dict]:
    """Generate mock library data for demonstration"""
    return [
        {
            'id': 1,
            'title': 'Dune: Part Two',
            'type': 'movie',
            'year': 2024,
            'rating': 8.8,
            'overview': 'Paul Atreides unites with Chani and the Fremen while seeking revenge against the conspirators who destroyed his family.',
            'poster': 'https://image.tmdb.org/t/p/w500/1pdfLvkbY9ohJlCjQH2CZjjYVvJ.jpg',
            'backdrop': 'https://image.tmdb.org/t/p/w1280/xOMo8BRK7PfcJv9JCnx7s5hj0PX.jpg',
            'genres': ['Sci-Fi', 'Action', 'Adventure'],
            'quality_features': {'4k_uhd': True, 'hdr': True, 'dolby_vision': True, 'atmos': True},
            'path': '/Movies/4K/Dune.Part.Two.2024.2160p.HDR.DV.Atmos.x265.mkv',
            'file_size': '15.2 GB',
            'duration': '2h 46m'
        },
        {
            'id': 2,
            'title': 'The Bear',
            'type': 'tv',
            'year': 2022,
            'rating': 8.7,
            'overview': 'A young chef from the fine dining world returns to Chicago to run his deceased brother\'s Italian beef sandwich shop.',
            'poster': 'https://image.tmdb.org/t/p/w500/sHFlbKS3WLqMnp9t2ghADIJFnuQ.jpg',
            'backdrop': 'https://image.tmdb.org/t/p/w1280/m7tG5Yx1XLDfHF8NbNaSvpLsk1C.jpg',
            'genres': ['Comedy', 'Drama'],
            'quality_features': {'4k_uhd': True, 'hdr': True},
            'path': '/TV/The.Bear.S03.2160p.HDR.x265/',
            'file_size': '8.4 GB',
            'duration': '30m per episode'
        },
        {
            'id': 3,
            'title': 'Atomic Habits',
            'type': 'book',
            'year': 2018,
            'rating': 9.1,
            'overview': 'An Easy & Proven Way to Build Good Habits & Break Bad Ones by James Clear.',
            'poster': 'https://images-na.ssl-images-amazon.com/images/I/51Tlm0GZTXL._SX329_BO1,204,203,200_.jpg',
            'genres': ['Self-Help', 'Psychology', 'Productivity'],
            'quality_features': {},
            'path': '/Books/Self-Help/Atomic.Habits.James.Clear.epub',
            'file_size': '2.1 MB',
            'duration': '9h 21m (audiobook)'
        },
        {
            'id': 4,
            'title': 'Random Access Memories',
            'type': 'album',
            'year': 2013,
            'rating': 8.9,
            'overview': 'The fourth studio album by French electronic music duo Daft Punk.',
            'poster': 'https://upload.wikimedia.org/wikipedia/en/a/a7/Random_Access_Memories.jpg',
            'genres': ['Electronic', 'Funk', 'Disco'],
            'quality_features': {'hi_res': True, 'lossless': True},
            'path': '/Music/Daft.Punk/Random.Access.Memories.2013.FLAC/',
            'file_size': '485 MB',
            'duration': '74m 4s'
        },
        {
            'id': 5,
            'title': 'Planet Earth II',
            'type': 'movie',
            'year': 2016,
            'rating': 9.5,
            'overview': 'A nature documentary series that explores the wildlife and landscapes of Earth.',
            'poster': 'https://image.tmdb.org/t/p/w500/z1TbCl8UXNBKs8bk1rVYLSgBXY9.jpg',
            'backdrop': 'https://image.tmdb.org/t/p/w1280/lZSzK7QyKKBcKuGO3JsLbKU7YAL.jpg',
            'genres': ['Documentary', 'Nature'],
            'quality_features': {'4k_uhd': True, 'hdr': True, 'atmos': True},
            'path': '/Movies/Documentary/Planet.Earth.II.2016.2160p.HDR.Atmos.x265.mkv',
            'file_size': '12.8 GB',
            'duration': '6h 0m'
        }
    ]

def get_recommended_rail(library_items: List[Dict], limit: int) -> List[Dict]:
    """Get recommended content for mobile"""
    # Simple recommendation based on rating
    recommended = sorted(library_items, key=lambda x: x.get('rating', 0), reverse=True)
    return recommended[:limit]

def get_premium_rail(library_items: List[Dict], limit: int) -> List[Dict]:
    """Get premium quality content for mobile"""
    premium_items = []
    for item in library_items:
        quality_features = item.get('quality_features', {})
        if any(quality_features.values()):  # Has any quality features
            premium_items.append(item)
    
    # Sort by quality score (number of quality features)
    premium_items.sort(key=lambda x: len([v for v in x.get('quality_features', {}).values() if v]), reverse=True)
    return premium_items[:limit]

def get_trending_rail(library_items: List[Dict], limit: int) -> List[Dict]:
    """Get trending content for mobile"""
    # Simple trending based on recent year and high rating
    trending = [item for item in library_items if item.get('year', 0) >= 2020]
    trending.sort(key=lambda x: (x.get('year', 0), x.get('rating', 0)), reverse=True)
    return trending[:limit]

def get_discovery_rail(library_items: List[Dict], limit: int) -> List[Dict]:
    """Get discovery content for mobile"""
    # Hidden gems - high rating but older content
    discovery = [item for item in library_items if item.get('rating', 0) >= 8.5]
    discovery.sort(key=lambda x: x.get('rating', 0), reverse=True)
    return discovery[:limit]

def get_collections_rail(limit: int) -> List[Dict]:
    """Get collections for mobile"""
    # Mock collections data
    collections = [
        {
            'id': 'mcu',
            'title': 'Marvel Cinematic Universe',
            'type': 'collection',
            'year': 2024,
            'rating': 8.2,
            'overview': 'The complete Marvel Cinematic Universe collection',
            'poster': 'https://image.tmdb.org/t/p/w500/yFuKvT4Vm3sKHdFY4eG6I4ldAnn.jpg',
            'genres': ['Action', 'Adventure', 'Sci-Fi'],
            'quality_features': {'4k_uhd': True, 'hdr': True},
            'item_count': 32
        },
        {
            'id': 'nolan',
            'title': 'Christopher Nolan Collection',
            'type': 'collection',
            'year': 2023,
            'rating': 8.8,
            'overview': 'Complete filmography of Christopher Nolan',
            'poster': 'https://image.tmdb.org/t/p/w500/6P3c80EOm7BodndGBUAJHHsHKrp.jpg',
            'genres': ['Sci-Fi', 'Thriller', 'Drama'],
            'quality_features': {'4k_uhd': True, 'hdr': True, 'atmos': True},
            'item_count': 11
        }
    ]
    
    return collections[:limit]

def optimize_for_mobile(items: List[Dict], rail_type: str) -> List[Dict]:
    """Optimize items for mobile display"""
    mobile_items = []
    
    for item in items:
        mobile_item = {
            'id': item.get('id'),
            'title': item.get('title', ''),
            'type': item.get('type', ''),
            'year': item.get('year'),
            'rating': item.get('rating'),
            'poster': item.get('poster'),
            'quality_features': item.get('quality_features', {}),
            'genres': item.get('genres', [])[:3],  # Limit genres for mobile
            'item_count': item.get('item_count')  # For collections
        }
        
        # Add mobile-specific optimizations
        mobile_item['mobile_optimized'] = True
        mobile_item['rail_type'] = rail_type
        
        mobile_items.append(mobile_item)
    
    return mobile_items

def find_item_by_id(item_id: str) -> Optional[Dict]:
    """Find item by ID in mock data"""
    mock_items = generate_mock_library_data()
    for item in mock_items:
        if str(item.get('id')) == str(item_id):
            return item
    return None

def get_available_actions(item: Dict) -> List[str]:
    """Get available actions for an item on mobile"""
    actions = ['view_details']
    
    item_type = item.get('type', '')
    
    if item_type in ['movie', 'tv']:
        actions.extend(['play', 'download', 'add_to_watchlist'])
    elif item_type == 'book':
        actions.extend(['read', 'download', 'add_to_library'])
    elif item_type == 'album':
        actions.extend(['play', 'download', 'add_to_playlist'])
    elif item_type == 'collection':
        actions.extend(['browse_collection', 'add_to_favorites'])
    
    return actions
