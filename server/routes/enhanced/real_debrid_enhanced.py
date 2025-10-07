"""
Enhanced Real-Debrid Manager with Advanced Features
Includes double extraction, reference lists, upload link export, and comprehensive management
"""

import os
import re
import json
import time
import requests
import threading
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from flask import Blueprint, request, jsonify, current_app
from urllib.parse import urlparse, unquote

bp = Blueprint('real_debrid_enhanced', __name__)

class RealDebridAPI:
    """Enhanced Real-Debrid API client with comprehensive functionality"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = 'https://api.real-debrid.com/rest/1.0'
        self.session = requests.Session()
        self.session.headers.update({
            'Authorization': f'Bearer {api_key}',
            'User-Agent': 'MediaHub/1.0'
        })
        self.rate_limit_delay = 0.5  # 500ms between requests
        self.last_request_time = 0
    
    def _make_request(self, method: str, endpoint: str, **kwargs) -> requests.Response:
        """Make rate-limited API request"""
        # Rate limiting
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        if time_since_last < self.rate_limit_delay:
            time.sleep(self.rate_limit_delay - time_since_last)
        
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        response = self.session.request(method, url, **kwargs)
        self.last_request_time = time.time()
        
        return response
    
    def get_user_info(self) -> Dict[str, Any]:
        """Get user account information"""
        try:
            response = self._make_request('GET', '/user')
            response.raise_for_status()
            return response.json()
        except Exception as e:
            current_app.logger.error(f"RD get_user_info error: {e}")
            return {}
    
    def get_downloads(self, offset: int = 0, limit: int = 50) -> List[Dict[str, Any]]:
        """Get download history"""
        try:
            params = {'offset': offset, 'limit': limit}
            response = self._make_request('GET', '/downloads', params=params)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            current_app.logger.error(f"RD get_downloads error: {e}")
            return []
    
    def get_torrents(self, offset: int = 0, limit: int = 50, filter_status: str = None) -> List[Dict[str, Any]]:
        """Get torrent list with optional filtering"""
        try:
            params = {'offset': offset, 'limit': limit}
            if filter_status:
                params['filter'] = filter_status
            
            response = self._make_request('GET', '/torrents', params=params)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            current_app.logger.error(f"RD get_torrents error: {e}")
            return []
    
    def add_torrent(self, torrent_data: bytes = None, magnet_link: str = None) -> Dict[str, Any]:
        """Add torrent or magnet link"""
        try:
            if magnet_link:
                data = {'magnet': magnet_link}
                response = self._make_request('POST', '/torrents/addMagnet', data=data)
            elif torrent_data:
                files = {'torrent': torrent_data}
                response = self._make_request('PUT', '/torrents/addTorrent', files=files)
            else:
                return {'success': False, 'error': 'No torrent data or magnet link provided'}
            
            response.raise_for_status()
            return {'success': True, 'data': response.json()}
        except Exception as e:
            current_app.logger.error(f"RD add_torrent error: {e}")
            return {'success': False, 'error': str(e)}
    
    def select_files(self, torrent_id: str, file_ids: str = 'all') -> Dict[str, Any]:
        """Select files from torrent"""
        try:
            data = {'files': file_ids}
            response = self._make_request('POST', f'/torrents/selectFiles/{torrent_id}', data=data)
            response.raise_for_status()
            return {'success': True}
        except Exception as e:
            current_app.logger.error(f"RD select_files error: {e}")
            return {'success': False, 'error': str(e)}
    
    def get_torrent_info(self, torrent_id: str) -> Dict[str, Any]:
        """Get detailed torrent information"""
        try:
            response = self._make_request('GET', f'/torrents/info/{torrent_id}')
            response.raise_for_status()
            return response.json()
        except Exception as e:
            current_app.logger.error(f"RD get_torrent_info error: {e}")
            return {}
    
    def delete_torrent(self, torrent_id: str) -> Dict[str, Any]:
        """Delete torrent"""
        try:
            response = self._make_request('DELETE', f'/torrents/delete/{torrent_id}')
            response.raise_for_status()
            return {'success': True}
        except Exception as e:
            current_app.logger.error(f"RD delete_torrent error: {e}")
            return {'success': False, 'error': str(e)}
    
    def unrestrict_link(self, link: str, password: str = None) -> Dict[str, Any]:
        """Unrestrict a download link"""
        try:
            data = {'link': link}
            if password:
                data['password'] = password
            
            response = self._make_request('POST', '/unrestrict/link', data=data)
            response.raise_for_status()
            return {'success': True, 'data': response.json()}
        except Exception as e:
            current_app.logger.error(f"RD unrestrict_link error: {e}")
            return {'success': False, 'error': str(e)}
    
    def check_link(self, link: str) -> Dict[str, Any]:
        """Check if link is supported"""
        try:
            data = {'link': link}
            response = self._make_request('POST', '/unrestrict/check', data=data)
            response.raise_for_status()
            return {'success': True, 'data': response.json()}
        except Exception as e:
            current_app.logger.error(f"RD check_link error: {e}")
            return {'success': False, 'error': str(e)}

class DeduplicationEngine:
    """Advanced deduplication with user-configurable rules"""
    
    def __init__(self):
        self.default_rules = {
            'hierarchy': ['ctrlhd', 'Cytsunee', 'oft'],
            'never_remove': ['ctrlhd'],
            'quality_preference': ['4K', '2160p', '1080p', '720p'],
            'codec_preference': ['x265', 'HEVC', 'x264'],
            'source_preference': ['BluRay', 'WEB-DL', 'WEBRip', 'HDTV'],
            'group_patterns': {
                'ctrlhd': r'(?i)ctrlhd',
                'Cytsunee': r'(?i)cytsunee',
                'oft': r'(?i)\boft\b'
            }
        }
    
    def apply_deduplication(self, torrents: List[Dict[str, Any]], 
                          rules: Dict[str, Any] = None) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """Apply deduplication rules and return (keep, remove) lists"""
        if not rules:
            rules = self.default_rules
        
        if not rules.get('enabled', False):
            return torrents, []
        
        # Group torrents by content (simplified by filename similarity)
        groups = self._group_similar_torrents(torrents)
        
        keep_list = []
        remove_list = []
        
        for group in groups:
            if len(group) <= 1:
                keep_list.extend(group)
                continue
            
            # Apply hierarchy rules
            keep, remove = self._apply_hierarchy_rules(group, rules)
            keep_list.extend(keep)
            remove_list.extend(remove)
        
        return keep_list, remove_list
    
    def _group_similar_torrents(self, torrents: List[Dict[str, Any]]) -> List[List[Dict[str, Any]]]:
        """Group similar torrents for deduplication"""
        groups = []
        processed = set()
        
        for i, torrent in enumerate(torrents):
            if i in processed:
                continue
            
            group = [torrent]
            processed.add(i)
            
            # Find similar torrents
            for j, other_torrent in enumerate(torrents[i+1:], i+1):
                if j in processed:
                    continue
                
                if self._are_similar(torrent, other_torrent):
                    group.append(other_torrent)
                    processed.add(j)
            
            groups.append(group)
        
        return groups
    
    def _are_similar(self, torrent1: Dict[str, Any], torrent2: Dict[str, Any]) -> bool:
        """Check if two torrents are similar content"""
        name1 = torrent1.get('filename', '').lower()
        name2 = torrent2.get('filename', '').lower()
        
        # Remove common patterns for comparison
        clean_name1 = re.sub(r'[\.\-_\[\]()]', ' ', name1)
        clean_name2 = re.sub(r'[\.\-_\[\]()]', ' ', name2)
        
        # Remove quality/group tags
        clean_name1 = re.sub(r'\b(1080p|720p|4k|2160p|x264|x265|hevc|bluray|web-dl|webrip)\b', '', clean_name1)
        clean_name2 = re.sub(r'\b(1080p|720p|4k|2160p|x264|x265|hevc|bluray|web-dl|webrip)\b', '', clean_name2)
        
        # Check similarity (simplified)
        words1 = set(clean_name1.split())
        words2 = set(clean_name2.split())
        
        if not words1 or not words2:
            return False
        
        intersection = words1.intersection(words2)
        union = words1.union(words2)
        
        similarity = len(intersection) / len(union) if union else 0
        return similarity > 0.7  # 70% similarity threshold
    
    def _apply_hierarchy_rules(self, group: List[Dict[str, Any]], 
                             rules: Dict[str, Any]) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """Apply hierarchy rules to a group of similar torrents"""
        hierarchy = rules.get('hierarchy', [])
        never_remove = rules.get('never_remove', [])
        
        # Score torrents based on rules
        scored_torrents = []
        for torrent in group:
            score = self._score_torrent(torrent, rules)
            scored_torrents.append((torrent, score))
        
        # Sort by score (higher is better)
        scored_torrents.sort(key=lambda x: x[1], reverse=True)
        
        keep_list = []
        remove_list = []
        
        for torrent, score in scored_torrents:
            filename = torrent.get('filename', '').lower()
            
            # Check if this torrent should never be removed
            should_never_remove = any(
                re.search(rules['group_patterns'].get(group_name, group_name.lower()), filename)
                for group_name in never_remove
            )
            
            if should_never_remove or not keep_list:
                keep_list.append(torrent)
            else:
                # Check hierarchy rules
                should_remove = False
                for keep_torrent in keep_list:
                    keep_filename = keep_torrent.get('filename', '').lower()
                    
                    # Apply ctrlhd > Cytsunee > oft rule
                    if 'ctrlhd' in hierarchy and 'cytsunee' in hierarchy:
                        if (re.search(r'(?i)ctrlhd', keep_filename) and 
                            re.search(r'(?i)cytsunee', filename)):
                            should_remove = True
                            break
                
                if should_remove:
                    remove_list.append(torrent)
                else:
                    keep_list.append(torrent)
        
        return keep_list, remove_list
    
    def _score_torrent(self, torrent: Dict[str, Any], rules: Dict[str, Any]) -> int:
        """Score torrent based on quality, codec, source preferences"""
        filename = torrent.get('filename', '').lower()
        score = 0
        
        # Quality scoring
        quality_prefs = rules.get('quality_preference', [])
        for i, quality in enumerate(quality_prefs):
            if quality.lower() in filename:
                score += (len(quality_prefs) - i) * 100
                break
        
        # Codec scoring
        codec_prefs = rules.get('codec_preference', [])
        for i, codec in enumerate(codec_prefs):
            if codec.lower() in filename:
                score += (len(codec_prefs) - i) * 50
                break
        
        # Source scoring
        source_prefs = rules.get('source_preference', [])
        for i, source in enumerate(source_prefs):
            if source.lower() in filename:
                score += (len(source_prefs) - i) * 25
                break
        
        # Hierarchy scoring
        hierarchy = rules.get('hierarchy', [])
        for i, group in enumerate(hierarchy):
            pattern = rules.get('group_patterns', {}).get(group, group.lower())
            if re.search(pattern, filename):
                score += (len(hierarchy) - i) * 200
                break
        
        return score

class ReferenceListManager:
    """Manages reference lists for import/export operations"""
    
    def __init__(self, db_connection, db_lock):
        self.db_connection = db_connection
        self.db_lock = db_lock
    
    def import_reference_list(self, list_data: str, list_type: str = 'auto') -> Dict[str, Any]:
        """Import reference list from various formats"""
        try:
            links = []
            
            if list_type == 'auto':
                list_type = self._detect_list_type(list_data)
            
            if list_type == 'magnet':
                links = self._extract_magnet_links(list_data)
            elif list_type == 'http':
                links = self._extract_http_links(list_data)
            elif list_type == 'mixed':
                links = self._extract_mixed_links(list_data)
            else:
                return {'success': False, 'error': f'Unsupported list type: {list_type}'}
            
            # Store in database
            list_id = self._store_reference_list(links, list_type)
            
            return {
                'success': True,
                'list_id': list_id,
                'links_count': len(links),
                'list_type': list_type
            }
        
        except Exception as e:
            current_app.logger.error(f"Import reference list error: {e}")
            return {'success': False, 'error': str(e)}
    
    def _detect_list_type(self, data: str) -> str:
        """Auto-detect reference list type"""
        magnet_count = len(re.findall(r'magnet:\?', data))
        http_count = len(re.findall(r'https?://', data))
        
        if magnet_count > 0 and http_count == 0:
            return 'magnet'
        elif http_count > 0 and magnet_count == 0:
            return 'http'
        elif magnet_count > 0 and http_count > 0:
            return 'mixed'
        else:
            return 'unknown'
    
    def _extract_magnet_links(self, data: str) -> List[str]:
        """Extract magnet links from data"""
        pattern = r'magnet:\?[^\s<>"{}|\\^`\[\]]+'
        return re.findall(pattern, data, re.IGNORECASE)
    
    def _extract_http_links(self, data: str) -> List[str]:
        """Extract HTTP links from data"""
        pattern = r'https?://[^\s<>"{}|\\^`\[\]]+'
        return re.findall(pattern, data, re.IGNORECASE)
    
    def _extract_mixed_links(self, data: str) -> List[str]:
        """Extract both magnet and HTTP links"""
        magnet_links = self._extract_magnet_links(data)
        http_links = self._extract_http_links(data)
        return magnet_links + http_links
    
    def _store_reference_list(self, links: List[str], list_type: str) -> str:
        """Store reference list in database"""
        try:
            list_id = f"ref_{int(time.time())}"
            
            with self.db_lock:
                cursor = self.db_connection.cursor()
                cursor.execute("""
                    INSERT INTO reference_lists (list_id, list_type, links, created_at)
                    VALUES (?, ?, ?, CURRENT_TIMESTAMP)
                """, (list_id, list_type, json.dumps(links)))
                self.db_connection.commit()
            
            return list_id
        
        except Exception as e:
            current_app.logger.error(f"Store reference list error: {e}")
            return ''
    
    def export_upload_links(self, torrent_ids: List[str], format_type: str = 'txt') -> Dict[str, Any]:
        """Export upload links for torrents"""
        try:
            api_manager = current_app.config['api_manager']
            rd_key = api_manager.get_key('real_debrid')
            
            if not rd_key:
                return {'success': False, 'error': 'Real-Debrid API key not configured'}
            
            rd_api = RealDebridAPI(rd_key)
            upload_links = []
            
            for torrent_id in torrent_ids:
                torrent_info = rd_api.get_torrent_info(torrent_id)
                if torrent_info and 'links' in torrent_info:
                    for link in torrent_info['links']:
                        upload_links.append(link)
            
            # Format output
            if format_type == 'txt':
                output = '\n'.join(upload_links)
            elif format_type == 'json':
                output = json.dumps(upload_links, indent=2)
            elif format_type == 'csv':
                output = 'Link\n' + '\n'.join(upload_links)
            else:
                return {'success': False, 'error': f'Unsupported format: {format_type}'}
            
            return {
                'success': True,
                'output': output,
                'format': format_type,
                'links_count': len(upload_links)
            }
        
        except Exception as e:
            current_app.logger.error(f"Export upload links error: {e}")
            return {'success': False, 'error': str(e)}

class DoubleExtractionManager:
    """Manages double extraction for nested archives"""
    
    def __init__(self):
        self.extraction_queue = {}
        self.archive_patterns = [
            r'\.rar$', r'\.zip$', r'\.7z$', r'\.tar\.gz$', r'\.tar\.bz2$'
        ]
    
    def detect_nested_archives(self, torrent_info: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Detect files that might contain nested archives"""
        nested_candidates = []
        
        files = torrent_info.get('files', [])
        for file_info in files:
            filename = file_info.get('path', '').lower()
            
            # Check if file is an archive
            is_archive = any(re.search(pattern, filename, re.IGNORECASE) 
                           for pattern in self.archive_patterns)
            
            if is_archive:
                nested_candidates.append({
                    'file_id': file_info.get('id'),
                    'filename': file_info.get('path'),
                    'size': file_info.get('bytes', 0),
                    'extraction_priority': self._calculate_extraction_priority(filename)
                })
        
        # Sort by priority
        nested_candidates.sort(key=lambda x: x['extraction_priority'], reverse=True)
        
        return nested_candidates
    
    def _calculate_extraction_priority(self, filename: str) -> int:
        """Calculate extraction priority based on filename patterns"""
        priority = 0
        
        # Higher priority for certain patterns
        if re.search(r'\.part\d+\.rar$', filename, re.IGNORECASE):
            priority += 100  # Multi-part archives
        elif re.search(r'\.rar$', filename, re.IGNORECASE):
            priority += 80   # RAR archives
        elif re.search(r'\.zip$', filename, re.IGNORECASE):
            priority += 60   # ZIP archives
        elif re.search(r'\.7z$', filename, re.IGNORECASE):
            priority += 70   # 7z archives
        
        # Lower priority for certain patterns
        if re.search(r'sample', filename, re.IGNORECASE):
            priority -= 50   # Sample files
        
        return priority
    
    def queue_double_extraction(self, torrent_id: str, files_to_extract: List[Dict[str, Any]]) -> str:
        """Queue files for double extraction"""
        extraction_id = f"extract_{int(time.time())}_{torrent_id}"
        
        self.extraction_queue[extraction_id] = {
            'torrent_id': torrent_id,
            'files': files_to_extract,
            'status': 'queued',
            'created_at': datetime.now().isoformat(),
            'progress': 0
        }
        
        return extraction_id
    
    def get_extraction_status(self, extraction_id: str) -> Optional[Dict[str, Any]]:
        """Get status of double extraction"""
        return self.extraction_queue.get(extraction_id)

