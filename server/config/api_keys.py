"""
API Key Manager with Pre-Configured Service Keys
Manages all external service API keys with secure handling
"""

import os
import json
import logging
from typing import Dict, Optional, Any
from pathlib import Path

class APIKeyManager:
    """Manages API keys for all external services with pre-configuration"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.config_path = Path("data/api_keys.json")
        self.config_path.parent.mkdir(exist_ok=True)
        
        # Pre-configured API keys as specified by user in custom.txt
        # These keys are activated by default for immediate functionality
        self.default_keys = {
            'real_debrid': 'HMPNSB7QFO4RL2DCIKRRPKFKLKBIR7LSWWUOVNDAADNHOTC2SAXA',
            'tmdb': '3aca2154c1d9223036904a86202897ba',
            'google_books': 'AIzaSyA8OHWm7_imDTRCAEvC7rja2NZCInTw3d8',
            'tvdb': '72f8b186-1eb8-471d-94e7-85063cf7a1bf',
            'discogs': 'DlYcCvjWkCSKwuoxWznBrUDFitmPFTqBpIuoqizm',
            'acoustid': 'W48qHR6eir',
            'omdb': '95b991d3',
            'anilist_client_id': '30444',
            'anilist_client_secret': 'dc63l21fPbnvgpx7Qinlg9miT5ismqUu77oVSTj2'
        }
        
        # Activate all keys by default
        self.active_keys = self.default_keys.copy()
        
        self.keys = {}
        self.load_keys()
        
        # Initialize with default keys if not already present
        self.initialize_default_keys()
    
    def load_keys(self):
        """Load API keys from configuration file"""
        try:
            if self.config_path.exists():
                with open(self.config_path, 'r') as f:
                    self.keys = json.load(f)
            else:
                self.keys = {}
        except Exception as e:
            self.logger.error(f"Error loading API keys: {e}")
            self.keys = {}
    
    def save_keys(self):
        """Save API keys to configuration file with proper security"""
        try:
            # Create backup of existing keys
            if self.config_path.exists():
                backup_path = self.config_path.with_suffix('.json.backup')
                self.config_path.rename(backup_path)
            
            # Save current keys
            with open(self.config_path, 'w') as f:
                json.dump(self.keys, f, indent=2)
            
            # Set restrictive permissions
            os.chmod(self.config_path, 0o600)
            
        except Exception as e:
            self.logger.error(f"Error saving API keys: {e}")
    
    def initialize_default_keys(self):
        """Initialize with pre-configured default keys - force activation"""
        # Always ensure all default keys are active
        for service, key in self.default_keys.items():
            self.keys[service] = key
            self.logger.info(f"Activated pre-configured API key for {service}")
        
        # Always save to ensure persistence
        self.save_keys()
        self.logger.info("All pre-configured API keys activated successfully")
    
    def get_key(self, service: str) -> Optional[str]:
        """Get API key for a service"""
        return self.keys.get(service)
    
    def set_key(self, service: str, key: str):
        """Set API key for a service"""
        self.keys[service] = key
        self.save_keys()
        self.logger.info(f"Updated API key for {service}")
    
    def remove_key(self, service: str):
        """Remove API key for a service"""
        if service in self.keys:
            del self.keys[service]
            self.save_keys()
            self.logger.info(f"Removed API key for {service}")
    
    def get_all_services(self) -> Dict[str, bool]:
        """Get list of all services and their key availability"""
        all_services = {
            'real_debrid': 'Real-Debrid',
            'tmdb': 'The Movie Database',
            'tvdb': 'TheTVDB',
            'google_books': 'Google Books',
            'discogs': 'Discogs',
            'acoustid': 'AcoustID',
            'omdb': 'OMDb',
            'anilist_client_id': 'AniList',
            'anilist_client_secret': 'AniList Secret',
            'trakt': 'Trakt.tv',
            'fanart': 'Fanart.tv',
            'musicbrainz': 'MusicBrainz',
            'lastfm': 'Last.fm',
            'spotify': 'Spotify',
            'youtube': 'YouTube Data API'
        }
        
        return {
            service: {
                'name': name,
                'configured': service in self.keys and bool(self.keys[service]),
                'masked_key': self.mask_key(self.keys.get(service, '')) if service in self.keys else None
            }
            for service, name in all_services.items()
        }
    
    def mask_key(self, key: str) -> str:
        """Mask API key for display purposes"""
        if not key:
            return ''
        if len(key) <= 8:
            return '*' * len(key)
        return key[:4] + '*' * (len(key) - 8) + key[-4:]
    
    def validate_key(self, service: str, key: str) -> Dict[str, Any]:
        """Validate an API key by testing it with the service"""
        try:
            if service == 'real_debrid':
                return self._validate_real_debrid(key)
            elif service == 'tmdb':
                return self._validate_tmdb(key)
            elif service == 'tvdb':
                return self._validate_tvdb(key)
            elif service == 'google_books':
                return self._validate_google_books(key)
            elif service == 'omdb':
                return self._validate_omdb(key)
            else:
                return {'valid': True, 'message': 'Validation not implemented for this service'}
        except Exception as e:
            return {'valid': False, 'message': f'Validation error: {str(e)}'}
    
    def _validate_real_debrid(self, key: str) -> Dict[str, Any]:
        """Validate Real-Debrid API key"""
        import requests
        try:
            response = requests.get(
                'https://api.real-debrid.com/rest/1.0/user',
                headers={'Authorization': f'Bearer {key}'},
                timeout=10
            )
            if response.status_code == 200:
                user_data = response.json()
                return {
                    'valid': True,
                    'message': f'Valid - User: {user_data.get("username", "Unknown")}',
                    'user_info': user_data
                }
            else:
                return {'valid': False, 'message': f'Invalid key - HTTP {response.status_code}'}
        except Exception as e:
            return {'valid': False, 'message': f'Connection error: {str(e)}'}
    
    def _validate_tmdb(self, key: str) -> Dict[str, Any]:
        """Validate TMDB API key"""
        import requests
        try:
            response = requests.get(
                f'https://api.themoviedb.org/3/configuration?api_key={key}',
                timeout=10
            )
            if response.status_code == 200:
                return {'valid': True, 'message': 'Valid TMDB API key'}
            else:
                return {'valid': False, 'message': f'Invalid key - HTTP {response.status_code}'}
        except Exception as e:
            return {'valid': False, 'message': f'Connection error: {str(e)}'}
    
    def _validate_tvdb(self, key: str) -> Dict[str, Any]:
        """Validate TVDB API key"""
        import requests
        try:
            response = requests.post(
                'https://api4.thetvdb.com/v4/login',
                json={'apikey': key},
                timeout=10
            )
            if response.status_code == 200:
                return {'valid': True, 'message': 'Valid TVDB API key'}
            else:
                return {'valid': False, 'message': f'Invalid key - HTTP {response.status_code}'}
        except Exception as e:
            return {'valid': False, 'message': f'Connection error: {str(e)}'}
    
    def _validate_google_books(self, key: str) -> Dict[str, Any]:
        """Validate Google Books API key"""
        import requests
        try:
            response = requests.get(
                f'https://www.googleapis.com/books/v1/volumes?q=test&key={key}',
                timeout=10
            )
            if response.status_code == 200:
                return {'valid': True, 'message': 'Valid Google Books API key'}
            else:
                return {'valid': False, 'message': f'Invalid key - HTTP {response.status_code}'}
        except Exception as e:
            return {'valid': False, 'message': f'Connection error: {str(e)}'}
    
    def _validate_omdb(self, key: str) -> Dict[str, Any]:
        """Validate OMDb API key"""
        import requests
        try:
            response = requests.get(
                f'http://www.omdbapi.com/?apikey={key}&t=test',
                timeout=10
            )
            if response.status_code == 200:
                data = response.json()
                if 'Error' not in data or 'Invalid API key' not in data.get('Error', ''):
                    return {'valid': True, 'message': 'Valid OMDb API key'}
                else:
                    return {'valid': False, 'message': 'Invalid API key'}
            else:
                return {'valid': False, 'message': f'Invalid key - HTTP {response.status_code}'}
        except Exception as e:
            return {'valid': False, 'message': f'Connection error: {str(e)}'}
    
    def get_service_status(self) -> Dict[str, Any]:
        """Get status of all configured services"""
        status = {}
        for service in self.keys:
            key = self.keys[service]
            if key:
                validation = self.validate_key(service, key)
                status[service] = {
                    'configured': True,
                    'valid': validation['valid'],
                    'message': validation['message'],
                    'masked_key': self.mask_key(key)
                }
            else:
                status[service] = {
                    'configured': False,
                    'valid': False,
                    'message': 'No key configured'
                }
        
        return status
    
    def export_keys(self, include_secrets: bool = False) -> Dict[str, Any]:
        """Export API key configuration"""
        if include_secrets:
            return self.keys.copy()
        else:
            return {
                service: self.mask_key(key) 
                for service, key in self.keys.items()
            }
    
    def import_keys(self, keys_data: Dict[str, str], overwrite: bool = False):
        """Import API key configuration"""
        updated = []
        for service, key in keys_data.items():
            if service not in self.keys or overwrite:
                self.keys[service] = key
                updated.append(service)
        
        if updated:
            self.save_keys()
            self.logger.info(f"Imported keys for services: {', '.join(updated)}")
        
        return updated
