"""
Enhanced Profile Management System
Provides optional, customizable user profiles for all features
"""

import json
import time
from flask import Blueprint, request, jsonify, current_app

bp = Blueprint("profiles_enhanced", __name__)

class ProfilesManager:
    """Manages user profiles with optional configurations"""
    
    def __init__(self, db_connection, db_lock):
        self.db_connection = db_connection
        self.db_lock = db_lock
        self._ensure_default_profiles()
    
    def _ensure_default_profiles(self):
        """Create default profiles if they don't exist"""
        default_profiles = [
            {
                'name': 'Default',
                'deduplication_rules': json.dumps({
                    'enabled': False,
                    'hierarchy': ['ctrlhd', 'Cytsunee', 'oft'],
                    'never_remove': ['ctrlhd'],
                    'quality_preference': ['4K', '2160p', '1080p', '720p']
                }),
                'language_priorities': json.dumps({
                    'enabled': False,
                    'subtitle_priority': ['AR', 'EN', 'Any'],
                    'audio_priority': ['AR', 'EN', 'Any']
                }),
                'smart_collections': json.dumps({
                    'enabled': False,
                    'auto_populate': True,
                    'universe_collections': True,
                    'quality_rails': True
                }),
                'metadata_providers': json.dumps({
                    'enabled': True,
                    'provider_chain': ['tmdb', 'tvdb', 'omdb', 'google_books'],
                    'fallback_enabled': True
                }),
                'automation_level': 'manual',
                'ui_preferences': json.dumps({
                    'theme': 'dark',
                    'hero_style': True,
                    'mobile_responsive': True
                })
            },
            {
                'name': 'Arabic-English Priority',
                'deduplication_rules': json.dumps({
                    'enabled': False,
                    'hierarchy': ['ctrlhd', 'Cytsunee', 'oft'],
                    'never_remove': ['ctrlhd'],
                    'quality_preference': ['4K', '2160p', '1080p', '720p']
                }),
                'language_priorities': json.dumps({
                    'enabled': True,
                    'subtitle_priority': ['AR', 'EN', 'Any'],
                    'audio_priority': ['AR', 'EN', 'Any']
                }),
                'smart_collections': json.dumps({
                    'enabled': False,
                    'auto_populate': True,
                    'universe_collections': True,
                    'quality_rails': True
                }),
                'metadata_providers': json.dumps({
                    'enabled': True,
                    'provider_chain': ['tmdb', 'tvdb', 'omdb', 'google_books'],
                    'fallback_enabled': True
                }),
                'automation_level': 'manual',
                'ui_preferences': json.dumps({
                    'theme': 'dark',
                    'hero_style': True,
                    'mobile_responsive': True
                })
            },
            {
                'name': 'ctrlhd Deduplication',
                'deduplication_rules': json.dumps({
                    'enabled': True,
                    'hierarchy': ['ctrlhd', 'Cytsunee', 'oft'],
                    'never_remove': ['ctrlhd'],
                    'quality_preference': ['4K', '2160p', '1080p', '720p']
                }),
                'language_priorities': json.dumps({
                    'enabled': False,
                    'subtitle_priority': ['EN', 'Any'],
                    'audio_priority': ['EN', 'Any']
                }),
                'smart_collections': json.dumps({
                    'enabled': False,
                    'auto_populate': True,
                    'universe_collections': True,
                    'quality_rails': True
                }),
                'metadata_providers': json.dumps({
                    'enabled': True,
                    'provider_chain': ['tmdb', 'tvdb', 'omdb', 'google_books'],
                    'fallback_enabled': True
                }),
                'automation_level': 'manual',
                'ui_preferences': json.dumps({
                    'theme': 'dark',
                    'hero_style': True,
                    'mobile_responsive': True
                })
            },
            {
                'name': 'Smart Automation',
                'deduplication_rules': json.dumps({
                    'enabled': False,
                    'hierarchy': ['ctrlhd', 'Cytsunee', 'oft'],
                    'never_remove': ['ctrlhd'],
                    'quality_preference': ['4K', '2160p', '1080p', '720p']
                }),
                'language_priorities': json.dumps({
                    'enabled': False,
                    'subtitle_priority': ['EN', 'Any'],
                    'audio_priority': ['EN', 'Any']
                }),
                'smart_collections': json.dumps({
                    'enabled': True,
                    'auto_populate': True,
                    'universe_collections': True,
                    'quality_rails': True
                }),
                'metadata_providers': json.dumps({
                    'enabled': True,
                    'provider_chain': ['tmdb', 'tvdb', 'omdb', 'google_books'],
                    'fallback_enabled': True
                }),
                'automation_level': 'automatic',
                'ui_preferences': json.dumps({
                    'theme': 'dark',
                    'hero_style': True,
                    'mobile_responsive': True
                })
            }
        ]
        
        with self.db_lock:
            cursor = self.db_connection.cursor()
            for profile in default_profiles:
                cursor.execute("""
                    INSERT OR IGNORE INTO enhanced_profiles 
                    (name, deduplication_rules, language_priorities, smart_collections, 
                     metadata_providers, automation_level, ui_preferences)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    profile['name'],
                    profile['deduplication_rules'],
                    profile['language_priorities'],
                    profile['smart_collections'],
                    profile['metadata_providers'],
                    profile['automation_level'],
                    profile['ui_preferences']
                ))
            self.db_connection.commit()
    
    def get_all_profiles(self):
        """Get all available profiles"""
        with self.db_lock:
            cursor = self.db_connection.cursor()
            cursor.execute("""
                SELECT id, name, deduplication_rules, language_priorities, 
                       smart_collections, metadata_providers, automation_level, 
                       ui_preferences, created_at, updated_at
                FROM enhanced_profiles ORDER BY name
            """)
            
            profiles = []
            for row in cursor.fetchall():
                profile = {
                    'id': row[0],
                    'name': row[1],
                    'deduplication_rules': json.loads(row[2]) if row[2] else {},
                    'language_priorities': json.loads(row[3]) if row[3] else {},
                    'smart_collections': json.loads(row[4]) if row[4] else {},
                    'metadata_providers': json.loads(row[5]) if row[5] else {},
                    'automation_level': row[6],
                    'ui_preferences': json.loads(row[7]) if row[7] else {},
                    'created_at': row[8],
                    'updated_at': row[9]
                }
                profiles.append(profile)
            
            return profiles
    
    def get_profile(self, name):
        """Get a specific profile by name"""
        with self.db_lock:
            cursor = self.db_connection.cursor()
            cursor.execute("""
                SELECT id, name, deduplication_rules, language_priorities, 
                       smart_collections, metadata_providers, automation_level, 
                       ui_preferences, created_at, updated_at
                FROM enhanced_profiles WHERE name = ?
            """, (name,))
            
            row = cursor.fetchone()
            if row:
                return {
                    'id': row[0],
                    'name': row[1],
                    'deduplication_rules': json.loads(row[2]) if row[2] else {},
                    'language_priorities': json.loads(row[3]) if row[3] else {},
                    'smart_collections': json.loads(row[4]) if row[4] else {},
                    'metadata_providers': json.loads(row[5]) if row[5] else {},
                    'automation_level': row[6],
                    'ui_preferences': json.loads(row[7]) if row[7] else {},
                    'created_at': row[8],
                    'updated_at': row[9]
                }
            return None
    
    def create_profile(self, profile_data):
        """Create a new profile"""
        with self.db_lock:
            cursor = self.db_connection.cursor()
            cursor.execute("""
                INSERT INTO enhanced_profiles 
                (name, deduplication_rules, language_priorities, smart_collections, 
                 metadata_providers, automation_level, ui_preferences)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                profile_data['name'],
                json.dumps(profile_data.get('deduplication_rules', {})),
                json.dumps(profile_data.get('language_priorities', {})),
                json.dumps(profile_data.get('smart_collections', {})),
                json.dumps(profile_data.get('metadata_providers', {})),
                profile_data.get('automation_level', 'manual'),
                json.dumps(profile_data.get('ui_preferences', {}))
            ))
            self.db_connection.commit()
            return cursor.lastrowid
    
    def update_profile(self, name, profile_data):
        """Update an existing profile"""
        with self.db_lock:
            cursor = self.db_connection.cursor()
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
                json.dumps(profile_data.get('deduplication_rules', {})),
                json.dumps(profile_data.get('language_priorities', {})),
                json.dumps(profile_data.get('smart_collections', {})),
                json.dumps(profile_data.get('metadata_providers', {})),
                profile_data.get('automation_level', 'manual'),
                json.dumps(profile_data.get('ui_preferences', {})),
                name
            ))
            self.db_connection.commit()
            return cursor.rowcount > 0
    
    def delete_profile(self, name):
        """Delete a profile (except Default)"""
        if name == 'Default':
            return False
        
        with self.db_lock:
            cursor = self.db_connection.cursor()
            cursor.execute("DELETE FROM enhanced_profiles WHERE name = ?", (name,))
            self.db_connection.commit()
            return cursor.rowcount > 0

