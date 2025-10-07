"""
UI/UX Golden Surface APIs - Master Rulebook Compliance
Provides locale/i18n and HLS streaming functionality
"""
from flask import Blueprint, request, jsonify, send_file
import os
import json
from datetime import datetime

uiux_golden_bp = Blueprint('uiux_golden', __name__)

# Storage paths
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
STORAGE = os.path.join(ROOT, 'storage')
LOCALE_PATH = os.path.join(STORAGE, 'locale_config.json')
HLS_SESSIONS_PATH = os.path.join(STORAGE, 'hls_sessions.json')

def load_json(path, default=None):
    """Load JSON file with default fallback"""
    if default is None:
        default = {}
    try:
        if os.path.exists(path):
            with open(path, 'r', encoding='utf-8') as f:
                return json.load(f)
    except:
        pass
    return default

def save_json(path, data):
    """Save JSON file"""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)

@uiux_golden_bp.route('/api/ui/locale', methods=['GET', 'POST'])
def ui_locale():
    """Get or set UI locale/language configuration"""
    if request.method == 'POST':
        data = request.get_json() or {}
        locale = data.get('locale', 'en')
        direction = data.get('direction', 'ltr')
        
        config = {
            'locale': locale,
            'direction': direction,
            'date_format': data.get('date_format', 'YYYY-MM-DD'),
            'time_format': data.get('time_format', '24h'),
            'number_format': data.get('number_format', 'en-US'),
            'currency': data.get('currency', 'USD'),
            'timezone': data.get('timezone', 'UTC'),
            'updated_at': datetime.now().isoformat()
        }
        
        save_json(LOCALE_PATH, config)
        
        return jsonify({
            'success': True,
            'config': config
        })
    
    else:
        # GET: Return current locale configuration
        config = load_json(LOCALE_PATH, {
            'locale': 'en',
            'direction': 'ltr',
            'date_format': 'YYYY-MM-DD',
            'time_format': '24h',
            'number_format': 'en-US',
            'currency': 'USD',
            'timezone': 'UTC'
        })
        
        # Add available locales
        available_locales = [
            {
                'code': 'en',
                'name': 'English',
                'native_name': 'English',
                'direction': 'ltr'
            },
            {
                'code': 'ar',
                'name': 'Arabic',
                'native_name': 'العربية',
                'direction': 'rtl'
            },
            {
                'code': 'es',
                'name': 'Spanish',
                'native_name': 'Español',
                'direction': 'ltr'
            },
            {
                'code': 'fr',
                'name': 'French',
                'native_name': 'Français',
                'direction': 'ltr'
            },
            {
                'code': 'de',
                'name': 'German',
                'native_name': 'Deutsch',
                'direction': 'ltr'
            },
            {
                'code': 'it',
                'name': 'Italian',
                'native_name': 'Italiano',
                'direction': 'ltr'
            },
            {
                'code': 'ja',
                'name': 'Japanese',
                'native_name': '日本語',
                'direction': 'ltr'
            },
            {
                'code': 'ko',
                'name': 'Korean',
                'native_name': '한국어',
                'direction': 'ltr'
            },
            {
                'code': 'zh',
                'name': 'Chinese',
                'native_name': '中文',
                'direction': 'ltr'
            },
            {
                'code': 'ru',
                'name': 'Russian',
                'native_name': 'Русский',
                'direction': 'ltr'
            }
        ]
        
        return jsonify({
            'success': True,
            'config': config,
            'available_locales': available_locales
        })

