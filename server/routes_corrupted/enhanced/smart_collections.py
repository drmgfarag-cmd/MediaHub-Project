"""
Smart Collections and Organization System with Profile Architecture
Includes universe collections, smart rules, and automated organization
"""

import os
import re
import json
import time
import threading
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from flask import Blueprint, request, jsonify, current_app

bp = Blueprint('smart_collections', __name__)

class UniverseCollectionManager:
    """Manages universe-based collections with regex patterns"""
    
    def __init__(self):
        self.universe_definitions = {
            'mcu': {
                'name': 'Marvel Cinematic Universe',
                'description': 'All MCU movies and TV shows',
                'patterns': [
                    r'(?i)\b(iron\s*man|captain\s*america|thor|hulk|avengers|guardians\s*of\s*the\s*galaxy)',
                    r'(?i)\b(ant[\-\s]*man|doctor\s*strange|black\s*panther|captain\s*marvel|spider[\-\s]*man)',
                    r'(?i)\b(falcon\s*and\s*winter\s*soldier|wandavision|loki|hawkeye|moon\s*knight)',
                    r'(?i)\b(she[\-\s]*hulk|ms\.?\s*marvel|eternals|shang[\-\s]*chi|black\s*widow)',
                    r'(?i)\b(what\s*if|agents\s*of\s*shield|daredevil|jessica\s*jones|luke\s*cage)',
                    r'(?i)\b(iron\s*fist|defenders|punisher|inhumans|cloak\s*and\s*dagger)',
                    r'(?i)\b(runaways|helstrom|multiverse\s*of\s*madness|love\s*and\s*thunder)',
                    r'(?i)\b(wakanda\s*forever|quantumania|gotg|guardians\s*3)'
                ],
                'exclusions': [
                    r'(?i)\b(x[\-\s]*men|fantastic\s*four|deadpool|wolverine)',  # Fox properties
                    r'(?i)\b(venom|morbius|spider[\-\s]*verse)'  # Sony properties
                ],
                'metadata_sources': ['tmdb', 'omdb'],
                'auto_update': True
            },
            'dceu': {
                'name': 'DC Extended Universe',
                'description': 'DCEU movies and related content',
                'patterns': [
                    r'(?i)\b(man\s*of\s*steel|batman\s*v\s*superman|suicide\s*squad|wonder\s*woman)',
                    r'(?i)\b(justice\s*league|aquaman|shazam|birds\s*of\s*prey|harley\s*quinn)',
                    r'(?i)\b(wonder\s*woman\s*1984|zack\s*snyder|snyder\s*cut|the\s*batman)',
                    r'(?i)\b(flash|black\s*adam|blue\s*beetle|peacemaker|titans)',
                    r'(?i)\b(doom\s*patrol|swamp\s*thing|watchmen|sandman)'
                ],
                'exclusions': [
                    r'(?i)\b(joker\s*2019|the\s*batman\s*2022)',  # Standalone films
                    r'(?i)\b(arrow|flash\s*tv|supergirl|legends)'  # CW shows
                ],
                'metadata_sources': ['tmdb', 'omdb'],
                'auto_update': True
            },
            'star_wars': {
                'name': 'Star Wars Universe',
                'description': 'All Star Wars content including movies, series, and animated shows',
                'patterns': [
                    r'(?i)\b(star\s*wars|a\s*new\s*hope|empire\s*strikes\s*back|return\s*of\s*the\s*jedi)',
                    r'(?i)\b(phantom\s*menace|attack\s*of\s*the\s*clones|revenge\s*of\s*the\s*sith)',
                    r'(?i)\b(force\s*awakens|last\s*jedi|rise\s*of\s*skywalker|rogue\s*one|solo)',
                    r'(?i)\b(mandalorian|book\s*of\s*boba\s*fett|obi[\-\s]*wan|andor|ahsoka)',
                    r'(?i)\b(clone\s*wars|rebels|bad\s*batch|resistance|visions)',
                    r'(?i)\b(sw\s|episode\s*[ivx]+|jedi|sith|skywalker|vader|yoda)'
                ],
                'exclusions': [],
                'metadata_sources': ['tmdb', 'omdb'],
                'auto_update': True
            },
            'arrowverse': {
                'name': 'Arrowverse',
                'description': 'CW DC TV shows universe',
                'patterns': [
                    r'(?i)\b(arrow|flash\s*(?:tv|series|s\d)|supergirl|legends\s*of\s*tomorrow)',
                    r'(?i)\b(batwoman|black\s*lightning|superman\s*and\s*lois|stargirl)',
                    r'(?i)\b(constantine|vixen|freedom\s*fighters|crisis\s*on\s*infinite)',
                    r'(?i)\b(elseworlds|invasion|flash\s*vs\s*arrow)'
                ],
                'exclusions': [
                    r'(?i)\b(titans|doom\s*patrol|watchmen|sandman)'  # HBO Max shows
                ],
                'metadata_sources': ['tvdb', 'tmdb'],
                'auto_update': True
            },
            'fast_furious': {
                'name': 'Fast & Furious Franchise',
                'description': 'Fast & Furious movie franchise',
                'patterns': [
                    r'(?i)\b(fast\s*(?:and|&|\+)\s*furious|f&f|2\s*fast\s*2\s*furious)',
                    r'(?i)\b(tokyo\s*drift|fast\s*five|fast\s*six|furious\s*7|fate\s*of\s*the\s*furious)',
                    r'(?i)\b(hobbs\s*(?:and|&)\s*shaw|f9|fast\s*9|fast\s*x)'
                ],
                'exclusions': [],
                'metadata_sources': ['tmdb', 'omdb'],
                'auto_update': True
            },
            'john_wick': {
                'name': 'John Wick Universe',
                'description': 'John Wick movie franchise',
                'patterns': [
                    r'(?i)\b(john\s*wick|continental|nobody)'
                ],
                'exclusions': [],
                'metadata_sources': ['tmdb', 'omdb'],
                'auto_update': True
            }
        }
    
    def get_available_universes(self) -> Dict[str, Dict[str, Any]]:
        """Get all available universe definitions"""
        return {
            universe_id: {
                'name': definition['name'],
                'description': definition['description'],
                'auto_update': definition['auto_update']
            }
            for universe_id, definition in self.universe_definitions.items()
        }
    
    def create_universe_collection(self, universe_id: str, media_items: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Create a collection for a specific universe"""
        if universe_id not in self.universe_definitions:
            return {'success': False, 'error': f'Unknown universe: {universe_id}'}
        
        universe_def = self.universe_definitions[universe_id]
        matched_items = []
        
        for item in media_items:
            if self._matches_universe(item, universe_def):
                matched_items.append(item)
        
        collection_data = {
            'id': f"universe_{universe_id}",
            'name': universe_def['name'],
            'description': universe_def['description'],
            'type': 'universe',
            'universe_id': universe_id,
            'items': matched_items,
            'item_count': len(matched_items),
            'created_at': datetime.now().isoformat(),
            'auto_update': universe_def['auto_update']
        }
        
        return {'success': True, 'collection': collection_data}
    
    def _matches_universe(self, item: Dict[str, Any], universe_def: Dict[str, Any]) -> bool:
        """Check if an item matches a universe definition"""
        title = item.get('title', '').lower()
        filename = item.get('filename', '').lower()
        search_text = f"{title} {filename}"
        
        # Check exclusions first
        for exclusion_pattern in universe_def.get('exclusions', []):
            if re.search(exclusion_pattern, search_text):
                return False
        
        # Check inclusion patterns
        for pattern in universe_def['patterns']:
            if re.search(pattern, search_text):
                return True
        
        return False
    
    def update_universe_collection(self, universe_id: str, collection_id: str, 
                                 new_items: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Update an existing universe collection with new items"""
        if universe_id not in self.universe_definitions:
            return {'success': False, 'error': f'Unknown universe: {universe_id}'}
        
        universe_def = self.universe_definitions[universe_id]
        matched_items = []
        
        for item in new_items:
            if self._matches_universe(item, universe_def):
                matched_items.append(item)
        
        return {
            'success': True,
            'new_matches': matched_items,
            'match_count': len(matched_items)
        }

class SmartRulesEngine:
    """Smart rules engine for automatic content organization"""
    
    def __init__(self):
        self.smart_rules = {
            'quality_detection': {
                '4K': [r'(?i)\b(4k|2160p|uhd|ultra\s*hd)\b'],
                'HDR': [r'(?i)\b(hdr|hdr10|dolby\s*vision|dv)\b'],
                'Dolby_Vision': [r'(?i)\b(dolby\s*vision|dv)\b'],
                'Dolby_Atmos': [r'(?i)\b(dolby\s*atmos|atmos)\b'],
                '1080p': [r'(?i)\b(1080p|full\s*hd|fhd)\b'],
                '720p': [r'(?i)\b(720p|hd)\b'],
                'x265': [r'(?i)\b(x265|hevc|h\.?265)\b'],
                'x264': [r'(?i)\b(x264|avc|h\.?264)\b']
            },
            'genre_detection': {
                'Action': [r'(?i)\b(action|fight|battle|war|combat)\b'],
                'Comedy': [r'(?i)\b(comedy|funny|humor|laugh)\b'],
                'Drama': [r'(?i)\b(drama|dramatic)\b'],
                'Horror': [r'(?i)\b(horror|scary|fear|terror)\b'],
                'Sci-Fi': [r'(?i)\b(sci[\-\s]*fi|science\s*fiction|space|alien)\b'],
                'Fantasy': [r'(?i)\b(fantasy|magic|wizard|dragon)\b'],
                'Thriller': [r'(?i)\b(thriller|suspense|mystery)\b'],
                'Romance': [r'(?i)\b(romance|romantic|love)\b'],
                'Documentary': [r'(?i)\b(documentary|docu|real\s*story)\b']
            },
            'decade_detection': {
                '2020s': [r'(?i)\b(202[0-9])\b'],
                '2010s': [r'(?i)\b(201[0-9])\b'],
                '2000s': [r'(?i)\b(200[0-9])\b'],
                '1990s': [r'(?i)\b(199[0-9])\b'],
                '1980s': [r'(?i)\b(198[0-9])\b'],
                '1970s': [r'(?i)\b(197[0-9])\b'],
                '1960s': [r'(?i)\b(196[0-9])\b']
            },
            'tv_series_detection': {
                'Season': [r'(?i)\b(s\d+|season\s*\d+)\b'],
                'Episode': [r'(?i)\b(e\d+|episode\s*\d+)\b'],
                'Complete_Series': [r'(?i)\b(complete\s*series|full\s*series|all\s*seasons)\b'],
                'Mini_Series': [r'(?i)\b(mini\s*series|limited\s*series)\b']
            },
            'source_detection': {
                'BluRay': [r'(?i)\b(blu[\-\s]*ray|bdrip|bdremux)\b'],
                'WEB-DL': [r'(?i)\b(web[\-\s]*dl|webdl)\b'],
                'WEBRip': [r'(?i)\b(web[\-\s]*rip|webrip)\b'],
                'HDTV': [r'(?i)\b(hdtv|tv[\-\s]*rip)\b'],
                'DVD': [r'(?i)\b(dvd|dvdrip)\b'],
                'CAM': [r'(?i)\b(cam|camrip|ts|telesync)\b']
            }
        }
    
    def analyze_content(self, item: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze content and extract smart metadata"""
        title = item.get('title', '')
        filename = item.get('filename', '')
        search_text = f"{title} {filename}".lower()
        
        analysis = {
            'quality': [],
            'genres': [],
            'decade': None,
            'tv_info': {},
            'source': None,
            'badges': []
        }
        
        # Quality detection
        for quality, patterns in self.smart_rules['quality_detection'].items():
            for pattern in patterns:
                if re.search(pattern, search_text):
                    analysis['quality'].append(quality)
                    analysis['badges'].append(quality)
        
        # Genre detection
        for genre, patterns in self.smart_rules['genre_detection'].items():
            for pattern in patterns:
                if re.search(pattern, search_text):
                    analysis['genres'].append(genre)
        
        # Decade detection
        for decade, patterns in self.smart_rules['decade_detection'].items():
            for pattern in patterns:
                if re.search(pattern, search_text):
                    analysis['decade'] = decade
                    break
        
        # TV series detection
        for tv_type, patterns in self.smart_rules['tv_series_detection'].items():
            for pattern in patterns:
                match = re.search(pattern, search_text)
                if match:
                    analysis['tv_info'][tv_type.lower()] = match.group()
        
        # Source detection
        for source, patterns in self.smart_rules['source_detection'].items():
            for pattern in patterns:
                if re.search(pattern, search_text):
                    analysis['source'] = source
                    break
        
        return analysis
    
    def create_smart_rails(self, media_items: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """Create smart rails based on content analysis"""
        rails = {
            '4K_HDR_Content': [],
            'Dolby_Vision_Atmos': [],
            'Recent_Releases': [],
            'Classic_Movies': [],
            'TV_Series': [],
            'Documentaries': [],
            'Action_Movies': [],
            'Comedy_Movies': [],
            'Horror_Movies': []
        }
        
        current_year = datetime.now().year
        
        for item in media_items:
            analysis = self.analyze_content(item)
            
            # 4K HDR Content
            if '4K' in analysis['quality'] and 'HDR' in analysis['quality']:
                rails['4K_HDR_Content'].append(item)
            
            # Dolby Vision & Atmos
            if 'Dolby_Vision' in analysis['quality'] or 'Dolby_Atmos' in analysis['quality']:
                rails['Dolby_Vision_Atmos'].append(item)
            
            # Recent releases (last 2 years)
            if analysis['decade'] == '2020s':
                year_match = re.search(r'\b(202[0-9])\b', item.get('filename', ''))
                if year_match and int(year_match.group(1)) >= current_year - 2:
                    rails['Recent_Releases'].append(item)
            
            # Classic movies (before 2000)
            if analysis['decade'] in ['1990s', '1980s', '1970s', '1960s']:
                rails['Classic_Movies'].append(item)
            
            # TV Series
            if analysis['tv_info']:
                rails['TV_Series'].append(item)
            
            # Genre-based rails
            if 'Documentary' in analysis['genres']:
                rails['Documentaries'].append(item)
            if 'Action' in analysis['genres']:
                rails['Action_Movies'].append(item)
            if 'Comedy' in analysis['genres']:
                rails['Comedy_Movies'].append(item)
            if 'Horror' in analysis['genres']:
                rails['Horror_Movies'].append(item)
        
        # Remove empty rails and limit items
        filtered_rails = {}
        for rail_name, items in rails.items():
            if items:
                # Sort by relevance and limit to 20 items per rail
                filtered_rails[rail_name] = items[:20]
        
        return filtered_rails

class CollectionManager:
    """Manages all types of collections with database persistence"""
    
    def __init__(self, db_connection, db_lock):
        self.db_connection = db_connection
        self.db_lock = db_lock
        self.universe_manager = UniverseCollectionManager()
        self.smart_rules = SmartRulesEngine()
    
    def create_collection(self, name: str, collection_type: str = 'manual', 
                         items: List[Dict[str, Any]] = None, 
                         universe_id: str = None) -> Dict[str, Any]:
        """Create a new collection"""
        try:
            collection_id = f"col_{int(time.time())}_{hash(name) % 10000}"
            
            if collection_type == 'universe' and universe_id:
                result = self.universe_manager.create_universe_collection(universe_id, items or [])
                if not result['success']:
                    return result
                collection_data = result['collection']
                collection_data['id'] = collection_id
            else:
                collection_data = {
                    'id': collection_id,
                    'name': name,
                    'description': '',
                    'type': collection_type,
                    'items': items or [],
                    'item_count': len(items or []),
                    'created_at': datetime.now().isoformat(),
                    'auto_update': collection_type in ['smart', 'universe']
                }
            
            # Save to database
            with self.db_lock:
                cursor = self.db_connection.cursor()
                cursor.execute("""
                    INSERT INTO collections 
                    (collection_id, name, description, type, items, auto_update)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    collection_id,
                    collection_data['name'],
                    collection_data.get('description', ''),
                    collection_data['type'],
                    json.dumps(collection_data['items']),
                    collection_data['auto_update']
                ))
                self.db_connection.commit()
            
            return {'success': True, 'collection': collection_data}
        
        except Exception as e:
            current_app.logger.error(f"Create collection error: {e}")
            return {'success': False, 'error': str(e)}
    
    def get_collection(self, collection_id: str) -> Optional[Dict[str, Any]]:
        """Get a collection by ID"""
        try:
            with self.db_lock:
                cursor = self.db_connection.cursor()
                cursor.execute("""
                    SELECT collection_id, name, description, type, items, auto_update, created_at, updated_at
                    FROM collections WHERE collection_id = ?
                """, (collection_id,))
                
                row = cursor.fetchone()
                if row:
                    return {
                        'id': row[0],
                        'name': row[1],
                        'description': row[2],
                        'type': row[3],
                        'items': json.loads(row[4]) if row[4] else [],
                        'auto_update': bool(row[5]),
                        'created_at': row[6],
                        'updated_at': row[7],
                        'item_count': len(json.loads(row[4])) if row[4] else 0
                    }
        
        except Exception as e:
            current_app.logger.error(f"Get collection error: {e}")
        
        return None
    
    def list_collections(self, collection_type: str = None) -> List[Dict[str, Any]]:
        """List all collections with optional type filtering"""
        try:
            with self.db_lock:
                cursor = self.db_connection.cursor()
                
                if collection_type:
                    cursor.execute("""
                        SELECT collection_id, name, description, type, auto_update, created_at, updated_at,
                               LENGTH(items) as items_length
                        FROM collections WHERE type = ? ORDER BY updated_at DESC
                    """, (collection_type,))
                else:
                    cursor.execute("""
                        SELECT collection_id, name, description, type, auto_update, created_at, updated_at,
                               LENGTH(items) as items_length
                        FROM collections ORDER BY updated_at DESC
                    """)
                
                collections = []
                for row in cursor.fetchall():
                    # Estimate item count from JSON length (rough approximation)
                    estimated_items = max(0, (row[7] - 2) // 100) if row[7] else 0
                    
                    collections.append({
                        'id': row[0],
                        'name': row[1],
                        'description': row[2],
                        'type': row[3],
                        'auto_update': bool(row[4]),
                        'created_at': row[5],
                        'updated_at': row[6],
                        'estimated_item_count': estimated_items
                    })
                
                return collections
        
        except Exception as e:
            current_app.logger.error(f"List collections error: {e}")
            return []
    
    def update_collection(self, collection_id: str, updates: Dict[str, Any]) -> Dict[str, Any]:
        """Update a collection"""
        try:
            current_collection = self.get_collection(collection_id)
            if not current_collection:
                return {'success': False, 'error': 'Collection not found'}
            
            # Apply updates
            for key, value in updates.items():
                if key in ['name', 'description', 'items', 'auto_update']:
                    current_collection[key] = value
            
            current_collection['updated_at'] = datetime.now().isoformat()
            current_collection['item_count'] = len(current_collection['items'])
            
            # Save to database
            with self.db_lock:
                cursor = self.db_connection.cursor()
                cursor.execute("""
                    UPDATE collections SET
                        name = ?, description = ?, items = ?, auto_update = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE collection_id = ?
                """, (
                    current_collection['name'],
                    current_collection['description'],
                    json.dumps(current_collection['items']),
                    current_collection['auto_update'],
                    collection_id
                ))
                self.db_connection.commit()
            
            return {'success': True, 'collection': current_collection}
        
        except Exception as e:
            current_app.logger.error(f"Update collection error: {e}")
            return {'success': False, 'error': str(e)}
    
    def delete_collection(self, collection_id: str) -> Dict[str, Any]:
        """Delete a collection"""
        try:
            with self.db_lock:
                cursor = self.db_connection.cursor()
                cursor.execute("DELETE FROM collections WHERE collection_id = ?", (collection_id,))
                self.db_connection.commit()
                
                if cursor.rowcount > 0:
                    return {'success': True, 'message': 'Collection deleted'}
                else:
                    return {'success': False, 'error': 'Collection not found'}
        
        except Exception as e:
            current_app.logger.error(f"Delete collection error: {e}")
            return {'success': False, 'error': str(e)}
    
    def generate_smart_collections(self, media_items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Generate smart collections based on content analysis"""
        try:
            # Create smart rails
            smart_rails = self.smart_rules.create_smart_rails(media_items)
            
            created_collections = []
            
            for rail_name, rail_items in smart_rails.items():
                if rail_items:
                    collection_name = rail_name.replace('_', ' ').title()
                    result = self.create_collection(
                        name=collection_name,
                        collection_type='smart',
                        items=rail_items
                    )
                    
                    if result['success']:
                        created_collections.append(result['collection'])
            
            return created_collections
        
        except Exception as e:
            current_app.logger.error(f"Generate smart collections error: {e}")
            return []

# Global instances
collection_manager = None

def init_collection_manager(db_connection, db_lock):
    """Initialize collection manager with database connection"""
    global collection_manager
    collection_manager = CollectionManager(db_connection, db_lock)

@bp.route('/universes/list')
def list_universes():
    """List available universe definitions"""
    try:
        universe_manager = UniverseCollectionManager()
        universes = universe_manager.get_available_universes()
        
        return jsonify({
            'success': True,
            'universes': universes
        })
    
    except Exception as e:
        current_app.logger.error(f"List universes error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@bp.route('/collections/create', methods=['POST'])
def create_collection():
    """Create a new collection"""
    try:
        data = request.json
        name = data.get('name')
        collection_type = data.get('type', 'manual')
        items = data.get('items', [])
        universe_id = data.get('universe_id')
        
        if not name:
            return jsonify({'success': False, 'error': 'Collection name is required'})
        
        if not collection_manager:
            return jsonify({'success': False, 'error': 'Collection manager not initialized'})
        
        result = collection_manager.create_collection(name, collection_type, items, universe_id)
        return jsonify(result)
    
    except Exception as e:
        current_app.logger.error(f"Create collection error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@bp.route('/collections/list')
def list_collections():
    """List all collections"""
    try:
        collection_type = request.args.get('type')
        
        if not collection_manager:
            return jsonify({'success': False, 'error': 'Collection manager not initialized'})
        
        collections = collection_manager.list_collections(collection_type)
        
        return jsonify({
            'success': True,
            'collections': collections,
            'total': len(collections)
        })
    
    except Exception as e:
        current_app.logger.error(f"List collections error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@bp.route('/collections/<collection_id>')
def get_collection(collection_id):
    """Get a specific collection"""
    try:
        if not collection_manager:
            return jsonify({'success': False, 'error': 'Collection manager not initialized'})
        
        collection = collection_manager.get_collection(collection_id)
        
        if collection:
            return jsonify({
                'success': True,
                'collection': collection
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Collection not found'
            }), 404
    
    except Exception as e:
        current_app.logger.error(f"Get collection error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@bp.route('/collections/<collection_id>/update', methods=['PUT'])
def update_collection(collection_id):
    """Update a collection"""
    try:
        data = request.json
        
        if not collection_manager:
            return jsonify({'success': False, 'error': 'Collection manager not initialized'})
        
        result = collection_manager.update_collection(collection_id, data)
        return jsonify(result)
    
    except Exception as e:
        current_app.logger.error(f"Update collection error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@bp.route('/collections/<collection_id>/delete', methods=['DELETE'])
def delete_collection(collection_id):
    """Delete a collection"""
    try:
        if not collection_manager:
            return jsonify({'success': False, 'error': 'Collection manager not initialized'})
        
        result = collection_manager.delete_collection(collection_id)
        return jsonify(result)
    
    except Exception as e:
        current_app.logger.error(f"Delete collection error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@bp.route('/smart-collections/generate', methods=['POST'])
def generate_smart_collections():
    """Generate smart collections from media items"""
    try:
        data = request.json
        media_items = data.get('media_items', [])
        
        if not media_items:
            return jsonify({'success': False, 'error': 'No media items provided'})
        
        if not collection_manager:
            return jsonify({'success': False, 'error': 'Collection manager not initialized'})
        
        collections = collection_manager.generate_smart_collections(media_items)
        
        return jsonify({
            'success': True,
            'collections': collections,
            'generated_count': len(collections)
        })
    
    except Exception as e:
        current_app.logger.error(f"Generate smart collections error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@bp.route('/smart-rules/analyze', methods=['POST'])
def analyze_content():
    """Analyze content with smart rules"""
    try:
        data = request.json
        item = data.get('item', {})
        
        if not item:
            return jsonify({'success': False, 'error': 'No item provided for analysis'})
        
        smart_rules = SmartRulesEngine()
        analysis = smart_rules.analyze_content(item)
        
        return jsonify({
            'success': True,
            'analysis': analysis
        })
    
    except Exception as e:
        current_app.logger.error(f"Analyze content error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@bp.route('/smart-rails/generate', methods=['POST'])
def generate_smart_rails():
    """Generate smart rails from media items"""
    try:
        data = request.json
        media_items = data.get('media_items', [])
        
        if not media_items:
            return jsonify({'success': False, 'error': 'No media items provided'})
        
        smart_rules = SmartRulesEngine()
        rails = smart_rules.create_smart_rails(media_items)
        
        return jsonify({
            'success': True,
            'rails': rails,
            'rail_count': len(rails)
        })
    
    except Exception as e:
        current_app.logger.error(f"Generate smart rails error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500
