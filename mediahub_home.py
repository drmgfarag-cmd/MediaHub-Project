#!/usr/bin/env python3
"""
MediaHub Home - Prime Video/Netflix Style Interface
Mainstream entertainment platform with cinematic UI
"""

import sys
import os
import json
import re
import threading
import time
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set, Tuple, Any
from dataclasses import dataclass, field
from urllib.parse import urlparse

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QFrame, QScrollArea, QPushButton, QLineEdit, QComboBox,
    QGridLayout, QStackedWidget, QSplitter, QTextEdit, QSlider,
    QProgressBar, QGroupBox, QTabWidget, QListWidget, QListWidgetItem,
    QTreeWidget, QTreeWidgetItem, QToolBar, QMenuBar, QStatusBar,
    QDialog, QDialogButtonBox, QFormLayout, QCheckBox, QSpinBox,
    QDateTimeEdit, QFileDialog, QMessageBox, QInputDialog,
    QGraphicsView, QGraphicsScene, QGraphicsPixmapItem, QGraphicsOpacityEffect
)
from PyQt6.QtCore import (
    Qt, QTimer, QThread, pyqtSignal, QSettings, QSize,
    QUrl, QRect, QPoint, QPropertyAnimation, QEasingCurve,
    QParallelAnimationGroup, QSequentialAnimationGroup
)
from PyQt6.QtGui import (
    QFont, QIcon, QPixmap, QKeySequence, QAction, QPainter,
    QBrush, QColor, QPen, QLinearGradient, QPalette,
    QRadialGradient, QFontMetrics, QMovie, QPolygon, QTransform, QFontDatabase
)

import requests
from PIL import Image, ImageFilter, ImageEnhance


@dataclass
class MediaItem:
    """Represents a media item (movie, TV show, etc.)"""
    id: str
    title: str
    type: str  # movie, tv_show, documentary, etc.
    description: str = ""
    year: int = 0
    rating: float = 0.0
    duration: str = ""
    genre: List[str] = field(default_factory=list)
    poster_url: str = ""
    backdrop_url: str = ""
    trailer_url: str = ""
    local_poster: str = ""
    local_backdrop: str = ""
    watch_progress: float = 0.0  # 0-100%
    last_watched: Optional[datetime] = None
    is_favorite: bool = False
    is_watchlist: bool = False
    quality: str = "HD"
    audio_tracks: List[str] = field(default_factory=list)
    subtitle_tracks: List[str] = field(default_factory=list)
    file_path: str = ""
    file_size: int = 0
    added_date: datetime = field(default_factory=datetime.now)
    tags: List[str] = field(default_factory=list)
    collections: List[str] = field(default_factory=list)