@uiux_golden_bp.route('/api/streaming/hls', methods=['POST', 'GET', 'DELETE'])
def streaming_hls():
    """HLS streaming session management"""
    
    if request.method == 'POST':
        # Start new HLS stream
        data = request.get_json() or {}
        media_path = data.get('media_path')
        quality = data.get('quality', 'auto')  # 'auto', '1080p', '720p', '480p'
        
        if not media_path:
            return jsonify({
                'success': False,
                'error': 'media_path required'
            }), 400
        
        if not os.path.exists(media_path):
            return jsonify({
                'success': False,
                'error': 'Media file not found'
            }), 404
        
        # Create session
        import uuid
        session_id = str(uuid.uuid4())
        
        session = {
            'id': session_id,
            'media_path': media_path,
            'quality': quality,
            'status': 'active',
            'created_at': datetime.now().isoformat(),
            'last_accessed': datetime.now().isoformat(),
            'playlist_url': f'/api/streaming/hls/{session_id}/playlist.m3u8',
            'segment_base_url': f'/api/streaming/hls/{session_id}/segment'
        }
        
        # Save session
        sessions = load_json(HLS_SESSIONS_PATH, {'sessions': {}})
        sessions['sessions'][session_id] = session
        save_json(HLS_SESSIONS_PATH, sessions)
        
        return jsonify({
            'success': True,
            'session': session
        })
    
    elif request.method == 'GET':
        # Get session info or list all sessions
        session_id = request.args.get('session_id')
        
        sessions = load_json(HLS_SESSIONS_PATH, {'sessions': {}})
        
        if session_id:
            session = sessions['sessions'].get(session_id)
            if session:
                # Update last accessed
                session['last_accessed'] = datetime.now().isoformat()
                sessions['sessions'][session_id] = session
                save_json(HLS_SESSIONS_PATH, sessions)
                
                return jsonify({
                    'success': True,
                    'session': session
                })
            else:
                return jsonify({
                    'success': False,
                    'error': 'Session not found'
                }), 404
        else:
            # List all active sessions
            return jsonify({
                'success': True,
                'sessions': list(sessions['sessions'].values()),
                'total': len(sessions['sessions'])
            })
    
    elif request.method == 'DELETE':
        # Stop/delete HLS stream session
        session_id = request.args.get('session_id')
        
        if not session_id:
            return jsonify({
                'success': False,
                'error': 'session_id required'
            }), 400
        
        sessions = load_json(HLS_SESSIONS_PATH, {'sessions': {}})
        
        if session_id in sessions['sessions']:
            del sessions['sessions'][session_id]
            save_json(HLS_SESSIONS_PATH, sessions)
            
            return jsonify({
                'success': True,
                'message': 'Session deleted'
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Session not found'
            }), 404

@uiux_golden_bp.route('/api/streaming/hls/<session_id>/playlist.m3u8', methods=['GET'])
def hls_playlist(session_id):
    """Serve HLS playlist for session"""
    sessions = load_json(HLS_SESSIONS_PATH, {'sessions': {}})
    session = sessions['sessions'].get(session_id)
    
    if not session:
        return jsonify({
            'success': False,
            'error': 'Session not found'
        }), 404
    
    # Generate simple HLS playlist
    playlist = """#EXTM3U
#EXT-X-VERSION:3
#EXT-X-TARGETDURATION:10
#EXT-X-MEDIA-SEQUENCE:0
#EXTINF:10.0,
/api/streaming/hls/{}/segment/0.ts
#EXTINF:10.0,
/api/streaming/hls/{}/segment/1.ts
#EXTINF:10.0,
/api/streaming/hls/{}/segment/2.ts
#EXT-X-ENDLIST
""".format(session_id, session_id, session_id)
    
    from flask import Response
    return Response(playlist, mimetype='application/vnd.apple.mpegurl')

@uiux_golden_bp.route('/api/streaming/hls/<session_id>/segment/<int:segment_id>.ts', methods=['GET'])
def hls_segment(session_id, segment_id):
    """Serve HLS segment for session"""
    sessions = load_json(HLS_SESSIONS_PATH, {'sessions': {}})
    session = sessions['sessions'].get(session_id)
    
    if not session:
        return jsonify({
            'success': False,
            'error': 'Session not found'
        }), 404
    
    media_path = session.get('media_path')
    
    # In production, this would transcode and serve actual segments
    # For now, return a simple response
    return jsonify({
        'success': False,
        'error': 'Segment generation not implemented (requires ffmpeg)'
    }), 501
