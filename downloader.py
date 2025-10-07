#!/usr/bin/env python3
"""
Advanced Downloader - MediaHub Ultimate
JDownloader-style download manager with comprehensive features
"""

import sys
import os
import json
import re
import threading
import time
import hashlib
import sqlite3
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set, Tuple, Any
from dataclasses import dataclass, field
from enum import Enum
from urllib.parse import urlparse, urljoin
from concurrent.futures import ThreadPoolExecutor, as_completed

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QTableWidget, QTableWidgetItem, QHeaderView, QMenuBar, QStatusBar,
    QToolBar, QFileDialog, QMessageBox, QInputDialog, QDialog,
    QTextEdit, QLineEdit, QPushButton, QLabel, QComboBox, QCheckBox,
    QSpinBox, QProgressBar, QSplitter, QTabWidget, QTreeWidget,
    QTreeWidgetItem, QListWidget, QListWidgetItem, QGridLayout,
    QGroupBox, QFrame, QScrollArea
)
from PyQt6.QtCore import (
    Qt, QTimer, QThread, pyqtSignal, QSettings, QSize,
    QUrl, QStandardPaths, QMutex, QMutexLocker
)
from PyQt6.QtGui import (
    QFont, QIcon, QPixmap, QKeySequence, QAction, QColor, QPalette,
    QStandardItemModel, QStandardItem
)

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


class DownloadStatus(Enum):
    """Download status enumeration"""
    PENDING = "Pending"
    DOWNLOADING = "Downloading"
    PAUSED = "Paused"
    COMPLETED = "Completed"
    FAILED = "Failed"
    CANCELLED = "Cancelled"
    EXTRACTING = "Extracting"
    QUEUED = "Queued"


class DownloadPriority(Enum):
    """Download priority levels"""
    HIGHEST = 5
    HIGH = 4
    NORMAL = 3
    LOW = 2
    LOWEST = 1


@dataclass
class DownloadItem:
    """Represents a download item"""
    id: str
    url: str
    filename: str
    destination: str
    size: int = 0
    downloaded: int = 0
    status: DownloadStatus = DownloadStatus.PENDING
    priority: DownloadPriority = DownloadPriority.NORMAL
    speed: float = 0.0
    eta: str = "--:--"
    added_date: datetime = field(default_factory=datetime.now)
    started_date: Optional[datetime] = None
    completed_date: Optional[datetime] = None
    error_message: str = ""
    retry_count: int = 0
    max_retries: int = 3
    headers: Dict[str, str] = field(default_factory=dict)
    cookies: Dict[str, str] = field(default_factory=dict)
    referrer: str = ""
    user_agent: str = "MediaHub Ultimate Downloader/1.0"
    connections: int = 4
    auto_extract: bool = False
    delete_after_extract: bool = False
    category: str = "General"
    tags: List[str] = field(default_factory=list)
    comment: str = ""
    
    @property
    def progress(self) -> float:
        """Calculate download progress percentage"""
        if self.size > 0:
            return (self.downloaded / self.size) * 100
        return 0.0
    
    @property
    def is_complete(self) -> bool:
        """Check if download is complete"""
        return self.status == DownloadStatus.COMPLETED
    
    @property
    def is_active(self) -> bool:
        """Check if download is actively downloading"""
        return self.status == DownloadStatus.DOWNLOADING
    
    @property
    def can_resume(self) -> bool:
        """Check if download can be resumed"""
        return self.status in [DownloadStatus.PAUSED, DownloadStatus.FAILED]


class DownloadWorker(QThread):
    """Worker thread for handling downloads"""
    
    progress_updated = pyqtSignal(str, int, int, float)  # id, downloaded, total, speed
    status_changed = pyqtSignal(str, str)  # id, status
    completed = pyqtSignal(str)  # id
    error_occurred = pyqtSignal(str, str)  # id, error_message
    
    def __init__(self, download_item: DownloadItem, parent=None):
        super().__init__(parent)
        self.download_item = download_item
        self.should_stop = False
        self.should_pause = False
        self.session = None
        
    def run(self):
        """Execute the download"""
        try:
            self.setup_session()
            self.download_file()
        except Exception as e:
            self.error_occurred.emit(self.download_item.id, str(e))
    
    def setup_session(self):
        """Setup requests session with retry strategy"""
        self.session = requests.Session()
        
        # Setup retry strategy
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504]
        )
        
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)
        
        # Set headers
        self.session.headers.update({
            'User-Agent': self.download_item.user_agent
        })
        
        if self.download_item.headers:
            self.session.headers.update(self.download_item.headers)
        
        if self.download_item.cookies:
            self.session.cookies.update(self.download_item.cookies)
        
        if self.download_item.referrer:
            self.session.headers['Referer'] = self.download_item.referrer
    
    def download_file(self):
        """Download the file with progress tracking"""
        url = self.download_item.url
        output_path = Path(self.download_item.destination) / self.download_item.filename
        
        # Create directory if it doesn't exist
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Check if file already exists and get resume position
        resume_pos = 0
        if output_path.exists():
            resume_pos = output_path.stat().st_size
            self.download_item.downloaded = resume_pos
        
        # Setup range header for resume
        headers = {}
        if resume_pos > 0:
            headers['Range'] = f'bytes={resume_pos}-'
        
        self.status_changed.emit(self.download_item.id, DownloadStatus.DOWNLOADING.value)
        
        # Start download
        response = self.session.get(url, headers=headers, stream=True)
        response.raise_for_status()
        
        # Get total size
        content_length = response.headers.get('content-length')
        if content_length:
            total_size = int(content_length)
            if resume_pos > 0:
                total_size += resume_pos
            self.download_item.size = total_size
        
        # Download with progress tracking
        start_time = time.time()
        last_update = start_time
        last_downloaded = resume_pos
        
        mode = 'ab' if resume_pos > 0 else 'wb'
        
        with open(output_path, mode) as f:
            for chunk in response.iter_content(chunk_size=8192):
                if self.should_stop:
                    return
                
                while self.should_pause:
                    time.sleep(0.1)
                    if self.should_stop:
                        return
                
                if chunk:
                    f.write(chunk)
                    self.download_item.downloaded += len(chunk)
                    
                    # Update progress every 0.5 seconds
                    current_time = time.time()
                    if current_time - last_update >= 0.5:
                        # Calculate speed
                        time_diff = current_time - last_update
                        bytes_diff = self.download_item.downloaded - last_downloaded
                        speed = bytes_diff / time_diff if time_diff > 0 else 0
                        
                        self.download_item.speed = speed
                        
                        # Calculate ETA
                        if speed > 0 and self.download_item.size > 0:
                            remaining = self.download_item.size - self.download_item.downloaded
                            eta_seconds = remaining / speed
                            eta_time = timedelta(seconds=int(eta_seconds))
                            self.download_item.eta = str(eta_time)
                        
                        self.progress_updated.emit(
                            self.download_item.id,
                            self.download_item.downloaded,
                            self.download_item.size,
                            speed
                        )
                        
                        last_update = current_time
                        last_downloaded = self.download_item.downloaded
        
        # Download completed
        self.download_item.completed_date = datetime.now()
        self.status_changed.emit(self.download_item.id, DownloadStatus.COMPLETED.value)
        self.completed.emit(self.download_item.id)
    
    def pause(self):
        """Pause the download"""
        self.should_pause = True
        self.status_changed.emit(self.download_item.id, DownloadStatus.PAUSED.value)
    
    def resume(self):
        """Resume the download"""
        self.should_pause = False
    
    def stop(self):
        """Stop the download"""
        self.should_stop = True
        self.status_changed.emit(self.download_item.id, DownloadStatus.CANCELLED.value)


