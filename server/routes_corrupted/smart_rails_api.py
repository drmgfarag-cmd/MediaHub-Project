"""
Smart Rails API - Endpoints for intelligent content organization
Provides API access to smart rails functionality
"""

from flask import Blueprint, jsonify, request
import os
import json
import logging
from datetime import datetime
import sqlite3
from utils.smart_rails_engine import generate_smart_rails_for_library

smart_rails_bp = Blueprint('smart_rails_api', __name__)
logger = logging.getLogger(__name__)

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
STO = os.path.join(ROOT, 'storage')
DB_PATH = os.path.join(STO, 'mediahub.db')

def get_library_items():
    """Get all library items from database"""
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Get items from various tables
        cursor.execute("""
            SELECT 'movie' as type, path, filename, metadata, year, genres, rating
            FROM movies 
            UNION ALL
            SELECT 'series' as type, path, filename, metadata, year, genres, rating
            FROM tv_series
            UNION ALL
            SELECT 'book' as type, path, filename, metadata, year, genres, rating
            FROM books
            UNION ALL
            SELECT 'audio' as type, path, filename, metadata, year, genres, rating
            FROM audio_tracks
        """)
        
        items = []
        for row in cursor.fetchall():
            item = dict(row)
            # Parse metadata if it's JSON string
            if item.get('metadata') and isinstance(item['metadata'], str):
                try:
                    item['metadata'] = json.loads(item['metadata'])
                except json.JSONDecodeError:
                    item['metadata'] = {}
            
            items.append(item)
        
        conn.close()
                    return items
        
    except Exception as e:
        logger.error(f"Error getting library items: {e}")
                    return []

@smart_rails_bp.route('/api/smart_rails/generate', methods=['POST'])
def generate_rails():
    """Generate smart rails for the entire library"""
    try:
        # Get library items
        library_items = get_library_items()
        
        if not library_items:
        return jsonify({
                'success': False,
                'message': 'No library items found',
                'rails': {}
            })
        
        # Generate smart rails
        result = generate_smart_rails_for_library(library_items)
        
        # Cache the results
        cache_path = os.path.join(STO, 'smart_rails_cache.json')
        os.makedirs(os.path.dirname(cache_path), exist_ok=True)
        
        with open(cache_path, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        
        return jsonify({
            'success': True,
            'message': f'Generated {result["total_rails"]} smart rails',
            'rails': result['rails'],
            'stats': {
                'total_rails': result['total_rails'],
                'total_items': result['total_items'],
                'library_size': len(library_items),
                'generated_at': result['generated_at']
            }
        })
        
    except Exception as e:
        logger.error(f"Error generating smart rails: {e}")
        return jsonify({
            'success': False,
            'error': str(e),
            'rails': {}
        }), 500

@smart_rails_bp.route('/api/smart_rails/list')
def list_rails():
    """List all available smart rails"""
    try:
        cache_path = os.path.join(STO, 'smart_rails_cache.json')
        
        if not os.path.exists(cache_path):
            # Generate rails if cache doesn't exist
        return generate_rails()
        
        with open(cache_path, 'r', encoding='utf-8') as f:
            cached_result = json.load(f)
        
        # Return just the rail metadata and counts
        rails_summary = {}
        for rail_name, rail_data in cached_result.get('rails', {}).items():
            rails_summary[rail_name] = {
                'metadata': rail_data.get('metadata', {}),
                'count': rail_data.get('count', 0),
                'last_updated': rail_data.get('last_updated')
            }
        
        return jsonify({
            'success': True,
            'rails': rails_summary,
            'total_rails': len(rails_summary),
            'cache_generated_at': cached_result.get('generated_at')
        })
        
    except Exception as e:
        logger.error(f"Error listing smart rails: {e}")
        return jsonify({
            'success': False,
            'error': str(e),
            'rails': {}
        }), 500

@smart_rails_bp.route('/api/smart_rails/get/<rail_name>')
def get_rail(rail_name):
    """Get items from a specific smart rail"""
    try:
        cache_path = os.path.join(STO, 'smart_rails_cache.json')
        
        if not os.path.exists(cache_path):
        return jsonify({
                'success': False,
                'message': 'Smart rails not generated yet. Call /api/smart_rails/generate first.',
                'items': []
            }), 404
        
        with open(cache_path, 'r', encoding='utf-8') as f:
            cached_result = json.load(f)
        
        rail_data = cached_result.get('rails', {}).get(rail_name)
        
        if not rail_data:
        return jsonify({
                'success': False,
                'message': f'Rail "{rail_name}" not found',
                'items': []
            }), 404
        
        # Get pagination parameters
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        
        items = rail_data.get('items', [])
        total_items = len(items)
        
        # Apply pagination
        start_idx = (page - 1) * per_page
        end_idx = start_idx + per_page
        paginated_items = items[start_idx:end_idx]
        
        return jsonify({
            'success': True,
            'rail_name': rail_name,
            'metadata': rail_data.get('metadata', {}),
            'items': paginated_items,
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total_items': total_items,
                'total_pages': (total_items + per_page - 1) // per_page,
                'has_next': end_idx < total_items,
                'has_prev': page > 1
            },
            'last_updated': rail_data.get('last_updated')
        })
        
    except Exception as e:
        logger.error(f"Error getting rail {rail_name}: {e}")
        return jsonify({
            'success': False,
            'error': str(e),
            'items': []
        }), 500

