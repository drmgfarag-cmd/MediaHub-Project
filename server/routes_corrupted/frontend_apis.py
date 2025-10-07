"""
API Routes for Frontend Pages
Connects new frontend pages to database models
"""
from flask import Blueprint, jsonify, request
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from models import (
        WatchHistory, Favorites, Collections, Recommendations,
        Calendar, RealDebrid, Comics
    )
except ImportError:
    # Fallback if models not in path
    import models
    WatchHistory = models.WatchHistory
    Favorites = models.Favorites
    Collections = models.Collections
    Recommendations = models.Recommendations
    Calendar = models.Calendar
    RealDebrid = models.RealDebrid
    Comics = models.Comics

bp = Blueprint('frontend_apis', __name__)

# Watch History Routes
@bp.route('/api/watch-history', methods=['GET'])
def get_watch_history():
    """Get watch history"""
    try:
        limit = request.args.get('limit', 50, type=int)
        history = WatchHistory.get_recent(limit)
        return jsonify({'success': True, 'history': history})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@bp.route('/api/watch-history', methods=['POST'])
def add_watch_history():
    """Add/update watch history"""
    try:
        data = request.get_json()
        WatchHistory.add_or_update(
            data['media_id'],
            data['media_type'],
            data['title'],
            data.get('progress', 0),
            data.get('duration', 0),
            **data
        )
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@bp.route('/api/watch-history', methods=['DELETE'])
def clear_watch_history():
    """Clear all watch history"""
    try:
        # Implementation would clear all history
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# Favorites Routes
@bp.route('/api/favorites', methods=['GET'])
def get_favorites():
    """Get all favorites"""
    try:
        favorites = Favorites.get_all()
        return jsonify({'success': True, 'favorites': favorites})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@bp.route('/api/favorites', methods=['POST'])
def add_favorite():
    """Add to favorites"""
    try:
        data = request.get_json()
        success = Favorites.add(
            data['media_id'],
            data['media_type'],
            data['title'],
            **data
        )
        return jsonify({'success': success})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@bp.route('/api/favorites/<media_id>', methods=['DELETE'])
def remove_favorite(media_id):
    """Remove from favorites"""
    try:
        Favorites.remove(media_id)
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@bp.route('/api/favorites/<media_id>/check', methods=['GET'])
def check_favorite(media_id):
    """Check if media is favorited"""
    try:
        is_fav = Favorites.is_favorite(media_id)
        return jsonify({'success': True, 'is_favorite': is_fav})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# Recommendations Routes
@bp.route('/api/recommendations', methods=['GET'])
def get_recommendations():
    """Get recommendations"""
    try:
        limit = request.args.get('limit', 20, type=int)
        recs = Recommendations.get_active(limit)
        return jsonify({'success': True, 'recommendations': recs})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@bp.route('/api/recommendations/<int:rec_id>/dismiss', methods=['POST'])
def dismiss_recommendation(rec_id):
    """Dismiss recommendation"""
    try:
        Recommendations.dismiss(rec_id)
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# Calendar Routes
@bp.route('/api/calendar', methods=['GET'])
def get_calendar():
    """Get calendar events"""
    try:
        days = request.args.get('days', 30, type=int)
        events = Calendar.get_upcoming(days)
        return jsonify({'success': True, 'events': events})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# Real-Debrid Routes
@bp.route('/api/rd/downloads', methods=['GET'])
def get_rd_downloads():
    """Get RD downloads"""
    try:
        downloads = RealDebrid.get_active()
        return jsonify({'success': True, 'downloads': downloads})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@bp.route('/api/rd/add', methods=['POST'])
def add_rd_download():
    """Add RD download"""
    try:
        data = request.get_json()
        link = data.get('link')
        # This would integrate with Real-Debrid API
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@bp.route('/api/rd/downloads/<rd_id>', methods=['DELETE'])
def delete_rd_download(rd_id):
    """Delete RD download"""
    try:
        # Implementation would delete from RD
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# Comics Routes
@bp.route('/api/comics', methods=['GET'])
def get_comics():
    """Get comics library"""
    try:
        comics = Comics.get_all()
        return jsonify({'success': True, 'comics': comics})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@bp.route('/api/comics/<int:comic_id>/progress', methods=['POST'])
def update_comic_progress(comic_id):
    """Update comic reading progress"""
    try:
        data = request.get_json()
        Comics.update_progress(comic_id, data['current_page'])
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# Register blueprint
def register_routes(app):
    """Register all frontend API routes"""
    app.register_blueprint(bp)
    print("✅ Frontend API routes registered")