class ContainerParser:
    """Parser for container files (DLC, RSDF, CCF)"""
    
    def __init__(self):
        self.supported_formats = ['.dlc', '.rsdf', '.ccf']
        
    def _is_valid_url(self, url: str) -> bool:
        """Validate if string is a valid URL"""
        try:
            from urllib.parse import urlparse
            result = urlparse(url)
            return all([result.scheme, result.netloc]) and result.scheme in ['http', 'https']
        except Exception:
            return False
    
    def parse_container(self, file_path: str) -> List[str]:
        """Parse container file and extract URLs"""
        file_path = Path(file_path)
        extension = file_path.suffix.lower()
        
        if extension == '.dlc':
            return self.parse_dlc(file_path)
        elif extension == '.rsdf':
            return self.parse_rsdf(file_path)
        elif extension == '.ccf':
            return self.parse_ccf(file_path)
        else:
            raise ValueError(f"Unsupported container format: {extension}")
    
    def parse_dlc(self, file_path: Path) -> List[str]:
        """Parse DLC container file"""
        try:
            import base64
            
            with open(file_path, 'rb') as f:
                content = f.read()
            
            # DLC files are Base64 encoded XML with RC4 encryption
            # This is a simplified version - real DLC parsing requires RC4 decryption
            try:
                # Try to decode as base64 first
                decoded = base64.b64decode(content)
                
                # Look for URL patterns in the decoded content
                url_pattern = rb'http[s]?://[^\s<>"\x00-\x20]+'
                matches = re.findall(url_pattern, decoded)
                
                urls = [match.decode('utf-8', errors='ignore') for match in matches]
                return [url for url in urls if self._is_valid_url(url)]
                
            except Exception:
                # If base64 fails, try to extract URLs directly from raw content
                content_str = content.decode('utf-8', errors='ignore')
                url_pattern = r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
                urls = re.findall(url_pattern, content_str)
                return [url for url in urls if self._is_valid_url(url)]
                
        except Exception as e:
            raise ValueError(f"Failed to parse DLC file: {e}")
    
    def parse_rsdf(self, file_path: Path) -> List[str]:
        """Parse RSDF container file"""
        try:
            urls = []
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Extract URLs from RSDF format
            url_pattern = r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
            urls = re.findall(url_pattern, content)
            
            return urls
        except Exception as e:
            raise ValueError(f"Failed to parse RSDF file: {e}")
    
    def parse_ccf(self, file_path: Path) -> List[str]:
        """Parse CCF container file"""
        try:
            with open(file_path, 'rb') as f:
                content = f.read()
            
            urls = []
            
            # CCF files have a specific binary structure
            # Look for URL patterns in the binary content
            try:
                # Convert binary to string and search for URLs
                content_str = content.decode('utf-8', errors='ignore')
                url_pattern = r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
                potential_urls = re.findall(url_pattern, content_str)
                
                # Validate and filter URLs
                for url in potential_urls:
                    if self._is_valid_url(url) and len(url) > 10:  # Filter out short false positives
                        urls.append(url)
                        
            except Exception:
                # Alternative: search for URL patterns in raw bytes
                url_pattern = rb'http[s]?://[^\s<>"\x00-\x20]+'
                matches = re.findall(url_pattern, content)
                
                for match in matches:
                    try:
                        url = match.decode('utf-8')
                        if self._is_valid_url(url):
                            urls.append(url)
                    except UnicodeDecodeError:
                        continue
            
            return urls
        except Exception as e:
            raise ValueError(f"Failed to parse CCF file: {e}")