@smart_rails_bp.route('/api/smart_rails/refresh', methods=['POST'])
def refresh_rails():
    """Refresh smart rails (regenerate from current library)"""
    try:
        # Clear cache
        cache_path = os.path.join(STO, 'smart_rails_cache.json')
        if os.path.exists(cache_path):
            os.remove(cache_path)
        
        # Regenerate
        return generate_rails()
        
    except Exception as e:
        logger.error(f"Error refreshing smart rails: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@smart_rails_bp.route('/api/smart_rails/stats')
def get_stats():
    """Get smart rails statistics"""
    try:
        cache_path = os.path.join(STO, 'smart_rails_cache.json')
        
        if not os.path.exists(cache_path):
        return jsonify({
                'success': False,
                'message': 'Smart rails not generated yet',
                'stats': {}
            })
        
        with open(cache_path, 'r', encoding='utf-8') as f:
            cached_result = json.load(f)
        
        rails = cached_result.get('rails', {})
        
        # Calculate statistics
        stats = {
            'total_rails': len(rails),
            'total_items': sum(rail.get('count', 0) for rail in rails.values()),
            'rails_by_category': {},
            'top_rails': [],
            'generated_at': cached_result.get('generated_at'),
            'cache_age_hours': 0
        }
        
        # Calculate cache age
        if cached_result.get('generated_at'):
            try:
                generated_time = datetime.fromisoformat(cached_result['generated_at'])
                cache_age = datetime.now() - generated_time
                stats['cache_age_hours'] = cache_age.total_seconds() / 3600
            except ValueError:
                pass
        
        # Group by category
        for rail_name, rail_data in rails.items():
            metadata = rail_data.get('metadata', {})
            category = metadata.get('category', 'general')
            
            if category not in stats['rails_by_category']:
                stats['rails_by_category'][category] = {
                    'count': 0,
                    'total_items': 0,
                    'rails': []
                }
            
            stats['rails_by_category'][category]['count'] += 1
            stats['rails_by_category'][category]['total_items'] += rail_data.get('count', 0)
            stats['rails_by_category'][category]['rails'].append(rail_name)
        
        # Top rails by item count
        rail_counts = [(name, data.get('count', 0)) for name, data in rails.items()]
        stats['top_rails'] = sorted(rail_counts, key=lambda x: x[1], reverse=True)[:10]
        
        return jsonify({
            'success': True,
            'stats': stats
        })
        
    except Exception as e:
        logger.error(f"Error getting smart rails stats: {e}")
        return jsonify({
            'success': False,
            'error': str(e),
            'stats': {}
        }), 500

@smart_rails_bp.route('/api/smart_rails/search')
def search_rails():
    """Search for content across all smart rails"""
    try:
        query = request.args.get('q', '').strip()
        if not query:
        return jsonify({
                'success': False,
                'message': 'Search query required',
                'results': []
            }), 400
        
        cache_path = os.path.join(STO, 'smart_rails_cache.json')
        
        if not os.path.exists(cache_path):
        return jsonify({
                'success': False,
                'message': 'Smart rails not generated yet',
                'results': []
            })
        
        with open(cache_path, 'r', encoding='utf-8') as f:
            cached_result = json.load(f)
        
        results = []
        query_lower = query.lower()
        
        # Search across all rails
        for rail_name, rail_data in cached_result.get('rails', {}).items():
            items = rail_data.get('items', [])
            
            for item in items:
                # Search in filename and path
                filename = item.get('filename', '').lower()
                path = item.get('path', '').lower()
                
                if query_lower in filename or query_lower in path:
                    results.append({
                        'item': item,
                        'rail': rail_name,
                        'rail_metadata': rail_data.get('metadata', {}),
                        'match_type': 'filename' if query_lower in filename else 'path'
                    })
        
        # Limit results
        results = results[:100]
        
        return jsonify({
            'success': True,
            'query': query,
            'results': results,
            'total_results': len(results)
        })
        
    except Exception as e:
        logger.error(f"Error searching smart rails: {e}")
        return jsonify({
            'success': False,
            'error': str(e),
            'results': []
        }), 500