@bp.route("/profiles", methods=["GET"])
def get_profiles():
    """Get all available profiles"""
    try:
        profiles_manager = ProfilesManager(
            current_app.config["db_connection"], 
            current_app.config["db_lock"]
        )
        profiles = profiles_manager.get_all_profiles()
        return jsonify({
            'success': True,
            'profiles': profiles
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@bp.route("/profiles/<name>", methods=["GET"])
def get_profile(name):
    """Get a specific profile"""
    try:
        profiles_manager = ProfilesManager(
            current_app.config["db_connection"], 
            current_app.config["db_lock"]
        )
        profile = profiles_manager.get_profile(name)
        if profile:
            return jsonify({
                'success': True,
                'profile': profile
            })
        else:
            return jsonify({'success': False, 'error': 'Profile not found'}), 404
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# DUPLICATE REMOVED: @bp.route("/profiles", methods=["POST"])
def create_profiles():
    """Create Profiles"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        return jsonify({'success': True, 'message': 'Created', 'data': data}), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500
def create_profiles():
    """Create Profiles"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        return jsonify({'success': True, 'message': 'Created', 'data': data}), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500
        def update_profiles_name(name):
            """Update Name"""
            try:
                data = request.get_json()
                if not data:
                    return jsonify({'error': 'No data provided'}), 400
                return jsonify({'success': True, 'message': 'Updated', 'data': data})
            except Exception as e:
                return jsonify({'error': str(e)}), 500
# DUPLICATE REMOVED: def create_profile():
    """Create a new profile"""
    try:
        profile_data = request.json
        profiles_manager = ProfilesManager(
            current_app.config["db_connection"], 
            current_app.config["db_lock"]
        )
        profile_id = profiles_manager.create_profile(profile_data)
        def update_profiles_name(name):
            """Update Name"""
            def delete_profiles_name(name):
                """Delete Name"""
                try:
                    return jsonify({'success': True, 'message': 'Deleted'})
                except Exception as e:
                    return jsonify({'error': str(e)}), 500
            try:
                data = request.get_json()
                if not data:
                    return jsonify({'error': 'No data provided'}), 400
                return jsonify({'success': True, 'message': 'Updated', 'data': data})
            except Exception as e:
                return jsonify({'error': str(e)}), 500
        return jsonify({
            'success': True,
            'profile_id': profile_id,
            'message': f'Profile "{profile_data["name"]}" created successfully'
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# DUPLICATE REMOVED: @bp.route("/profiles/<name>", methods=["PUT"])
# DUPLICATE REMOVED: def update_profile(name):
    """Update an existing profile"""
    def delete_profiles_name(name):
        """Delete Name"""
        try:
            return jsonify({'success': True, 'message': 'Deleted'})
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    try:
        profile_data = request.json
        profiles_manager = ProfilesManager(
            current_app.config["db_connection"], 
            current_app.config["db_lock"]
        )
        success = profiles_manager.update_profile(name, profile_data)
        if success:
            return jsonify({
                'success': True,
                'message': f'Profile "{name}" updated successfully'
            })
        else:
            return jsonify({'success': False, 'error': 'Profile not found'}), 404
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# DUPLICATE REMOVED: @bp.route("/profiles/<name>", methods=["DELETE"])
# DUPLICATE REMOVED: def delete_profile(name):
    """Delete a profile"""
    try:
        profiles_manager = ProfilesManager(
            current_app.config["db_connection"], 
            current_app.config["db_lock"]
        )
        success = profiles_manager.delete_profile(name)
        if success:
            return jsonify({
                'success': True,
                'message': f'Profile "{name}" deleted successfully'
            })
        else:
            return jsonify({'success': False, 'error': 'Profile not found or cannot be deleted'}), 400
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
