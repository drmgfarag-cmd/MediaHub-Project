"""
Collections Initialization - Pre-configured Collections from custom.txt
Creates sample collections based on user specifications
"""

import os
import json
import logging
from pathlib import Path

class CollectionsInitializer:
    """Initialize pre-configured collections from user specifications"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.collections_path = Path("storage/collections.json")
        self.collections_path.parent.mkdir(exist_ok=True)
        
        # Pre-configured collections from custom.txt
        self.default_collections = [
            {
                "name": "Franchise — Marvel Cinematic Universe",
                "rules": [
                    {"type": "movie", "path_re": "(?i)\\b(Marvel|MCU|Avengers|Iron Man|Captain America|Thor|Guardians)\\b"},
                    {"type": "series", "path_re": "(?i)\\b(Marvel|MCU|Loki|WandaVision|Hawkeye|Ms Marvel|Moon Knight)\\b"}
                ],
                "description": "Complete Marvel Cinematic Universe collection including movies and TV series",
                "category": "franchise"
            },
            {
                "name": "Universe — Star Wars",
                "rules": [
                    {"type": "movie", "path_re": "(?i)\\b(Star Wars|Rogue One|Solo)\\b"},
                    {"type": "series", "path_re": "(?i)\\b(Mandalorian|Andor|Ahsoka|Bad Batch|Obi-Wan)\\b"}
                ],
                "description": "Complete Star Wars universe including movies and TV series",
                "category": "universe"
            },
            {
                "name": "Crossovers — Arrowverse",
                "rules": [
                    {"type": "series", "path_re": "(?i)\\b(Arrow|Flash|Supergirl|Legends of Tomorrow|Crisis on)\\b"},
                    {"type": "episode", "path_re": "(?i)\\b(Crossover|Elseworlds|Crisis)\\b"}
                ],
                "description": "DC Arrowverse crossover events and series",
                "category": "crossover"
            },
            {
                "name": "Top Awards — Oscar Winners",
                "rules": [
                    {"type": "movie", "path_re": "(?i)\\b(Oscar|Academy Award|Best Picture|Best Director|Best Actor|Best Actress)\\b"}
                ],
                "description": "Academy Award winning films",
                "category": "awards"
            },
            {
                "name": "Director — Christopher Nolan",
                "rules": [
                    {"type": "movie", "path_re": "(?i)\\b(Inception|Interstellar|Dark Knight|Dunkirk|Tenet|Memento|Prestige)\\b"}
                ],
                "description": "Christopher Nolan filmography",
                "category": "director"
            },
            {
                "name": "Director — Denis Villeneuve",
                "rules": [
                    {"type": "movie", "path_re": "(?i)\\b(Dune|Blade Runner 2049|Arrival|Sicario|Prisoners)\\b"}
                ],
                "description": "Denis Villeneuve filmography",
                "category": "director"
            },
            {
                "name": "Director — Hayao Miyazaki",
                "rules": [
                    {"type": "movie", "path_re": "(?i)\\b(Spirited Away|Princess Mononoke|My Neighbor Totoro|Howl|Castle in the Sky)\\b"}
                ],
                "description": "Hayao Miyazaki Studio Ghibli films",
                "category": "director"
            },
            {
                "name": "Franchise — Harry Potter Universe",
                "rules": [
                    {"type": "movie", "path_re": "(?i)\\b(Harry Potter|Fantastic Beasts)\\b"},
                    {"type": "book", "path_re": "(?i)\\b(Harry Potter|J.K. Rowling)\\b"}
                ],
                "description": "Harry Potter universe including movies and books",
                "category": "franchise"
            },
            {
                "name": "Franchise — Lord of the Rings",
                "rules": [
                    {"type": "movie", "path_re": "(?i)\\b(Lord of the Rings|Hobbit|LOTR)\\b"},
                    {"type": "series", "path_re": "(?i)\\b(Rings of Power)\\b"},
                    {"type": "book", "path_re": "(?i)\\b(Tolkien|Middle Earth)\\b"}
                ],
                "description": "Middle-earth saga including movies, series, and books",
                "category": "franchise"
            },
            {
                "name": "Genre — Documentaries",
                "rules": [
                    {"type": "movie", "path_re": "(?i)\\b(Documentary|Docs|Docu)\\b"},
                    {"type": "series", "path_re": "(?i)\\b(Documentary|Nature|Planet Earth|Our Planet)\\b"}
                ],
                "description": "Documentary films and series",
                "category": "genre"
            },
            {
                "name": "Genre — Stand-Up Comedy",
                "rules": [
                    {"type": "movie", "path_re": "(?i)\\b(Standup|Stand-up|Stand up|Comedy Special)\\b"},
                    {"type": "series", "path_re": "(?i)\\b(Comedy Central|Netflix Comedy)\\b"}
                ],
                "description": "Stand-up comedy specials and shows",
                "category": "genre"
            },
            {
                "name": "Quality — 4K HDR Collection",
                "rules": [
                    {"type": "movie", "path_re": "(?i)\\b(2160p|UHD|4K|HDR|Dolby Vision|DV)\\b"},
                    {"type": "series", "path_re": "(?i)\\b(2160p|UHD|4K|HDR)\\b"}
                ],
                "description": "High-quality 4K HDR content",
                "category": "quality"
            }
        ]
    
    def load_existing_collections(self):
        """Load existing collections from file"""
        try:
            if self.collections_path.exists():
                with open(self.collections_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            return {"collections": []}
        except Exception as e:
            self.logger.error(f"Error loading collections: {e}")
            return {"collections": []}
    
    def save_collections(self, collections_data):
        """Save collections to file"""
        try:
            with open(self.collections_path, 'w', encoding='utf-8') as f:
                json.dump(collections_data, f, indent=2, ensure_ascii=False)
            self.logger.info(f"Saved {len(collections_data.get('collections', []))} collections")
        except Exception as e:
            self.logger.error(f"Error saving collections: {e}")
    
    def initialize_collections(self):
        """Initialize pre-configured collections"""
        existing_data = self.load_existing_collections()
        existing_names = {c.get('name') for c in existing_data.get('collections', [])}
        
        added_count = 0
        for collection in self.default_collections:
            if collection['name'] not in existing_names:
                # Add timestamp
                collection['ts'] = int(__import__('time').time())
                collection['auto_created'] = True
                existing_data.setdefault('collections', []).append(collection)
                added_count += 1
                self.logger.info(f"Added collection: {collection['name']}")
        
        if added_count > 0:
            self.save_collections(existing_data)
            self.logger.info(f"Initialized {added_count} new collections")
        else:
            self.logger.info("All collections already exist")
        
        return added_count
    
    def get_collections_by_category(self, category=None):
        """Get collections filtered by category"""
        data = self.load_existing_collections()
        collections = data.get('collections', [])
        
        if category:
            collections = [c for c in collections if c.get('category') == category]
        
        return collections
    
    def create_top_lists(self):
        """Create auto-refreshable Top-50 lists per category"""
        top_lists = [
            {
                "name": "Top 50 — Movies (IMDb)",
                "rules": [{"type": "movie", "sort_by": "imdb_rating", "limit": 50}],
                "description": "Top 50 highest rated movies",
                "category": "top_list",
                "auto_refresh": True,
                "refresh_interval": 86400  # 24 hours
            },
            {
                "name": "Top 50 — TV Series (IMDb)",
                "rules": [{"type": "series", "sort_by": "imdb_rating", "limit": 50}],
                "description": "Top 50 highest rated TV series",
                "category": "top_list",
                "auto_refresh": True,
                "refresh_interval": 86400
            },
            {
                "name": "Top 50 — Books (Rating)",
                "rules": [{"type": "book", "sort_by": "rating", "limit": 50}],
                "description": "Top 50 highest rated books",
                "category": "top_list",
                "auto_refresh": True,
                "refresh_interval": 86400
            },
            {
                "name": "Top 50 — Albums (Rating)",
                "rules": [{"type": "album", "sort_by": "rating", "limit": 50}],
                "description": "Top 50 highest rated albums",
                "category": "top_list",
                "auto_refresh": True,
                "refresh_interval": 86400
            }
        ]
        
        existing_data = self.load_existing_collections()
        existing_names = {c.get('name') for c in existing_data.get('collections', [])}
        
        added_count = 0
        for top_list in top_lists:
            if top_list['name'] not in existing_names:
                top_list['ts'] = int(__import__('time').time())
                top_list['auto_created'] = True
                existing_data.setdefault('collections', []).append(top_list)
                added_count += 1
        
        if added_count > 0:
            self.save_collections(existing_data)
            self.logger.info(f"Created {added_count} top lists")
        
        return added_count

# Initialize collections on import
def initialize_default_collections():
    """Initialize default collections - called during app startup"""
    initializer = CollectionsInitializer()
    collections_added = initializer.initialize_collections()
    top_lists_added = initializer.create_top_lists()
    
    return {
        "collections_added": collections_added,
        "top_lists_added": top_lists_added,
        "total_added": collections_added + top_lists_added
    }

if __name__ == "__main__":
    # Can be run standalone for testing
    result = initialize_default_collections()
    print(f"Initialization complete: {result}")
