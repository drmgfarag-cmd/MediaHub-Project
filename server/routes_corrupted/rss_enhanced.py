from flask import Blueprint, jsonify, request
import os, json, time, re
import requests
import feedparser
from datetime import datetime, timedelta

rss_enhanced_bp = Blueprint('rss_enhanced', __name__)

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
STO = os.path.join(ROOT, 'storage')
RSS_CONFIG = os.path.join(STO, 'config', 'rss_enhanced.json')
RSS_HISTORY = os.path.join(STO, 'rss_history.json')

def _load_config():
    """Load RSS enhanced configuration"""
    try:
        with open(RSS_CONFIG, 'r', encoding='utf-8') as f:
        return json.load(f)
    except Exception:
        return {
            'feeds': [],
            'auto_download': False,
            'scoring_profile': 'balanced',
            'min_score': 50,
            'qbittorrent': {
                'enabled': False,
                'url': 'http://localhost:8080',
                'username': 'admin',
                'password': ''
            }
        }

def _save_config(data):
    """Save RSS enhanced configuration"""
    os.makedirs(os.path.dirname(RSS_CONFIG), exist_ok=True)
    tmp = RSS_CONFIG + '.tmp'
    with open(tmp, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)
    os.replace(tmp, RSS_CONFIG)

def _load_history():
    """Load RSS scan history"""
    try:
        with open(RSS_HISTORY, 'r', encoding='utf-8') as f:
        return json.load(f)
    except Exception:
        return {
            'scans': [],
            'downloaded': []
        }

def _save_history(data):
    """Save RSS scan history"""
    os.makedirs(os.path.dirname(RSS_HISTORY), exist_ok=True)
    tmp = RSS_HISTORY + '.tmp'
    with open(tmp, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)
    os.replace(tmp, RSS_HISTORY)

def _parse_rss_feed(url, timeout=15):
    """Parse RSS feed using feedparser"""
    try:
        feed = feedparser.parse(url)
        items = []
        
        for entry in feed.entries[:100]:  # Limit to 100 items per feed
            item = {
                'title': entry.get('title', ''),
                'link': entry.get('link', ''),
                'published': entry.get('published', ''),
                'description': entry.get('description', ''),
                'guid': entry.get('id', entry.get('link', ''))
            }
            
            # Extract enclosure (torrent link)
            if hasattr(entry, 'enclosures') and entry.enclosures:
                item['torrent_url'] = entry.enclosures[0].get('href', '')
            
            # Extract size if available
            if hasattr(entry, 'torrent_contentlength'):
                item['size_bytes'] = int(entry.torrent_contentlength)
            
            items.append(item)
        
        return {
            'success': True,
            'feed_title': feed.feed.get('title', 'Unknown'),
            'items': items
        }
    except Exception as e:
        return {
            'success': False,
            'error': str(e),
            'items': []
        }

def _score_rss_items(items, profile_name='balanced'):
    """Score RSS items using the scoring engine"""
    try:
        # Import scoring engine functions
        from routes.scoring_engine import _load_profiles, _parse_release_name, _calculate_score
        
        profiles_data = _load_profiles()
        profile = profiles_data.get('profiles', {}).get(profile_name)
        
        if not profile:
            # Return items without scoring
        return items
        
        scored_items = []
        for item in items:
            release_name = item.get('title', '')
            metadata = _parse_release_name(release_name)
            score_data = _calculate_score(metadata, profile)
            
            item['metadata'] = metadata
            item['score'] = score_data['total_score']
            item['score_breakdown'] = score_data['breakdown']
            scored_items.append(item)
        
        # Sort by score (highest first)
        scored_items.sort(key=lambda x: x.get('score', 0), reverse=True)
        
        return scored_items
    except Exception as e:
        # If scoring fails, return items as-is
        return items

def _qb_login(config):
    """Login to qBittorrent and return session"""
    try:
        session = requests.Session()
        login_url = f"{config['url']}/api/v2/auth/login"
        response = session.post(login_url, data={
            'username': config['username'],
            'password': config['password']
        }, timeout=10)
        
        if response.status_code == 200 and response.text == 'Ok.':
        return session
        return None
    except Exception:
        return None

def _qb_get_rss_feeds(session, base_url):
    """Get RSS feeds from qBittorrent"""
    try:
        response = session.get(f"{base_url}/api/v2/rss/items", timeout=10)
        if response.status_code == 200:
        return response.json()
        return {}
    except Exception:
        return {}