class LinkExtractor:
    """Extract download links from web pages and text"""
    
    def __init__(self):
        self.file_extensions = {
            'video': ['.mp4', '.mkv', '.avi', '.mov', '.wmv', '.flv', '.webm', '.m4v'],
            'audio': ['.mp3', '.flac', '.wav', '.aac', '.ogg', '.m4a', '.wma'],
            'archive': ['.zip', '.rar', '.7z', '.tar', '.gz', '.bz2', '.xz'],
            'document': ['.pdf', '.doc', '.docx', '.txt', '.rtf', '.odt'],
            'image': ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.webp'],
            'software': ['.exe', '.msi', '.dmg', '.deb', '.rpm', '.appimage']
        }
    
    def extract_links(self, text: str, filter_types: List[str] = None) -> List[str]:
        """Extract download links from text"""
        # URL pattern
        url_pattern = r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
        urls = re.findall(url_pattern, text)
        
        if filter_types:
            filtered_urls = []
            for url in urls:
                for file_type in filter_types:
                    if file_type in self.file_extensions:
                        extensions = self.file_extensions[file_type]
                        if any(url.lower().endswith(ext) for ext in extensions):
                            filtered_urls.append(url)
                            break
            return filtered_urls
        
        return urls
    
    def categorize_url(self, url: str) -> str:
        """Categorize URL by file type"""
        url_lower = url.lower()
        
        for category, extensions in self.file_extensions.items():
            if any(url_lower.endswith(ext) for ext in extensions):
                return category.title()
        
        return "General"


class DownloadFilter:
    """Filter and deduplicate downloads"""
    
    def __init__(self):
        self.sample_patterns = [
            r'sample',
            r'trailer',
            r'preview',
            r'demo',
            r'\bts\b',  # teaser
            r'proof',
            r'\bscr\b',  # screener
            r'cam',
            r'hdcam'
        ]
        
        self.preferred_patterns = [
            r'\b(1080p|720p|4k|2160p)\b',
            r'\b(bluray|brrip|bdrip)\b',
            r'\b(web-dl|webdl|webrip)\b',
            r'\bsubs?\b',
            r'\bsubtitle[s]?\b'
        ]
        
        self.junk_patterns = [
            r'\b(xxx|adult|porn)\b',
            r'\b(virus|malware|trojan)\b',
            r'\b(crack|keygen|patch)\b',
            r'\bfake\b'
        ]
    
    def is_sample_file(self, filename: str) -> bool:
        """Check if file is a sample"""
        filename_lower = filename.lower()
        return any(re.search(pattern, filename_lower) for pattern in self.sample_patterns)
    
    def is_junk_file(self, filename: str) -> bool:
        """Check if file is junk/unwanted"""
        filename_lower = filename.lower()
        return any(re.search(pattern, filename_lower) for pattern in self.junk_patterns)
    
    def calculate_priority(self, filename: str) -> int:
        """Calculate download priority based on filename"""
        filename_lower = filename.lower()
        priority = 3  # Normal priority
        
        # Increase priority for preferred content
        for pattern in self.preferred_patterns:
            if re.search(pattern, filename_lower):
                priority += 1
                break
        
        # Decrease priority for samples
        if self.is_sample_file(filename):
            priority = 1
        
        return min(5, max(1, priority))
    
    def deduplicate_urls(self, urls: List[str]) -> List[str]:
        """Remove duplicate URLs"""
        seen = set()
        unique_urls = []
        
        for url in urls:
            # Normalize URL for comparison
            normalized = url.lower().strip()
            if normalized not in seen:
                seen.add(normalized)
                unique_urls.append(url)
        
        return unique_urls
    
    def filter_downloads(self, items: List[DownloadItem], 
                        exclude_samples: bool = True,
                        exclude_junk: bool = True,
                        prefer_quality: bool = True) -> List[DownloadItem]:
        """Filter download items based on criteria"""
        filtered_items = []
        
        for item in items:
            # Skip samples if enabled
            if exclude_samples and self.is_sample_file(item.filename):
                continue
            
            # Skip junk if enabled
            if exclude_junk and self.is_junk_file(item.filename):
                continue
            
            # Adjust priority if enabled
            if prefer_quality:
                priority_score = self.calculate_priority(item.filename)
                item.priority = DownloadPriority(priority_score)
            
            filtered_items.append(item)
        
        return filtered_items


