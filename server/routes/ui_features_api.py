"""
UI Features API - MediaHub v5.6
Backend APIs for hero banner, watch history, and UI enhancements
"""

from flask import Blueprint, jsonify, request
import json
import os
from datetime import datetime, timedelta
import random

ui_features_bp = Blueprint('ui_features', __name__)

# Storage paths
STORAGE_DIR = os.path.join(os.path.dirname(__file__), '..', '..', 'storage')
WATCH_HISTORY_FILE = os.path.join(STORAGE_DIR, 'watch_history.json')
FEATURED_CONTENT_FILE = os.path.join(STORAGE_DIR, 'featured_content.json')

# Ensure storage directory exists
os.makedirs(STORAGE_DIR, exist_ok=True)

# ============================================================================
# HERO BANNER APIs
# ============================================================================

@ui_features_bp.route('/api/home/hero', methods=['GET'])
def get_hero_content():
    """Get featured content for hero banner"""
    try:
        # Load featured content from file or database
        if os.path.exists(FEATURED_CONTENT_FILE):
            with open(FEATURED_CONTENT_FILE, 'r') as f:
                featured = json.load(f)
        else:
            # Generate default featured content
            featured = generate_default_featured_content()
            save_featured_content(featured)
        
        return jsonify({
            'success': True,
            'items': featured.get('items', []),
            'count': len(featured.get('items', []))
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'items': []
        }), 500


