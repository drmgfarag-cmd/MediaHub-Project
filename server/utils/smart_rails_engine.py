"""
Smart Rails Engine - Token-based Content Detection and Organization
Implements heuristics from custom.txt for intelligent content categorization
"""

import os
import re
import json
import logging
from typing import Dict, List, Any, Optional
from pathlib import Path
from datetime import datetime, timedelta

class SmartRailsEngine:
    """Smart content detection and rail population engine"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # Token patterns from custom.txt specifications
        self.quality_patterns = {
            '4k_hdr': re.compile(r'(?i)\b(2160p|UHD|4K|HDR)\b'),
            'dolby_vision': re.compile(r'(?i)\b(DV|Dolby\.Vision|DoVi)\b'),
            'atmos': re.compile(r'(?i)\b(Atmos|EAC3\.Atmos|TrueHD\.Atmos)\b'),
            'remux': re.compile(r'(?i)\bREMUX\b'),
            '1080p': re.compile(r'(?i)\b1080p\b'),
            '720p': re.compile(r'(?i)\b720p\b')
        }
        
        self.codec_patterns = {
            'x265_hevc': re.compile(r'(?i)\b(x265|HEVC)\b'),
            'x264': re.compile(r'(?i)\bx264\b')
        }
        
        self.genre_patterns = {
            'documentary': re.compile(r'(?i)\b(Documentary|Docs|Docu)\b'),
            'standup': re.compile(r'(?i)\b(Standup|Stand-up|Stand up|Comedy\.Special)\b'),
            'animation': re.compile(r'(?i)\b(Animation|Animated)\b'),
            'educational': re.compile(r'(?i)\b(Educational|Learning|NatGeo Kids)\b')
        }
        
        self.audio_patterns = {
            'hi_res': re.compile(r'(?i)\.(flac|alac|wav)$'),
            'lossless': re.compile(r'(?i)\b(Lossless|FLAC|ALAC)\b'),
            'spatial': re.compile(r'(?i)\b(Atmos|Spatial|Dolby\.Atmos)\b'),
            'live': re.compile(r'(?i)\bLive\b'),
            'soundtrack': re.compile(r'(?i)\b(OST|Score|Soundtrack)\b')
        }
        
        self.book_patterns = {
            'ebook': re.compile(r'(?i)\.(epub|pdf)$'),
            'comic': re.compile(r'(?i)\.(cbz|cbr)$'),
            'manga': re.compile(r'(?i)(/Manga/|manga)'),
            'audiobook': re.compile(r'(?i)\.(m4b|mp3)$')
        }
        
        self.kids_patterns = {
            'kids_folder': re.compile(r'(?i)/Kids/'),
            'kids_tokens': re.compile(r'(?i)\b(Kids|Children|Family)\b')
        }
    
    def detect_quality_features(self, path: str, filename: str) -> Dict[str, bool]:
        """Detect quality features from path and filename"""
        full_path = f"{path}/{filename}"
        features = {}
        
        for feature, pattern in self.quality_patterns.items():
            features[feature] = bool(pattern.search(full_path))
        
        for codec, pattern in self.codec_patterns.items():
            features[codec] = bool(pattern.search(full_path))
        
        return features
    
    def detect_genre_features(self, path: str, filename: str, metadata: Dict = None) -> List[str]:
        """Detect genre from path, filename, and metadata"""
        full_path = f"{path}/{filename}"
        genres = []
        
        # Check metadata genres first
        if metadata and metadata.get('genres'):
            genres.extend(metadata['genres'])
        
        # Check path-based genre detection
        for genre, pattern in self.genre_patterns.items():
            if pattern.search(full_path):
                genres.append(genre)
        
        # Folder-based genre detection
        path_parts = path.lower().split('/')
        for part in path_parts:
            if part in ['action', 'drama', 'comedy', 'horror', 'thriller', 'sci-fi', 'fantasy']:
                genres.append(part)
        
        return list(set(genres))  # Remove duplicates
    
    def calculate_decade(self, year: Optional[int]) -> Optional[str]:
        """Calculate decade from year"""
        if not year or year < 1900:
            return None
        
        decade_start = (year // 10) * 10
        return f"{decade_start}s"
    
    def detect_series_activity(self, episodes: List[Dict], days_threshold: int = 90) -> bool:
        """Detect if series is ongoing (has episodes in last N days)"""
        if not episodes:
            return False
        
        cutoff_date = datetime.now() - timedelta(days=days_threshold)
        
        for episode in episodes:
            if episode.get('added_ts'):
                try:
                    added_date = datetime.fromtimestamp(episode['added_ts'])
                    if added_date > cutoff_date:
                        return True
                except (ValueError, TypeError):
                    continue
        
        return False
    
    def detect_miniseries(self, series_info: Dict) -> bool:
        """Detect if series is a miniseries (≤8 episodes)"""
        total_episodes = series_info.get('total_episodes', 0)
        if total_episodes > 0 and total_episodes <= 8:
            return True
        
        # Check for miniseries tokens
        path = series_info.get('path', '')
        filename = series_info.get('filename', '')
        full_path = f"{path}/{filename}"
        
        return bool(re.search(r'(?i)\bminiseries\b', full_path))
    
    def detect_anthology_series(self, series_info: Dict) -> bool:
        """Detect anthology series"""
        path = series_info.get('path', '')
        filename = series_info.get('filename', '')
        full_path = f"{path}/{filename}"
        
        # Check for anthology tokens
        if re.search(r'(?i)\banthology\b', full_path):
            return True
        
        # Check for non-numeric season names
        seasons = series_info.get('seasons', [])
        for season in seasons:
            season_name = season.get('name', '')
            if season_name and not re.match(r'^\d+$', season_name.strip()):
                return True
        
        return False
    
    def detect_audio_features(self, path: str, filename: str, metadata: Dict = None) -> Dict[str, bool]:
        """Detect audio-specific features"""
        full_path = f"{path}/{filename}"
        features = {}
        
        for feature, pattern in self.audio_patterns.items():
            features[feature] = bool(pattern.search(full_path))
        
        # Check sample rate for hi-res detection
        if metadata and metadata.get('sample_rate'):
            try:
                sample_rate = int(metadata['sample_rate'])
                features['hi_res'] = features.get('hi_res', False) or sample_rate >= 48000
            except (ValueError, TypeError):
                pass
        
        return features
    
    def detect_book_features(self, path: str, filename: str) -> Dict[str, bool]:
        """Detect book-specific features"""
        full_path = f"{path}/{filename}"
        features = {}
        
        for feature, pattern in self.book_patterns.items():
            features[feature] = bool(pattern.search(full_path))
        
        # Special handling for manga (CBZ/CBR in manga folders)
        if features.get('comic') and self.book_patterns['manga'].search(full_path):
            features['manga'] = True
            features['comic'] = False  # Reclassify as manga
        
        return features
    
    def detect_kids_content(self, path: str, filename: str, metadata: Dict = None) -> bool:
        """Detect kids content across all categories"""
        full_path = f"{path}/{filename}"
        
        # Check folder patterns
        if self.kids_patterns['kids_folder'].search(full_path):
            return True
        
        # Check filename tokens
        if self.kids_patterns['kids_tokens'].search(full_path):
            return True
        
        # Check metadata
        if metadata:
            genres = metadata.get('genres', [])
            for genre in genres:
                if re.search(r'(?i)\b(Kids|Children|Family|Animation)\b', genre):
                    return True
        
        return False
    
    def generate_smart_rails(self, library_items: List[Dict]) -> Dict[str, List[Dict]]:
        """Generate smart rails from library items"""
        rails = {
            # Quality rails
            '4k_hdr_content': [],
            'dolby_vision_content': [],
            'atmos_content': [],
            'remux_content': [],
            
            # Genre rails
            'documentaries': [],
            'standup_comedy': [],
            'animated_content': [],
            'educational_content': [],
            
            # Decade rails
            '2020s': [],
            '2010s': [],
            '2000s': [],
            '1990s': [],
            '1980s': [],
            '1970s': [],
            
            # TV-specific rails
            'ongoing_series': [],
            'miniseries': [],
            'anthology_series': [],
            
            # Audio rails
            'hi_res_audio': [],
            'lossless_audio': [],
            'spatial_audio': [],
            'live_recordings': [],
            'soundtracks': [],
            
            # Book rails
            'ebooks': [],
            'comics': [],
            'manga': [],
            'audiobooks': [],
            
            # Kids rails
            'kids_movies': [],
            'kids_tv': [],
            'kids_books': [],
            'kids_music': []
        }
        
        for item in library_items:
            path = item.get('path', '')
            filename = item.get('filename', '')
            item_type = item.get('type', '')
            metadata = item.get('metadata', {})
            year = metadata.get('year')
            
            # Quality detection
            quality_features = self.detect_quality_features(path, filename)
            if quality_features.get('4k_hdr'):
                rails['4k_hdr_content'].append(item)
            if quality_features.get('dolby_vision'):
                rails['dolby_vision_content'].append(item)
            if quality_features.get('atmos'):
                rails['atmos_content'].append(item)
            if quality_features.get('remux'):
                rails['remux_content'].append(item)
            
            # Genre detection
            genres = self.detect_genre_features(path, filename, metadata)
            if 'documentary' in genres:
                rails['documentaries'].append(item)
            if 'standup' in genres:
                rails['standup_comedy'].append(item)
            if 'animation' in genres:
                rails['animated_content'].append(item)
            if 'educational' in genres:
                rails['educational_content'].append(item)
            
            # Decade detection
            decade = self.calculate_decade(year)
            if decade and decade in rails:
                rails[decade].append(item)
            
            # TV-specific detection
            if item_type in ['series', 'tv']:
                if self.detect_series_activity(item.get('episodes', [])):
                    rails['ongoing_series'].append(item)
                if self.detect_miniseries(item):
                    rails['miniseries'].append(item)
                if self.detect_anthology_series(item):
                    rails['anthology_series'].append(item)
            
            # Audio-specific detection
            if item_type in ['audio', 'track', 'album']:
                audio_features = self.detect_audio_features(path, filename, metadata)
                if audio_features.get('hi_res'):
                    rails['hi_res_audio'].append(item)
                if audio_features.get('lossless'):
                    rails['lossless_audio'].append(item)
                if audio_features.get('spatial'):
                    rails['spatial_audio'].append(item)
                if audio_features.get('live'):
                    rails['live_recordings'].append(item)
                if audio_features.get('soundtrack'):
                    rails['soundtracks'].append(item)
            
            # Book-specific detection
            if item_type in ['book', 'ebook']:
                book_features = self.detect_book_features(path, filename)
                if book_features.get('ebook'):
                    rails['ebooks'].append(item)
                if book_features.get('comic'):
                    rails['comics'].append(item)
                if book_features.get('manga'):
                    rails['manga'].append(item)
                if book_features.get('audiobook'):
                    rails['audiobooks'].append(item)
            
            # Kids content detection
            if self.detect_kids_content(path, filename, metadata):
                if item_type in ['movie']:
                    rails['kids_movies'].append(item)
                elif item_type in ['series', 'tv']:
                    rails['kids_tv'].append(item)
                elif item_type in ['book', 'ebook']:
                    rails['kids_books'].append(item)
                elif item_type in ['audio', 'track']:
                    rails['kids_music'].append(item)
        
        # Filter out empty rails and limit items per rail
        filtered_rails = {}
        for rail_name, items in rails.items():
            if items:
                # Sort by relevance/quality and limit to top 50
                sorted_items = sorted(items, key=lambda x: x.get('rating', 0), reverse=True)[:50]
                filtered_rails[rail_name] = sorted_items
        
        return filtered_rails
    
    def get_rail_metadata(self, rail_name: str) -> Dict[str, Any]:
        """Get metadata for a specific rail"""
        rail_metadata = {
            '4k_hdr_content': {
                'title': '4K HDR Collection',
                'description': 'High-quality 4K HDR content with enhanced visual experience',
                'icon': '🎬',
                'category': 'quality'
            },
            'dolby_vision_content': {
                'title': 'Dolby Vision',
                'description': 'Premium Dolby Vision enhanced content',
                'icon': '✨',
                'category': 'quality'
            },
            'atmos_content': {
                'title': 'Dolby Atmos',
                'description': 'Immersive Dolby Atmos audio experience',
                'icon': '🔊',
                'category': 'quality'
            },
            'documentaries': {
                'title': 'Documentaries',
                'description': 'Educational and informative documentary content',
                'icon': '📚',
                'category': 'genre'
            },
            'standup_comedy': {
                'title': 'Stand-Up Comedy',
                'description': 'Comedy specials and stand-up performances',
                'icon': '😂',
                'category': 'genre'
            },
            'ongoing_series': {
                'title': 'Currently Airing',
                'description': 'TV series with recent episodes (last 90 days)',
                'icon': '📺',
                'category': 'tv'
            },
            'hi_res_audio': {
                'title': 'Hi-Res Audio',
                'description': 'High-resolution lossless audio content',
                'icon': '🎵',
                'category': 'audio'
            }
        }
        
        return rail_metadata.get(rail_name, {
            'title': rail_name.replace('_', ' ').title(),
            'description': f'Smart collection: {rail_name}',
            'icon': '📁',
            'category': 'general'
        })

# Initialize smart rails engine
smart_rails_engine = SmartRailsEngine()

def generate_smart_rails_for_library(library_items: List[Dict]) -> Dict[str, Any]:
    """Generate smart rails for library items - main entry point"""
    try:
        rails = smart_rails_engine.generate_smart_rails(library_items)
        
        # Add metadata for each rail
        rails_with_metadata = {}
        for rail_name, items in rails.items():
            rails_with_metadata[rail_name] = {
                'items': items,
                'metadata': smart_rails_engine.get_rail_metadata(rail_name),
                'count': len(items),
                'last_updated': datetime.now().isoformat()
            }
        
        return {
            'rails': rails_with_metadata,
            'total_rails': len(rails_with_metadata),
            'total_items': sum(len(items) for items in rails.values()),
            'generated_at': datetime.now().isoformat()
        }
        
    except Exception as e:
        logging.getLogger(__name__).error(f"Error generating smart rails: {e}")
        return {'rails': {}, 'error': str(e)}

if __name__ == "__main__":
    # Test the smart rails engine
    test_items = [
        {
            'path': '/Movies/Action',
            'filename': 'Dune.2021.2160p.HDR.DV.Atmos.x265.mkv',
            'type': 'movie',
            'metadata': {'year': 2021, 'genres': ['Sci-Fi', 'Action']}
        },
        {
            'path': '/TV/Ongoing',
            'filename': 'The Mandalorian S03E01.1080p.mkv',
            'type': 'series',
            'episodes': [{'added_ts': datetime.now().timestamp()}]
        }
    ]
    
    result = generate_smart_rails_for_library(test_items)
    print(json.dumps(result, indent=2))
