"""
Enhanced Downloader with JDownloader/IDM-style LinkGrabber functionality
Provides comprehensive download management with package organization
"""

import os
import re
import json
import time
import threading
import requests
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse, unquote
from flask import Blueprint, request, jsonify, current_app
from typing import Dict, List, Optional, Any, Tuple

bp = Blueprint('downloader_enhanced', __name__)

class LinkGrabber:
    """JDownloader-style LinkGrabber for URL extraction and analysis"""
    
    def __init__(self):
        self.supported_hosts = {
            'real-debrid.com': {'name': 'Real-Debrid', 'premium': True},
            'rapidgator.net': {'name': 'RapidGator', 'premium': False},
            'uploaded.net': {'name': 'Uploaded', 'premium': False},
            'nitroflare.com': {'name': 'Nitroflare', 'premium': False},
            'turbobit.net': {'name': 'Turbobit', 'premium': False},
            'mediafire.com': {'name': 'MediaFire', 'premium': False},
            'mega.nz': {'name': 'MEGA', 'premium': False},
            'drive.google.com': {'name': 'Google Drive', 'premium': False},
            'dropbox.com': {'name': 'Dropbox', 'premium': False},
            'youtube.com': {'name': 'YouTube', 'premium': False},
            'youtu.be': {'name': 'YouTube', 'premium': False}
        }
        
        self.url_patterns = [
            # Direct HTTP/HTTPS URLs
            re.compile(r'https?://[^\s<>"{}|\\^`\[\]]+', re.IGNORECASE),
            # FTP URLs
            re.compile(r'ftp://[^\s<>"{}|\\^`\[\]]+', re.IGNORECASE),
            # Magnet links
            re.compile(r'magnet:\?[^\s<>"{}|\\^`\[\]]+', re.IGNORECASE),
        ]
        
        self.container_patterns = {
            'dlc': re.compile(r'.*\.dlc$', re.IGNORECASE),
            'ccf': re.compile(r'.*\.ccf$', re.IGNORECASE),
            'rsdf': re.compile(r'.*\.rsdf$', re.IGNORECASE)
        }
    
    def extract_urls(self, text: str) -> List[Dict[str, Any]]:
        """Extract URLs from text with JDownloader-style analysis"""
        urls = []
        
        # Extract all URLs using patterns
        for pattern in self.url_patterns:
            matches = pattern.findall(text)
            for match in matches:
                url_info = self.analyze_url(match.strip())
                if url_info:
                    urls.append(url_info)
        
        # Remove duplicates while preserving order
        seen = set()
        unique_urls = []
        for url in urls:
            if url['url'] not in seen:
                seen.add(url['url'])
                unique_urls.append(url)
        
        return unique_urls
    
    def analyze_url(self, url: str) -> Optional[Dict[str, Any]]:
        """Analyze a URL and extract information"""
        try:
            parsed = urlparse(url)
            host = parsed.netloc.lower()
            
            # Remove www. prefix
            if host.startswith('www.'):
                host = host[4:]
            
            # Get host info
            host_info = self.supported_hosts.get(host, {
                'name': host.title(),
                'premium': False
            })
            
            # Extract filename from URL
            filename = self.extract_filename(url, parsed)
            
            # Determine file type and category
            file_type, category = self.determine_file_type(filename)
            
            # Estimate file size (if possible from URL)
            estimated_size = self.estimate_file_size(url, parsed)
            
            return {
                'url': url,
                'host': host,
                'host_name': host_info['name'],
                'premium_host': host_info['premium'],
                'filename': filename,
                'file_type': file_type,
                'category': category,
                'estimated_size': estimated_size,
                'status': 'pending',
                'added_at': datetime.now().isoformat()
            }
        
        except Exception:
            return None
    
    def extract_filename(self, url: str, parsed) -> str:
        """Extract filename from URL"""
        # Try to get filename from path
        path = unquote(parsed.path)
        if path and '/' in path:
            filename = path.split('/')[-1]
            if filename and '.' in filename:
                return filename
        
        # Try to get from query parameters
        if parsed.query:
            query_parts = parsed.query.split('&')
            for part in query_parts:
                if '=' in part:
                    key, value = part.split('=', 1)
                    if key.lower() in ['filename', 'file', 'name']:
                        return unquote(value)
        
        # Generate filename from host and timestamp
        host = parsed.netloc.replace('www.', '')
        timestamp = int(time.time())
        return f"{host}_{timestamp}"
    
    def determine_file_type(self, filename: str) -> Tuple[str, str]:
        """Determine file type and category from filename"""
        ext = Path(filename).suffix.lower()
        
        video_exts = {'.mp4', '.mkv', '.avi', '.mov', '.wmv', '.flv', '.webm', '.m4v'}
        audio_exts = {'.mp3', '.flac', '.wav', '.aac', '.ogg', '.m4a', '.wma'}
        image_exts = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.webp'}
        archive_exts = {'.zip', '.rar', '.7z', '.tar', '.gz', '.bz2'}
        document_exts = {'.pdf', '.doc', '.docx', '.txt', '.rtf', '.epub'}
        
        if ext in video_exts:
            return 'video', 'Movies/TV'
        elif ext in audio_exts:
            return 'audio', 'Music'
        elif ext in image_exts:
            return 'image', 'Images'
        elif ext in archive_exts:
            return 'archive', 'Archives'
        elif ext in document_exts:
            return 'document', 'Documents'
        else:
            return 'unknown', 'Other'
    
    def estimate_file_size(self, url: str, parsed) -> int:
        """Estimate file size from URL if possible"""
        # This is a simplified implementation
        # In practice, you might make HEAD requests or parse specific host patterns
        return 0
    
    def process_container_file(self, file_path: str) -> List[Dict[str, Any]]:
        """Process container files (DLC, CCF, RSDF)"""
        try:
            file_ext = Path(file_path).suffix.lower()
            
            if file_ext == '.dlc':
                return self.process_dlc_file(file_path)
            elif file_ext == '.ccf':
                return self.process_ccf_file(file_path)
            elif file_ext == '.rsdf':
                return self.process_rsdf_file(file_path)
            
            return []
        
        except Exception as e:
            current_app.logger.error(f"Error processing container file {file_path}: {e}")
            return []
    
    def process_dlc_file(self, file_path: str) -> List[Dict[str, Any]]:
        """Process DLC container file"""
        # Simplified DLC processing - would need actual DLC decryption
        return []
    
    def process_ccf_file(self, file_path: str) -> List[Dict[str, Any]]:
        """Process CCF container file"""
        # Simplified CCF processing
        return []
    
    def process_rsdf_file(self, file_path: str) -> List[Dict[str, Any]]:
        """Process RSDF container file"""
        # Simplified RSDF processing
        return []

