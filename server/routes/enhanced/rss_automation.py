"""
RSS Automation and Comprehensive Metadata Integration
Includes RSS feeder with missing episode search, metadata providers integration, and automation
"""

import os
import re
import json
import time
import threading
import feedparser
import requests
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from flask import Blueprint, request, jsonify, current_app
from urllib.parse import urljoin, urlparse
import xml.etree.ElementTree as ET

bp = Blueprint('rss_automation', __name__)

class MetadataProviderManager:
    """Manages multiple metadata providers with fallback chains"""
    
    def __init__(self, api_manager):
        self.api_manager = api_manager
        self.providers = {
            'tmdb': TMDBProvider(api_manager),
            'tvdb': TVDBProvider(api_manager),
            'omdb': OMDBProvider(api_manager),
            'google_books': GoogleBooksProvider(api_manager),
            'discogs': DiscogsProvider(api_manager),
            'acoustid': AcoustIDProvider(api_manager),
            'anilist': AniListProvider(api_manager)
        }
        
        # Default provider chains for different content types
        self.provider_chains = {
            'movie': ['tmdb', 'omdb'],
            'tv': ['tvdb', 'tmdb', 'omdb'],
            'book': ['google_books'],
            'music': ['discogs', 'acoustid'],
            'anime': ['anilist', 'tmdb']
        }
    
    def get_metadata(self, content_type: str, query: str, 
                    provider_chain: List[str] = None) -> Dict[str, Any]:
        """Get metadata using provider chain with fallback"""
        if not provider_chain:
            provider_chain = self.provider_chains.get(content_type, ['tmdb'])
        
        metadata = {}
        errors = []
        
        for provider_name in provider_chain:
            try:
                provider = self.providers.get(provider_name)
                if provider:
                    result = provider.search(query, content_type)
                    if result and result.get('success'):
                        metadata.update(result.get('data', {}))
                        metadata['provider'] = provider_name
                        break
                    else:
                        errors.append(f"{provider_name}: {result.get('error', 'No results')}")
            except Exception as e:
                errors.append(f"{provider_name}: {str(e)}")
        
        return {
            'success': bool(metadata),
            'metadata': metadata,
            'errors': errors
        }

class TMDBProvider:
    """The Movie Database provider"""
    
    def __init__(self, api_manager):
        self.api_key = api_manager.get_key('tmdb')
        self.base_url = 'https://api.themoviedb.org/3'
        self.image_base_url = 'https://image.tmdb.org/t/p/w500'
    
    def search(self, query: str, content_type: str) -> Dict[str, Any]:
        """Search TMDB for content"""
        if not self.api_key:
            return {'success': False, 'error': 'TMDB API key not configured'}
        
        try:
            endpoint = 'search/movie' if content_type == 'movie' else 'search/tv'
            url = f"{self.base_url}/{endpoint}"
            
            params = {
                'api_key': self.api_key,
                'query': query,
                'language': 'en-US'
            }
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            results = data.get('results', [])
            
            if results:
                item = results[0]  # Get first result
                
                # Get detailed information
                detail_url = f"{self.base_url}/{content_type}/{item['id']}"
                detail_response = requests.get(detail_url, params={'api_key': self.api_key}, timeout=10)
                detail_data = detail_response.json() if detail_response.ok else item
                
                metadata = {
                    'title': item.get('title') or item.get('name'),
                    'overview': item.get('overview'),
                    'release_date': item.get('release_date') or item.get('first_air_date'),
                    'poster_path': f"{self.image_base_url}{item['poster_path']}" if item.get('poster_path') else None,
                    'backdrop_path': f"{self.image_base_url}{item['backdrop_path']}" if item.get('backdrop_path') else None,
                    'vote_average': item.get('vote_average'),
                    'vote_count': item.get('vote_count'),
                    'genres': [g['name'] for g in detail_data.get('genres', [])],
                    'tmdb_id': item['id'],
                    'imdb_id': detail_data.get('imdb_id')
                }
                
                if content_type == 'tv':
                    metadata.update({
                        'number_of_seasons': detail_data.get('number_of_seasons'),
                        'number_of_episodes': detail_data.get('number_of_episodes'),
                        'status': detail_data.get('status'),
                        'networks': [n['name'] for n in detail_data.get('networks', [])]
                    })
                
                return {'success': True, 'data': metadata}
            
            return {'success': False, 'error': 'No results found'}
        
        except Exception as e:
            return {'success': False, 'error': str(e)}

