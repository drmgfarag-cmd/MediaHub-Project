"""
Advanced Downloader Features - Clipboard Watcher and Password Manager
JDownloader-style functionality with intelligent link detection and management
"""

import os
import re
import json
import time
import logging
import threading
import subprocess
from typing import Dict, List, Any, Optional, Set
from pathlib import Path
from datetime import datetime, timedelta
from urllib.parse import urlparse, parse_qs
from collections import defaultdict
import hashlib
import base64

try:
    import pyperclip
    CLIPBOARD_AVAILABLE = True
except ImportError:
    CLIPBOARD_AVAILABLE = False
    logging.warning("pyperclip not available - clipboard monitoring disabled")

class ClipboardWatcher:
    """Advanced clipboard monitoring for automatic link detection"""
    
    def __init__(self, callback=None):
        self.logger = logging.getLogger(__name__)
        self.callback = callback
        self.running = False
        self.thread = None
        self.last_clipboard = ""
        self.processed_links = set()
        
        # Link patterns for various services
        self.link_patterns = {
            'magnet': re.compile(r'magnet:\?xt=urn:btih:[a-fA-F0-9]{40}[^\s]*'),
            'real_debrid': re.compile(r'https?://.*\.real-debrid\.com/[^\s]*'),
            'mega': re.compile(r'https?://mega\.nz/[^\s]*'),
            'mediafire': re.compile(r'https?://.*\.mediafire\.com/[^\s]*'),
            'rapidgator': re.compile(r'https?://rapidgator\.net/[^\s]*'),
            'uploaded': re.compile(r'https?://uploaded\.net/[^\s]*'),
            'torrent_file': re.compile(r'https?://[^\s]*\.torrent'),
            'ddl_links': re.compile(r'https?://[^\s]*\.(zip|rar|7z|mkv|mp4|avi)'),
            'youtube': re.compile(r'https?://(?:www\.)?(?:youtube\.com/watch\?v=|youtu\.be/)[^\s]*'),
            'streaming': re.compile(r'https?://(?:streamtape|doodstream|mixdrop)\.com/[^\s]*')
        }
        
        # Container file patterns
        self.container_patterns = {
            'dlc': re.compile(r'https?://[^\s]*\.dlc'),
            'ccf': re.compile(r'https?://[^\s]*\.ccf'),
            'rsdf': re.compile(r'https?://[^\s]*\.rsdf')
        }
        
        self.user_confirmation_required = True
        self.auto_add_trusted_domains = set()
        
    def start_monitoring(self):
        """Start clipboard monitoring in background thread"""
        if not CLIPBOARD_AVAILABLE:
            self.logger.warning("Clipboard monitoring not available - pyperclip not installed")
            return False
        
        if self.running:
            return True
        
        self.running = True
        self.thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.thread.start()
        self.logger.info("Clipboard monitoring started")
        return True
    
    def stop_monitoring(self):
        """Stop clipboard monitoring"""
        self.running = False
        if self.thread:
            self.thread.join(timeout=2)
        self.logger.info("Clipboard monitoring stopped")
    
    def _monitor_loop(self):
        """Main monitoring loop"""
        while self.running:
            try:
                current_clipboard = pyperclip.paste()
                
                if current_clipboard != self.last_clipboard and current_clipboard.strip():
                    self.last_clipboard = current_clipboard
                    self._process_clipboard_content(current_clipboard)
                
                time.sleep(1)  # Check every second
                
            except Exception as e:
                self.logger.error(f"Clipboard monitoring error: {e}")
                time.sleep(5)  # Wait longer on error
    
    def _process_clipboard_content(self, content: str):
        """Process clipboard content for downloadable links"""
        detected_links = self.detect_links(content)
        
        if detected_links:
            # Create unique hash for this set of links
            content_hash = hashlib.md5(content.encode()).hexdigest()
            
            if content_hash not in self.processed_links:
                self.processed_links.add(content_hash)
                
                # Clean up old processed links (keep last 100)
                if len(self.processed_links) > 100:
                    self.processed_links = set(list(self.processed_links)[-100:])
                
                if self.callback:
                    self.callback(detected_links, content)
    
    def detect_links(self, text: str) -> Dict[str, List[str]]:
        """Detect various types of downloadable links in text"""
        detected = {}
        
        # Check for each link type
        for link_type, pattern in self.link_patterns.items():
            matches = pattern.findall(text)
            if matches:
                detected[link_type] = matches
        
        # Check for container files
        for container_type, pattern in self.container_patterns.items():
            matches = pattern.findall(text)
            if matches:
                detected[f'container_{container_type}'] = matches
        
        return detected
    
    def add_trusted_domain(self, domain: str):
        """Add domain to auto-add list (no confirmation required)"""
        self.auto_add_trusted_domains.add(domain.lower())
    
    def is_trusted_domain(self, url: str) -> bool:
        """Check if URL is from a trusted domain"""
        try:
            domain = urlparse(url).netloc.lower()
            return domain in self.auto_add_trusted_domains
        except:
            return False