# Global instances
deduplication_engine = DeduplicationEngine()

@bp.route('/user/info')
def get_user_info():
    """Get Real-Debrid user information"""
    try:
        api_manager = current_app.config['api_manager']
        rd_key = api_manager.get_key('real_debrid')
        
        if not rd_key:
            return jsonify({'success': False, 'error': 'Real-Debrid API key not configured'})
        
        rd_api = RealDebridAPI(rd_key)
        user_info = rd_api.get_user_info()
        
        return jsonify({
            'success': True,
            'user_info': user_info
        })
    
    except Exception as e:
        current_app.logger.error(f"RD user info error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@bp.route('/torrents/list')
def list_torrents():
    """List torrents with optional filtering"""
    try:
        offset = request.args.get('offset', 0, type=int)
        limit = request.args.get('limit', 50, type=int)
        filter_status = request.args.get('filter')
        
        api_manager = current_app.config['api_manager']
        rd_key = api_manager.get_key('real_debrid')
        
        if not rd_key:
            return jsonify({'success': False, 'error': 'Real-Debrid API key not configured'})
        
        rd_api = RealDebridAPI(rd_key)
        torrents = rd_api.get_torrents(offset, limit, filter_status)
        
        return jsonify({
            'success': True,
            'torrents': torrents,
            'count': len(torrents)
        })
    
    except Exception as e:
        current_app.logger.error(f"RD list torrents error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@bp.route('/torrents/add', methods=['POST'])
def add_torrent():
    """Add torrent or magnet link"""
    try:
        api_manager = current_app.config['api_manager']
        rd_key = api_manager.get_key('real_debrid')
        
        if not rd_key:
            return jsonify({'success': False, 'error': 'Real-Debrid API key not configured'})
        
        rd_api = RealDebridAPI(rd_key)
        
        # Check if it's a file upload or magnet link
        if 'torrent_file' in request.files:
            torrent_file = request.files['torrent_file']
            torrent_data = torrent_file.read()
            result = rd_api.add_torrent(torrent_data=torrent_data)
        else:
            data = request.json
            magnet_link = data.get('magnet_link')
            if not magnet_link:
                return jsonify({'success': False, 'error': 'No magnet link or torrent file provided'})
            
            result = rd_api.add_torrent(magnet_link=magnet_link)
        
        return jsonify(result)
    
    except Exception as e:
        current_app.logger.error(f"RD add torrent error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@bp.route('/torrents/<torrent_id>/select', methods=['POST'])
def select_torrent_files(torrent_id):
    """Select files from torrent"""
    try:
        data = request.json
        file_ids = data.get('file_ids', 'all')
        
        api_manager = current_app.config['api_manager']
        rd_key = api_manager.get_key('real_debrid')
        
        if not rd_key:
            return jsonify({'success': False, 'error': 'Real-Debrid API key not configured'})
        
        rd_api = RealDebridAPI(rd_key)
        result = rd_api.select_files(torrent_id, file_ids)
        
        return jsonify(result)
    
    except Exception as e:
        current_app.logger.error(f"RD select files error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@bp.route('/torrents/<torrent_id>/info')
def get_torrent_info(torrent_id):
    """Get detailed torrent information"""
    try:
        api_manager = current_app.config['api_manager']
        rd_key = api_manager.get_key('real_debrid')
        
        if not rd_key:
            return jsonify({'success': False, 'error': 'Real-Debrid API key not configured'})
        
        rd_api = RealDebridAPI(rd_key)
        torrent_info = rd_api.get_torrent_info(torrent_id)
        
        # Check for nested archives
        double_extraction = DoubleExtractionManager()
        nested_archives = double_extraction.detect_nested_archives(torrent_info)
        
        return jsonify({
            'success': True,
            'torrent_info': torrent_info,
            'nested_archives': nested_archives
        })
    
    except Exception as e:
        current_app.logger.error(f"RD torrent info error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@bp.route('/deduplication/analyze', methods=['POST'])
def analyze_duplicates():
    """Analyze torrents for duplicates using profile rules"""
    try:
        data = request.json
        profile_name = data.get('profile', 'default')
        
        # Get profile rules
        profile_manager = current_app.config['profile_manager']
        dedup_rules = profile_manager.get_deduplication_rules(profile_name)
        
        # Get torrents
        api_manager = current_app.config['api_manager']
        rd_key = api_manager.get_key('real_debrid')
        
        if not rd_key:
            return jsonify({'success': False, 'error': 'Real-Debrid API key not configured'})
        
        rd_api = RealDebridAPI(rd_key)
        torrents = rd_api.get_torrents(limit=1000)  # Get more torrents for analysis
        
        # Apply deduplication
        keep_list, remove_list = deduplication_engine.apply_deduplication(torrents, dedup_rules)
        
        return jsonify({
            'success': True,
            'analysis': {
                'total_torrents': len(torrents),
                'keep_count': len(keep_list),
                'remove_count': len(remove_list),
                'keep_list': keep_list,
                'remove_list': remove_list
            },
            'rules_applied': dedup_rules
        })
    
    except Exception as e:
        current_app.logger.error(f"RD deduplication analysis error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@bp.route('/reference-lists/import', methods=['POST'])
def import_reference_list():
    """Import reference list"""
    try:
        data = request.json
        list_data = data.get('list_data', '')
        list_type = data.get('list_type', 'auto')
        
        db_connection = current_app.config['db_connection']
        db_lock = current_app.config['db_lock']
        
        ref_manager = ReferenceListManager(db_connection, db_lock)
        result = ref_manager.import_reference_list(list_data, list_type)
        
        return jsonify(result)
    
    except Exception as e:
        current_app.logger.error(f"RD import reference list error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@bp.route('/upload-links/export', methods=['POST'])
def export_upload_links():
    """Export upload links for selected torrents"""
    try:
        data = request.json
        torrent_ids = data.get('torrent_ids', [])
        format_type = data.get('format', 'txt')
        
        db_connection = current_app.config['db_connection']
        db_lock = current_app.config['db_lock']
        
        ref_manager = ReferenceListManager(db_connection, db_lock)
        result = ref_manager.export_upload_links(torrent_ids, format_type)
        
        return jsonify(result)
    
    except Exception as e:
        current_app.logger.error(f"RD export upload links error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@bp.route('/double-extraction/queue', methods=['POST'])
def queue_double_extraction():
    """Queue files for double extraction"""
    try:
        data = request.json
        torrent_id = data.get('torrent_id')
        files_to_extract = data.get('files', [])
        
        if not torrent_id:
            return jsonify({'success': False, 'error': 'No torrent ID provided'})
        
        double_extraction = DoubleExtractionManager()
        extraction_id = double_extraction.queue_double_extraction(torrent_id, files_to_extract)
        
        return jsonify({
            'success': True,
            'extraction_id': extraction_id
        })
    
    except Exception as e:
        current_app.logger.error(f"RD queue double extraction error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@bp.route('/double-extraction/<extraction_id>/status')
def get_extraction_status(extraction_id):
    """Get double extraction status"""
    try:
        double_extraction = DoubleExtractionManager()
        status = double_extraction.get_extraction_status(extraction_id)
        
        if status:
            return jsonify({
                'success': True,
                'status': status
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Extraction not found'
            })
    
    except Exception as e:
        current_app.logger.error(f"RD extraction status error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500