class TVDBProvider:
    """TheTVDB provider"""
    
    def __init__(self, api_manager):
        self.api_key = api_manager.get_key('tvdb')
        self.base_url = 'https://api4.thetvdb.com/v4'
        self.token = None
    
    def _get_token(self):
        """Get authentication token"""
        if not self.api_key:
            return None
        
        try:
            url = f"{self.base_url}/login"
            data = {'apikey': self.api_key}
            
            response = requests.post(url, json=data, timeout=10)
            response.raise_for_status()
            
            result = response.json()
            self.token = result.get('data', {}).get('token')
            return self.token
        
        except Exception:
            return None
    
    def search(self, query: str, content_type: str) -> Dict[str, Any]:
        """Search TVDB for TV content"""
        if content_type != 'tv':
            return {'success': False, 'error': 'TVDB only supports TV content'}
        
        if not self.token:
            self.token = self._get_token()
        
        if not self.token:
            return {'success': False, 'error': 'TVDB authentication failed'}
        
        try:
            url = f"{self.base_url}/search"
            headers = {'Authorization': f'Bearer {self.token}'}
            params = {'query': query, 'type': 'series'}
            
            response = requests.get(url, headers=headers, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            results = data.get('data', [])
            
            if results:
                item = results[0]
                
                metadata = {
                    'title': item.get('name'),
                    'overview': item.get('overview'),
                    'first_air_date': item.get('first_air_date'),
                    'status': item.get('status', {}).get('name'),
                    'tvdb_id': item.get('id'),
                    'imdb_id': item.get('remote_ids', [{}])[0].get('id') if item.get('remote_ids') else None,
                    'poster_path': item.get('image_url'),
                    'networks': [item.get('primary_language')] if item.get('primary_language') else []
                }
                
                return {'success': True, 'data': metadata}
            
            return {'success': False, 'error': 'No results found'}
        
        except Exception as e:
            return {'success': False, 'error': str(e)}

class OMDBProvider:
    """Open Movie Database provider"""
    
    def __init__(self, api_manager):
        self.api_key = api_manager.get_key('omdb')
        self.base_url = 'http://www.omdbapi.com/'
    
    def search(self, query: str, content_type: str) -> Dict[str, Any]:
        """Search OMDB for content"""
        if not self.api_key:
            return {'success': False, 'error': 'OMDB API key not configured'}
        
        try:
            params = {
                'apikey': self.api_key,
                't': query,
                'plot': 'full'
            }
            
            if content_type == 'tv':
                params['type'] = 'series'
            elif content_type == 'movie':
                params['type'] = 'movie'
            
            response = requests.get(self.base_url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            if data.get('Response') == 'True':
                metadata = {
                    'title': data.get('Title'),
                    'year': data.get('Year'),
                    'rated': data.get('Rated'),
                    'released': data.get('Released'),
                    'runtime': data.get('Runtime'),
                    'genre': data.get('Genre'),
                    'director': data.get('Director'),
                    'writer': data.get('Writer'),
                    'actors': data.get('Actors'),
                    'plot': data.get('Plot'),
                    'language': data.get('Language'),
                    'country': data.get('Country'),
                    'awards': data.get('Awards'),
                    'poster': data.get('Poster'),
                    'imdb_rating': data.get('imdbRating'),
                    'imdb_votes': data.get('imdbVotes'),
                    'imdb_id': data.get('imdbID'),
                    'type': data.get('Type')
                }
                
                if content_type == 'tv':
                    metadata.update({
                        'total_seasons': data.get('totalSeasons')
                    })
                
                return {'success': True, 'data': metadata}
            
            return {'success': False, 'error': data.get('Error', 'No results found')}
        
        except Exception as e:
            return {'success': False, 'error': str(e)}

class GoogleBooksProvider:
    """Google Books API provider"""
    
    def __init__(self, api_manager):
        self.api_key = api_manager.get_key('google_books')
        self.base_url = 'https://www.googleapis.com/books/v1'
    
    def search(self, query: str, content_type: str) -> Dict[str, Any]:
        """Search Google Books for book content"""
        if content_type != 'book':
            return {'success': False, 'error': 'Google Books only supports book content'}
        
        try:
            url = f"{self.base_url}/volumes"
            params = {'q': query}
            
            if self.api_key:
                params['key'] = self.api_key
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            items = data.get('items', [])
            
            if items:
                item = items[0]
                volume_info = item.get('volumeInfo', {})
                
                metadata = {
                    'title': volume_info.get('title'),
                    'subtitle': volume_info.get('subtitle'),
                    'authors': volume_info.get('authors', []),
                    'publisher': volume_info.get('publisher'),
                    'published_date': volume_info.get('publishedDate'),
                    'description': volume_info.get('description'),
                    'isbn': [id_info['identifier'] for id_info in volume_info.get('industryIdentifiers', [])],
                    'page_count': volume_info.get('pageCount'),
                    'categories': volume_info.get('categories', []),
                    'average_rating': volume_info.get('averageRating'),
                    'ratings_count': volume_info.get('ratingsCount'),
                    'language': volume_info.get('language'),
                    'thumbnail': volume_info.get('imageLinks', {}).get('thumbnail'),
                    'google_books_id': item.get('id')
                }
                
                return {'success': True, 'data': metadata}
            
            return {'success': False, 'error': 'No results found'}
        
        except Exception as e:
            return {'success': False, 'error': str(e)}

class DiscogsProvider:
    """Discogs API provider for music"""
    
    def __init__(self, api_manager):
        self.api_key = api_manager.get_key('discogs')
        self.base_url = 'https://api.discogs.com'
    
    def search(self, query: str, content_type: str) -> Dict[str, Any]:
        """Search Discogs for music content"""
        if content_type != 'music':
            return {'success': False, 'error': 'Discogs only supports music content'}
        
        try:
            url = f"{self.base_url}/database/search"
            headers = {'User-Agent': 'MediaHub/1.0'}
            params = {'q': query, 'type': 'release'}
            
            if self.api_key:
                params['token'] = self.api_key
            
            response = requests.get(url, headers=headers, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            results = data.get('results', [])
            
            if results:
                item = results[0]
                
                metadata = {
                    'title': item.get('title'),
                    'artist': item.get('artist'),
                    'year': item.get('year'),
                    'label': item.get('label', []),
                    'genre': item.get('genre', []),
                    'style': item.get('style', []),
                    'country': item.get('country'),
                    'format': item.get('format', []),
                    'discogs_id': item.get('id'),
                    'thumb': item.get('thumb'),
                    'resource_url': item.get('resource_url')
                }
                
                return {'success': True, 'data': metadata}
            
            return {'success': False, 'error': 'No results found'}
        
        except Exception as e:
            return {'success': False, 'error': str(e)}

class AcoustIDProvider:
    """AcoustID provider for music fingerprinting"""
    
    def __init__(self, api_manager):
        self.api_key = api_manager.get_key('acoustid')
        self.base_url = 'https://api.acoustid.org/v2'
    
    def search(self, query: str, content_type: str) -> Dict[str, Any]:
        """AcoustID requires audio fingerprints, not text search"""
        return {'success': False, 'error': 'AcoustID requires audio fingerprint data'}

class AniListProvider:
    """AniList provider for anime content"""
    
    def __init__(self, api_manager):
        self.base_url = 'https://graphql.anilist.co'
    
    def search(self, query: str, content_type: str) -> Dict[str, Any]:
        """Search AniList for anime content"""
        if content_type != 'anime':
            return {'success': False, 'error': 'AniList only supports anime content'}
        
        try:
            query_string = '''
            query ($search: String) {
                Media (search: $search, type: ANIME) {
                    id
                    title {
                        romaji
                        english
                        native
                    }
                    description
                    startDate {
                        year
                        month
                        day
                    }
                    endDate {
                        year
                        month
                        day
                    }
                    episodes
                    duration
                    status
                    genres
                    averageScore
                    popularity
                    coverImage {
                        large
                        medium
                    }
                    bannerImage
                    studios {
                        nodes {
                            name
                        }
                    }
                }
            }
            '''
            
            variables = {'search': query}
            
            response = requests.post(
                self.base_url,
                json={'query': query_string, 'variables': variables},
                timeout=10
            )
            response.raise_for_status()
            
            data = response.json()
            media = data.get('data', {}).get('Media')
            
            if media:
                metadata = {
                    'title': media.get('title', {}).get('english') or media.get('title', {}).get('romaji'),
                    'title_romaji': media.get('title', {}).get('romaji'),
                    'title_english': media.get('title', {}).get('english'),
                    'title_native': media.get('title', {}).get('native'),
                    'description': media.get('description'),
                    'start_date': media.get('startDate'),
                    'end_date': media.get('endDate'),
                    'episodes': media.get('episodes'),
                    'duration': media.get('duration'),
                    'status': media.get('status'),
                    'genres': media.get('genres', []),
                    'average_score': media.get('averageScore'),
                    'popularity': media.get('popularity'),
                    'cover_image': media.get('coverImage', {}).get('large'),
                    'banner_image': media.get('bannerImage'),
                    'studios': [studio['name'] for studio in media.get('studios', {}).get('nodes', [])],
                    'anilist_id': media.get('id')
                }
                
                return {'success': True, 'data': metadata}
            
            return {'success': False, 'error': 'No results found'}
        
        except Exception as e:
            return {'success': False, 'error': str(e)}

class RSSFeedManager:
    """Manages RSS feeds with missing episode detection"""
    
    def __init__(self, db_connection, db_lock):
        self.db_connection = db_connection
        self.db_lock = db_lock
        self.feeds = {}
        self.update_interval = 3600  # 1 hour
        self.running = False
        self.update_thread = None
    
    def add_feed(self, name: str, url: str, content_type: str = 'tv', 
                filters: Dict[str, Any] = None) -> Dict[str, Any]:
        """Add RSS feed for monitoring"""
        try:
            feed_id = f"feed_{int(time.time())}_{hash(name) % 10000}"
            
            # Test feed first
            test_result = self._parse_feed(url)
            if not test_result['success']:
                return test_result
            
            feed_data = {
                'id': feed_id,
                'name': name,
                'url': url,
                'content_type': content_type,
                'filters': filters or {},
                'last_updated': None,
                'last_items': [],
                'active': True,
                'created_at': datetime.now().isoformat()
            }
            
            # Save to database
            with self.db_lock:
                cursor = self.db_connection.cursor()
                cursor.execute("""
                    INSERT INTO rss_feeds (feed_id, name, url, content_type, filters, active)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    feed_id, name, url, content_type,
                    json.dumps(filters or {}), True
                ))
                self.db_connection.commit()
            
            self.feeds[feed_id] = feed_data
            
            return {'success': True, 'feed': feed_data}
        
        except Exception as e:
            current_app.logger.error(f"Add RSS feed error: {e}")
            return {'success': False, 'error': str(e)}
    
    def _parse_feed(self, url: str) -> Dict[str, Any]:
        """Parse RSS feed and return items"""
        try:
            feed = feedparser.parse(url)
            
            if feed.bozo and feed.bozo_exception:
                return {'success': False, 'error': f'Feed parse error: {feed.bozo_exception}'}
            
            items = []
            for entry in feed.entries[:50]:  # Limit to recent 50 items
                item = {
                    'title': entry.get('title', ''),
                    'description': entry.get('description', ''),
                    'link': entry.get('link', ''),
                    'published': entry.get('published', ''),
                    'guid': entry.get('guid', entry.get('link', '')),
                    'enclosures': [
                        {
                            'url': enc.get('href', ''),
                            'type': enc.get('type', ''),
                            'length': enc.get('length', 0)
                        }
                        for enc in entry.get('enclosures', [])
                    ]
                }
                items.append(item)
            
            return {'success': True, 'items': items, 'feed_info': feed.feed}
        
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def check_missing_episodes(self, series_name: str, available_episodes: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Check for missing episodes in a series"""
        try:
            # Extract season/episode info from available episodes
            episode_map = {}
            for ep in available_episodes:
                season_ep = self._extract_season_episode(ep.get('title', ''))
                if season_ep:
                    season, episode = season_ep
                    if season not in episode_map:
                        episode_map[season] = set()
                    episode_map[season].add(episode)
            
            missing_episodes = []
            
            # Check for gaps in episodes
            for season, episodes in episode_map.items():
                if episodes:
                    max_ep = max(episodes)
                    for ep_num in range(1, max_ep + 1):
                        if ep_num not in episodes:
                            missing_episodes.append({
                                'series': series_name,
                                'season': season,
                                'episode': ep_num,
                                'search_query': f"{series_name} S{season:02d}E{ep_num:02d}"
                            })
            
            return missing_episodes
        
        except Exception as e:
            current_app.logger.error(f"Check missing episodes error: {e}")
            return []
    
    def _extract_season_episode(self, title: str) -> Optional[Tuple[int, int]]:
        """Extract season and episode numbers from title"""
        patterns = [
            r'[Ss](\d+)[Ee](\d+)',  # S01E01
            r'(\d+)x(\d+)',         # 1x01
            r'Season\s*(\d+).*Episode\s*(\d+)',  # Season 1 Episode 1
        ]
        
        for pattern in patterns:
            match = re.search(pattern, title)
            if match:
                try:
                    season = int(match.group(1))
                    episode = int(match.group(2))
                    return (season, episode)
                except ValueError:
                    continue
        
        return None
    
    def search_missing_episodes(self, missing_episodes: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Search RSS feeds for missing episodes"""
        found_episodes = []
        
        for missing in missing_episodes:
            search_query = missing['search_query']
            
            # Search through all active feeds
            for feed_id, feed_data in self.feeds.items():
                if not feed_data.get('active'):
                    continue
                
                # Parse feed
                feed_result = self._parse_feed(feed_data['url'])
                if not feed_result['success']:
                    continue
                
                # Search items
                for item in feed_result['items']:
                    if self._matches_search(item['title'], search_query):
                        found_episodes.append({
                            'missing_info': missing,
                            'found_item': item,
                            'feed_name': feed_data['name'],
                            'feed_id': feed_id
                        })
                        break
        
        return found_episodes
    
    def _matches_search(self, title: str, search_query: str) -> bool:
        """Check if RSS item matches search query"""
        title_lower = title.lower()
        query_lower = search_query.lower()
        
        # Extract series name and episode info from query
        parts = query_lower.split()
        series_parts = []
        episode_part = None
        
        for part in parts:
            if re.match(r's\d+e\d+', part):
                episode_part = part
                break
            else:
                series_parts.append(part)
        
        series_name = ' '.join(series_parts)
        
        # Check if title contains series name and episode info
        return (series_name in title_lower and 
                episode_part and episode_part in title_lower)
    
    def start_monitoring(self):
        """Start RSS feed monitoring"""
        if self.running:
            return
        
        self.running = True
        self.update_thread = threading.Thread(target=self._monitor_feeds)
        self.update_thread.daemon = True
        self.update_thread.start()
    
    def stop_monitoring(self):
        """Stop RSS feed monitoring"""
        self.running = False
        if self.update_thread:
            self.update_thread.join(timeout=5)
    
    def _monitor_feeds(self):
        """Monitor RSS feeds for updates"""
        while self.running:
            try:
                for feed_id, feed_data in self.feeds.items():
                    if not feed_data.get('active'):
                        continue
                    
                    # Check if feed needs update
                    last_updated = feed_data.get('last_updated')
                    if last_updated:
                        last_time = datetime.fromisoformat(last_updated)
                        if datetime.now() - last_time < timedelta(seconds=self.update_interval):
                            continue
                    
                    # Update feed
                    self._update_feed(feed_id)
                
                # Sleep before next check
                time.sleep(300)  # Check every 5 minutes
            
            except Exception as e:
                current_app.logger.error(f"RSS monitoring error: {e}")
                time.sleep(60)  # Wait 1 minute on error
    
    def _update_feed(self, feed_id: str):
        """Update a specific RSS feed"""
        try:
            feed_data = self.feeds.get(feed_id)
            if not feed_data:
                return
            
            # Parse feed
            result = self._parse_feed(feed_data['url'])
            if not result['success']:
                return
            
            # Check for new items
            new_items = []
            last_items = set(item.get('guid', '') for item in feed_data.get('last_items', []))
            
            for item in result['items']:
                if item.get('guid', '') not in last_items:
                    new_items.append(item)
            
            if new_items:
                # Process new items (could trigger downloads, notifications, etc.)
                self._process_new_items(feed_id, new_items)
            
            # Update feed data
            feed_data['last_updated'] = datetime.now().isoformat()
            feed_data['last_items'] = result['items'][:20]  # Keep last 20 items
            
            # Update database
            with self.db_lock:
                cursor = self.db_connection.cursor()
                cursor.execute("""
                    UPDATE rss_feeds SET last_updated = CURRENT_TIMESTAMP
                    WHERE feed_id = ?
                """, (feed_id,))
                self.db_connection.commit()
        
        except Exception as e:
            current_app.logger.error(f"Update feed {feed_id} error: {e}")
    
    def _process_new_items(self, feed_id: str, new_items: List[Dict[str, Any]]):
        """Process new RSS items"""
        # This could trigger automatic downloads, send notifications, etc.
        # For now, just log the new items
        feed_name = self.feeds[feed_id]['name']
        current_app.logger.info(f"RSS feed '{feed_name}' has {len(new_items)} new items")

# Global instances
metadata_provider_manager = None
rss_feed_manager = None

def init_rss_automation(api_manager, db_connection, db_lock):
    """Initialize RSS automation with dependencies"""
    global metadata_provider_manager, rss_feed_manager
    metadata_provider_manager = MetadataProviderManager(api_manager)
    rss_feed_manager = RSSFeedManager(db_connection, db_lock)

@bp.route('/metadata/search', methods=['POST'])
def search_metadata():
    """Search metadata providers"""
    try:
        data = request.json
        query = data.get('query')
        content_type = data.get('content_type', 'movie')
        provider_chain = data.get('provider_chain')
        
        if not query:
            return jsonify({'success': False, 'error': 'Query is required'})
        
        if not metadata_provider_manager:
            return jsonify({'success': False, 'error': 'Metadata provider manager not initialized'})
        
        result = metadata_provider_manager.get_metadata(content_type, query, provider_chain)
        return jsonify(result)
    
    except Exception as e:
        current_app.logger.error(f"Search metadata error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@bp.route('/rss/feeds/add', methods=['POST'])
def add_rss_feed():
    """Add RSS feed for monitoring"""
    try:
        data = request.json
        name = data.get('name')
        url = data.get('url')
        content_type = data.get('content_type', 'tv')
        filters = data.get('filters')
        
        if not name or not url:
            return jsonify({'success': False, 'error': 'Name and URL are required'})
        
        if not rss_feed_manager:
            return jsonify({'success': False, 'error': 'RSS feed manager not initialized'})
        
        result = rss_feed_manager.add_feed(name, url, content_type, filters)
        return jsonify(result)
    
    except Exception as e:
        current_app.logger.error(f"Add RSS feed error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@bp.route('/rss/missing-episodes/check', methods=['POST'])
def check_missing_episodes():
    """Check for missing episodes in a series"""
    try:
        data = request.json
        series_name = data.get('series_name')
        available_episodes = data.get('available_episodes', [])
        
        if not series_name:
            return jsonify({'success': False, 'error': 'Series name is required'})
        
        if not rss_feed_manager:
            return jsonify({'success': False, 'error': 'RSS feed manager not initialized'})
        
        missing_episodes = rss_feed_manager.check_missing_episodes(series_name, available_episodes)
        
        return jsonify({
            'success': True,
            'missing_episodes': missing_episodes,
            'count': len(missing_episodes)
        })
    
    except Exception as e:
        current_app.logger.error(f"Check missing episodes error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@bp.route('/rss/missing-episodes/search', methods=['POST'])
def search_missing_episodes():
    """Search RSS feeds for missing episodes"""
    try:
        data = request.json
        missing_episodes = data.get('missing_episodes', [])
        
        if not missing_episodes:
            return jsonify({'success': False, 'error': 'Missing episodes list is required'})
        
        if not rss_feed_manager:
            return jsonify({'success': False, 'error': 'RSS feed manager not initialized'})
        
        found_episodes = rss_feed_manager.search_missing_episodes(missing_episodes)
        
        return jsonify({
            'success': True,
            'found_episodes': found_episodes,
            'count': len(found_episodes)
        })
    
    except Exception as e:
        current_app.logger.error(f"Search missing episodes error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@bp.route('/rss/monitoring/start', methods=['POST'])
def start_rss_monitoring():
    """Start RSS feed monitoring"""
    try:
        if not rss_feed_manager:
            return jsonify({'success': False, 'error': 'RSS feed manager not initialized'})
        
        rss_feed_manager.start_monitoring()
        
        return jsonify({
            'success': True,
            'message': 'RSS monitoring started'
        })
    
    except Exception as e:
        current_app.logger.error(f"Start RSS monitoring error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@bp.route('/rss/monitoring/stop', methods=['POST'])
def stop_rss_monitoring():
    """Stop RSS feed monitoring"""
    try:
        if not rss_feed_manager:
            return jsonify({'success': False, 'error': 'RSS feed manager not initialized'})
        
        rss_feed_manager.stop_monitoring()
        
        return jsonify({
            'success': True,
            'message': 'RSS monitoring stopped'
        })
    
    except Exception as e:
        current_app.logger.error(f"Stop RSS monitoring error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500