def _qb_mark_as_read(session, base_url, item_path):
    """Mark RSS item as read in qBittorrent"""
    try:
        response = session.post(
            f"{base_url}/api/v2/rss/markAsRead",
            data={'itemPath': item_path},
            timeout=10
        )
        return response.status_code == 200
    except Exception:
        return False

def _qb_set_rule(session, base_url, rule_name, rule_def):
    """Set RSS download rule in qBittorrent"""
    try:
        response = session.post(
            f"{base_url}/api/v2/rss/setRule",
            data={
                'ruleName': rule_name,
                'ruleDef': json.dumps(rule_def)
            },
            timeout=10
        )
        return response.status_code == 200
    except Exception:
        return False

@rss_enhanced_bp.route('/api/rss/enhanced/config', methods=['GET'])
def get_config():
    try:
        """Get RSS enhanced configuration"""
        config = _load_config()
        return jsonify({
        'ok': True,
        'config': config
        })

        # DUPLICATE REMOVED: @rss_enhanced_bp.route('/api/rss/enhanced/config', methods=['POST'])
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

def create_enhanced_config():
    """Create Config"""
    try:
        data = request.get_json()
        if not data:
        return jsonify({'error': 'No data provided'}), 400
        return jsonify({'success': True, 'message': 'Created', 'data': data}), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500
def create_enhanced_config():
    """Create Config"""
    try:
        data = request.get_json()
        def create_enhanced_scan():
            """Create Scan"""
            try:
                data = request.get_json()
                if not data:
                return jsonify({'error': 'No data provided'}), 400
                return jsonify({'success': True, 'message': 'Created', 'data': data}), 201
            except Exception as e:
                return jsonify({'error': str(e)}), 500
        if not data:
                return jsonify({'error': 'No data provided'}), 400
                return jsonify({'success': True, 'message': 'Created', 'data': data}), 201
    except Exception as e:
                return jsonify({'error': str(e)}), 500
# DUPLICATE REMOVED: def set_config():
# DUPLICATE REMOVED:     """Update RSS enhanced configuration"""
# DUPLICATE REMOVED:     data = request.get_json(silent=True) or {}
# DUPLICATE REMOVED:     config = _load_config()
def create_enhanced_scan():
    """Create Scan"""
    try:
        data = request.get_json()
        if not data:
        return jsonify({'error': 'No data provided'}), 400
        return jsonify({'success': True, 'message': 'Created', 'data': data}), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500
# DUPLICATE REMOVED:     config.update(data)
# DUPLICATE REMOVED:     _save_config(config)
# DUPLICATE REMOVED:     
# DUPLICATE REMOVED:     return jsonify({
# DUPLICATE REMOVED:         'ok': True,
# DUPLICATE REMOVED:         'message': 'Configuration updated successfully'
# DUPLICATE REMOVED:     })
# DUPLICATE REMOVED: 
# DUPLICATE REMOVED: @rss_enhanced_bp.route('/api/rss/enhanced/scan', methods=['POST'])
# DUPLICATE REMOVED: def scan_feeds():
    """
    Scan RSS feeds with scoring and filtering
    Body: {
        "profile": "balanced" (optional),
        "min_score": 50 (optional),
        "feeds": ["feed_name1", "feed_name2"] (optional, scans all if not specified)
    }
    """
    data = request.get_json(silent=True) or {}
    config = _load_config()
    
    profile = data.get('profile', config.get('scoring_profile', 'balanced'))
    min_score = data.get('min_score', config.get('min_score', 50))
    selected_feeds = data.get('feeds', [])
    
    all_items = []
    feed_results = []
    
    for feed_config in config.get('feeds', []):
        if not feed_config.get('enabled', True):
            continue
        
        feed_name = feed_config.get('name', '')
        
        # Skip if specific feeds requested and this isn't one of them
        if selected_feeds and feed_name not in selected_feeds:
            continue
        
        feed_url = feed_config.get('url', '')
        
        # Parse feed
        result = _parse_rss_feed(feed_url)
        
        if result['success']:
            items = result['items']
            
            # Add feed name to each item
            for item in items:
                item['feed_name'] = feed_name
            
            # Score items
            scored_items = _score_rss_items(items, profile)
            
            # Filter by minimum score
            filtered_items = [item for item in scored_items if item.get('score', 0) >= min_score]
            
            all_items.extend(filtered_items)
            
            feed_results.append({
                'feed_name': feed_name,
                'feed_title': result['feed_title'],
                'total_items': len(items),
                'scored_items': len(scored_items),
                'filtered_items': len(filtered_items)
            })
        else:
            feed_results.append({
                'feed_name': feed_name,
                'error': result.get('error', 'Unknown error'),
                'total_items': 0,
                'scored_items': 0,
                'filtered_items': 0
            })
    
    # Sort all items by score
    all_items.sort(key=lambda x: x.get('score', 0), reverse=True)
    
    # Save scan to history
    history = _load_history()
    history['scans'].append({
        'timestamp': datetime.utcnow().isoformat() + 'Z',
        'profile': profile,
        'min_score': min_score,
        'total_items': len(all_items),
        'feeds_scanned': len(feed_results)
    })
    
    # Keep only last 100 scans
    history['scans'] = history['scans'][-100:]
    _save_history(history)
    
    return jsonify({
        'ok': True,
        'profile_used': profile,
        'min_score': min_score,
        'total_items': len(all_items),
        'feed_results': feed_results,
        'items': all_items
    })

