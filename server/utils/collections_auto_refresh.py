"""
Collections Auto-Refresh System - Scheduled Updates for Dynamic Collections
Automatically updates Top-50 lists, trending content, and dynamic collections
"""

import os
import json
import logging
import threading
import time
import requests
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from pathlib import Path
import schedule
from concurrent.futures import ThreadPoolExecutor, as_completed

class CollectionsAutoRefresh:
    """Auto-refresh system for dynamic collections"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.running = False
        self.scheduler_thread = None
        
        # API configurations
        self.api_configs = {
            'tmdb': {
                'base_url': 'https://api.themoviedb.org/3',
                'endpoints': {
                    'popular_movies': '/movie/popular',
                    'top_rated_movies': '/movie/top_rated',
                    'popular_tv': '/tv/popular',
                    'top_rated_tv': '/tv/top_rated',
                    'trending_movies': '/trending/movie/week',
                    'trending_tv': '/trending/tv/week'
                }
            },
            'google_books': {
                'base_url': 'https://www.googleapis.com/books/v1',
                'endpoints': {
                    'bestsellers': '/volumes?q=subject:fiction&orderBy=newest&maxResults=50',
                    'top_rated': '/volumes?q=*&orderBy=relevance&maxResults=50'
                }
            },
            'discogs': {
                'base_url': 'https://api.discogs.com',
                'endpoints': {
                    'trending': '/database/search?type=release&sort=hot&per_page=50'
                }
            }
        }
        
        # Collection refresh schedules
        self.refresh_schedules = {
            'top_50_movies': {
                'schedule': 'daily',
                'time': '02:00',
                'api': 'tmdb',
                'endpoint': 'top_rated_movies',
                'last_refresh': None
            },
            'top_50_tv': {
                'schedule': 'daily',
                'time': '02:15',
                'api': 'tmdb',
                'endpoint': 'top_rated_tv',
                'last_refresh': None
            },
            'trending_movies': {
                'schedule': 'hourly',
                'api': 'tmdb',
                'endpoint': 'trending_movies',
                'last_refresh': None
            },
            'trending_tv': {
                'schedule': 'hourly',
                'api': 'tmdb',
                'endpoint': 'trending_tv',
                'last_refresh': None
            },
            'top_50_books': {
                'schedule': 'weekly',
                'day': 'monday',
                'time': '03:00',
                'api': 'google_books',
                'endpoint': 'bestsellers',
                'last_refresh': None
            },
            'top_50_albums': {
                'schedule': 'weekly',
                'day': 'sunday',
                'time': '03:00',
                'api': 'discogs',
                'endpoint': 'trending',
                'last_refresh': None
            }
        }
        
        # Collection data cache
        self.collections_cache = {}
        self.cache_file = Path("data/collections_cache.json")
        self.cache_file.parent.mkdir(exist_ok=True)
        
        # Settings
        self.settings = {
            'auto_refresh_enabled': True,
            'max_concurrent_requests': 3,
            'request_timeout': 30,
            'retry_attempts': 3,
            'cache_duration_hours': 24,
            'update_library_after_refresh': True,
            'notify_on_updates': True
        }
        
        self.load_cache()
        self.load_settings()
    
    def start(self):
        """Start the auto-refresh scheduler"""
        if self.running:
            return
        
        if not self.settings['auto_refresh_enabled']:
            self.logger.info("Collections auto-refresh is disabled")
            return
        
        self.running = True
        self._setup_schedules()
        
        # Start scheduler thread
        self.scheduler_thread = threading.Thread(target=self._scheduler_loop, daemon=True)
        self.scheduler_thread.start()
        
        self.logger.info("Collections auto-refresh started")
    
    def stop(self):
        """Stop the auto-refresh scheduler"""
        self.running = False
        if self.scheduler_thread:
            self.scheduler_thread.join(timeout=5)
        
        schedule.clear()
        self.save_cache()
        self.logger.info("Collections auto-refresh stopped")
    
    def _setup_schedules(self):
        """Setup refresh schedules"""
        for collection_name, config in self.refresh_schedules.items():
            if config['schedule'] == 'hourly':
                schedule.every().hour.do(self._refresh_collection, collection_name)
            elif config['schedule'] == 'daily':
                schedule.every().day.at(config['time']).do(self._refresh_collection, collection_name)
            elif config['schedule'] == 'weekly':
                day = config.get('day', 'monday')
                time_str = config.get('time', '03:00')
                getattr(schedule.every(), day).at(time_str).do(self._refresh_collection, collection_name)
        
        self.logger.info(f"Setup {len(self.refresh_schedules)} collection refresh schedules")
    
    def _scheduler_loop(self):
        """Main scheduler loop"""
        while self.running:
            try:
                schedule.run_pending()
                time.sleep(60)  # Check every minute
            except Exception as e:
                self.logger.error(f"Scheduler error: {e}")
                time.sleep(300)  # Wait 5 minutes on error
    
    def _refresh_collection(self, collection_name: str):
        """Refresh a specific collection"""
        try:
            self.logger.info(f"Starting refresh for collection: {collection_name}")
            
            config = self.refresh_schedules.get(collection_name)
            if not config:
                self.logger.error(f"No config found for collection: {collection_name}")
                return
            
            # Check if we need to refresh (cache still valid)
            if self._is_cache_valid(collection_name):
                self.logger.info(f"Cache still valid for {collection_name}, skipping refresh")
                return
            
            # Fetch new data
            new_data = self._fetch_collection_data(collection_name, config)
            
            if new_data:
                # Update cache
                self.collections_cache[collection_name] = {
                    'data': new_data,
                    'last_updated': datetime.now().isoformat(),
                    'source': config['api'],
                    'endpoint': config['endpoint']
                }
                
                # Update last refresh time
                config['last_refresh'] = datetime.now().isoformat()
                
                # Save cache
                self.save_cache()
                
                # Update library if enabled
                if self.settings['update_library_after_refresh']:
                    self._update_library_collection(collection_name, new_data)
                
                self.logger.info(f"Successfully refreshed collection: {collection_name} ({len(new_data)} items)")
                
                # Send notification if enabled
                if self.settings['notify_on_updates']:
                    self._send_update_notification(collection_name, len(new_data))
            else:
                self.logger.warning(f"Failed to refresh collection: {collection_name}")
                
        except Exception as e:
            self.logger.error(f"Error refreshing collection {collection_name}: {e}")
    
    def _is_cache_valid(self, collection_name: str) -> bool:
        """Check if cached data is still valid"""
        if collection_name not in self.collections_cache:
            return False
        
        cache_entry = self.collections_cache[collection_name]
        last_updated = datetime.fromisoformat(cache_entry['last_updated'])
        cache_duration = timedelta(hours=self.settings['cache_duration_hours'])
        
        return datetime.now() - last_updated < cache_duration
    
    def _fetch_collection_data(self, collection_name: str, config: Dict) -> Optional[List[Dict]]:
        """Fetch collection data from API"""
        api_name = config['api']
        endpoint = config['endpoint']
        
        if api_name not in self.api_configs:
            self.logger.error(f"Unknown API: {api_name}")
            return None
        
        api_config = self.api_configs[api_name]
        
        try:
            # Get API key from environment or config
            api_key = self._get_api_key(api_name)
            if not api_key:
                self.logger.error(f"No API key found for {api_name}")
                return None
            
            # Build request URL
            base_url = api_config['base_url']
            endpoint_path = api_config['endpoints'][endpoint]
            url = f"{base_url}{endpoint_path}"
            
            # Add API key to params
            params = self._get_api_params(api_name, api_key)
            
            # Make request with retries
            for attempt in range(self.settings['retry_attempts']):
                try:
                    response = requests.get(
                        url, 
                        params=params, 
                        timeout=self.settings['request_timeout']
                    )
                    response.raise_for_status()
                    
                    # Parse response based on API
                    return self._parse_api_response(api_name, response.json(), collection_name)
                    
                except requests.RequestException as e:
                    self.logger.warning(f"Request attempt {attempt + 1} failed for {collection_name}: {e}")
                    if attempt < self.settings['retry_attempts'] - 1:
                        time.sleep(2 ** attempt)  # Exponential backoff
                    else:
                        raise
            
        except Exception as e:
            self.logger.error(f"Error fetching data for {collection_name}: {e}")
            return None
    
    def _get_api_key(self, api_name: str) -> Optional[str]:
        """Get API key for service"""
        # Try to get from environment variables first
        env_var_map = {
            'tmdb': 'TMDB_API_KEY',
            'google_books': 'GOOGLE_BOOKS_API_KEY',
            'discogs': 'DISCOGS_API_KEY'
        }
        
        env_var = env_var_map.get(api_name)
        if env_var:
            api_key = os.getenv(env_var)
            if api_key:
                return api_key
        
        # Try to get from API keys config
        try:
            from config.api_keys import APIKeyManager
            key_manager = APIKeyManager()
            return key_manager.get_key(api_name)
        except ImportError:
            pass
        
        # Fallback to hardcoded keys (from custom.txt)
        fallback_keys = {
            'tmdb': '3aca2154c1d9223036904a86202897ba',
            'google_books': 'AIzaSyA8OHWm7_imDTRCAEvC7rja2NZCInTw3d8',
            'discogs': 'DlYcCvjWkCSKwuoxWznBrUDFitmPFTqBpIuoqizm'
        }
        
        return fallback_keys.get(api_name)
    
    def _get_api_params(self, api_name: str, api_key: str) -> Dict[str, str]:
        """Get API parameters for request"""
        if api_name == 'tmdb':
            return {'api_key': api_key}
        elif api_name == 'google_books':
            return {'key': api_key}
        elif api_name == 'discogs':
            return {'token': api_key}
        else:
            return {'api_key': api_key}
    
    def _parse_api_response(self, api_name: str, response_data: Dict, collection_name: str) -> List[Dict]:
        """Parse API response based on service"""
        items = []
        
        try:
            if api_name == 'tmdb':
                results = response_data.get('results', [])
                for item in results[:50]:  # Limit to top 50
                    parsed_item = {
                        'id': item.get('id'),
                        'title': item.get('title') or item.get('name'),
                        'overview': item.get('overview', ''),
                        'release_date': item.get('release_date') or item.get('first_air_date'),
                        'rating': item.get('vote_average', 0),
                        'popularity': item.get('popularity', 0),
                        'poster_path': item.get('poster_path'),
                        'backdrop_path': item.get('backdrop_path'),
                        'genre_ids': item.get('genre_ids', []),
                        'source': 'tmdb',
                        'type': 'movie' if 'title' in item else 'tv'
                    }
                    items.append(parsed_item)
            
            elif api_name == 'google_books':
                book_items = response_data.get('items', [])
                for item in book_items[:50]:
                    volume_info = item.get('volumeInfo', {})
                    parsed_item = {
                        'id': item.get('id'),
                        'title': volume_info.get('title', ''),
                        'authors': volume_info.get('authors', []),
                        'description': volume_info.get('description', ''),
                        'published_date': volume_info.get('publishedDate'),
                        'rating': volume_info.get('averageRating', 0),
                        'ratings_count': volume_info.get('ratingsCount', 0),
                        'thumbnail': volume_info.get('imageLinks', {}).get('thumbnail'),
                        'categories': volume_info.get('categories', []),
                        'source': 'google_books',
                        'type': 'book'
                    }
                    items.append(parsed_item)
            
            elif api_name == 'discogs':
                results = response_data.get('results', [])
                for item in results[:50]:
                    parsed_item = {
                        'id': item.get('id'),
                        'title': item.get('title', ''),
                        'artist': ', '.join(item.get('artist', [])) if isinstance(item.get('artist'), list) else item.get('artist', ''),
                        'year': item.get('year'),
                        'genre': item.get('genre', []),
                        'style': item.get('style', []),
                        'format': item.get('format', []),
                        'thumb': item.get('thumb'),
                        'source': 'discogs',
                        'type': 'album'
                    }
                    items.append(parsed_item)
            
        except Exception as e:
            self.logger.error(f"Error parsing {api_name} response for {collection_name}: {e}")
        
        return items
    
    def _update_library_collection(self, collection_name: str, items: List[Dict]):
        """Update library collection with new data"""
        try:
            # This would integrate with the main MediaHub collection system
            # For now, we'll just log the update
            self.logger.info(f"Would update library collection {collection_name} with {len(items)} items")
            
            # In a real implementation, this would:
            # 1. Connect to the main collections database
            # 2. Update the collection with new items
            # 3. Remove items no longer in the top list
            # 4. Update metadata for existing items
            # 5. Trigger UI refresh
            
        except Exception as e:
            self.logger.error(f"Error updating library collection {collection_name}: {e}")
    
    def _send_update_notification(self, collection_name: str, item_count: int):
        """Send notification about collection update"""
        try:
            # This would send a notification to the UI or user
            notification = {
                'type': 'collection_updated',
                'collection': collection_name,
                'item_count': item_count,
                'timestamp': datetime.now().isoformat()
            }
            
            self.logger.info(f"Collection update notification: {notification}")
            
            # In a real implementation, this would:
            # 1. Send WebSocket notification to connected clients
            # 2. Show desktop notification if enabled
            # 3. Add to notification history
            
        except Exception as e:
            self.logger.error(f"Error sending notification for {collection_name}: {e}")
    
    def manual_refresh(self, collection_name: str) -> Dict[str, Any]:
        """Manually refresh a specific collection"""
        try:
            if collection_name not in self.refresh_schedules:
                return {
                    'success': False,
                    'error': f'Unknown collection: {collection_name}'
                }
            
            # Force refresh by clearing cache
            if collection_name in self.collections_cache:
                del self.collections_cache[collection_name]
            
            # Trigger refresh
            self._refresh_collection(collection_name)
            
            # Check if refresh was successful
            if collection_name in self.collections_cache:
                cache_entry = self.collections_cache[collection_name]
                return {
                    'success': True,
                    'collection': collection_name,
                    'item_count': len(cache_entry['data']),
                    'last_updated': cache_entry['last_updated']
                }
            else:
                return {
                    'success': False,
                    'error': 'Refresh failed - no data retrieved'
                }
                
        except Exception as e:
            self.logger.error(f"Error in manual refresh for {collection_name}: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def manual_refresh_all(self) -> Dict[str, Any]:
        """Manually refresh all collections"""
        results = {}
        
        # Use thread pool for concurrent refreshes
        with ThreadPoolExecutor(max_workers=self.settings['max_concurrent_requests']) as executor:
            future_to_collection = {
                executor.submit(self.manual_refresh, collection_name): collection_name
                for collection_name in self.refresh_schedules.keys()
            }
            
            for future in as_completed(future_to_collection):
                collection_name = future_to_collection[future]
                try:
                    result = future.result()
                    results[collection_name] = result
                except Exception as e:
                    results[collection_name] = {
                        'success': False,
                        'error': str(e)
                    }
        
        # Summary
        successful = sum(1 for r in results.values() if r.get('success'))
        total = len(results)
        
        return {
            'success': successful > 0,
            'results': results,
            'summary': {
                'successful': successful,
                'failed': total - successful,
                'total': total
            }
        }
    
    def get_collection_data(self, collection_name: str) -> Optional[Dict[str, Any]]:
        """Get cached collection data"""
        return self.collections_cache.get(collection_name)
    
    def get_all_collections_data(self) -> Dict[str, Any]:
        """Get all cached collection data"""
        return self.collections_cache.copy()
    
    def get_refresh_status(self) -> Dict[str, Any]:
        """Get refresh status for all collections"""
        status = {}
        
        for collection_name, config in self.refresh_schedules.items():
            cache_entry = self.collections_cache.get(collection_name)
            
            status[collection_name] = {
                'schedule': config['schedule'],
                'last_refresh': config.get('last_refresh'),
                'cached_items': len(cache_entry['data']) if cache_entry else 0,
                'cache_valid': self._is_cache_valid(collection_name),
                'api_source': config['api'],
                'endpoint': config['endpoint']
            }
        
        return {
            'collections': status,
            'auto_refresh_enabled': self.settings['auto_refresh_enabled'],
            'scheduler_running': self.running,
            'total_collections': len(status)
        }
    
    def load_cache(self):
        """Load collections cache from file"""
        try:
            if self.cache_file.exists():
                with open(self.cache_file, 'r') as f:
                    self.collections_cache = json.load(f)
                self.logger.info(f"Loaded cache for {len(self.collections_cache)} collections")
        except Exception as e:
            self.logger.error(f"Error loading cache: {e}")
            self.collections_cache = {}
    
    def save_cache(self):
        """Save collections cache to file"""
        try:
            with open(self.cache_file, 'w') as f:
                json.dump(self.collections_cache, f, indent=2)
        except Exception as e:
            self.logger.error(f"Error saving cache: {e}")
    
    def load_settings(self):
        """Load settings from file"""
        try:
            settings_file = Path("data/collections_auto_refresh_settings.json")
            if settings_file.exists():
                with open(settings_file, 'r') as f:
                    saved_settings = json.load(f)
                    self.settings.update(saved_settings)
        except Exception as e:
            self.logger.error(f"Error loading settings: {e}")
    
    def save_settings(self):
        """Save settings to file"""
        try:
            settings_file = Path("data/collections_auto_refresh_settings.json")
            settings_file.parent.mkdir(exist_ok=True)
            
            with open(settings_file, 'w') as f:
                json.dump(self.settings, f, indent=2)
        except Exception as e:
            self.logger.error(f"Error saving settings: {e}")

# Global instance
collections_auto_refresh = CollectionsAutoRefresh()

def get_collections_auto_refresh() -> CollectionsAutoRefresh:
    """Get the global collections auto-refresh instance"""
    return collections_auto_refresh

if __name__ == "__main__":
    # Test the collections auto-refresh system
    refresh_system = CollectionsAutoRefresh()
    refresh_system.start()
    
    # Test manual refresh
    result = refresh_system.manual_refresh('top_50_movies')
    print(f"Manual refresh result: {result}")
    
    # Keep running for a bit to test scheduler
    try:
        time.sleep(30)
    except KeyboardInterrupt:
        pass
    finally:
        refresh_system.stop()