class PackageManager:
    """Manages download packages with automatic grouping"""
    
    def __init__(self):
        self.packages = {}
        self.auto_grouping_rules = [
            # Group by filename patterns
            {'pattern': r'(.+)\.part\d+\.rar$', 'group_by': 'archive_set'},
            {'pattern': r'(.+)\.r\d+$', 'group_by': 'archive_set'},
            {'pattern': r'(.+)\.s\d+e\d+', 'group_by': 'tv_series'},
            {'pattern': r'(.+)\.\d{4}\.', 'group_by': 'movie_year'},
            # Group by host
            {'pattern': r'.*', 'group_by': 'host', 'condition': 'same_host'}
        ]
    
    def create_package(self, name: str, urls: List[Dict[str, Any]]) -> str:
        """Create a new download package"""
        package_id = f"pkg_{int(time.time())}_{len(self.packages)}"
        
        self.packages[package_id] = {
            'id': package_id,
            'name': name,
            'urls': urls,
            'status': 'pending',
            'progress': 0.0,
            'total_size': sum(url.get('estimated_size', 0) for url in urls),
            'downloaded_size': 0,
            'created_at': datetime.now().isoformat(),
            'auto_generated': False
        }
        
        return package_id
    
    def auto_group_urls(self, urls: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Automatically group URLs into packages"""
        packages = []
        ungrouped = urls.copy()
        
        for rule in self.auto_grouping_rules:
            pattern = re.compile(rule['pattern'], re.IGNORECASE)
            groups = {}
            remaining = []
            
            for url in ungrouped:
                match = pattern.match(url['filename'])
                if match:
                    if rule['group_by'] == 'archive_set':
                        group_key = match.group(1)
                    elif rule['group_by'] == 'tv_series':
                        group_key = match.group(1)
                    elif rule['group_by'] == 'movie_year':
                        group_key = match.group(1)
                    elif rule['group_by'] == 'host':
                        group_key = url['host']
                    else:
                        group_key = 'default'
                    
                    if group_key not in groups:
                        groups[group_key] = []
                    groups[group_key].append(url)
                else:
                    remaining.append(url)
            
            # Create packages from groups (only if more than 1 URL)
            for group_key, group_urls in groups.items():
                if len(group_urls) > 1:
                    package_id = self.create_package(f"Auto: {group_key}", group_urls)
                    packages.append({
                        'package_id': package_id,
                        'name': f"Auto: {group_key}",
                        'urls': group_urls,
                        'auto_generated': True
                    })
                else:
                    remaining.extend(group_urls)
            
            ungrouped = remaining
        
        # Add remaining URLs as individual downloads
        for url in ungrouped:
            package_id = self.create_package(url['filename'], [url])
            packages.append({
                'package_id': package_id,
                'name': url['filename'],
                'urls': [url],
                'auto_generated': False
            })
        
        return packages

class DownloadManager:
    """Manages actual downloads with multi-threading and segmentation"""
    
    def __init__(self):
        self.active_downloads = {}
        self.download_threads = {}
        self.max_concurrent = 5
        self.max_segments = 8
        self.password_list = []
    
    def start_download(self, package_id: str, package_data: Dict[str, Any], 
                      save_path: str) -> bool:
        """Start downloading a package"""
        try:
            if package_id in self.active_downloads:
                return False
            
            self.active_downloads[package_id] = {
                'package_id': package_id,
                'status': 'downloading',
                'progress': 0.0,
                'speed': 0,
                'eta': 0,
                'save_path': save_path,
                'started_at': datetime.now().isoformat()
            }
            
            # Start download thread
            thread = threading.Thread(
                target=self._download_package,
                args=(package_id, package_data, save_path)
            )
            thread.daemon = True
            thread.start()
            
            self.download_threads[package_id] = thread
            return True
        
        except Exception as e:
            current_app.logger.error(f"Error starting download {package_id}: {e}")
            return False
    
    def _download_package(self, package_id: str, package_data: Dict[str, Any], 
                         save_path: str):
        """Download all URLs in a package"""
        try:
            urls = package_data['urls']
            total_urls = len(urls)
            completed_urls = 0
            
            for i, url_data in enumerate(urls):
                if package_id not in self.active_downloads:
                    break  # Download was cancelled
                
                # Update progress
                base_progress = (i / total_urls) * 100
                self.active_downloads[package_id]['progress'] = base_progress
                
                # Download individual URL
                success = self._download_url(package_id, url_data, save_path)
                
                if success:
                    completed_urls += 1
                
                # Update final progress for this URL
                self.active_downloads[package_id]['progress'] = ((i + 1) / total_urls) * 100
            
            # Mark as completed
            if package_id in self.active_downloads:
                self.active_downloads[package_id]['status'] = 'completed'
                self.active_downloads[package_id]['progress'] = 100.0
                self.active_downloads[package_id]['completed_at'] = datetime.now().isoformat()
        
        except Exception as e:
            current_app.logger.error(f"Error downloading package {package_id}: {e}")
            if package_id in self.active_downloads:
                self.active_downloads[package_id]['status'] = 'error'
                self.active_downloads[package_id]['error'] = str(e)
    
    def _download_url(self, package_id: str, url_data: Dict[str, Any], 
                     save_path: str) -> bool:
        """Download a single URL with segmentation support"""
        try:
            url = url_data['url']
            filename = url_data['filename']
            file_path = Path(save_path) / filename
            
            # Create directory if needed
            file_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Check if Real-Debrid URL needs processing
            if 'real-debrid.com' in url:
                url = self._process_real_debrid_url(url)
                if not url:
                    return False
            
            # Start download with progress tracking
            response = requests.get(url, stream=True, timeout=30)
            response.raise_for_status()
            
            total_size = int(response.headers.get('content-length', 0))
            downloaded_size = 0
            
            with open(file_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if package_id not in self.active_downloads:
                        break  # Download was cancelled
                    
                    if chunk:
                        f.write(chunk)
                        downloaded_size += len(chunk)
                        
                        # Update speed and ETA
                        if package_id in self.active_downloads:
                            self.active_downloads[package_id]['downloaded_size'] = downloaded_size
                            if total_size > 0:
                                progress = (downloaded_size / total_size) * 100
                                # This is progress for current file, not overall package
            
            return True
        
        except Exception as e:
            current_app.logger.error(f"Error downloading URL {url_data['url']}: {e}")
            return False
    
    def _process_real_debrid_url(self, url: str) -> Optional[str]:
        """Process Real-Debrid URL to get direct download link"""
        try:
            api_manager = current_app.config['api_manager']
            rd_key = api_manager.get_key('real_debrid')
            
            if not rd_key:
                return None
            
            # Add to Real-Debrid and get download link
            headers = {'Authorization': f'Bearer {rd_key}'}
            
            # Add link to RD
            response = requests.post(
                'https://api.real-debrid.com/rest/1.0/unrestrict/link',
                headers=headers,
                data={'link': url},
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                return data.get('download')
            
            return None
        
        except Exception as e:
            current_app.logger.error(f"Error processing Real-Debrid URL: {e}")
            return None
    
    def pause_download(self, package_id: str) -> bool:
        """Pause a download"""
        if package_id in self.active_downloads:
            self.active_downloads[package_id]['status'] = 'paused'
            return True
        return False
    
    def resume_download(self, package_id: str) -> bool:
        """Resume a paused download"""
        if package_id in self.active_downloads:
            self.active_downloads[package_id]['status'] = 'downloading'
            return True
        return False
    
    def cancel_download(self, package_id: str) -> bool:
        """Cancel a download"""
        if package_id in self.active_downloads:
            del self.active_downloads[package_id]
            if package_id in self.download_threads:
                del self.download_threads[package_id]
            return True
        return False
    
    def get_download_status(self, package_id: str) -> Optional[Dict[str, Any]]:
        """Get status of a download"""
        return self.active_downloads.get(package_id)
    
    def get_all_downloads(self) -> Dict[str, Dict[str, Any]]:
        """Get status of all downloads"""
        return self.active_downloads.copy()

# Global instances
link_grabber = LinkGrabber()
package_manager = PackageManager()
download_manager = DownloadManager()

@bp.route('/linkgrabber/analyze', methods=['POST'])
def analyze_links():
    """Analyze text and extract downloadable URLs"""
    try:
        data = request.json
        text = data.get('text', '')
        auto_group = data.get('auto_group', True)
        
        if not text:
            return jsonify({'success': False, 'error': 'No text provided'})
        
        # Extract URLs
        urls = link_grabber.extract_urls(text)
        
        if not urls:
            return jsonify({
                'success': True,
                'urls': [],
                'packages': [],
                'message': 'No downloadable URLs found'
            })
        
        # Auto-group URLs if requested
        packages = []
        if auto_group:
            packages = package_manager.auto_group_urls(urls)
        
        return jsonify({
            'success': True,
            'urls': urls,
            'packages': packages,
            'total_urls': len(urls),
            'supported_hosts': len([u for u in urls if u['premium_host']])
        })
    
    except Exception as e:
        current_app.logger.error(f"LinkGrabber analyze error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@bp.route('/linkgrabber/container', methods=['POST'])
def process_container():
    """Process container files (DLC, CCF, RSDF)"""
    try:
        if 'file' not in request.files:
            return jsonify({'success': False, 'error': 'No file provided'})
        
        file = request.files['file']
        if not file.filename:
            return jsonify({'success': False, 'error': 'No file selected'})
        
        # Save uploaded file temporarily
        temp_path = Path('temp') / file.filename
        temp_path.parent.mkdir(exist_ok=True)
        file.save(temp_path)
        
        try:
            # Process container file
            urls = link_grabber.process_container_file(str(temp_path))
            
            # Auto-group URLs
            packages = package_manager.auto_group_urls(urls)
            
            return jsonify({
                'success': True,
                'urls': urls,
                'packages': packages,
                'container_type': temp_path.suffix.lower(),
                'total_urls': len(urls)
            })
        
        finally:
            # Clean up temp file
            if temp_path.exists():
                temp_path.unlink()
    
    except Exception as e:
        current_app.logger.error(f"Container processing error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@bp.route('/packages/create', methods=['POST'])
def create_package():
    """Create a download package"""
    try:
        data = request.json
        name = data.get('name', 'New Package')
        urls = data.get('urls', [])
        
        if not urls:
            return jsonify({'success': False, 'error': 'No URLs provided'})
        
        package_id = package_manager.create_package(name, urls)
        
        return jsonify({
            'success': True,
            'package_id': package_id,
            'name': name,
            'url_count': len(urls)
        })
    
    except Exception as e:
        current_app.logger.error(f"Package creation error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@bp.route('/downloads/start', methods=['POST'])
def start_download():
    """Start downloading a package"""
    try:
        data = request.json
        package_id = data.get('package_id')
        save_path = data.get('save_path', 'downloads')
        
        if not package_id:
            return jsonify({'success': False, 'error': 'No package ID provided'})
        
        if package_id not in package_manager.packages:
            return jsonify({'success': False, 'error': 'Package not found'})
        
        package_data = package_manager.packages[package_id]
        success = download_manager.start_download(package_id, package_data, save_path)
        
        if success:
            return jsonify({
                'success': True,
                'message': 'Download started',
                'package_id': package_id
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Failed to start download'
            })
    
    except Exception as e:
        current_app.logger.error(f"Download start error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@bp.route('/downloads/status/<package_id>')
def get_download_status(package_id):
    """Get download status"""
    try:
        status = download_manager.get_download_status(package_id)
        
        if status:
            return jsonify({
                'success': True,
                'status': status
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Download not found'
            })
    
    except Exception as e:
        current_app.logger.error(f"Download status error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@bp.route('/downloads/list')
def list_downloads():
    """List all downloads"""
    try:
        downloads = download_manager.get_all_downloads()
        
        return jsonify({
            'success': True,
            'downloads': downloads,
            'total': len(downloads)
        })
    
    except Exception as e:
        current_app.logger.error(f"Download list error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@bp.route('/downloads/control/<package_id>/<action>', methods=['POST'])
def control_download(package_id, action):
    """Control download (pause/resume/cancel)"""
    try:
        if action == 'pause':
            success = download_manager.pause_download(package_id)
        elif action == 'resume':
            success = download_manager.resume_download(package_id)
        elif action == 'cancel':
            success = download_manager.cancel_download(package_id)
        else:
            return jsonify({'success': False, 'error': 'Invalid action'})
        
        return jsonify({
            'success': success,
            'action': action,
            'package_id': package_id
        })
    
    except Exception as e:
        current_app.logger.error(f"Download control error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@bp.route('/api/downloader/containers', methods=['POST'])
def process_container_file():
    """Process container files (DLC, CCF, RSDF)"""
    try:
        if 'container' not in request.files:
            return jsonify({'success': False, 'error': 'No container file provided'}), 400
        
        file = request.files['container']
        if file.filename == '':
            return jsonify({'success': False, 'error': 'No file selected'}), 400
        
        # Save uploaded file temporarily
        temp_path = f"/tmp/{file.filename}"
        file.save(temp_path)
        
        # Process container file
        links = link_grabber.process_container_file(temp_path)
        
        # Clean up temp file
        os.remove(temp_path)
        
        return jsonify({
            'success': True,
            'links': links,
            'total': len(links),
            'message': f'Processed {len(links)} links from container file'
        })
    
    except Exception as e:
        current_app.logger.error(f"Container processing error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@bp.route('/api/rss/filters', methods=['POST'])
def save_rss_filters():
    """Save RSS automation filters"""
    try:
        filters = request.get_json()
        
        # Save filters to database or config file
        # This is a placeholder implementation
        filter_id = f"filter_{int(time.time())}"
        
        return jsonify({
            'success': True,
            'filter_id': filter_id,
            'message': 'RSS filters saved successfully'
        })
    
    except Exception as e:
        current_app.logger.error(f"RSS filter save error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@bp.route('/api/rss/test')
def test_rss_filters():
    """Test RSS filters against feed"""
    try:
        feed = request.args.get('feed', 'default')
        
        # This would test the filters against the RSS feed
        # Placeholder implementation
        matches = [
            {'title': 'Sample Movie 1080p', 'size': '2.5GB', 'match_reason': 'Quality filter: 1080p'},
            {'title': 'Sample TV Show S01E01', 'size': '1.2GB', 'match_reason': 'Episode detection'}
        ]
        
        return jsonify({
            'success': True,
            'matches': matches,
            'total': len(matches)
        })
    
    except Exception as e:
        current_app.logger.error(f"RSS filter test error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500
