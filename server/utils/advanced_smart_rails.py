"""
Advanced Smart Rails Engine - ML-Powered Content Analysis and Recommendations
Extends basic smart rails with machine learning capabilities and advanced heuristics
"""

import os
import re
import json
import logging
import sqlite3
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path
from datetime import datetime, timedelta
from collections import defaultdict, Counter
import hashlib

class AdvancedSmartRailsEngine:
    """Advanced smart rails with ML-powered content analysis"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # Advanced pattern matching with confidence scoring
        self.quality_patterns = {
            '4k_uhd': {
                'patterns': [
                    re.compile(r'(?i)\b(2160p|UHD|4K)\b'),
                    re.compile(r'(?i)\b(Ultra\.HD|Ultra-HD)\b')
                ],
                'confidence': 0.95
            },
            'hdr': {
                'patterns': [
                    re.compile(r'(?i)\b(HDR|HDR10|HDR10\+)\b'),
                    re.compile(r'(?i)\b(High\.Dynamic\.Range)\b')
                ],
                'confidence': 0.90
            },
            'dolby_vision': {
                'patterns': [
                    re.compile(r'(?i)\b(DV|Dolby\.Vision|DoVi)\b'),
                    re.compile(r'(?i)\b(Vision)\b')
                ],
                'confidence': 0.95
            },
            'atmos': {
                'patterns': [
                    re.compile(r'(?i)\b(Atmos|EAC3\.Atmos|TrueHD\.Atmos)\b'),
                    re.compile(r'(?i)\b(Dolby\.Atmos)\b')
                ],
                'confidence': 0.92
            },
            'remux': {
                'patterns': [
                    re.compile(r'(?i)\bREMUX\b'),
                    re.compile(r'(?i)\b(BD\.REMUX|Blu-ray\.REMUX)\b')
                ],
                'confidence': 0.98
            }
        }
        
        # Advanced codec detection with quality scoring
        self.codec_patterns = {
            'x265_hevc': {
                'patterns': [re.compile(r'(?i)\b(x265|HEVC|H\.265)\b')],
                'quality_score': 8.5,
                'efficiency': 9.0
            },
            'x264_avc': {
                'patterns': [re.compile(r'(?i)\b(x264|AVC|H\.264)\b')],
                'quality_score': 7.0,
                'efficiency': 6.0
            },
            'av1': {
                'patterns': [re.compile(r'(?i)\b(AV1)\b')],
                'quality_score': 9.0,
                'efficiency': 9.5
            }
        }
        
        # Release group quality hierarchy (from custom.txt)
        self.release_group_hierarchy = {
            'ctrlhd': {'score': 10.0, 'never_remove': True},
            'cytsunee': {'score': 8.5, 'remove_if_ctrlhd': True},
            'oft': {'score': 7.0, 'remove_if_better': True},
            'sparks': {'score': 6.5},
            'ntg': {'score': 6.0},
            'rarbg': {'score': 5.5},
            'yts': {'score': 4.0}  # Lower quality but popular
        }
        
        # Advanced genre detection with context awareness
        self.genre_context = {
            'documentary': {
                'folder_hints': ['documentary', 'docs', 'docu', 'nature', 'history'],
                'title_hints': ['documentary', 'behind the scenes', 'making of'],
                'confidence_boost': 0.3
            },
            'standup_comedy': {
                'folder_hints': ['standup', 'comedy', 'stand-up'],
                'title_hints': ['comedy special', 'live at', 'standup'],
                'confidence_boost': 0.4
            },
            'animation': {
                'folder_hints': ['animation', 'animated', 'anime', 'cartoon'],
                'title_hints': ['animated', 'anime'],
                'confidence_boost': 0.2
            }
        }
        
        # User behavior tracking for recommendations
        self.user_preferences = {
            'quality_preference': 0.0,  # -1 to 1 (size vs quality)
            'genre_preferences': defaultdict(float),
            'decade_preferences': defaultdict(float),
            'language_preferences': defaultdict(float),
            'recently_watched': [],
            'watch_time_patterns': {}
        }
        
        # Content similarity cache
        self.similarity_cache = {}
        
    def analyze_content_quality(self, path: str, filename: str, metadata: Dict = None) -> Dict[str, Any]:
        """Advanced content quality analysis with confidence scoring"""
        full_path = f"{path}/{filename}"
        quality_analysis = {
            'overall_score': 0.0,
            'quality_features': {},
            'codec_info': {},
            'release_group': None,
            'confidence': 0.0
        }
        
        # Quality feature detection
        total_confidence = 0.0
        feature_count = 0
        
        for feature, config in self.quality_patterns.items():
            detected = False
            max_confidence = 0.0
            
            for pattern in config['patterns']:
                if pattern.search(full_path):
                    detected = True
                    max_confidence = max(max_confidence, config['confidence'])
            
            if detected:
                quality_analysis['quality_features'][feature] = {
                    'detected': True,
                    'confidence': max_confidence
                }
                total_confidence += max_confidence
                feature_count += 1
        
        # Codec analysis
        for codec, config in self.codec_patterns.items():
            for pattern in config['patterns']:
                if pattern.search(full_path):
                    quality_analysis['codec_info'][codec] = {
                        'detected': True,
                        'quality_score': config['quality_score'],
                        'efficiency': config['efficiency']
                    }
        
        # Release group detection
        for group, config in self.release_group_hierarchy.items():
            if re.search(rf'(?i)\b{re.escape(group)}\b', full_path):
                quality_analysis['release_group'] = {
                    'name': group,
                    'score': config['score'],
                    'never_remove': config.get('never_remove', False)
                }
                break
        
        # Calculate overall quality score
        if feature_count > 0:
            quality_analysis['confidence'] = total_confidence / feature_count
            
            # Base score from features
            base_score = len(quality_analysis['quality_features']) * 2.0
            
            # Codec bonus
            codec_bonus = sum(info['quality_score'] for info in quality_analysis['codec_info'].values()) * 0.1
            
            # Release group bonus
            release_bonus = quality_analysis['release_group']['score'] * 0.5 if quality_analysis['release_group'] else 0
            
            quality_analysis['overall_score'] = min(10.0, base_score + codec_bonus + release_bonus)
        
        return quality_analysis
    
    def detect_content_similarity(self, item1: Dict, item2: Dict) -> float:
        """Calculate content similarity score between two items"""
        cache_key = f"{item1.get('id', 0)}_{item2.get('id', 0)}"
        if cache_key in self.similarity_cache:
            return self.similarity_cache[cache_key]
        
        similarity_score = 0.0
        
        # Genre similarity
        genres1 = set(item1.get('metadata', {}).get('genres', []))
        genres2 = set(item2.get('metadata', {}).get('genres', []))
        if genres1 and genres2:
            genre_similarity = len(genres1.intersection(genres2)) / len(genres1.union(genres2))
            similarity_score += genre_similarity * 0.3
        
        # Year similarity (decade-based)
        year1 = item1.get('metadata', {}).get('year')
        year2 = item2.get('metadata', {}).get('year')
        if year1 and year2:
            year_diff = abs(year1 - year2)
            year_similarity = max(0, 1 - (year_diff / 20))  # 20-year window
            similarity_score += year_similarity * 0.2
        
        # Director/Creator similarity
        director1 = item1.get('metadata', {}).get('director', '')
        director2 = item2.get('metadata', {}).get('director', '')
        if director1 and director2 and director1.lower() == director2.lower():
            similarity_score += 0.4
        
        # Quality similarity
        quality1 = self.analyze_content_quality(item1.get('path', ''), item1.get('filename', ''))
        quality2 = self.analyze_content_quality(item2.get('path', ''), item2.get('filename', ''))
        quality_diff = abs(quality1['overall_score'] - quality2['overall_score'])
        quality_similarity = max(0, 1 - (quality_diff / 10))
        similarity_score += quality_similarity * 0.1
        
        # Cache the result
        self.similarity_cache[cache_key] = similarity_score
        return similarity_score
    
    def generate_recommendations(self, user_history: List[Dict], library_items: List[Dict], limit: int = 20) -> List[Dict]:
        """Generate ML-powered content recommendations"""
        if not user_history:
            return self.generate_trending_recommendations(library_items, limit)
        
        recommendations = []
        recommendation_scores = {}
        
        # Analyze user preferences from history
        self.update_user_preferences(user_history)
        
        for item in library_items:
            if item.get('id') in [h.get('id') for h in user_history]:
                continue  # Skip already watched
            
            score = 0.0
            
            # Genre preference scoring
            item_genres = item.get('metadata', {}).get('genres', [])
            for genre in item_genres:
                score += self.user_preferences['genre_preferences'].get(genre.lower(), 0) * 0.3
            
            # Quality preference scoring
            quality_analysis = self.analyze_content_quality(item.get('path', ''), item.get('filename', ''))
            if self.user_preferences['quality_preference'] > 0:
                score += quality_analysis['overall_score'] * 0.2
            
            # Similarity to recently watched
            for watched_item in user_history[-5:]:  # Last 5 items
                similarity = self.detect_content_similarity(item, watched_item)
                score += similarity * 0.3
            
            # Decade preference
            year = item.get('metadata', {}).get('year')
            if year:
                decade = f"{(year // 10) * 10}s"
                score += self.user_preferences['decade_preferences'].get(decade, 0) * 0.2
            
            recommendation_scores[item.get('id')] = score
            
        # Sort by score and return top recommendations
        sorted_items = sorted(library_items, 
                            key=lambda x: recommendation_scores.get(x.get('id'), 0), 
                            reverse=True)
        
        return sorted_items[:limit]
    
    def generate_trending_recommendations(self, library_items: List[Dict], limit: int = 20) -> List[Dict]:
        """Generate trending recommendations based on quality and recency"""
        scored_items = []
        
        for item in library_items:
            score = 0.0
            
            # Quality score
            quality_analysis = self.analyze_content_quality(item.get('path', ''), item.get('filename', ''))
            score += quality_analysis['overall_score'] * 0.4
            
            # Recency score (newer content gets higher score)
            year = item.get('metadata', {}).get('year')
            if year:
                current_year = datetime.now().year
                recency_score = max(0, 1 - ((current_year - year) / 20))  # 20-year window
                score += recency_score * 0.3
            
            # Rating score
            rating = item.get('metadata', {}).get('rating', 0)
            if rating:
                score += (rating / 10) * 0.3
            
            scored_items.append((item, score))
        
        # Sort by score and return top items
        sorted_items = sorted(scored_items, key=lambda x: x[1], reverse=True)
        return [item[0] for item in sorted_items[:limit]]
    
    def update_user_preferences(self, user_history: List[Dict]):
        """Update user preferences based on viewing history"""
        if not user_history:
            return
        
        # Genre preferences
        genre_counts = Counter()
        for item in user_history:
            genres = item.get('metadata', {}).get('genres', [])
            for genre in genres:
                genre_counts[genre.lower()] += 1
        
        total_items = len(user_history)
        for genre, count in genre_counts.items():
            self.user_preferences['genre_preferences'][genre] = count / total_items
        
        # Decade preferences
        decade_counts = Counter()
        for item in user_history:
            year = item.get('metadata', {}).get('year')
            if year:
                decade = f"{(year // 10) * 10}s"
                decade_counts[decade] += 1
        
        for decade, count in decade_counts.items():
            self.user_preferences['decade_preferences'][decade] = count / total_items
        
        # Quality preference (analyze if user prefers quality over size)
        quality_scores = []
        for item in user_history:
            quality_analysis = self.analyze_content_quality(item.get('path', ''), item.get('filename', ''))
            quality_scores.append(quality_analysis['overall_score'])
        
        if quality_scores:
            avg_quality = sum(quality_scores) / len(quality_scores)
            self.user_preferences['quality_preference'] = (avg_quality - 5) / 5  # Normalize to -1 to 1
    
    def generate_advanced_smart_rails(self, library_items: List[Dict], user_history: List[Dict] = None) -> Dict[str, Any]:
        """Generate advanced smart rails with ML recommendations"""
        rails = {}
        
        # Quality-based rails with advanced scoring
        quality_rails = self.generate_quality_rails(library_items)
        rails.update(quality_rails)
        
        # Genre rails with context awareness
        genre_rails = self.generate_contextual_genre_rails(library_items)
        rails.update(genre_rails)
        
        # Recommendation rails
        if user_history:
            recommendation_rails = self.generate_recommendation_rails(library_items, user_history)
            rails.update(recommendation_rails)
        else:
            trending_rails = self.generate_trending_rails(library_items)
            rails.update(trending_rails)
        
        # Advanced discovery rails
        discovery_rails = self.generate_discovery_rails(library_items)
        rails.update(discovery_rails)
        
        return rails
    
    def generate_quality_rails(self, library_items: List[Dict]) -> Dict[str, List[Dict]]:
        """Generate quality-focused rails with advanced analysis"""
        rails = {
            'premium_4k_hdr': [],
            'dolby_vision_collection': [],
            'atmos_experience': [],
            'remux_quality': [],
            'high_efficiency_x265': [],
            'ctrlhd_releases': []
        }
        
        for item in library_items:
            quality_analysis = self.analyze_content_quality(item.get('path', ''), item.get('filename', ''))
            
            # Premium 4K HDR (multiple quality features)
            if (quality_analysis['quality_features'].get('4k_uhd', {}).get('detected') and 
                quality_analysis['quality_features'].get('hdr', {}).get('detected')):
                rails['premium_4k_hdr'].append({**item, 'quality_score': quality_analysis['overall_score']})
            
            # Dolby Vision
            if quality_analysis['quality_features'].get('dolby_vision', {}).get('detected'):
                rails['dolby_vision_collection'].append({**item, 'quality_score': quality_analysis['overall_score']})
            
            # Atmos
            if quality_analysis['quality_features'].get('atmos', {}).get('detected'):
                rails['atmos_experience'].append({**item, 'quality_score': quality_analysis['overall_score']})
            
            # REMUX
            if quality_analysis['quality_features'].get('remux', {}).get('detected'):
                rails['remux_quality'].append({**item, 'quality_score': quality_analysis['overall_score']})
            
            # High efficiency x265
            if quality_analysis['codec_info'].get('x265_hevc', {}).get('detected'):
                rails['high_efficiency_x265'].append({**item, 'quality_score': quality_analysis['overall_score']})
            
            # ctrlhd releases (premium release group)
            if (quality_analysis['release_group'] and 
                quality_analysis['release_group']['name'] == 'ctrlhd'):
                rails['ctrlhd_releases'].append({**item, 'quality_score': quality_analysis['overall_score']})
        
        # Sort each rail by quality score
        for rail_name in rails:
            rails[rail_name] = sorted(rails[rail_name], 
                                    key=lambda x: x.get('quality_score', 0), 
                                    reverse=True)[:50]  # Limit to top 50
        
        # Remove empty rails
        return {k: v for k, v in rails.items() if v}
    
    def generate_contextual_genre_rails(self, library_items: List[Dict]) -> Dict[str, List[Dict]]:
        """Generate genre rails with contextual awareness"""
        rails = {
            'premium_documentaries': [],
            'professional_standup': [],
            'award_winning_animation': [],
            'educational_content': []
        }
        
        for item in library_items:
            path = item.get('path', '').lower()
            filename = item.get('filename', '').lower()
            metadata = item.get('metadata', {})
            
            # Premium documentaries (high quality + documentary)
            if self.is_contextual_match('documentary', path, filename, metadata):
                quality_analysis = self.analyze_content_quality(item.get('path', ''), item.get('filename', ''))
                if quality_analysis['overall_score'] >= 6.0:  # High quality threshold
                    rails['premium_documentaries'].append({**item, 'context_score': quality_analysis['overall_score']})
            
            # Professional standup (high quality comedy specials)
            if self.is_contextual_match('standup_comedy', path, filename, metadata):
                quality_analysis = self.analyze_content_quality(item.get('path', ''), item.get('filename', ''))
                rails['professional_standup'].append({**item, 'context_score': quality_analysis['overall_score']})
            
            # Award-winning animation
            if self.is_contextual_match('animation', path, filename, metadata):
                # Check for award indicators
                award_indicators = ['oscar', 'academy', 'golden globe', 'annie award', 'bafta']
                has_award = any(indicator in f"{path} {filename}".lower() for indicator in award_indicators)
                if has_award or metadata.get('rating', 0) >= 8.0:
                    rails['award_winning_animation'].append({**item, 'context_score': metadata.get('rating', 7.0)})
        
        # Sort and limit each rail
        for rail_name in rails:
            rails[rail_name] = sorted(rails[rail_name], 
                                    key=lambda x: x.get('context_score', 0), 
                                    reverse=True)[:30]
        
        return {k: v for k, v in rails.items() if v}
    
    def is_contextual_match(self, genre_type: str, path: str, filename: str, metadata: Dict) -> bool:
        """Check if content matches genre with contextual awareness"""
        if genre_type not in self.genre_context:
            return False
        
        context = self.genre_context[genre_type]
        confidence = 0.0
        
        # Check folder hints
        for hint in context['folder_hints']:
            if hint in path:
                confidence += 0.3
        
        # Check title hints
        for hint in context['title_hints']:
            if hint in filename:
                confidence += 0.4
        
        # Check metadata genres
        metadata_genres = [g.lower() for g in metadata.get('genres', [])]
        for hint in context['folder_hints']:
            if hint in metadata_genres:
                confidence += 0.5
        
        return confidence >= 0.3  # Minimum confidence threshold
    
    def generate_recommendation_rails(self, library_items: List[Dict], user_history: List[Dict]) -> Dict[str, List[Dict]]:
        """Generate personalized recommendation rails"""
        rails = {
            'recommended_for_you': [],
            'because_you_watched': [],
            'similar_to_favorites': []
        }
        
        # Main recommendations
        recommendations = self.generate_recommendations(user_history, library_items, 30)
        rails['recommended_for_you'] = recommendations
        
        # Because you watched (based on last watched item)
        if user_history:
            last_watched = user_history[-1]
            similar_items = []
            
            for item in library_items:
                if item.get('id') != last_watched.get('id'):
                    similarity = self.detect_content_similarity(item, last_watched)
                    if similarity >= 0.3:  # Similarity threshold
                        similar_items.append({**item, 'similarity_score': similarity})
            
            rails['because_you_watched'] = sorted(similar_items, 
                                                key=lambda x: x.get('similarity_score', 0), 
                                                reverse=True)[:20]
        
        return {k: v for k, v in rails.items() if v}
    
    def generate_trending_rails(self, library_items: List[Dict]) -> Dict[str, List[Dict]]:
        """Generate trending content rails for new users"""
        rails = {
            'trending_now': [],
            'highest_rated': [],
            'recent_additions': []
        }
        
        # Trending (quality + recency)
        rails['trending_now'] = self.generate_trending_recommendations(library_items, 30)
        
        # Highest rated
        rated_items = [item for item in library_items if item.get('metadata', {}).get('rating', 0) > 0]
        rails['highest_rated'] = sorted(rated_items, 
                                      key=lambda x: x.get('metadata', {}).get('rating', 0), 
                                      reverse=True)[:25]
        
        # Recent additions (if we have added_date)
        recent_items = []
        for item in library_items:
            added_date = item.get('added_date')
            if added_date:
                try:
                    added_dt = datetime.fromisoformat(added_date)
                    days_ago = (datetime.now() - added_dt).days
                    if days_ago <= 30:  # Last 30 days
                        recent_items.append({**item, 'days_ago': days_ago})
                except ValueError:
                    continue
        
        rails['recent_additions'] = sorted(recent_items, 
                                         key=lambda x: x.get('days_ago', 999))[:20]
        
        return {k: v for k, v in rails.items() if v}
    
    def generate_discovery_rails(self, library_items: List[Dict]) -> Dict[str, List[Dict]]:
        """Generate content discovery rails"""
        rails = {
            'hidden_gems': [],
            'underrated_classics': [],
            'director_spotlight': {},
            'franchise_deep_dive': {}
        }
        
        # Hidden gems (high quality, low popularity indicators)
        for item in library_items:
            quality_analysis = self.analyze_content_quality(item.get('path', ''), item.get('filename', ''))
            rating = item.get('metadata', {}).get('rating', 0)
            
            # High quality but not mainstream (no popular release groups)
            if (quality_analysis['overall_score'] >= 7.0 and rating >= 7.5 and
                not any(popular in item.get('filename', '').lower() 
                       for popular in ['yts', 'rarbg', 'ettv'])):
                rails['hidden_gems'].append({**item, 'discovery_score': quality_analysis['overall_score'] + rating})
        
        # Sort discovery rails
        rails['hidden_gems'] = sorted(rails['hidden_gems'], 
                                    key=lambda x: x.get('discovery_score', 0), 
                                    reverse=True)[:15]
        
        return {k: v for k, v in rails.items() if v}

# Initialize advanced smart rails engine
advanced_smart_rails_engine = AdvancedSmartRailsEngine()

def generate_advanced_smart_rails(library_items: List[Dict], user_history: List[Dict] = None) -> Dict[str, Any]:
    """Generate advanced smart rails with ML capabilities - main entry point"""
    try:
        rails = advanced_smart_rails_engine.generate_advanced_smart_rails(library_items, user_history)
        
        # Add metadata for each rail
        rails_with_metadata = {}
        for rail_name, items in rails.items():
            if items:  # Only include non-empty rails
                rails_with_metadata[rail_name] = {
                    'items': items,
                    'metadata': get_advanced_rail_metadata(rail_name),
                    'count': len(items),
                    'last_updated': datetime.now().isoformat(),
                    'ml_powered': True
                }
        
        return {
            'rails': rails_with_metadata,
            'total_rails': len(rails_with_metadata),
            'total_items': sum(len(items) for items in rails.values()),
            'generated_at': datetime.now().isoformat(),
            'engine_version': 'advanced_ml_v2.0'
        }
        
    except Exception as e:
        logging.getLogger(__name__).error(f"Error generating advanced smart rails: {e}")
        return {'rails': {}, 'error': str(e)}

def get_advanced_rail_metadata(rail_name: str) -> Dict[str, Any]:
    """Get metadata for advanced rails"""
    metadata_map = {
        'premium_4k_hdr': {
            'title': 'Premium 4K HDR',
            'description': 'Ultra-high quality 4K content with HDR enhancement',
            'icon': '💎',
            'category': 'premium_quality',
            'ml_powered': True
        },
        'dolby_vision_collection': {
            'title': 'Dolby Vision',
            'description': 'Premium Dolby Vision enhanced content',
            'icon': '✨',
            'category': 'premium_quality',
            'ml_powered': True
        },
        'ctrlhd_releases': {
            'title': 'CTRLHD Premium',
            'description': 'Highest quality releases from CTRLHD group',
            'icon': '👑',
            'category': 'premium_quality',
            'ml_powered': True
        },
        'recommended_for_you': {
            'title': 'Recommended for You',
            'description': 'Personalized recommendations based on your viewing history',
            'icon': '🎯',
            'category': 'personalized',
            'ml_powered': True
        },
        'because_you_watched': {
            'title': 'Because You Watched',
            'description': 'Similar content to your recently watched items',
            'icon': '🔄',
            'category': 'personalized',
            'ml_powered': True
        },
        'trending_now': {
            'title': 'Trending Now',
            'description': 'Popular high-quality content trending in your library',
            'icon': '🔥',
            'category': 'trending',
            'ml_powered': True
        },
        'hidden_gems': {
            'title': 'Hidden Gems',
            'description': 'High-quality content you might have missed',
            'icon': '💎',
            'category': 'discovery',
            'ml_powered': True
        }
    }
    
    return metadata_map.get(rail_name, {
        'title': rail_name.replace('_', ' ').title(),
        'description': f'Advanced smart collection: {rail_name}',
        'icon': '🎬',
        'category': 'advanced',
        'ml_powered': True
    })

if __name__ == "__main__":
    # Test the advanced smart rails engine
    test_items = [
        {
            'id': 1,
            'path': '/Movies/4K',
            'filename': 'Dune.2021.2160p.HDR.DV.Atmos.CTRLHD.x265.mkv',
            'type': 'movie',
            'metadata': {'year': 2021, 'genres': ['Sci-Fi', 'Action'], 'rating': 8.5}
        },
        {
            'id': 2,
            'path': '/Movies/Documentary',
            'filename': 'Planet.Earth.II.2016.2160p.HDR.x265.mkv',
            'type': 'movie',
            'metadata': {'year': 2016, 'genres': ['Documentary', 'Nature'], 'rating': 9.2}
        }
    ]
    
    result = generate_advanced_smart_rails(test_items)
    print(json.dumps(result, indent=2))