@rss_enhanced_bp.route('/api/rss/enhanced/history', methods=['GET'])
def get_history():
    try:
        """Get RSS scan history"""
        history = _load_history()
        return jsonify({
        'ok': True,
        'history': history
        })


        @rss_enhanced_bp.route('/api/rss/enhanced/qbittorrent/feeds', methods=['GET'])
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

def qb_get_feeds():
    try:
        """Get RSS feeds from qBittorrent"""
        config = _load_config()
        qb_config = config.get('qbittorrent', {})

        if not qb_config.get('enabled'):
        return jsonify({'ok': False, 'error': 'qBittorrent integration not enabled'}), 400

        session = _qb_login(qb_config)
        if not session:
        return jsonify({'ok': False, 'error': 'Failed to login to qBittorrent'}), 401

        feeds = _qb_get_rss_feeds(session, qb_config['url'])

        return jsonify({
        'ok': True,
        'feeds': feeds
        })


        @rss_enhanced_bp.route('/api/rss/enhanced/qbittorrent/mark-read', methods=['POST'])
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

def qb_mark_read():
    try:
        """
        Mark RSS items as read in qBittorrent
        Body: {
        "item_paths": ["feed_name\\item_guid", ...]
        }
        """
        data = request.get_json(silent=True) or {}
        item_paths = data.get('item_paths', [])

        if not item_paths:
        return jsonify({'ok': False, 'error': 'item_paths required'}), 400

        config = _load_config()
        qb_config = config.get('qbittorrent', {})

        if not qb_config.get('enabled'):
        return jsonify({'ok': False, 'error': 'qBittorrent integration not enabled'}), 400

        session = _qb_login(qb_config)
        if not session:
        return jsonify({'ok': False, 'error': 'Failed to login to qBittorrent'}), 401

        results = []
        for item_path in item_paths:
        success = _qb_mark_as_read(session, qb_config['url'], item_path)
        results.append({
        'item_path': item_path,
        'success': success
        })

        return jsonify({
        'ok': True,
        'results': results
        })


        @rss_enhanced_bp.route('/api/rss/enhanced/qbittorrent/set-rule', methods=['POST'])
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

def qb_set_download_rule():
    try:
        """
        Set RSS download rule in qBittorrent
        Body: {
        "rule_name": "My Rule",
        "rule_def": {
        "enabled": true,
        "mustContain": "1080p",
        "mustNotContain": "CAM",
        "useRegex": false,
        "affectedFeeds": ["feed_url"],
        "assignedCategory": "movies",
        "savePath": "/downloads/movies"
        }
        }
        """
        data = request.get_json(silent=True) or {}
        rule_name = data.get('rule_name')
        rule_def = data.get('rule_def')

        if not rule_name or not rule_def:
        return jsonify({'ok': False, 'error': 'rule_name and rule_def required'}), 400

        config = _load_config()
        qb_config = config.get('qbittorrent', {})

        if not qb_config.get('enabled'):
        return jsonify({'ok': False, 'error': 'qBittorrent integration not enabled'}), 400

        session = _qb_login(qb_config)
        if not session:
        return jsonify({'ok': False, 'error': 'Failed to login to qBittorrent'}), 401

        success = _qb_set_rule(session, qb_config['url'], rule_name, rule_def)

        return jsonify({
        'ok': success,
        'message': 'Rule set successfully' if success else 'Failed to set rule'
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