class DownloadDatabase:
    """SQLite database for persistent download management"""
    
    def __init__(self, db_path: str = "downloads.db"):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Initialize database tables"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS downloads (
                    id TEXT PRIMARY KEY,
                    url TEXT NOT NULL,
                    filename TEXT NOT NULL,
                    destination TEXT NOT NULL,
                    size INTEGER DEFAULT 0,
                    downloaded INTEGER DEFAULT 0,
                    status TEXT DEFAULT 'Pending',
                    priority INTEGER DEFAULT 3,
                    added_date TEXT,
                    started_date TEXT,
                    completed_date TEXT,
                    error_message TEXT DEFAULT '',
                    retry_count INTEGER DEFAULT 0,
                    max_retries INTEGER DEFAULT 3,
                    headers TEXT DEFAULT '{}',
                    cookies TEXT DEFAULT '{}',
                    referrer TEXT DEFAULT '',
                    user_agent TEXT DEFAULT 'MediaHub Ultimate Downloader/1.0',
                    connections INTEGER DEFAULT 4,
                    auto_extract BOOLEAN DEFAULT FALSE,
                    delete_after_extract BOOLEAN DEFAULT FALSE,
                    category TEXT DEFAULT 'General',
                    tags TEXT DEFAULT '[]',
                    comment TEXT DEFAULT ''
                )
            """)
            
            conn.execute("""
                CREATE TABLE IF NOT EXISTS categories (
                    name TEXT PRIMARY KEY,
                    description TEXT,
                    default_path TEXT,
                    auto_extract BOOLEAN DEFAULT FALSE
                )
            """)
            
            conn.execute("""
                CREATE TABLE IF NOT EXISTS settings (
                    key TEXT PRIMARY KEY,
                    value TEXT
                )
            """)
    
    def save_download(self, item: DownloadItem):
        """Save download item to database"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT OR REPLACE INTO downloads VALUES (
                    ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?
                )
            """, (
                item.id, item.url, item.filename, item.destination,
                item.size, item.downloaded, item.status.value, item.priority.value,
                item.added_date.isoformat(),
                item.started_date.isoformat() if item.started_date else None,
                item.completed_date.isoformat() if item.completed_date else None,
                item.error_message, item.retry_count, item.max_retries,
                json.dumps(item.headers), json.dumps(item.cookies),
                item.referrer, item.user_agent, item.connections,
                item.auto_extract, item.delete_after_extract,
                item.category, json.dumps(item.tags), item.comment
            ))
    
    def load_downloads(self) -> List[DownloadItem]:
        """Load all download items from database"""
        downloads = []
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("SELECT * FROM downloads ORDER BY added_date DESC")
            
            for row in cursor.fetchall():
                item = DownloadItem(
                    id=row[0],
                    url=row[1],
                    filename=row[2],
                    destination=row[3],
                    size=row[4],
                    downloaded=row[5],
                    status=DownloadStatus(row[6]),
                    priority=DownloadPriority(row[7]),
                    added_date=datetime.fromisoformat(row[8]),
                    started_date=datetime.fromisoformat(row[9]) if row[9] else None,
                    completed_date=datetime.fromisoformat(row[10]) if row[10] else None,
                    error_message=row[11],
                    retry_count=row[12],
                    max_retries=row[13],
                    headers=json.loads(row[14]),
                    cookies=json.loads(row[15]),
                    referrer=row[16],
                    user_agent=row[17],
                    connections=row[18],
                    auto_extract=bool(row[19]),
                    delete_after_extract=bool(row[20]),
                    category=row[21],
                    tags=json.loads(row[22]),
                    comment=row[23]
                )
                downloads.append(item)
        
        return downloads
    
    def delete_download(self, download_id: str):
        """Delete download from database"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("DELETE FROM downloads WHERE id = ?", (download_id,))


class AddDownloadDialog(QDialog):
    """Dialog for adding new downloads"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Add Downloads")
        self.setModal(True)
        self.resize(600, 500)
        self.setup_ui()
    
    def setup_ui(self):
        """Setup the dialog UI"""
        layout = QVBoxLayout()
        
        # URL input
        url_group = QGroupBox("URLs")
        url_layout = QVBoxLayout()
        
        self.url_text = QPlainTextEdit()
        self.url_text.setPlaceholderText("Enter URLs (one per line)...")
        url_layout.addWidget(self.url_text)
        
        # Container file
        container_layout = QHBoxLayout()
        container_layout.addWidget(QLabel("Container File:"))
        self.container_path = QLineEdit()
        container_browse = QPushButton("Browse")
        container_browse.clicked.connect(self.browse_container)
        container_layout.addWidget(self.container_path)
        container_layout.addWidget(container_browse)
        url_layout.addLayout(container_layout)
        
        url_group.setLayout(url_layout)
        layout.addWidget(url_group)
        
        # Download options
        options_group = QGroupBox("Download Options")
        options_layout = QFormLayout()
        
        self.destination = QLineEdit()
        dest_browse = QPushButton("Browse")
        dest_browse.clicked.connect(self.browse_destination)
        dest_layout = QHBoxLayout()
        dest_layout.addWidget(self.destination)
        dest_layout.addWidget(dest_browse)
        options_layout.addRow("Destination:", dest_layout)
        
        self.category = QComboBox()
        self.category.addItems(["General", "Video", "Audio", "Software", "Documents", "Archives"])
        options_layout.addRow("Category:", self.category)
        
        self.priority = QComboBox()
        self.priority.addItems(["Lowest", "Low", "Normal", "High", "Highest"])
        self.priority.setCurrentText("Normal")
        options_layout.addRow("Priority:", self.priority)
        
        self.connections = QSpinBox()
        self.connections.setRange(1, 16)
        self.connections.setValue(4)
        options_layout.addRow("Connections:", self.connections)
        
        options_group.setLayout(options_layout)
        layout.addWidget(options_group)
        
        # Filters
        filter_group = QGroupBox("Filters")
        filter_layout = QVBoxLayout()
        
        self.exclude_samples = QCheckBox("Exclude sample files")
        self.exclude_samples.setChecked(True)
        filter_layout.addWidget(self.exclude_samples)
        
        self.exclude_junk = QCheckBox("Exclude junk files")
        self.exclude_junk.setChecked(True)
        filter_layout.addWidget(self.exclude_junk)
        
        self.auto_extract = QCheckBox("Auto-extract archives")
        filter_layout.addWidget(self.auto_extract)
        
        filter_group.setLayout(filter_layout)
        layout.addWidget(filter_group)
        
        # Buttons
        button_box = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
        
        self.setLayout(layout)
        
        # Set default destination
        self.destination.setText(str(Path.home() / "Downloads"))
    
    def browse_container(self):
        """Browse for container file"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select Container File",
            "", "Container Files (*.dlc *.rsdf *.ccf);;All Files (*.*)"
        )
        if file_path:
            self.container_path.setText(file_path)
    
    def browse_destination(self):
        """Browse for destination directory"""
        directory = QFileDialog.getExistingDirectory(
            self, "Select Destination Directory"
        )
        if directory:
            self.destination.setText(directory)
    
    def get_downloads(self) -> List[DownloadItem]:
        """Get download items from dialog input"""
        downloads = []
        
        # Process URLs
        urls = []
        url_text = self.url_text.toPlainText().strip()
        if url_text:
            urls.extend(line.strip() for line in url_text.split('\n') if line.strip())
        
        # Process container file
        container_path = self.container_path.text().strip()
        if container_path and Path(container_path).exists():
            try:
                parser = ContainerParser()
                container_urls = parser.parse_container(container_path)
                urls.extend(container_urls)
            except Exception as e:
                QMessageBox.warning(self, "Container Error", f"Failed to parse container: {e}")
        
        # Create download items
        link_extractor = LinkExtractor()
        download_filter = DownloadFilter()
        
        # Deduplicate URLs
        urls = download_filter.deduplicate_urls(urls)
        
        for url in urls:
            # Extract filename from URL
            parsed_url = urlparse(url)
            filename = Path(parsed_url.path).name
            if not filename:
                filename = f"download_{int(time.time())}"
            
            # Create download item
            item = DownloadItem(
                id=hashlib.md5(url.encode()).hexdigest(),
                url=url,
                filename=filename,
                destination=self.destination.text(),
                category=self.category.currentText(),
                priority=DownloadPriority(self.priority.currentIndex() + 1),
                connections=self.connections.value(),
                auto_extract=self.auto_extract.isChecked()
            )
            
            downloads.append(item)
        
        # Apply filters
        if downloads:
            downloads = download_filter.filter_downloads(
                downloads,
                exclude_samples=self.exclude_samples.isChecked(),
                exclude_junk=self.exclude_junk.isChecked(),
                prefer_quality=True
            )
        
        return downloads