class PasswordManager:
    """JDownloader-style password manager for protected archives"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.password_file = Path("data/archive_passwords.json")
        self.password_file.parent.mkdir(exist_ok=True)
        
        # Common password patterns and lists
        self.common_passwords = [
            "123", "password", "archive", "extract", "download",
            "www.torrentday.com", "www.scenetime.com", "www.torrentleech.org",
            "rarbg.to", "1337x.to", "thepiratebay.org"
        ]
        
        # Site-specific password patterns
        self.site_passwords = {
            'rarbg': ['rarbg'],
            'yts': ['yts.mx', 'yts.am'],
            'eztv': ['eztv.re', 'eztv'],
            'torrentgalaxy': ['tgx'],
            'limetorrents': ['limetorrents.info']
        }
        
        self.password_history = {}
        self.successful_passwords = {}
        
        self.load_passwords()
    
    def load_passwords(self):
        """Load saved passwords from file"""
        try:
            if self.password_file.exists():
                with open(self.password_file, 'r') as f:
                    data = json.load(f)
                    self.password_history = data.get('history', {})
                    self.successful_passwords = data.get('successful', {})
        except Exception as e:
            self.logger.error(f"Error loading passwords: {e}")
    
    def save_passwords(self):
        """Save passwords to file"""
        try:
            data = {
                'history': self.password_history,
                'successful': self.successful_passwords,
                'updated': datetime.now().isoformat()
            }
            with open(self.password_file, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            self.logger.error(f"Error saving passwords: {e}")
    
    def add_password(self, password: str, source: str = "manual"):
        """Add a password to the list"""
        if password and password not in self.common_passwords:
            self.common_passwords.append(password)
            self.password_history[password] = {
                'added': datetime.now().isoformat(),
                'source': source,
                'used_count': 0
            }
            self.save_passwords()
            self.logger.info(f"Added password from {source}")
    
    def get_password_list(self, archive_name: str = "", source_url: str = "") -> List[str]:
        """Get prioritized password list for an archive"""
        passwords = []
        
        # Add successful passwords for similar archives first
        archive_key = self._get_archive_key(archive_name)
        if archive_key in self.successful_passwords:
            passwords.extend(self.successful_passwords[archive_key])
        
        # Add site-specific passwords
        if source_url:
            site_passwords = self._get_site_passwords(source_url)
            passwords.extend(site_passwords)
        
        # Add filename-based passwords
        filename_passwords = self._extract_filename_passwords(archive_name)
        passwords.extend(filename_passwords)
        
        # Add common passwords
        passwords.extend(self.common_passwords)
        
        # Remove duplicates while preserving order
        seen = set()
        unique_passwords = []
        for pwd in passwords:
            if pwd not in seen:
                seen.add(pwd)
                unique_passwords.append(pwd)
        
        return unique_passwords
    
    def _get_archive_key(self, archive_name: str) -> str:
        """Generate key for archive similarity matching"""
        # Extract base name without extension and version numbers
        base_name = re.sub(r'\.(rar|zip|7z)(\.\d+)?$', '', archive_name.lower())
        base_name = re.sub(r'\.part\d+$', '', base_name)
        return base_name
    
    def _get_site_passwords(self, url: str) -> List[str]:
        """Get passwords based on source URL"""
        passwords = []
        try:
            domain = urlparse(url).netloc.lower()
            for site, site_passwords in self.site_passwords.items():
                if site in domain:
                    passwords.extend(site_passwords)
            
            # Add domain as password
            if domain:
                passwords.append(domain)
                passwords.append(domain.replace('www.', ''))
        except:
            pass
        
        return passwords
    
    def _extract_filename_passwords(self, filename: str) -> List[str]:
        """Extract potential passwords from filename"""
        passwords = []
        
        # Release group names
        release_groups = re.findall(r'-([A-Z0-9]+)(?:\.|$)', filename.upper())
        passwords.extend([group.lower() for group in release_groups])
        
        # Site names in filename
        site_patterns = [
            r'www\.([^\.]+)\.(?:com|net|org)',
            r'([^\.]+)\.(?:com|net|org)',
            r'\[([^\]]+)\]'
        ]
        
        for pattern in site_patterns:
            matches = re.findall(pattern, filename.lower())
            passwords.extend(matches)
        
        return passwords
    
    def mark_successful(self, password: str, archive_name: str):
        """Mark a password as successful for an archive"""
        archive_key = self._get_archive_key(archive_name)
        
        if archive_key not in self.successful_passwords:
            self.successful_passwords[archive_key] = []
        
        if password not in self.successful_passwords[archive_key]:
            self.successful_passwords[archive_key].insert(0, password)  # Add to front
            
            # Limit to 5 successful passwords per archive pattern
            self.successful_passwords[archive_key] = self.successful_passwords[archive_key][:5]
        
        # Update usage count
        if password in self.password_history:
            self.password_history[password]['used_count'] += 1
            self.password_history[password]['last_used'] = datetime.now().isoformat()
        
        self.save_passwords()
        self.logger.info(f"Marked password successful for {archive_key}")
    
    def import_passwords(self, password_list: List[str], source: str = "import"):
        """Import a list of passwords"""
        added_count = 0
        for password in password_list:
            if password.strip() and password not in self.common_passwords:
                self.add_password(password.strip(), source)
                added_count += 1
        
        return added_count
    
    def export_passwords(self) -> Dict[str, Any]:
        """Export passwords for backup"""
        return {
            'common_passwords': self.common_passwords,
            'password_history': self.password_history,
            'successful_passwords': self.successful_passwords,
            'exported_at': datetime.now().isoformat()
        }

class AdvancedDownloaderManager:
    """Advanced downloader with clipboard monitoring and password management"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.clipboard_watcher = ClipboardWatcher(callback=self._handle_detected_links)
        self.password_manager = PasswordManager()
        
        # Download queue management
        self.download_queue = []
        self.active_downloads = {}
        self.completed_downloads = []
        self.failed_downloads = []
        
        # Per-host download limits
        self.host_limits = {
            'default': 2,
            'mega.nz': 1,
            'rapidgator.net': 1,
            'uploaded.net': 2,
            'real-debrid.com': 5
        }
        
        self.active_host_counts = defaultdict(int)
        
        # Settings
        self.settings = {
            'auto_extract_archives': True,
            'delete_archives_after_extract': False,
            'max_concurrent_downloads': 5,
            'retry_failed_downloads': True,
            'max_retries': 3,
            'download_timeout': 300,  # 5 minutes
            'clipboard_monitoring': True,
            'auto_add_clipboard_links': False,  # Require confirmation by default
            'trusted_domains': set()
        }
        
        self.load_settings()
    
    def start(self):
        """Start the advanced downloader"""
        if self.settings['clipboard_monitoring']:
            success = self.clipboard_watcher.start_monitoring()
            if success:
                self.logger.info("Advanced downloader started with clipboard monitoring")
            else:
                self.logger.warning("Advanced downloader started without clipboard monitoring")
        else:
            self.logger.info("Advanced downloader started (clipboard monitoring disabled)")
    
    def stop(self):
        """Stop the advanced downloader"""
        self.clipboard_watcher.stop_monitoring()
        self.save_settings()
        self.logger.info("Advanced downloader stopped")
    
    def _handle_detected_links(self, detected_links: Dict[str, List[str]], raw_content: str):
        """Handle links detected from clipboard"""
        self.logger.info(f"Detected {sum(len(links) for links in detected_links.values())} links from clipboard")
        
        # Process each type of link
        for link_type, links in detected_links.items():
            for link in links:
                self._process_detected_link(link, link_type, raw_content)
    
    def _process_detected_link(self, link: str, link_type: str, context: str):
        """Process a single detected link"""
        # Check if auto-add is enabled for trusted domains
        auto_add = (self.settings['auto_add_clipboard_links'] or 
                   self.clipboard_watcher.is_trusted_domain(link))
        
        link_info = {
            'url': link,
            'type': link_type,
            'detected_at': datetime.now().isoformat(),
            'context': context[:200],  # First 200 chars of context
            'auto_added': auto_add,
            'status': 'pending_confirmation' if not auto_add else 'queued'
        }
        
        if auto_add:
            self.add_to_queue(link_info)
        else:
            # Store for user confirmation
            self._store_pending_link(link_info)
    
    def _store_pending_link(self, link_info: Dict):
        """Store link pending user confirmation"""
        # This would typically trigger a UI notification
        # For now, we'll log it
        self.logger.info(f"Link pending confirmation: {link_info['url']}")
        
        # In a real implementation, this would:
        # 1. Show a desktop notification
        # 2. Add to a pending links queue in the UI
        # 3. Allow user to approve/reject
    
    def add_to_queue(self, download_info: Dict):
        """Add download to queue"""
        # Generate unique ID
        download_id = hashlib.md5(f"{download_info['url']}{time.time()}".encode()).hexdigest()[:8]
        download_info['id'] = download_id
        download_info['added_to_queue'] = datetime.now().isoformat()
        download_info['status'] = 'queued'
        
        self.download_queue.append(download_info)
        self.logger.info(f"Added to download queue: {download_info['url']}")
        
        # Try to start download if slots available
        self._try_start_downloads()
    
    def _try_start_downloads(self):
        """Try to start queued downloads if slots available"""
        if len(self.active_downloads) >= self.settings['max_concurrent_downloads']:
            return
        
        for download_info in self.download_queue[:]:
            if download_info['status'] == 'queued':
                host = self._get_host(download_info['url'])
                host_limit = self.host_limits.get(host, self.host_limits['default'])
                
                if self.active_host_counts[host] < host_limit:
                    self._start_download(download_info)
                    break
    
    def _get_host(self, url: str) -> str:
        """Extract host from URL"""
        try:
            return urlparse(url).netloc.lower()
        except:
            return 'unknown'
    
    def _start_download(self, download_info: Dict):
        """Start a download"""
        download_id = download_info['id']
        host = self._get_host(download_info['url'])
        
        # Move from queue to active
        if download_info in self.download_queue:
            self.download_queue.remove(download_info)
        
        download_info['status'] = 'downloading'
        download_info['started_at'] = datetime.now().isoformat()
        
        self.active_downloads[download_id] = download_info
        self.active_host_counts[host] += 1
        
        self.logger.info(f"Started download: {download_info['url']}")
        
        # In a real implementation, this would start the actual download
        # For now, we'll simulate it
        self._simulate_download(download_info)
    
    def _simulate_download(self, download_info: Dict):
        """Simulate download process (for testing)"""
        # This would be replaced with actual download logic
        def download_worker():
            time.sleep(2)  # Simulate download time
            self._complete_download(download_info['id'], success=True)
        
        thread = threading.Thread(target=download_worker, daemon=True)
        thread.start()
    
    def _complete_download(self, download_id: str, success: bool = True, error: str = None):
        """Mark download as completed"""
        if download_id not in self.active_downloads:
            return
        
        download_info = self.active_downloads[download_id]
        host = self._get_host(download_info['url'])
        
        # Update counters
        self.active_host_counts[host] -= 1
        del self.active_downloads[download_id]
        
        # Update download info
        download_info['completed_at'] = datetime.now().isoformat()
        
        if success:
            download_info['status'] = 'completed'
            self.completed_downloads.append(download_info)
            self.logger.info(f"Download completed: {download_info['url']}")
            
            # Handle post-download processing
            self._post_download_processing(download_info)
        else:
            download_info['status'] = 'failed'
            download_info['error'] = error
            self.failed_downloads.append(download_info)
            self.logger.error(f"Download failed: {download_info['url']} - {error}")
            
            # Retry if enabled
            if (self.settings['retry_failed_downloads'] and 
                download_info.get('retry_count', 0) < self.settings['max_retries']):
                self._retry_download(download_info)
        
        # Try to start next download
        self._try_start_downloads()
    
    def _post_download_processing(self, download_info: Dict):
        """Handle post-download processing (extraction, etc.)"""
        if not self.settings['auto_extract_archives']:
            return
        
        # Check if downloaded file is an archive
        url = download_info['url']
        if any(ext in url.lower() for ext in ['.rar', '.zip', '.7z']):
            self._extract_archive(download_info)
    
    def _extract_archive(self, download_info: Dict):
        """Extract downloaded archive"""
        # Get password list for this archive
        filename = download_info['url'].split('/')[-1]
        passwords = self.password_manager.get_password_list(filename, download_info['url'])
        
        self.logger.info(f"Attempting to extract archive: {filename}")
        self.logger.info(f"Trying {len(passwords)} passwords")
        
        # In a real implementation, this would:
        # 1. Try to extract with each password
        # 2. Mark successful password
        # 3. Delete archive if setting enabled
        # 4. Move extracted files to appropriate location
        
        # Simulate successful extraction
        if passwords:
            successful_password = passwords[0]  # Simulate first password working
            self.password_manager.mark_successful(successful_password, filename)
            self.logger.info(f"Archive extracted successfully with password: {successful_password}")
    
    def _retry_download(self, download_info: Dict):
        """Retry a failed download"""
        download_info['retry_count'] = download_info.get('retry_count', 0) + 1
        download_info['status'] = 'queued'
        download_info['retried_at'] = datetime.now().isoformat()
        
        # Remove from failed list and add back to queue
        if download_info in self.failed_downloads:
            self.failed_downloads.remove(download_info)
        
        self.download_queue.append(download_info)
        self.logger.info(f"Retrying download (attempt {download_info['retry_count']}): {download_info['url']}")
    
    def get_status(self) -> Dict[str, Any]:
        """Get downloader status"""
        return {
            'active_downloads': len(self.active_downloads),
            'queued_downloads': len([d for d in self.download_queue if d['status'] == 'queued']),
            'completed_downloads': len(self.completed_downloads),
            'failed_downloads': len(self.failed_downloads),
            'clipboard_monitoring': self.clipboard_watcher.running,
            'host_limits': dict(self.active_host_counts),
            'settings': self.settings.copy()
        }
    
    def load_settings(self):
        """Load settings from file"""
        try:
            settings_file = Path("data/downloader_settings.json")
            if settings_file.exists():
                with open(settings_file, 'r') as f:
                    saved_settings = json.load(f)
                    self.settings.update(saved_settings)
                    
                    # Convert trusted_domains back to set
                    if 'trusted_domains' in saved_settings:
                        self.settings['trusted_domains'] = set(saved_settings['trusted_domains'])
        except Exception as e:
            self.logger.error(f"Error loading settings: {e}")
    
    def save_settings(self):
        """Save settings to file"""
        try:
            settings_file = Path("data/downloader_settings.json")
            settings_file.parent.mkdir(exist_ok=True)
            
            # Convert set to list for JSON serialization
            settings_copy = self.settings.copy()
            settings_copy['trusted_domains'] = list(self.settings['trusted_domains'])
            
            with open(settings_file, 'w') as f:
                json.dump(settings_copy, f, indent=2)
        except Exception as e:
            self.logger.error(f"Error saving settings: {e}")

# Global instance
advanced_downloader = AdvancedDownloaderManager()

def get_advanced_downloader() -> AdvancedDownloaderManager:
    """Get the global advanced downloader instance"""
    return advanced_downloader

if __name__ == "__main__":
    # Test the advanced downloader
    downloader = AdvancedDownloaderManager()
    downloader.start()
    
    # Test password manager
    pm = downloader.password_manager
    pm.add_password("test123", "manual")
    passwords = pm.get_password_list("Movie.2021.1080p.x264-RARBG.rar", "https://rarbg.to/torrent/123")
    print(f"Generated {len(passwords)} passwords for archive")
    
    # Keep running for a bit to test clipboard monitoring
    try:
        time.sleep(10)
    except KeyboardInterrupt:
        pass
    finally:
        downloader.stop()
