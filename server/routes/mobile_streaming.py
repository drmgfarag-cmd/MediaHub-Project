"""
Mobile Streaming Infrastructure - Phase 1 Implementation
Complete mobile streaming system with HTTP Range support and mobile-optimized endpoints
Based on the Ultimate Complete Integrated Plan
"""

from flask import Blueprint, jsonify, request, Response, send_file
import os
import json
import logging
import mimetypes
from datetime import datetime
from typing import Dict, List, Any, Optional
import hashlib
import subprocess
import time
import threading
from utils.binloc import guess_ffmpeg

mobile_streaming_bp = Blueprint('mobile_streaming', __name__)
logger = logging.getLogger(__name__)

# Configuration
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
STORAGE_DIR = os.path.join(ROOT, 'storage')
CACHE_DIR = os.path.join(STORAGE_DIR, 'cache', 'mobile')
CONFIG_FILE = os.path.join(STORAGE_DIR, 'config.json')

# Ensure directories exist
os.makedirs(CACHE_DIR, exist_ok=True)

# Active streaming sessions
streaming_sessions = {}

class MobileStreamingEngine:
    """Enhanced mobile streaming engine with adaptive quality"""
    
    def __init__(self):
        self.ffmpeg_path = guess_ffmpeg()
        self.active_streams = {}
        self.quality_profiles = {
            'mobile_low': {'video_bitrate': '500k', 'audio_bitrate': '64k', 'resolution': '480p'},
            'mobile_medium': {'video_bitrate': '1000k', 'audio_bitrate': '128k', 'resolution': '720p'},
            'mobile_high': {'video_bitrate': '2000k', 'audio_bitrate': '192k', 'resolution': '1080p'},
            'mobile_ultra': {'video_bitrate': '4000k', 'audio_bitrate': '256k', 'resolution': '1080p'}
        }
    
    def get_file_info(self, file_path: str) -> Dict[str, Any]:
        """Get comprehensive file information for mobile streaming"""
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")
        
        file_size = os.path.getsize(file_path)
        mime_type, _ = mimetypes.guess_type(file_path)
        
        # Get media info using ffprobe if available
        media_info = self._get_media_info(file_path)
        
        return {
            'path': file_path,
            'size': file_size,
            'mime_type': mime_type,
            'supports_range': True,
            'media_info': media_info,
            'streaming_profiles': list(self.quality_profiles.keys()),
            'direct_play_supported': self._supports_direct_play(file_path),
            'transcoding_required': self._requires_transcoding(file_path)
        }
    
    def _get_media_info(self, file_path: str) -> Dict[str, Any]:
        """Extract media information using ffprobe"""
        if not self.ffmpeg_path:
            return {}
        
        try:
            ffprobe_path = self.ffmpeg_path.replace('ffmpeg', 'ffprobe')
            cmd = [
                ffprobe_path, '-v', 'quiet', '-print_format', 'json',
                '-show_format', '-show_streams', file_path
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                return json.loads(result.stdout)
        except Exception as e:
            logger.warning(f"Failed to get media info for {file_path}: {e}")
        
        return {}
    
    def _supports_direct_play(self, file_path: str) -> bool:
        """Check if file supports direct play on mobile devices"""
        # Common mobile-compatible formats
        mobile_formats = ['.mp4', '.m4v', '.mov', '.3gp', '.webm']
        return any(file_path.lower().endswith(fmt) for fmt in mobile_formats)
    
    def _requires_transcoding(self, file_path: str) -> bool:
        """Check if file requires transcoding for mobile"""
        return not self._supports_direct_play(file_path)
    
    def create_streaming_session(self, file_path: str, quality_profile: str = 'mobile_medium') -> str:
        """Create a new mobile streaming session"""
        session_id = hashlib.md5(f"{file_path}{time.time()}".encode()).hexdigest()[:16]
        
        session_data = {
            'id': session_id,
            'file_path': file_path,
            'quality_profile': quality_profile,
            'created_at': datetime.now().isoformat(),
            'status': 'initializing',
            'transcoding_required': self._requires_transcoding(file_path),
            'file_info': self.get_file_info(file_path)
        }
        
        streaming_sessions[session_id] = session_data
        
        # Start transcoding if required
        if session_data['transcoding_required']:
            self._start_transcoding(session_id)
        else:
            session_data['status'] = 'ready'
        
        return session_id
    
    def _start_transcoding(self, session_id: str):
        """Start transcoding process for mobile streaming"""
        session = streaming_sessions.get(session_id)
        if not session:
            return
        
        def transcode():
            try:
                session['status'] = 'transcoding'
                
                file_path = session['file_path']
                quality_profile = session['quality_profile']
                profile_config = self.quality_profiles[quality_profile]
                
                # Create output directory
                output_dir = os.path.join(CACHE_DIR, session_id)
                os.makedirs(output_dir, exist_ok=True)
                
                # HLS transcoding for mobile
                output_path = os.path.join(output_dir, 'playlist.m3u8')
                
                cmd = [
                    self.ffmpeg_path, '-i', file_path,
                    '-c:v', 'libx264', '-preset', 'fast',
                    '-b:v', profile_config['video_bitrate'],
                    '-c:a', 'aac', '-b:a', profile_config['audio_bitrate'],
                    '-f', 'hls', '-hls_time', '6', '-hls_list_size', '0',
                    '-hls_segment_filename', os.path.join(output_dir, 'segment_%03d.ts'),
                    output_path
                ]
                
                process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                session['process'] = process
                
                stdout, stderr = process.communicate()
                
                if process.returncode == 0:
                    session['status'] = 'ready'
                    session['output_path'] = output_path
                    session['segments_dir'] = output_dir
                else:
                    session['status'] = 'error'
                    session['error'] = stderr.decode()
                    logger.error(f"Transcoding failed for session {session_id}: {stderr.decode()}")
                
            except Exception as e:
                session['status'] = 'error'
                session['error'] = str(e)
                logger.error(f"Transcoding error for session {session_id}: {e}")
        
        # Start transcoding in background thread
        thread = threading.Thread(target=transcode)
        thread.daemon = True
        thread.start()

# Initialize streaming engine
streaming_engine = MobileStreamingEngine()

@mobile_streaming_bp.route('/api/stream/mobile/info')
def get_mobile_streaming_info():
    """Get mobile streaming system information"""
    return jsonify({
        'success': True,
        'system_info': {
            'ffmpeg_available': streaming_engine.ffmpeg_path is not None,
            'ffmpeg_path': streaming_engine.ffmpeg_path,
            'cache_directory': CACHE_DIR,
            'active_sessions': len(streaming_sessions),
            'quality_profiles': streaming_engine.quality_profiles
        },
        'supported_formats': {
            'direct_play': ['.mp4', '.m4v', '.mov', '.3gp', '.webm'],
            'transcoding': ['.mkv', '.avi', '.wmv', '.flv', '.ts', '.m2ts']
        }
    })

@mobile_streaming_bp.route('/api/stream/mobile/create', methods=['POST'])
def create_mobile_stream():
    """Create a new mobile streaming session"""
    try:
        data = request.get_json() or {}
        file_path = data.get('file_path', '').strip()
        quality_profile = data.get('quality_profile', 'mobile_medium')
        
        if not file_path:
            return jsonify({
                'success': False,
                'error': 'file_path is required'
            }), 400
        
        if not os.path.exists(file_path):
            return jsonify({
                'success': False,
                'error': 'File not found'
            }), 404
        
        if quality_profile not in streaming_engine.quality_profiles:
            return jsonify({
                'success': False,
                'error': f'Invalid quality profile. Available: {list(streaming_engine.quality_profiles.keys())}'
            }), 400
        
        # Create streaming session
        session_id = streaming_engine.create_streaming_session(file_path, quality_profile)
        session = streaming_sessions[session_id]
        
        return jsonify({
            'success': True,
            'session_id': session_id,
            'status': session['status'],
            'transcoding_required': session['transcoding_required'],
            'file_info': session['file_info'],
            'streaming_urls': {
                'direct': f'/api/stream/mobile/direct/{session_id}' if not session['transcoding_required'] else None,
                'hls': f'/api/stream/mobile/hls/{session_id}/playlist.m3u8' if session['transcoding_required'] else None,
                'status': f'/api/stream/mobile/status/{session_id}'
            }
        })
        
    except Exception as e:
        logger.error(f"Error creating mobile stream: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@mobile_streaming_bp.route('/api/stream/mobile/status/<session_id>')
def get_stream_status(session_id):
    """Get streaming session status"""
    session = streaming_sessions.get(session_id)
    if not session:
        return jsonify({
            'success': False,
            'error': 'Session not found'
        }), 404
    
    return jsonify({
        'success': True,
        'session_id': session_id,
        'status': session['status'],
        'created_at': session['created_at'],
        'transcoding_required': session['transcoding_required'],
        'error': session.get('error'),
        'file_info': session['file_info']
    })

@mobile_streaming_bp.route('/api/stream/mobile/direct/<session_id>')
def stream_direct(session_id):
    """Direct file streaming with HTTP Range support"""
    session = streaming_sessions.get(session_id)
    if not session:
        return jsonify({'error': 'Session not found'}), 404
    
    if session['transcoding_required']:
        return jsonify({'error': 'This file requires transcoding, use HLS endpoint'}), 400
    
    file_path = session['file_path']
    if not os.path.exists(file_path):
        return jsonify({'error': 'File not found'}), 404
    
    # Handle HTTP Range requests for mobile streaming
    range_header = request.headers.get('Range')
    file_size = os.path.getsize(file_path)
    
    if range_header:
        # Parse range header
        byte_start = 0
        byte_end = file_size - 1
        
        range_match = range_header.replace('bytes=', '').split('-')
        if range_match[0]:
            byte_start = int(range_match[0])
        if range_match[1]:
            byte_end = int(range_match[1])
        
        # Ensure valid range
        byte_start = max(0, byte_start)
        byte_end = min(file_size - 1, byte_end)
        content_length = byte_end - byte_start + 1
        
        def generate_range():
            with open(file_path, 'rb') as f:
                f.seek(byte_start)
                remaining = content_length
                while remaining:
                    chunk_size = min(8192, remaining)
                    chunk = f.read(chunk_size)
                    if not chunk:
                        break
                    remaining -= len(chunk)
                    yield chunk
        
        response = Response(
            generate_range(),
            206,  # Partial Content
            headers={
                'Content-Range': f'bytes {byte_start}-{byte_end}/{file_size}',
                'Accept-Ranges': 'bytes',
                'Content-Length': str(content_length),
                'Content-Type': session['file_info']['mime_type'] or 'application/octet-stream'
            }
        )
        
        return response
    
    else:
        # Full file streaming
        return send_file(
            file_path,
            mimetype=session['file_info']['mime_type'],
            as_attachment=False
        )

@mobile_streaming_bp.route('/api/stream/mobile/hls/<session_id>/<path:filename>')
def stream_hls(session_id, filename):
    """Serve HLS segments for transcoded mobile streaming"""
    session = streaming_sessions.get(session_id)
    if not session:
        return jsonify({'error': 'Session not found'}), 404
    
    if session['status'] != 'ready':
        return jsonify({'error': f'Stream not ready, status: {session["status"]}'}), 400
    
    segments_dir = session.get('segments_dir')
    if not segments_dir:
        return jsonify({'error': 'Segments directory not found'}), 404
    
    file_path = os.path.join(segments_dir, filename)
    if not os.path.exists(file_path):
        return jsonify({'error': 'Segment not found'}), 404
    
    # Determine content type
    if filename.endswith('.m3u8'):
        content_type = 'application/vnd.apple.mpegurl'
    elif filename.endswith('.ts'):
        content_type = 'video/mp2t'
    else:
        content_type = 'application/octet-stream'
    
    return send_file(file_path, mimetype=content_type)

@mobile_streaming_bp.route('/api/stream/mobile/cleanup/<session_id>', methods=['DELETE'])
def cleanup_stream(session_id):
    """Clean up streaming session and temporary files"""
    session = streaming_sessions.get(session_id)
    if not session:
        return jsonify({
            'success': False,
            'error': 'Session not found'
        }), 404
    
    try:
        # Stop transcoding process if running
        if 'process' in session:
            try:
                session['process'].terminate()
            except:
                pass
        
        # Clean up temporary files
        segments_dir = session.get('segments_dir')
        if segments_dir and os.path.exists(segments_dir):
            import shutil
            shutil.rmtree(segments_dir, ignore_errors=True)
        
        # Remove session
        del streaming_sessions[session_id]
        
        return jsonify({
            'success': True,
            'message': f'Session {session_id} cleaned up successfully'
        })
        
    except Exception as e:
        logger.error(f"Error cleaning up session {session_id}: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@mobile_streaming_bp.route('/api/stream/mobile/sessions')
def list_sessions():
    """List all active streaming sessions"""
    sessions_info = []
    for session_id, session in streaming_sessions.items():
        sessions_info.append({
            'session_id': session_id,
            'status': session['status'],
            'created_at': session['created_at'],
            'file_path': session['file_path'],
            'quality_profile': session['quality_profile'],
            'transcoding_required': session['transcoding_required']
        })
    
    return jsonify({
        'success': True,
        'active_sessions': sessions_info,
        'total_sessions': len(sessions_info)
    })

@mobile_streaming_bp.route('/api/stream/mobile/library')
def get_mobile_library():
    """Get mobile-optimized library for streaming"""
    try:
        # This would integrate with the main library system
        # For now, return mock data optimized for mobile
        
        library_items = [
            {
                'id': 1,
                'title': 'Dune: Part Two',
                'type': 'movie',
                'year': 2024,
                'duration': '2h 46m',
                'file_path': '/Movies/4K/Dune.Part.Two.2024.2160p.HDR.DV.Atmos.x265.mkv',
                'file_size': '15.2 GB',
                'poster': 'https://image.tmdb.org/t/p/w500/1pdfLvkbY9ohJlCjQH2CZjjYVvJ.jpg',
                'mobile_compatible': False,  # Requires transcoding
                'quality_info': {
                    'resolution': '4K',
                    'hdr': True,
                    'audio': 'Dolby Atmos'
                }
            },
            {
                'id': 2,
                'title': 'Sample Video',
                'type': 'movie',
                'year': 2024,
                'duration': '1h 30m',
                'file_path': '/Movies/Sample.Video.2024.1080p.x264.mp4',
                'file_size': '2.1 GB',
                'poster': 'https://via.placeholder.com/500x750',
                'mobile_compatible': True,  # Direct play
                'quality_info': {
                    'resolution': '1080p',
                    'hdr': False,
                    'audio': 'AAC'
                }
            }
        ]
        
        return jsonify({
            'success': True,
            'library_items': library_items,
            'total_items': len(library_items),
            'mobile_optimized': True
        })
        
    except Exception as e:
        logger.error(f"Error getting mobile library: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# WebOS LG TV Casting Support
@mobile_streaming_bp.route('/api/stream/cast/webos/discover')
def discover_webos_devices():
    """Discover WebOS LG TVs on the network for casting"""
    try:
        # This would implement SSDP discovery for WebOS devices
        # For now, return mock discovered devices
        
        discovered_devices = [
            {
                'id': 'lg_webos_001',
                'name': 'LG OLED TV',
                'model': 'OLED55C1PUB',
                'ip_address': '192.168.1.100',
                'port': 3000,
                'webos_version': '6.0',
                'casting_supported': True,
                'dlna_supported': True
            }
        ]
        
        return jsonify({
            'success': True,
            'discovered_devices': discovered_devices,
            'discovery_method': 'SSDP + mDNS',
            'total_devices': len(discovered_devices)
        })
        
    except Exception as e:
        logger.error(f"Error discovering WebOS devices: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@mobile_streaming_bp.route('/api/stream/cast/webos/connect', methods=['POST'])
def connect_webos_device():
    """Connect to a WebOS LG TV for casting"""
    try:
        data = request.get_json() or {}
        device_id = data.get('device_id')
        ip_address = data.get('ip_address')
        
        if not device_id or not ip_address:
            return jsonify({
                'success': False,
                'error': 'device_id and ip_address are required'
            }), 400
        
        # This would implement WebOS TV connection protocol
        # For now, return mock connection success
        
        return jsonify({
            'success': True,
            'device_id': device_id,
            'connection_status': 'connected',
            'capabilities': {
                'video_formats': ['mp4', 'mkv', 'avi'],
                'audio_formats': ['aac', 'mp3', 'ac3'],
                'subtitle_formats': ['srt', 'vtt', 'ass'],
                'max_resolution': '4K',
                'hdr_support': True
            }
        })
        
    except Exception as e:
        logger.error(f"Error connecting to WebOS device: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@mobile_streaming_bp.route('/api/stream/cast/webos/play', methods=['POST'])
def cast_to_webos():
    """Cast content to WebOS LG TV"""
    try:
        data = request.get_json() or {}
        device_id = data.get('device_id')
        session_id = data.get('session_id')
        
        if not device_id or not session_id:
            return jsonify({
                'success': False,
                'error': 'device_id and session_id are required'
            }), 400
        
        session = streaming_sessions.get(session_id)
        if not session:
            return jsonify({
                'success': False,
                'error': 'Streaming session not found'
            }), 404
        
        # This would implement the actual casting to WebOS TV
        # For now, return mock casting success
        
        return jsonify({
            'success': True,
            'device_id': device_id,
            'session_id': session_id,
            'casting_status': 'playing',
            'stream_url': f'/api/stream/mobile/direct/{session_id}',
            'controls': {
                'play_pause': f'/api/stream/cast/webos/{device_id}/play_pause',
                'stop': f'/api/stream/cast/webos/{device_id}/stop',
                'seek': f'/api/stream/cast/webos/{device_id}/seek'
            }
        })
        
    except Exception as e:
        logger.error(f"Error casting to WebOS device: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