class AdvancedDownloader(QMainWindow):
    """Advanced Download Manager with JDownloader-style interface"""
    
    def __init__(self):
        super().__init__()
        self.downloads = {}  # id -> DownloadItem
        self.workers = {}   # id -> DownloadWorker
        self.max_concurrent = 3
        self.max_queue_size = 10000
        
        # Components
        self.database = DownloadDatabase()
        self.download_filter = DownloadFilter()
        self.link_extractor = LinkExtractor()
        self.container_parser = ContainerParser()
        
        self.setup_ui()
        self.load_downloads()
        
        # Auto-save timer
        self.save_timer = QTimer()
        self.save_timer.timeout.connect(self.save_downloads)
        self.save_timer.start(30000)  # Save every 30 seconds
    
    def setup_ui(self):
        """Setup the main UI"""
        self.setWindowTitle("MediaHub Ultimate - Advanced Downloader")
        self.setGeometry(100, 100, 1200, 800)
        
        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout
        layout = QVBoxLayout(central_widget)
        
        # Create download table
        self.create_download_table()
        layout.addWidget(self.download_table)
        
        # Create menus and toolbars
        self.create_menus()
        self.create_toolbar()
        self.create_status_bar()
        
        # Apply theme
        self.apply_theme()
    
    def create_download_table(self):
        """Create the main download table"""
        self.download_table = QTableWidget()
        
        # Set columns
        columns = [
            "Filename", "Status", "Progress", "Size", "Downloaded",
            "Speed", "ETA", "Priority", "Category", "Added", "Actions"
        ]
        self.download_table.setColumnCount(len(columns))
        self.download_table.setHorizontalHeaderLabels(columns)
        
        # Configure table
        header = self.download_table.horizontalHeader()
        header.setStretchLastSection(True)
        header.setSectionResizeMode(QHeaderView.Interactive)
        
        # Set column widths
        self.download_table.setColumnWidth(0, 300)  # Filename
        self.download_table.setColumnWidth(1, 100)  # Status
        self.download_table.setColumnWidth(2, 120)  # Progress
        self.download_table.setColumnWidth(3, 100)  # Size
        self.download_table.setColumnWidth(4, 100)  # Downloaded
        self.download_table.setColumnWidth(5, 100)  # Speed
        self.download_table.setColumnWidth(6, 80)   # ETA
        self.download_table.setColumnWidth(7, 80)   # Priority
        self.download_table.setColumnWidth(8, 100)  # Category
        self.download_table.setColumnWidth(9, 150)  # Added
        
        # Enable sorting
        self.download_table.setSortingEnabled(True)
        
        # Context menu
        self.download_table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.download_table.customContextMenuRequested.connect(self.show_context_menu)
    
    def create_menus(self):
        """Create menu bar"""
        menubar = self.menuBar()
        
        # File menu
        file_menu = menubar.addMenu('&File')
        
        add_action = QAction('&Add Downloads...', self)
        add_action.setShortcut(QKeySequence.New)
        add_action.triggered.connect(self.add_downloads)
        file_menu.addAction(add_action)
        
        import_action = QAction('&Import Container...', self)
        import_action.triggered.connect(self.import_container)
        file_menu.addAction(import_action)
        
        file_menu.addSeparator()
        
        exit_action = QAction('E&xit', self)
        exit_action.setShortcut(QKeySequence.Quit)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # Downloads menu
        downloads_menu = menubar.addMenu('&Downloads')
        
        start_all_action = QAction('&Start All', self)
        start_all_action.triggered.connect(self.start_all_downloads)
        downloads_menu.addAction(start_all_action)
        
        pause_all_action = QAction('&Pause All', self)
        pause_all_action.triggered.connect(self.pause_all_downloads)
        downloads_menu.addAction(pause_all_action)
        
        downloads_menu.addSeparator()
        
        clear_completed_action = QAction('&Clear Completed', self)
        clear_completed_action.triggered.connect(self.clear_completed)
        downloads_menu.addAction(clear_completed_action)
        
        # Tools menu
        tools_menu = menubar.addMenu('&Tools')
        
        settings_action = QAction('&Settings...', self)
        settings_action.triggered.connect(self.show_settings)
        tools_menu.addAction(settings_action)
    
    def create_toolbar(self):
        """Create toolbar"""
        toolbar = self.addToolBar('Main')
        
        # Add downloads
        add_action = QAction('Add', self)
        add_action.triggered.connect(self.add_downloads)
        toolbar.addAction(add_action)
        
        toolbar.addSeparator()
        
        # Start/Pause/Stop
        start_action = QAction('Start', self)
        start_action.triggered.connect(self.start_selected)
        toolbar.addAction(start_action)
        
        pause_action = QAction('Pause', self)
        pause_action.triggered.connect(self.pause_selected)
        toolbar.addAction(pause_action)
        
        stop_action = QAction('Stop', self)
        stop_action.triggered.connect(self.stop_selected)
        toolbar.addAction(stop_action)
        
        toolbar.addSeparator()
        
        # Remove
        remove_action = QAction('Remove', self)
        remove_action.triggered.connect(self.remove_selected)
        toolbar.addAction(remove_action)
    
    def create_status_bar(self):
        """Create status bar"""
        self.status_bar = self.statusBar()
        
        # Download stats
        self.download_stats = QLabel("Downloads: 0 Total, 0 Active, 0 Completed")
        self.status_bar.addWidget(self.download_stats)
        
        # Speed indicator
        self.speed_label = QLabel("Speed: 0 KB/s")
        self.status_bar.addPermanentWidget(self.speed_label)
        
        # Queue size
        self.queue_label = QLabel("Queue: 0/10000")
        self.status_bar.addPermanentWidget(self.queue_label)
    
    def apply_theme(self):
        """Apply dark theme"""
        self.setStyleSheet("""
            QMainWindow {
                background-color: #1e1e1e;
                color: #d4d4d4;
            }
            QTableWidget {
                background-color: #252526;
                color: #d4d4d4;
                gridline-color: #3c3c3c;
                selection-background-color: #264f78;
            }
            QTableWidget::item {
                padding: 5px;
                border-bottom: 1px solid #3c3c3c;
            }
            QTableWidget::item:selected {
                background-color: #264f78;
            }
            QHeaderView::section {
                background-color: #2d2d30;
                color: #d4d4d4;
                padding: 5px;
                border: 1px solid #3c3c3c;
            }
            QMenuBar {
                background-color: #2d2d30;
                color: #d4d4d4;
            }
            QMenuBar::item:selected {
                background-color: #3c3c3c;
            }
            QMenu {
                background-color: #2d2d30;
                color: #d4d4d4;
                border: 1px solid #3c3c3c;
            }
            QMenu::item:selected {
                background-color: #3c3c3c;
            }
            QToolBar {
                background-color: #2d2d30;
                border: none;
                spacing: 3px;
            }
            QStatusBar {
                background-color: #2d2d30;
                color: #d4d4d4;
            }
            QProgressBar {
                border: 1px solid #3c3c3c;
                border-radius: 3px;
                text-align: center;
                background-color: #252526;
                color: #d4d4d4;
            }
            QProgressBar::chunk {
                background-color: #007acc;
                border-radius: 2px;
            }
        """)
    
    # Download Management Methods
    def add_downloads(self):
        """Show add downloads dialog"""
        if len(self.downloads) >= self.max_queue_size:
            QMessageBox.warning(
                self, "Queue Full",
                f"Download queue is full (maximum {self.max_queue_size} items)."
            )
            return
        
        dialog = AddDownloadDialog(self)
        if dialog.exec_() == QDialog.Accepted:
            new_downloads = dialog.get_downloads()
            
            for download in new_downloads:
                if len(self.downloads) >= self.max_queue_size:
                    QMessageBox.information(
                        self, "Queue Limit Reached",
                        f"Added maximum allowed downloads. Queue limit: {self.max_queue_size}"
                    )
                    break
                
                self.downloads[download.id] = download
                self.add_download_to_table(download)
                self.database.save_download(download)
            
            self.update_stats()
            
            if new_downloads:
                self.status_bar.showMessage(f"Added {len(new_downloads)} downloads", 3000)
    
    def add_download_to_table(self, download: DownloadItem):
        """Add download item to table"""
        row = self.download_table.rowCount()
        self.download_table.insertRow(row)
        
        # Filename
        self.download_table.setItem(row, 0, QTableWidgetItem(download.filename))
        
        # Status
        self.download_table.setItem(row, 1, QTableWidgetItem(download.status.value))
        
        # Progress
        progress_widget = QProgressBar()
        progress_widget.setValue(int(download.progress))
        self.download_table.setCellWidget(row, 2, progress_widget)
        
        # Size
        size_text = self.format_bytes(download.size) if download.size > 0 else "Unknown"
        self.download_table.setItem(row, 3, QTableWidgetItem(size_text))
        
        # Downloaded
        downloaded_text = self.format_bytes(download.downloaded)
        self.download_table.setItem(row, 4, QTableWidgetItem(downloaded_text))
        
        # Speed
        speed_text = f"{self.format_bytes(download.speed)}/s" if download.speed > 0 else "--"
        self.download_table.setItem(row, 5, QTableWidgetItem(speed_text))
        
        # ETA
        self.download_table.setItem(row, 6, QTableWidgetItem(download.eta))
        
        # Priority
        self.download_table.setItem(row, 7, QTableWidgetItem(download.priority.name))
        
        # Category
        self.download_table.setItem(row, 8, QTableWidgetItem(download.category))
        
        # Added date
        added_text = download.added_date.strftime("%Y-%m-%d %H:%M")
        self.download_table.setItem(row, 9, QTableWidgetItem(added_text))
        
        # Actions (placeholder)
        self.download_table.setItem(row, 10, QTableWidgetItem(""))
        
        # Store download ID in row
        self.download_table.item(row, 0).setData(Qt.UserRole, download.id)
    
    def update_download_row(self, download_id: str):
        """Update download row in table"""
        if download_id not in self.downloads:
            return
        
        download = self.downloads[download_id]
        
        # Find row
        for row in range(self.download_table.rowCount()):
            item = self.download_table.item(row, 0)
            if item and item.data(Qt.UserRole) == download_id:
                # Update status
                self.download_table.item(row, 1).setText(download.status.value)
                
                # Update progress
                progress_widget = self.download_table.cellWidget(row, 2)
                if progress_widget:
                    progress_widget.setValue(int(download.progress))
                
                # Update downloaded
                downloaded_text = self.format_bytes(download.downloaded)
                self.download_table.item(row, 4).setText(downloaded_text)
                
                # Update speed
                speed_text = f"{self.format_bytes(download.speed)}/s" if download.speed > 0 else "--"
                self.download_table.item(row, 5).setText(speed_text)
                
                # Update ETA
                self.download_table.item(row, 6).setText(download.eta)
                
                break
    
    def start_selected(self):
        """Start selected downloads"""
        selected_rows = self.get_selected_rows()
        for row in selected_rows:
            download_id = self.download_table.item(row, 0).data(Qt.UserRole)
            self.start_download(download_id)
    
    def start_download(self, download_id: str):
        """Start a specific download"""
        if download_id not in self.downloads:
            return
        
        download = self.downloads[download_id]
        
        # Check if already downloading
        if download_id in self.workers:
            return
        
        # Check concurrent download limit
        active_downloads = len([w for w in self.workers.values() if w.isRunning()])
        if active_downloads >= self.max_concurrent:
            download.status = DownloadStatus.QUEUED
            self.update_download_row(download_id)
            return
        
        # Create and start worker
        worker = DownloadWorker(download)
        worker.progress_updated.connect(self.on_progress_updated)
        worker.status_changed.connect(self.on_status_changed)
        worker.completed.connect(self.on_download_completed)
        worker.error_occurred.connect(self.on_download_error)
        
        self.workers[download_id] = worker
        download.started_date = datetime.now()
        worker.start()
    
    def pause_selected(self):
        """Pause selected downloads"""
        selected_rows = self.get_selected_rows()
        for row in selected_rows:
            download_id = self.download_table.item(row, 0).data(Qt.UserRole)
            self.pause_download(download_id)
    
    def pause_download(self, download_id: str):
        """Pause a specific download"""
        if download_id in self.workers:
            self.workers[download_id].pause()
    
    def stop_selected(self):
        """Stop selected downloads"""
        selected_rows = self.get_selected_rows()
        for row in selected_rows:
            download_id = self.download_table.item(row, 0).data(Qt.UserRole)
            self.stop_download(download_id)
    
    def stop_download(self, download_id: str):
        """Stop a specific download"""
        if download_id in self.workers:
            self.workers[download_id].stop()
            self.workers[download_id].wait()
            del self.workers[download_id]
    
    def remove_selected(self):
        """Remove selected downloads"""
        selected_rows = self.get_selected_rows()
        
        if not selected_rows:
            return
        
        reply = QMessageBox.question(
            self, "Remove Downloads",
            f"Remove {len(selected_rows)} selected download(s)?",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            for row in reversed(sorted(selected_rows)):
                download_id = self.download_table.item(row, 0).data(Qt.UserRole)
                
                # Stop download if active
                self.stop_download(download_id)
                
                # Remove from database
                self.database.delete_download(download_id)
                
                # Remove from memory
                if download_id in self.downloads:
                    del self.downloads[download_id]
                
                # Remove from table
                self.download_table.removeRow(row)
            
            self.update_stats()
    
    def get_selected_rows(self) -> List[int]:
        """Get list of selected row indices"""
        selection = self.download_table.selectionModel()
        if selection.hasSelection():
            return [index.row() for index in selection.selectedRows()]
        return []
    
    # Event Handlers
    def on_progress_updated(self, download_id: str, downloaded: int, total: int, speed: float):
        """Handle download progress update"""
        if download_id in self.downloads:
            download = self.downloads[download_id]
            download.downloaded = downloaded
            download.size = total if total > 0 else download.size
            download.speed = speed
            
            self.update_download_row(download_id)
            self.update_stats()
    
    def on_status_changed(self, download_id: str, status: str):
        """Handle download status change"""
        if download_id in self.downloads:
            download = self.downloads[download_id]
            download.status = DownloadStatus(status)
            self.update_download_row(download_id)
            self.update_stats()
    
    def on_download_completed(self, download_id: str):
        """Handle download completion"""
        if download_id in self.downloads:
            download = self.downloads[download_id]
            download.completed_date = datetime.now()
            self.database.save_download(download)
            
            # Remove worker
            if download_id in self.workers:
                del self.workers[download_id]
            
            # Auto-extract if enabled
            if download.auto_extract:
                self.extract_archive(download)
            
            # Start next queued download
            self.start_next_queued()
            
            self.update_stats()
    
    def on_download_error(self, download_id: str, error_message: str):
        """Handle download error"""
        if download_id in self.downloads:
            download = self.downloads[download_id]
            download.error_message = error_message
            download.retry_count += 1
            
            # Retry if under limit
            if download.retry_count < download.max_retries:
                # Retry after delay
                QTimer.singleShot(5000, lambda: self.start_download(download_id))
            else:
                download.status = DownloadStatus.FAILED
            
            self.update_download_row(download_id)
            self.database.save_download(download)
            
            # Remove worker
            if download_id in self.workers:
                del self.workers[download_id]
            
            self.update_stats()
    
    def start_next_queued(self):
        """Start next queued download if slot available"""
        active_downloads = len([w for w in self.workers.values() if w.isRunning()])
        if active_downloads >= self.max_concurrent:
            return
        
        # Find next queued download
        for download in self.downloads.values():
            if download.status == DownloadStatus.QUEUED:
                self.start_download(download.id)
                break
    
    def extract_archive(self, download: DownloadItem):
        """Extract archive file (placeholder)"""
        # Implementation would handle archive extraction
        pass
    
    def start_all_downloads(self):
        """Start all pending downloads"""
        for download in self.downloads.values():
            if download.status == DownloadStatus.PENDING:
                self.start_download(download.id)
    
    def pause_all_downloads(self):
        """Pause all active downloads"""
        for download_id in list(self.workers.keys()):
            self.pause_download(download_id)
    
    def clear_completed(self):
        """Clear completed downloads"""
        to_remove = []
        
        for row in range(self.download_table.rowCount()):
            download_id = self.download_table.item(row, 0).data(Qt.UserRole)
            if download_id in self.downloads:
                download = self.downloads[download_id]
                if download.status == DownloadStatus.COMPLETED:
                    to_remove.append((row, download_id))
        
        # Remove in reverse order
        for row, download_id in reversed(to_remove):
            self.database.delete_download(download_id)
            del self.downloads[download_id]
            self.download_table.removeRow(row)
        
        self.update_stats()
    
    def import_container(self):
        """Import container file"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Import Container File",
            "", "Container Files (*.dlc *.rsdf *.ccf);;All Files (*.*)"
        )
        
        if file_path:
            try:
                urls = self.container_parser.parse_container(file_path)
                
                # Create download items
                downloads = []
                for url in urls:
                    parsed_url = urlparse(url)
                    filename = Path(parsed_url.path).name or f"download_{int(time.time())}"
                    
                    download = DownloadItem(
                        id=hashlib.md5(url.encode()).hexdigest(),
                        url=url,
                        filename=filename,
                        destination=str(Path.home() / "Downloads")
                    )
                    downloads.append(download)
                
                # Add to queue
                for download in downloads:
                    if len(self.downloads) >= self.max_queue_size:
                        break
                    
                    self.downloads[download.id] = download
                    self.add_download_to_table(download)
                    self.database.save_download(download)
                
                self.update_stats()
                self.status_bar.showMessage(f"Imported {len(downloads)} downloads from container", 3000)
                
            except Exception as e:
                QMessageBox.critical(self, "Import Error", f"Failed to import container: {e}")
    
    def show_context_menu(self, position):
        """Show context menu for download table"""
        if self.download_table.itemAt(position) is None:
            return
        
        menu = QMenu(self)
        
        start_action = menu.addAction("Start")
        pause_action = menu.addAction("Pause")
        stop_action = menu.addAction("Stop")
        menu.addSeparator()
        
        remove_action = menu.addAction("Remove")
        
        action = menu.exec_(self.download_table.mapToGlobal(position))
        
        if action == start_action:
            self.start_selected()
        elif action == pause_action:
            self.pause_selected()
        elif action == stop_action:
            self.stop_selected()
        elif action == remove_action:
            self.remove_selected()
    
    def show_settings(self):
        """Show settings dialog (placeholder)"""
        QMessageBox.information(self, "Settings", "Settings dialog not implemented yet.")
    
    # Utility Methods
    def format_bytes(self, bytes_count: int) -> str:
        """Format bytes to human readable format"""
        if bytes_count == 0:
            return "0 B"
        
        size_names = ["B", "KB", "MB", "GB", "TB"]
        import math
        i = int(math.floor(math.log(bytes_count, 1024)))
        p = math.pow(1024, i)
        s = round(bytes_count / p, 2)
        return f"{s} {size_names[i]}"
    
    def update_stats(self):
        """Update download statistics"""
        total = len(self.downloads)
        active = len([d for d in self.downloads.values() if d.is_active])
        completed = len([d for d in self.downloads.values() if d.is_complete])
        
        self.download_stats.setText(f"Downloads: {total} Total, {active} Active, {completed} Completed")
        
        # Calculate total speed
        total_speed = sum(d.speed for d in self.downloads.values() if d.is_active)
        self.speed_label.setText(f"Speed: {self.format_bytes(total_speed)}/s")
        
        # Update queue
        self.queue_label.setText(f"Queue: {total}/{self.max_queue_size}")
    
    def load_downloads(self):
        """Load downloads from database"""
        downloads = self.database.load_downloads()
        
        for download in downloads:
            self.downloads[download.id] = download
            self.add_download_to_table(download)
        
        self.update_stats()
    
    def save_downloads(self):
        """Save all downloads to database"""
        for download in self.downloads.values():
            self.database.save_download(download)
    
    def closeEvent(self, event):
        """Handle application close"""
        # Stop all downloads
        for worker in self.workers.values():
            worker.stop()
            worker.wait()
        
        # Save downloads
        self.save_downloads()
        
        event.accept()


def main():
    """Main entry point"""
    app = QApplication(sys.argv)
    
    # Set application properties
    app.setApplicationName("MediaHub Ultimate Downloader")
    app.setApplicationVersion("1.0.0")
    app.setOrganizationName("MediaHub")
    
    # Create and show the downloader
    downloader = AdvancedDownloader()
    downloader.show()
    
    # Start the application
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
