"""
Profile Manager for User Customization System
Manages all user profiles with optional feature configurations
"""

import json
import logging
import sqlite3
import threading
from datetime import datetime
from typing import Dict, List, Optional, Any

class ProfileManager:
    """Manages user profiles with optional feature configurations"""
    
    def __init__(self, db_connection: sqlite3.Connection, db_lock: threading.Lock):
        self.logger = logging.getLogger(__name__)
        self.db_connection = db_connection
        self.db_lock = db_lock
        
        # Default profile templates
        self.default_profiles = {
            'default': {
                'name': 'Default',
                'deduplication_rules': {
                    'enabled': False,
                    'hierarchy': [],
                    'never_remove': [],
                    'conditions': {}
                },
                'language_priorities': {
                    'subtitles': ['en'],
                    'audio': ['en'],
                    'interface': 'en'
                },
                'smart_collections': {
                    'enabled': False,
                    'universe_collections': [],
                    'auto_populate': False,
                    'update_interval': 86400
                },
                'metadata_providers': {
                    'movie_chain': ['tmdb', 'omdb'],
                    'tv_chain': ['tvdb', 'tmdb'],
                    'book_chain': ['google_books'],
                    'music_chain': ['discogs', 'musicbrainz'],
                    'cache_ttl': 86400
                },
                'automation_level': 'manual',
                'ui_preferences': {
                    'theme': 'hero',
                    'mobile_optimized': False,
                    'show_badges': True,
                    'auto_play_trailers': False
                }
            },
            'power_user': {
                'name': 'Power User',
                'deduplication_rules': {
                    'enabled': True,
                    'hierarchy': ['ctrlhd', 'Cytsunee', 'oft'],
                    'never_remove': ['ctrlhd'],
                    'conditions': {
                        'remove_cytsunee_if_ctrlhd': True,
                        'quality_preference': '4K > 1080p > 720p',
                        'codec_preference': 'x265 > x264'
                    }
                },
                'language_priorities': {
                    'subtitles': ['ar', 'en'],
                    'audio': ['ar', 'en'],
                    'interface': 'en'
                },
                'smart_collections': {
                    'enabled': True,
                    'universe_collections': ['mcu', 'dceu', 'star_wars', 'arrowverse'],
                    'auto_populate': True,
                    'update_interval': 3600
                },
                'metadata_providers': {
                    'movie_chain': ['tmdb', 'omdb', 'fanart'],
                    'tv_chain': ['tvdb', 'tmdb', 'fanart'],
                    'book_chain': ['google_books'],
                    'music_chain': ['discogs', 'musicbrainz', 'lastfm'],
                    'cache_ttl': 43200
                },
                'automation_level': 'automatic',
                'ui_preferences': {
                    'theme': 'hero',
                    'mobile_optimized': True,
                    'show_badges': True,
                    'auto_play_trailers': True
                }
            },
            'minimal': {
                'name': 'Minimal',
                'deduplication_rules': {
                    'enabled': False,
                    'hierarchy': [],
                    'never_remove': [],
                    'conditions': {}
                },
                'language_priorities': {
                    'subtitles': ['en'],
                    'audio': ['en'],
                    'interface': 'en'
                },
                'smart_collections': {
                    'enabled': False,
                    'universe_collections': [],
                    'auto_populate': False,
                    'update_interval': 86400
                },
                'metadata_providers': {
                    'movie_chain': ['tmdb'],
                    'tv_chain': ['tvdb'],
                    'book_chain': ['google_books'],
                    'music_chain': ['discogs'],
                    'cache_ttl': 86400
                },
                'automation_level': 'manual',
                'ui_preferences': {
                    'theme': 'minimal',
                    'mobile_optimized': False,
                    'show_badges': False,
                    'auto_play_trailers': False
                }
            }
        }
        
        self.initialize_default_profiles()
    
    def initialize_default_profiles(self):
        """Initialize default profiles if they don't exist"""
        try:
            with self.db_lock:
                cursor = self.db_connection.cursor()
                
                for profile_id, profile_data in self.default_profiles.items():
                    cursor.execute("""
                        SELECT COUNT(*) FROM enhanced_profiles WHERE name = ?
                    """, (profile_data['name'],))
                    
                    if cursor.fetchone()[0] == 0:
                        self.create_profile(profile_data['name'], profile_data)
                        self.logger.info(f"Created default profile: {profile_data['name']}")
        
        except Exception as e:
            self.logger.error(f"Error initializing default profiles: {e}")
    
    def create_profile(self, name: str, settings: Dict[str, Any]) -> bool:
        """Create a new user profile"""
        try:
            with self.db_lock:
                cursor = self.db_connection.cursor()
                
                cursor.execute("""
                    INSERT INTO enhanced_profiles 
                    (name, deduplication_rules, language_priorities, smart_collections, 
                     metadata_providers, automation_level, ui_preferences)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    name,
                    json.dumps(settings.get('deduplication_rules', {})),
                    json.dumps(settings.get('language_priorities', {})),
                    json.dumps(settings.get('smart_collections', {})),
                    json.dumps(settings.get('metadata_providers', {})),
                    settings.get('automation_level', 'manual'),
                    json.dumps(settings.get('ui_preferences', {}))
                ))
                
                self.db_connection.commit()
                self.logger.info(f"Created profile: {name}")
                return True
        
        except Exception as e:
            self.logger.error(f"Error creating profile {name}: {e}")
            return False
    
    def get_profile(self, name: str) -> Optional[Dict[str, Any]]:
        """Get a user profile by name"""
        try:
            with self.db_lock:
                cursor = self.db_connection.cursor()
                
                cursor.execute("""
                    SELECT name, deduplication_rules, language_priorities, smart_collections,
                           metadata_providers, automation_level, ui_preferences, created_at, updated_at
                    FROM enhanced_profiles WHERE name = ?
                """, (name,))
                
                row = cursor.fetchone()
                if row:
                    return {
                        'name': row[0],
                        'deduplication_rules': json.loads(row[1]) if row[1] else {},
                        'language_priorities': json.loads(row[2]) if row[2] else {},
                        'smart_collections': json.loads(row[3]) if row[3] else {},
                        'metadata_providers': json.loads(row[4]) if row[4] else {},
                        'automation_level': row[5],
                        'ui_preferences': json.loads(row[6]) if row[6] else {},
                        'created_at': row[7],
                        'updated_at': row[8]
                    }
                
                return None
        
        except Exception as e:
            self.logger.error(f"Error getting profile {name}: {e}")
            return None
    
    def update_profile(self, name: str, settings: Dict[str, Any]) -> bool:
        """Update an existing user profile"""
        try:
            with self.db_lock:
                cursor = self.db_connection.cursor()
                
                # Get current profile to merge settings
                current = self.get_profile(name)
                if not current:
                    return False
                
                # Merge settings
                for key, value in settings.items():
                    if key in current:
                        current[key] = value
                
                cursor.execute("""
                    UPDATE enhanced_profiles SET
                        deduplication_rules = ?,
                        language_priorities = ?,
                        smart_collections = ?,
                        metadata_providers = ?,
                        automation_level = ?,
                        ui_preferences = ?,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE name = ?
                """, (
                    json.dumps(current.get('deduplication_rules', {})),
                    json.dumps(current.get('language_priorities', {})),
                    json.dumps(current.get('smart_collections', {})),
                    json.dumps(current.get('metadata_providers', {})),
                    current.get('automation_level', 'manual'),
                    json.dumps(current.get('ui_preferences', {})),
                    name
                ))
                
                self.db_connection.commit()
                self.logger.info(f"Updated profile: {name}")
                return True
        
        except Exception as e:
            self.logger.error(f"Error updating profile {name}: {e}")
            return False
    
    def delete_profile(self, name: str) -> bool:
        """Delete a user profile"""
        try:
            # Don't allow deletion of default profiles
            if name in ['Default', 'Power User', 'Minimal']:
                return False
            
            with self.db_lock:
                cursor = self.db_connection.cursor()
                cursor.execute("DELETE FROM enhanced_profiles WHERE name = ?", (name,))
                self.db_connection.commit()
                
                self.logger.info(f"Deleted profile: {name}")
                return True
        
        except Exception as e:
            self.logger.error(f"Error deleting profile {name}: {e}")
            return False
    
    def get_all_profiles(self) -> List[Dict[str, Any]]:
        """Get all user profiles"""
        try:
            with self.db_lock:
                cursor = self.db_connection.cursor()
                
                cursor.execute("""
                    SELECT name, automation_level, created_at, updated_at
                    FROM enhanced_profiles ORDER BY name
                """)
                
                profiles = []
                for row in cursor.fetchall():
                    profiles.append({
                        'name': row[0],
                        'automation_level': row[1],
                        'created_at': row[2],
                        'updated_at': row[3]
                    })
                
                return profiles
        
        except Exception as e:
            self.logger.error(f"Error getting all profiles: {e}")
            return []
    
    def get_profile_count(self) -> int:
        """Get total number of profiles"""
        try:
            with self.db_lock:
                cursor = self.db_connection.cursor()
                cursor.execute("SELECT COUNT(*) FROM enhanced_profiles")
                return cursor.fetchone()[0]
        except Exception as e:
            self.logger.error(f"Error getting profile count: {e}")
            return 0
    
    def clone_profile(self, source_name: str, new_name: str) -> bool:
        """Clone an existing profile with a new name"""
        try:
            source_profile = self.get_profile(source_name)
            if not source_profile:
                return False
            
            # Remove metadata fields
            source_profile.pop('created_at', None)
            source_profile.pop('updated_at', None)
            source_profile['name'] = new_name
            
            return self.create_profile(new_name, source_profile)
        
        except Exception as e:
            self.logger.error(f"Error cloning profile {source_name} to {new_name}: {e}")
            return False
    
    def export_profile(self, name: str) -> Optional[Dict[str, Any]]:
        """Export a profile for backup or sharing"""
        profile = self.get_profile(name)
        if profile:
            # Remove internal metadata
            profile.pop('created_at', None)
            profile.pop('updated_at', None)
            profile['export_timestamp'] = datetime.now().isoformat()
            profile['export_version'] = '1.0'
        
        return profile
    
    def import_profile(self, profile_data: Dict[str, Any], overwrite: bool = False) -> bool:
        """Import a profile from backup or sharing"""
        try:
            name = profile_data.get('name')
            if not name:
                return False
            
            # Check if profile exists
            existing = self.get_profile(name)
            if existing and not overwrite:
                return False
            
            # Remove export metadata
            profile_data.pop('export_timestamp', None)
            profile_data.pop('export_version', None)
            
            if existing:
                return self.update_profile(name, profile_data)
            else:
                return self.create_profile(name, profile_data)
        
        except Exception as e:
            self.logger.error(f"Error importing profile: {e}")
            return False
    
    def get_deduplication_rules(self, profile_name: str) -> Dict[str, Any]:
        """Get deduplication rules for a profile"""
        profile = self.get_profile(profile_name)
        if profile:
            return profile.get('deduplication_rules', {})
        return {}
    
    def get_language_priorities(self, profile_name: str) -> Dict[str, List[str]]:
        """Get language priorities for a profile"""
        profile = self.get_profile(profile_name)
        if profile:
            return profile.get('language_priorities', {})
        return {'subtitles': ['en'], 'audio': ['en'], 'interface': 'en'}
    
    def get_smart_collections_config(self, profile_name: str) -> Dict[str, Any]:
        """Get smart collections configuration for a profile"""
        profile = self.get_profile(profile_name)
        if profile:
            return profile.get('smart_collections', {})
        return {'enabled': False}
    
    def get_metadata_providers(self, profile_name: str) -> Dict[str, List[str]]:
        """Get metadata provider chains for a profile"""
        profile = self.get_profile(profile_name)
        if profile:
            return profile.get('metadata_providers', {})
        return {
            'movie_chain': ['tmdb'],
            'tv_chain': ['tvdb'],
            'book_chain': ['google_books'],
            'music_chain': ['discogs']
        }
    
    def get_automation_level(self, profile_name: str) -> str:
        """Get automation level for a profile"""
        profile = self.get_profile(profile_name)
        if profile:
            return profile.get('automation_level', 'manual')
        return 'manual'
    
    def get_ui_preferences(self, profile_name: str) -> Dict[str, Any]:
        """Get UI preferences for a profile"""
        profile = self.get_profile(profile_name)
        if profile:
            return profile.get('ui_preferences', {})
        return {
            'theme': 'hero',
            'mobile_optimized': False,
            'show_badges': True,
            'auto_play_trailers': False
        }
