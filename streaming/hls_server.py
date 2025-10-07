#!/usr/bin/env python3
"""
HLS (HTTP Live Streaming) Server with Adaptive Bitrate Support
Phase 1A Streaming Infrastructure Component
"""

import os
import re
import json
import time
import threading
import subprocess
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from flask import Flask, Response, request, jsonify, send_file
import requests
from datetime import datetime, timedelta


class HLSAdaptiveBitrateEncoder:
    """Handles video encoding for multiple bitrates"""
    
    BITRATE_PROFILES = {
        '240p': {
            'resolution': '426x240',
            'video_bitrate': '400k',
            'audio_bitrate': '64k',
            'framerate': 24
        },
        '480p': {
            'resolution': '854x480', 
            'video_bitrate': '1000k',
            'audio_bitrate': '128k',
            'framerate': 30
        },
        '720p': {
            'resolution': '1280x720',
            'video_bitrate': '2500k', 
            'audio_bitrate': '192k',
            'framerate': 30
        },
        '1080p': {
            'resolution': '1920x1080',
            'video_bitrate': '5000k',
            'audio_bitrate': '256k', 
            'framerate': 30
        }
    }
    
    def __init__(self, output_dir: str = "streaming/hls_output"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.encoding_jobs = {}
        
    def encode_video_hls(self, input_file: str, video_id: str) -> Dict[str, str]:
        """Encode video into multiple HLS streams"""
        try:
            input_path = Path(input_file)
            if not input_path.exists():
                raise FileNotFoundError(f"Input file not found: {input_file}")
            
            video_output_dir = self.output_dir / video_id
            video_output_dir.mkdir(exist_ok=True)
            
            # Check if already encoded
            master_playlist = video_output_dir / "master.m3u8"
            if master_playlist.exists():
                return self._get_existing_streams(video_id)
            
            # Start encoding in background
            threading.Thread(
                target=self._encode_worker,
                args=(str(input_path), video_id, str(video_output_dir)),
                daemon=True
            ).start()
            
            # Return job status
            self.encoding_jobs[video_id] = {
                'status': 'encoding',
                'progress': 0,
                'started_at': datetime.now().isoformat()
            }
            
            return {
                'video_id': video_id,
                'status': 'encoding',
                'master_playlist': f"/streaming/hls/{video_id}/master.m3u8"
            }
            
        except Exception as e:
            print(f"HLS encoding error: {e}")
            return {'error': str(e)}
    
    def _encode_worker(self, input_path: str, video_id: str, output_dir: str):
        """Background worker for encoding"""
        try:
            # Create variant streams
            variant_streams = []
            
            for quality, profile in self.BITRATE_PROFILES.items():
                variant_dir = Path(output_dir) / quality
                variant_dir.mkdir(exist_ok=True)
                
                playlist_file = variant_dir / "playlist.m3u8"
                
                # FFmpeg command for HLS encoding
                cmd = [
                    'ffmpeg', '-i', input_path,
                    '-c:v', 'libx264',
                    '-c:a', 'aac',
                    '-b:v', profile['video_bitrate'],
                    '-b:a', profile['audio_bitrate'],
                    '-s', profile['resolution'],
                    '-r', str(profile['framerate']),
                    '-hls_time', '6',
                    '-hls_list_size', '0',
                    '-hls_segment_filename', str(variant_dir / f"segment_%03d.ts"),
                    '-f', 'hls',
                    str(playlist_file)
                ]
                
                # Run encoding
                result = subprocess.run(cmd, capture_output=True, text=True)
                
                if result.returncode == 0:
                    # Extract bandwidth from video bitrate for manifest
                    bandwidth = int(profile['video_bitrate'].replace('k', '')) * 1000
                    
                    variant_streams.append({
                        'quality': quality,
                        'bandwidth': bandwidth,
                        'resolution': profile['resolution'],
                        'playlist': f"{quality}/playlist.m3u8"
                    })
                    
                    self._update_progress(video_id, quality)
                else:
                    print(f"Encoding failed for {quality}: {result.stderr}")
            
            # Create master playlist
            if variant_streams:
                self._create_master_playlist(output_dir, variant_streams)
                self.encoding_jobs[video_id] = {
                    'status': 'completed',
                    'progress': 100,
                    'completed_at': datetime.now().isoformat(),
                    'streams': variant_streams
                }
            else:
                self.encoding_jobs[video_id] = {
                    'status': 'failed',
                    'error': 'No streams encoded successfully'
                }
                
        except Exception as e:
            print(f"Encoding worker error: {e}")
            self.encoding_jobs[video_id] = {
                'status': 'failed',
                'error': str(e)
            }
    
    def _create_master_playlist(self, output_dir: str, streams: List[Dict]):
        """Create HLS master playlist"""
        master_content = "#EXTM3U\n#EXT-X-VERSION:3\n\n"
        
        for stream in sorted(streams, key=lambda x: x['bandwidth']):
            master_content += (
                f"#EXT-X-STREAM-INF:BANDWIDTH={stream['bandwidth']},"
                f"RESOLUTION={stream['resolution']}\n"
                f"{stream['playlist']}\n"
            )
        
        master_file = Path(output_dir) / "master.m3u8"
        with open(master_file, 'w') as f:
            f.write(master_content)
    
    def _update_progress(self, video_id: str, completed_quality: str):
        """Update encoding progress"""
        if video_id in self.encoding_jobs:
            completed = len([q for q in self.BITRATE_PROFILES.keys() 
                            if (self.output_dir / video_id / q / "playlist.m3u8").exists()])
            total = len(self.BITRATE_PROFILES)
            progress = int((completed / total) * 100)
            
            self.encoding_jobs[video_id]['progress'] = progress
    
    def _get_existing_streams(self, video_id: str) -> Dict[str, str]:
        """Get information about existing encoded streams"""
        video_dir = self.output_dir / video_id
        streams = []
        
        for quality in self.BITRATE_PROFILES.keys():
            playlist_file = video_dir / quality / "playlist.m3u8"
            if playlist_file.exists():
                profile = self.BITRATE_PROFILES[quality]
                bandwidth = int(profile['video_bitrate'].replace('k', '')) * 1000
                streams.append({
                    'quality': quality,
                    'bandwidth': bandwidth,
                    'resolution': profile['resolution'],
                    'playlist': f"{quality}/playlist.m3u8"
                })
        
        return {
            'video_id': video_id,
            'status': 'completed',
            'master_playlist': f"/streaming/hls/{video_id}/master.m3u8",
            'streams': streams
        }
    
    def get_encoding_status(self, video_id: str) -> Dict:
        """Get encoding job status"""
        return self.encoding_jobs.get(video_id, {'status': 'not_found'})


class HLSStreamingServer:
    """HLS streaming server with adaptive bitrate support"""
    
    def __init__(self, port: int = 8888):
        self.port = port
        self.encoder = HLSAdaptiveBitrateEncoder()
        self.app = Flask(__name__)
        self.setup_routes()
        self.active_sessions = {}
        
    def setup_routes(self):
        """Setup Flask routes for HLS streaming"""
        
        @self.app.route('/streaming/encode', methods=['POST'])
        def encode_video():
            """Endpoint to start video encoding"""
            try:
                data = request.get_json()
                input_file = data.get('input_file')
                video_id = data.get('video_id')
                
                if not input_file or not video_id:
                    return jsonify({'error': 'Missing input_file or video_id'}), 400
                
                result = self.encoder.encode_video_hls(input_file, video_id)
                return jsonify(result)
                
            except Exception as e:
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/streaming/status/<video_id>')
        def encoding_status(video_id):
            """Get encoding status for video"""
            status = self.encoder.get_encoding_status(video_id)
            return jsonify(status)
        
        @self.app.route('/streaming/hls/<video_id>/<path:filename>')
        def serve_hls_file(video_id, filename):
            """Serve HLS playlist and segment files"""
            try:
                file_path = self.encoder.output_dir / video_id / filename
                
                if not file_path.exists():
                    return "File not found", 404
                
                # Set appropriate content type
                if filename.endswith('.m3u8'):
                    content_type = 'application/vnd.apple.mpegurl'
                elif filename.endswith('.ts'):
                    content_type = 'video/mp2t'
                else:
                    content_type = 'application/octet-stream'
                
                # Track streaming session
                session_id = f"{video_id}_{request.remote_addr}"
                self.active_sessions[session_id] = {
                    'video_id': video_id,
                    'client_ip': request.remote_addr,
                    'last_access': datetime.now(),
                    'user_agent': request.headers.get('User-Agent', '')
                }
                
                return send_file(file_path, mimetype=content_type)
                
            except Exception as e:
                return f"Error serving file: {e}", 500
        
        @self.app.route('/streaming/sessions')
        def active_sessions():
            """Get active streaming sessions"""
            # Clean old sessions (inactive for 10+ minutes)
            cutoff = datetime.now() - timedelta(minutes=10)
            active = {
                k: v for k, v in self.active_sessions.items()
                if v['last_access'] > cutoff
            }
            self.active_sessions = active
            
            return jsonify({
                'active_sessions': len(active),
                'sessions': list(active.values())
            })
        
        @self.app.route('/streaming/health')
        def health_check():
            """Health check endpoint"""
            return jsonify({
                'status': 'healthy',
                'timestamp': datetime.now().isoformat(),
                'active_encodings': len([j for j in self.encoder.encoding_jobs.values() 
                                       if j.get('status') == 'encoding']),
                'completed_encodings': len([j for j in self.encoder.encoding_jobs.values() 
                                          if j.get('status') == 'completed'])
            })
    
    def run(self, host='0.0.0.0', debug=False):
        """Start the HLS streaming server"""
        print(f"Starting HLS Streaming Server on {host}:{self.port}")
        self.app.run(host=host, port=self.port, debug=debug, threaded=True)


# Standalone server for testing
if __name__ == '__main__':
    server = HLSStreamingServer()
    server.run()