@ui_features_bp.route('/api/home/hero', methods=['POST'])
def update_hero_content():
    """Update featured content for hero banner"""
    try:
        data = request.get_json()
        items = data.get('items', [])
        
        featured = {
            'items': items,
            'updated_at': datetime.now().isoformat()
        }
        
        save_featured_content(featured)
        
        return jsonify({
            'success': True,
            'message': 'Featured content updated',
            'count': len(items)
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


# ============================================================================
# WATCH HISTORY APIs
# ============================================================================

@ui_features_bp.route('/api/watch_history/recent', methods=['GET'])
def get_recent_watch_history():
    """Get recent watch history for Continue Watching section"""
    try:
        limit = request.args.get('limit', 12, type=int)
        
        # Load watch history
        history = load_watch_history()
        
        # Filter items with progress > 0 and < 95%
        continue_watching = []
        for item in history.get('items', []):
            progress_percent = (item.get('progress', 0) / item.get('duration', 1)) * 100
            if 0 < progress_percent < 95:
                continue_watching.append(item)
        
        # Sort by last watched (most recent first)
        continue_watching.sort(
            key=lambda x: x.get('last_watched_timestamp', 0),
            reverse=True
        )
        
        # Limit results
        continue_watching = continue_watching[:limit]
        
        # Format for frontend
        formatted_items = []
        for item in continue_watching:
            formatted_items.append({
                'id': item.get('id'),
                'title': item.get('title'),
                'type': item.get('type'),
                'season': item.get('season'),
                'episode': item.get('episode'),
                'episodeTitle': item.get('episode_title'),
                'thumbnail': item.get('thumbnail'),
                'progress': item.get('progress', 0),
                'duration': item.get('duration', 0),
                'lastWatched': format_time_ago(item.get('last_watched_timestamp', 0))
            })
        
        return jsonify({
            'success': True,
            'items': formatted_items,
            'count': len(formatted_items)
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'items': []
        }), 500


@ui_features_bp.route('/api/watch_history/update', methods=['POST'])
def update_watch_history():
    """Update watch history (progress, timestamp)"""
    try:
        data = request.get_json()
        media_id = data.get('id')
        media_type = data.get('type')
        action = data.get('action', 'resume')
        progress = data.get('progress')
        duration = data.get('duration')
        
        if not media_id or not media_type:
            return jsonify({
                'success': False,
                'error': 'Missing required fields: id, type'
            }), 400
        
        # Load history
        history = load_watch_history()
        items = history.get('items', [])
        
        # Find existing item
        existing_item = None
        for item in items:
            if item.get('id') == media_id and item.get('type') == media_type:
                existing_item = item
                break
        
        # Update or create item
        if existing_item:
            existing_item['last_watched_timestamp'] = datetime.now().timestamp()
            if progress is not None:
                existing_item['progress'] = progress
            if duration is not None:
                existing_item['duration'] = duration
        else:
            # Create new item (would need to fetch metadata)
            new_item = {
                'id': media_id,
                'type': media_type,
                'title': data.get('title', f'{media_type.capitalize()} {media_id}'),
                'thumbnail': data.get('thumbnail', f'/api/placeholder/480/270?text={media_id}'),
                'progress': progress or 0,
                'duration': duration or 0,
                'last_watched_timestamp': datetime.now().timestamp()
            }
            
            if media_type == 'tv':
                new_item['season'] = data.get('season', 1)
                new_item['episode'] = data.get('episode', 1)
                new_item['episode_title'] = data.get('episode_title', '')
            
            items.append(new_item)
        
        # Save history
        history['items'] = items
        history['updated_at'] = datetime.now().isoformat()
        save_watch_history(history)
        
        return jsonify({
            'success': True,
            'message': 'Watch history updated'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@ui_features_bp.route('/api/watch_history/reset', methods=['POST'])
def reset_watch_progress():
    """Reset watch progress for a media item"""
    try:
        data = request.get_json()
        media_id = data.get('id')
        media_type = data.get('type')
        
        if not media_id or not media_type:
            return jsonify({
                'success': False,
                'error': 'Missing required fields: id, type'
            }), 400
        
        # Load history
        history = load_watch_history()
        items = history.get('items', [])
        
        # Find and reset item
        for item in items:
            if item.get('id') == media_id and item.get('type') == media_type:
                item['progress'] = 0
                item['last_watched_timestamp'] = datetime.now().timestamp()
                break
        
        # Save history
        history['items'] = items
        history['updated_at'] = datetime.now().isoformat()
        save_watch_history(history)
        
        return jsonify({
            'success': True,
            'message': 'Progress reset'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@ui_features_bp.route('/api/watch_history/<int:media_id>', methods=['DELETE'])
def delete_watch_history_item(media_id):
    """Remove item from watch history"""
    try:
        # Load history
        history = load_watch_history()
        items = history.get('items', [])
        
        # Remove item
        items = [item for item in items if item.get('id') != media_id]
        
        # Save history
        history['items'] = items
        history['updated_at'] = datetime.now().isoformat()
        save_watch_history(history)
        
        return jsonify({
            'success': True,
            'message': 'Item removed from watch history'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def load_watch_history():
    """Load watch history from file"""
    if os.path.exists(WATCH_HISTORY_FILE):
        try:
            with open(WATCH_HISTORY_FILE, 'r') as f:
                return json.load(f)
        except:
            pass
    return {'items': [], 'updated_at': datetime.now().isoformat()}


def save_watch_history(history):
    """Save watch history to file"""
    with open(WATCH_HISTORY_FILE, 'w') as f:
        json.dump(history, f, indent=2)


def load_featured_content():
    """Load featured content from file"""
    if os.path.exists(FEATURED_CONTENT_FILE):
        try:
            with open(FEATURED_CONTENT_FILE, 'r') as f:
                return json.load(f)
        except:
            pass
    return generate_default_featured_content()


def save_featured_content(featured):
    """Save featured content to file"""
    with open(FEATURED_CONTENT_FILE, 'w') as f:
        json.dump(featured, f, indent=2)


def generate_default_featured_content():
    """Generate default featured content"""
    return {
        'items': [
            {
                'id': 1,
                'title': 'The Matrix Resurrections',
                'year': 2021,
                'rating': 8.7,
                'quality': '4K',
                'description': 'Return to a world of two realities: one, everyday life; the other, what lies behind it. To find out if his reality is a physical or mental construct, to truly know himself, Mr. Anderson will have to choose to follow the white rabbit once more.',
                'backdrop': '/api/placeholder/1920/1080?text=Matrix',
                'mediaType': 'movie'
            },
            {
                'id': 2,
                'title': 'Stranger Things',
                'year': 2022,
                'rating': 9.1,
                'quality': 'HD',
                'description': 'When a young boy disappears, his mother, a police chief and his friends must confront terrifying supernatural forces in order to get him back.',
                'backdrop': '/api/placeholder/1920/1080?text=Stranger+Things',
                'mediaType': 'tv'
            },
            {
                'id': 3,
                'title': 'Dune',
                'year': 2021,
                'rating': 8.5,
                'quality': '4K',
                'description': 'A noble family becomes embroiled in a war for control over the galaxy\'s most valuable asset while its heir becomes troubled by visions of a dark future.',
                'backdrop': '/api/placeholder/1920/1080?text=Dune',
                'mediaType': 'movie'
            }
        ],
        'updated_at': datetime.now().isoformat()
    }


def format_time_ago(timestamp):
    """Format timestamp as 'X time ago'"""
    if not timestamp:
        return 'Unknown'
    
    try:
        dt = datetime.fromtimestamp(timestamp)
        now = datetime.now()
        diff = now - dt
        
        seconds = diff.total_seconds()
        
        if seconds < 60:
            return 'Just now'
        elif seconds < 3600:
            minutes = int(seconds / 60)
            return f'{minutes} minute{"s" if minutes != 1 else ""} ago'
        elif seconds < 86400:
            hours = int(seconds / 3600)
            return f'{hours} hour{"s" if hours != 1 else ""} ago'
        elif seconds < 604800:
            days = int(seconds / 86400)
            return f'{days} day{"s" if days != 1 else ""} ago'
        elif seconds < 2592000:
            weeks = int(seconds / 604800)
            return f'{weeks} week{"s" if weeks != 1 else ""} ago'
        else:
            months = int(seconds / 2592000)
            return f'{months} month{"s" if months != 1 else ""} ago'
    except:
        return 'Unknown'