class AnimatedCard(QFrame):
    """Animated card widget for media items"""
    
    clicked = pyqtSignal(str)  # media_id
    hover_entered = pyqtSignal(str)  # media_id
    hover_left = pyqtSignal(str)  # media_id
    
    def __init__(self, media_item: MediaItem, card_size: QSize = QSize(200, 300)):
        super().__init__()
        self.media_item = media_item
        self.card_size = card_size
        self.is_hovered = False
        self.hover_animation = None
        self.setup_ui()
        self.setup_animations()
    
    def setup_ui(self):
        """Setup the card UI"""
        self.setFixedSize(self.card_size)
        self.setFrameStyle(QFrame.NoFrame)
        self.setStyleSheet("""
            AnimatedCard {
                background-color: #1a1a1a;
                border-radius: 8px;
                border: 2px solid transparent;
            }
            AnimatedCard:hover {
                border: 2px solid #00a8ff;
                background-color: #252525;
            }
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Poster image
        self.poster_label = QLabel()
        self.poster_label.setFixedSize(self.card_size.width(), int(self.card_size.height() * 0.75))
        self.poster_label.setAlignment(Qt.AlignCenter)
        self.poster_label.setStyleSheet("""
            QLabel {
                background-color: #2a2a2a;
                border-radius: 6px;
                border: 1px solid #3a3a3a;
            }
        """)
        
        # Load poster image if available
        self.load_poster()
        
        layout.addWidget(self.poster_label)
        
        # Info section
        info_widget = QFrame()
        info_widget.setFixedHeight(int(self.card_size.height() * 0.25))
        info_layout = QVBoxLayout(info_widget)
        info_layout.setContentsMargins(8, 4, 8, 4)
        info_layout.setSpacing(2)
        
        # Title
        self.title_label = QLabel(self.media_item.title)
        self.title_label.setWordWrap(True)
        self.title_label.setStyleSheet("""
            QLabel {
                color: #ffffff;
                font-size: 12px;
                font-weight: bold;
            }
        """)
        info_layout.addWidget(self.title_label)
        
        # Metadata
        metadata_text = f"{self.media_item.year} • {self.media_item.type.replace('_', ' ').title()}"
        if self.media_item.rating > 0:
            metadata_text += f" • ★ {self.media_item.rating:.1f}"
        
        self.metadata_label = QLabel(metadata_text)
        self.metadata_label.setStyleSheet("""
            QLabel {
                color: #b0b0b0;
                font-size: 10px;
            }
        """)
        info_layout.addWidget(self.metadata_label)
        
        # Progress bar for watched content
        if self.media_item.watch_progress > 0:
            self.progress_bar = QProgressBar()
            self.progress_bar.setValue(int(self.media_item.watch_progress))
            self.progress_bar.setFixedHeight(3)
            self.progress_bar.setStyleSheet("""
                QProgressBar {
                    border: none;
                    background-color: #3a3a3a;
                    border-radius: 1px;
                }
                QProgressBar::chunk {
                    background-color: #00a8ff;
                    border-radius: 1px;
                }
            """)
            info_layout.addWidget(self.progress_bar)
        
        layout.addWidget(info_widget)
        
        # Quality badge
        if self.media_item.quality:
            self.quality_badge = QLabel(self.media_item.quality)
            self.quality_badge.setParent(self)
            self.quality_badge.setStyleSheet("""
                QLabel {
                    background-color: rgba(0, 168, 255, 200);
                    color: white;
                    font-size: 9px;
                    font-weight: bold;
                    padding: 2px 6px;
                    border-radius: 3px;
                }
            """)
            self.quality_badge.adjustSize()
            self.quality_badge.move(5, 5)
    
    def setup_animations(self):
        """Setup hover animations"""
        self.scale_effect = QGraphicsOpacityEffect()
        self.setGraphicsEffect(self.scale_effect)
        
        self.hover_animation = QPropertyAnimation(self, b"geometry")
        self.hover_animation.setDuration(200)
        self.hover_animation.setEasingCurve(QEasingCurve.OutCubic)
    
    def load_poster(self):
        """Load poster image"""
        if self.media_item.local_poster and Path(self.media_item.local_poster).exists():
            pixmap = QPixmap(self.media_item.local_poster)
            self.set_poster_pixmap(pixmap)
        elif self.media_item.poster_url:
            # Load poster from URL (would be implemented with threading)
            self.poster_label.setText("Loading...")
            self.poster_label.setStyleSheet("""
                QLabel {
                    background-color: #2a2a2a;
                    color: #666666;
                    border-radius: 6px;
                    border: 1px solid #3a3a3a;
                }
            """)
        else:
            # Default placeholder
            self.poster_label.setText("No Image")
            self.poster_label.setStyleSheet("""
                QLabel {
                    background-color: #2a2a2a;
                    color: #666666;
                    border-radius: 6px;
                    border: 1px solid #3a3a3a;
                }
            """)
    
    def set_poster_pixmap(self, pixmap: QPixmap):
        """Set poster pixmap with proper scaling"""
        if not pixmap.isNull():
            scaled_pixmap = pixmap.scaled(
                self.poster_label.size(),
                Qt.KeepAspectRatioByExpanding,
                Qt.SmoothTransformation
            )
            self.poster_label.setPixmap(scaled_pixmap)
    
    def enterEvent(self, event):
        """Handle mouse enter event"""
        self.is_hovered = True
        self.hover_entered.emit(self.media_item.id)
        
        # Scale animation
        current_rect = self.geometry()
        scale_factor = 1.05
        new_width = int(current_rect.width() * scale_factor)
        new_height = int(current_rect.height() * scale_factor)
        new_x = current_rect.x() - (new_width - current_rect.width()) // 2
        new_y = current_rect.y() - (new_height - current_rect.height()) // 2
        
        self.hover_animation.setStartValue(current_rect)
        self.hover_animation.setEndValue(QRect(new_x, new_y, new_width, new_height))
        self.hover_animation.start()
        
        # Raise widget to bring to front
        self.raise_()
        
        super().enterEvent(event)
    
    def leaveEvent(self, event):
        """Handle mouse leave event"""
        self.is_hovered = False
        self.hover_left.emit(self.media_item.id)
        
        # Scale back animation
        current_rect = self.geometry()
        scale_factor = 1.0 / 1.05
        new_width = int(current_rect.width() * scale_factor)
        new_height = int(current_rect.height() * scale_factor)
        new_x = current_rect.x() + (current_rect.width() - new_width) // 2
        new_y = current_rect.y() + (current_rect.height() - new_height) // 2
        
        self.hover_animation.setStartValue(current_rect)
        self.hover_animation.setEndValue(QRect(new_x, new_y, new_width, new_height))
        self.hover_animation.start()
        
        super().leaveEvent(event)
    
    def mousePressEvent(self, event):
        """Handle mouse click"""
        if event.button() == Qt.LeftButton:
            self.clicked.emit(self.media_item.id)
        super().mousePressEvent(event)


class HorizontalCarousel(QFrame):
    """Horizontal scrolling carousel for media items"""
    
    item_clicked = pyqtSignal(str)  # media_id
    
    def __init__(self, title: str, items: List[MediaItem]):
        super().__init__()
        self.title = title
        self.items = items
        self.cards = []
        self.current_offset = 0
        self.card_width = 200
        self.card_height = 300
        self.spacing = 10
        self.setup_ui()
    
    def setup_ui(self):
        """Setup carousel UI"""
        self.setFixedHeight(self.card_height + 60)  # Extra space for title and controls
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 10, 20, 10)
        layout.setSpacing(10)
        
        # Title section
        title_layout = QHBoxLayout()
        
        title_label = QLabel(self.title)
        title_label.setStyleSheet("""
            QLabel {
                color: #ffffff;
                font-size: 18px;
                font-weight: bold;
            }
        """)
        title_layout.addWidget(title_label)
        
        title_layout.addStretch()
        
        # Navigation buttons
        self.prev_btn = QPushButton("‹")
        self.prev_btn.setFixedSize(30, 30)
        self.prev_btn.setStyleSheet("""
            QPushButton {
                background-color: rgba(0, 0, 0, 150);
                color: white;
                border: none;
                border-radius: 15px;
                font-size: 18px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: rgba(0, 168, 255, 200);
            }
        """)
        self.prev_btn.clicked.connect(self.scroll_left)
        
        self.next_btn = QPushButton("›")
        self.next_btn.setFixedSize(30, 30)
        self.next_btn.setStyleSheet(self.prev_btn.styleSheet())
        self.next_btn.clicked.connect(self.scroll_right)
        
        title_layout.addWidget(self.prev_btn)
        title_layout.addWidget(self.next_btn)
        
        layout.addLayout(title_layout)
        
        # Scrollable cards area
        self.scroll_area = QScrollArea()
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scroll_area.setWidgetResizable(False)
        self.scroll_area.setFixedHeight(self.card_height + 10)
        
        # Container for cards
        self.cards_container = QWidget()
        total_width = len(self.items) * (self.card_width + self.spacing)
        self.cards_container.setFixedSize(total_width, self.card_height)
        
        # Create cards
        for i, item in enumerate(self.items):
            card = AnimatedCard(item, QSize(self.card_width, self.card_height))
            card.setParent(self.cards_container)
            card.move(i * (self.card_width + self.spacing), 0)
            card.clicked.connect(self.item_clicked.emit)
            self.cards.append(card)
        
        self.scroll_area.setWidget(self.cards_container)
        layout.addWidget(self.scroll_area)
    
    def scroll_left(self):
        """Scroll carousel left"""
        if self.current_offset > 0:
            self.current_offset = max(0, self.current_offset - self.card_width - self.spacing)
            self.scroll_area.horizontalScrollBar().setValue(self.current_offset)
    
    def scroll_right(self):
        """Scroll carousel right"""
        max_offset = max(0, self.cards_container.width() - self.scroll_area.width())
        if self.current_offset < max_offset:
            self.current_offset = min(max_offset, self.current_offset + self.card_width + self.spacing)
            self.scroll_area.horizontalScrollBar().setValue(self.current_offset)


class HeroSection(QFrame):
    """Large hero section for featured content"""
    
    play_clicked = pyqtSignal(str)  # media_id
    info_clicked = pyqtSignal(str)  # media_id
    
    def __init__(self, featured_item: MediaItem):
        super().__init__()
        self.featured_item = featured_item
        self.setup_ui()
        self.setup_auto_slide()
    
    def setup_ui(self):
        """Setup hero section UI"""
        self.setFixedHeight(500)
        self.setStyleSheet("""
            HeroSection {
                background-color: #000000;
                border-radius: 0px;
            }
        """)
        
        # Background image
        self.background_label = QLabel(self)
        self.background_label.setGeometry(0, 0, self.width(), self.height())
        self.background_label.setAlignment(Qt.AlignCenter)
        
        # Load background image
        if self.featured_item.local_backdrop and Path(self.featured_item.local_backdrop).exists():
            self.load_background_image(self.featured_item.local_backdrop)
        
        # Gradient overlay
        self.gradient_overlay = QLabel(self)
        self.gradient_overlay.setGeometry(0, 0, self.width(), self.height())
        self.gradient_overlay.setStyleSheet("""
            QLabel {
                background: qlineargradient(
                    spread:pad, x1:0, y1:0, x2:1, y2:0,
                    stop:0 rgba(0, 0, 0, 200),
                    stop:0.6 rgba(0, 0, 0, 100),
                    stop:1 rgba(0, 0, 0, 0)
                );
            }
        """)
        
        # Content area
        content_widget = QWidget(self)
        content_widget.setGeometry(50, 50, 600, 400)
        
        layout = QVBoxLayout(content_widget)
        layout.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        layout.setSpacing(15)
        
        # Title
        title_label = QLabel(self.featured_item.title)
        title_label.setStyleSheet("""
            QLabel {
                color: #ffffff;
                font-size: 48px;
                font-weight: bold;
                background: transparent;
            }
        """)
        title_label.setWordWrap(True)
        layout.addWidget(title_label)
        
        # Metadata
        metadata_parts = []
        if self.featured_item.year:
            metadata_parts.append(str(self.featured_item.year))
        if self.featured_item.duration:
            metadata_parts.append(self.featured_item.duration)
        if self.featured_item.rating > 0:
            metadata_parts.append(f"★ {self.featured_item.rating:.1f}")
        if self.featured_item.genre:
            metadata_parts.append(" • ".join(self.featured_item.genre[:3]))
        
        metadata_text = " • ".join(metadata_parts)
        metadata_label = QLabel(metadata_text)
        metadata_label.setStyleSheet("""
            QLabel {
                color: #e0e0e0;
                font-size: 16px;
                background: transparent;
            }
        """)
        layout.addWidget(metadata_label)
        
        # Description
        if self.featured_item.description:
            description_label = QLabel(self.featured_item.description[:300] + "..." 
                                     if len(self.featured_item.description) > 300 
                                     else self.featured_item.description)
            description_label.setWordWrap(True)
            description_label.setFixedWidth(500)
            description_label.setStyleSheet("""
                QLabel {
                    color: #c0c0c0;
                    font-size: 14px;
                    line-height: 1.4;
                    background: transparent;
                }
            """)
            layout.addWidget(description_label)
        
        # Buttons
        button_layout = QHBoxLayout()
        button_layout.setSpacing(15)
        
        # Play button
        self.play_btn = QPushButton("▶ Play")
        self.play_btn.setFixedSize(120, 45)
        self.play_btn.setStyleSheet("""
            QPushButton {
                background-color: #ffffff;
                color: #000000;
                border: none;
                border-radius: 5px;
                font-size: 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #e0e0e0;
            }
        """)
        self.play_btn.clicked.connect(lambda: self.play_clicked.emit(self.featured_item.id))
        
        # Info button
        self.info_btn = QPushButton("ⓘ More Info")
        self.info_btn.setFixedSize(120, 45)
        self.info_btn.setStyleSheet("""
            QPushButton {
                background-color: rgba(100, 100, 100, 150);
                color: #ffffff;
                border: 2px solid #ffffff;
                border-radius: 5px;
                font-size: 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: rgba(255, 255, 255, 200);
                color: #000000;
            }
        """)
        self.info_btn.clicked.connect(lambda: self.info_clicked.emit(self.featured_item.id))
        
        button_layout.addWidget(self.play_btn)
        button_layout.addWidget(self.info_btn)
        button_layout.addStretch()
        
        layout.addLayout(button_layout)
        layout.addStretch()
    
    def load_background_image(self, image_path: str):
        """Load and set background image with blur effect"""
        try:
            pixmap = QPixmap(image_path)
            if not pixmap.isNull():
                # Scale to fit
                scaled_pixmap = pixmap.scaled(
                    self.size(),
                    Qt.KeepAspectRatioByExpanding,
                    Qt.SmoothTransformation
                )
                self.background_label.setPixmap(scaled_pixmap)
        except Exception as e:
            print(f"Error loading background image: {e}")
    
    def setup_auto_slide(self):
        """Setup auto-sliding for multiple featured items"""
        # This would be implemented for cycling through multiple featured items
        pass
    
    def resizeEvent(self, event):
        """Handle resize event"""
        self.background_label.setGeometry(0, 0, self.width(), self.height())
        self.gradient_overlay.setGeometry(0, 0, self.width(), self.height())
        super().resizeEvent(event)


class SearchWidget(QFrame):
    """Advanced search widget with voice and visual search"""
    
    search_triggered = pyqtSignal(str, dict)  # query, filters
    
    def __init__(self):
        super().__init__()
        self.setup_ui()
    
    def setup_ui(self):
        """Setup search UI"""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 5, 10, 5)
        layout.setSpacing(10)
        
        # Search input
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search movies, TV shows, documentaries...")
        self.search_input.setFixedHeight(40)
        self.search_input.setStyleSheet("""
            QLineEdit {
                background-color: #2a2a2a;
                color: #ffffff;
                border: 2px solid #3a3a3a;
                border-radius: 20px;
                padding: 0 20px;
                font-size: 14px;
            }
            QLineEdit:focus {
                border: 2px solid #00a8ff;
            }
        """)
        self.search_input.returnPressed.connect(self.perform_search)
        
        # Voice search button
        self.voice_btn = QPushButton("🎤")
        self.voice_btn.setFixedSize(40, 40)
        self.voice_btn.setStyleSheet("""
            QPushButton {
                background-color: #2a2a2a;
                border: 2px solid #3a3a3a;
                border-radius: 20px;
                font-size: 16px;
            }
            QPushButton:hover {
                border: 2px solid #00a8ff;
                background-color: #3a3a3a;
            }
        """)
        self.voice_btn.clicked.connect(self.start_voice_search)
        
        # Visual search button
        self.visual_btn = QPushButton("📷")
        self.visual_btn.setFixedSize(40, 40)
        self.visual_btn.setStyleSheet(self.voice_btn.styleSheet())
        self.visual_btn.clicked.connect(self.start_visual_search)
        
        # Filter button
        self.filter_btn = QPushButton("⚙")
        self.filter_btn.setFixedSize(40, 40)
        self.filter_btn.setStyleSheet(self.voice_btn.styleSheet())
        self.filter_btn.clicked.connect(self.show_filters)
        
        layout.addWidget(self.search_input)
        layout.addWidget(self.voice_btn)
        layout.addWidget(self.visual_btn)
        layout.addWidget(self.filter_btn)
    
    def perform_search(self):
        """Perform text search"""
        query = self.search_input.text().strip()
        if query:
            filters = {}  # Add filter logic here
            self.search_triggered.emit(query, filters)
    
    def start_voice_search(self):
        """Start voice search (placeholder)"""
        QMessageBox.information(self, "Voice Search", "Voice search not implemented yet.")
    
    def start_visual_search(self):
        """Start visual search (placeholder)"""
        QMessageBox.information(self, "Visual Search", "Visual search not implemented yet.")
    
    def show_filters(self):
        """Show search filters (placeholder)"""
        QMessageBox.information(self, "Filters", "Search filters not implemented yet.")


class SmartCollection(QFrame):
    """Smart collection with auto-population rules"""
    
    def __init__(self, name: str, rules: Dict[str, Any]):
        super().__init__()
        self.name = name
        self.rules = rules
        self.items = []
        self.setup_ui()
    
    def setup_ui(self):
        """Setup collection UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Collection header
        header = QFrame()
        header.setFixedHeight(50)
        header.setStyleSheet("""
            QFrame {
                background-color: #1a1a1a;
                border-bottom: 1px solid #3a3a3a;
            }
        """)
        
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(20, 10, 20, 10)
        
        title_label = QLabel(self.name)
        title_label.setStyleSheet("""
            QLabel {
                color: #ffffff;
                font-size: 16px;
                font-weight: bold;
            }
        """)
        
        count_label = QLabel(f"{len(self.items)} items")
        count_label.setStyleSheet("""
            QLabel {
                color: #b0b0b0;
                font-size: 12px;
            }
        """)
        
        header_layout.addWidget(title_label)
        header_layout.addStretch()
        header_layout.addWidget(count_label)
        
        layout.addWidget(header)
        
        # Items grid (placeholder)
        items_widget = QLabel(f"Collection: {self.name}\nRules: {self.rules}")
        items_widget.setStyleSheet("""
            QLabel {
                color: #888888;
                padding: 20px;
            }
        """)
        layout.addWidget(items_widget)
    
    def populate_collection(self, all_items: List[MediaItem]):
        """Populate collection based on rules"""
        # Implementation would filter items based on rules
        pass


class MediaHubHome(QMainWindow):
    """Main MediaHub Home interface with Prime Video/Netflix styling"""
    
    def __init__(self):
        super().__init__()
        self.media_items = []
        self.collections = []
        self.current_user = "User"
        self.setup_sample_data()
        self.setup_ui()
        self.setup_theme()
    
    def setup_sample_data(self):
        """Setup sample media data"""
        # Sample media items
        self.media_items = [
            MediaItem(
                id="1",
                title="The Matrix",
                type="movie",
                description="A computer programmer discovers reality is a simulation.",
                year=1999,
                rating=8.7,
                duration="2h 16m",
                genre=["Action", "Sci-Fi"],
                quality="4K"
            ),
            MediaItem(
                id="2",
                title="Stranger Things",
                type="tv_show",
                description="Kids in a small town face supernatural forces.",
                year=2016,
                rating=8.7,
                duration="8 seasons",
                genre=["Drama", "Fantasy", "Horror"],
                quality="HD",
                watch_progress=65.0
            ),
            MediaItem(
                id="3",
                title="Inception",
                type="movie",
                description="A thief who enters people's dreams to steal secrets.",
                year=2010,
                rating=8.8,
                duration="2h 28m",
                genre=["Action", "Sci-Fi", "Thriller"],
                quality="4K"
            ),
            MediaItem(
                id="4",
                title="The Crown",
                type="tv_show",
                description="The reign of Queen Elizabeth II.",
                year=2016,
                rating=8.7,
                duration="6 seasons",
                genre=["Biography", "Drama", "History"],
                quality="4K"
            ),
            MediaItem(
                id="5",
                title="Dune",
                type="movie",
                description="Feature adaptation of Frank Herbert's science fiction novel.",
                year=2021,
                rating=8.0,
                duration="2h 35m",
                genre=["Action", "Adventure", "Drama"],
                quality="4K"
            )
        ]
        
        # Duplicate items for carousel demonstration
        self.media_items = self.media_items * 4
    
    def setup_ui(self):
        """Setup the main UI"""
        self.setWindowTitle("MediaHub Ultimate - Home")
        self.setGeometry(100, 100, 1400, 900)
        
        # Central widget with scroll area
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        
        main_widget = QWidget()
        scroll_area.setWidget(main_widget)
        self.setCentralWidget(scroll_area)
        
        # Main layout
        layout = QVBoxLayout(main_widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Top navigation bar
        self.create_navigation_bar(layout)
        
        # Hero section
        if self.media_items:
            hero = HeroSection(self.media_items[0])
            hero.play_clicked.connect(self.play_media)
            hero.info_clicked.connect(self.show_media_info)
            layout.addWidget(hero)
        
        # Content sections
        self.create_content_sections(layout)
        
        # Add spacing at bottom
        layout.addSpacing(50)
    
    def create_navigation_bar(self, parent_layout):
        """Create top navigation bar"""
        nav_bar = QFrame()
        nav_bar.setFixedHeight(80)
        nav_bar.setStyleSheet("""
            QFrame {
                background-color: rgba(0, 0, 0, 200);
                border-bottom: 1px solid #2a2a2a;
            }
        """)
        
        nav_layout = QHBoxLayout(nav_bar)
        nav_layout.setContentsMargins(30, 15, 30, 15)
        nav_layout.setSpacing(30)
        
        # Logo
        logo_label = QLabel("MEDIAHUB")
        logo_label.setStyleSheet("""
            QLabel {
                color: #00a8ff;
                font-size: 24px;
                font-weight: bold;
                background: transparent;
            }
        """)
        nav_layout.addWidget(logo_label)
        
        # Navigation links
        nav_links = ["Home", "Movies", "TV Shows", "Documentaries", "My List"]
        for link in nav_links:
            link_btn = QPushButton(link)
            link_btn.setStyleSheet("""
                QPushButton {
                    color: #ffffff;
                    background: transparent;
                    border: none;
                    font-size: 14px;
                    padding: 5px 10px;
                }
                QPushButton:hover {
                    color: #00a8ff;
                }
            """)
            nav_layout.addWidget(link_btn)
        
        nav_layout.addStretch()
        
        # Search widget
        search_widget = SearchWidget()
        search_widget.search_triggered.connect(self.perform_search)
        nav_layout.addWidget(search_widget)
        
        # User profile
        profile_btn = QPushButton(f"👤 {self.current_user}")
        profile_btn.setStyleSheet("""
            QPushButton {
                color: #ffffff;
                background: transparent;
                border: none;
                font-size: 14px;
                padding: 5px 10px;
            }
            QPushButton:hover {
                color: #00a8ff;
            }
        """)
        nav_layout.addWidget(profile_btn)
        
        parent_layout.addWidget(nav_bar)
    
    def create_content_sections(self, parent_layout):
        """Create content carousels and sections"""
        # Continue watching
        continue_watching = [item for item in self.media_items if item.watch_progress > 0]
        if continue_watching:
            carousel = HorizontalCarousel("Continue Watching", continue_watching[:10])
            carousel.item_clicked.connect(self.play_media)
            parent_layout.addWidget(carousel)
        
        # Trending now
        trending = self.media_items[:15]
        carousel = HorizontalCarousel("Trending Now", trending)
        carousel.item_clicked.connect(self.show_media_info)
        parent_layout.addWidget(carousel)
        
        # New releases
        new_releases = [item for item in self.media_items if item.year >= 2020][:15]
        if new_releases:
            carousel = HorizontalCarousel("New Releases", new_releases)
            carousel.item_clicked.connect(self.show_media_info)
            parent_layout.addWidget(carousel)
        
        # Movies
        movies = [item for item in self.media_items if item.type == "movie"][:15]
        if movies:
            carousel = HorizontalCarousel("Popular Movies", movies)
            carousel.item_clicked.connect(self.show_media_info)
            parent_layout.addWidget(carousel)
        
        # TV Shows
        tv_shows = [item for item in self.media_items if item.type == "tv_show"][:15]
        if tv_shows:
            carousel = HorizontalCarousel("TV Shows", tv_shows)
            carousel.item_clicked.connect(self.show_media_info)
            parent_layout.addWidget(carousel)
        
        # Action movies
        action_items = [item for item in self.media_items if "Action" in item.genre][:15]
        if action_items:
            carousel = HorizontalCarousel("Action & Adventure", action_items)
            carousel.item_clicked.connect(self.show_media_info)
            parent_layout.addWidget(carousel)
        
        # Sci-Fi
        scifi_items = [item for item in self.media_items if "Sci-Fi" in item.genre][:15]
        if scifi_items:
            carousel = HorizontalCarousel("Sci-Fi", scifi_items)
            carousel.item_clicked.connect(self.show_media_info)
            parent_layout.addWidget(carousel)
    
    def setup_theme(self):
        """Setup dark cinematic theme"""
        self.setStyleSheet("""
            QMainWindow {
                background-color: #0a0a0a;
                color: #ffffff;
            }
            QScrollArea {
                background-color: #0a0a0a;
                border: none;
            }
            QScrollBar:vertical {
                background-color: #1a1a1a;
                width: 12px;
                border-radius: 6px;
            }
            QScrollBar::handle:vertical {
                background-color: #3a3a3a;
                border-radius: 6px;
                min-height: 20px;
            }
            QScrollBar::handle:vertical:hover {
                background-color: #00a8ff;
            }
            QScrollBar::add-line:vertical,
            QScrollBar::sub-line:vertical {
                height: 0px;
            }
        """)
    
    # Event Handlers
    def play_media(self, media_id: str):
        """Handle media play request"""
        media_item = next((item for item in self.media_items if item.id == media_id), None)
        if media_item:
            QMessageBox.information(
                self, "Play Media",
                f"Playing: {media_item.title}\n\nThis would launch the media player."
            )
    
    def show_media_info(self, media_id: str):
        """Show detailed media information"""
        media_item = next((item for item in self.media_items if item.id == media_id), None)
        if media_item:
            info_text = f"""
            Title: {media_item.title}
            Type: {media_item.type.replace('_', ' ').title()}
            Year: {media_item.year}
            Rating: {media_item.rating}/10
            Duration: {media_item.duration}
            Genre: {', '.join(media_item.genre)}
            Quality: {media_item.quality}
            
            Description:
            {media_item.description}
            """
            
            QMessageBox.information(self, "Media Information", info_text)
    
    def perform_search(self, query: str, filters: Dict[str, Any]):
        """Perform media search"""
        QMessageBox.information(
            self, "Search",
            f"Searching for: {query}\nFilters: {filters}\n\nSearch functionality not fully implemented."
        )


def main():
    """Main entry point"""
    app = QApplication(sys.argv)
    
    # Set application properties
    app.setApplicationName("MediaHub Ultimate Home")
    app.setApplicationVersion("1.0.0")
    app.setOrganizationName("MediaHub")
    
    # Create and show the home interface
    home = MediaHubHome()
    home.show()
    
    # Start the application
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
