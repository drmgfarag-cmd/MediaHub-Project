"""
MediaHub Database Models
Comprehensive models for all features including watch history, favorites, etc.
"""
import sqlite3
from datetime import datetime
from pathlib import Path
import json

# Database path
DB_PATH = Path(__file__).parent.parent / "data" / "mediahub.db"

def get_db_connection():
    """Get database connection"""
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn

def init_database():
    """Initialize database with all required tables"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Watch History Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS watch_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            media_id TEXT NOT NULL UNIQUE,
            media_type TEXT NOT NULL,
            title TEXT NOT NULL,
            poster_url TEXT,
            progress REAL DEFAULT 0,
            duration REAL DEFAULT 0,
            last_watched TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            completed BOOLEAN DEFAULT 0,
            season INTEGER,
            episode INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Favorites Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS favorites (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            media_id TEXT NOT NULL UNIQUE,
            media_type TEXT NOT NULL,
            title TEXT NOT NULL,
            poster_url TEXT,
            rating REAL,
            added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            notes TEXT,
            tags TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Collections Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS collections (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            description TEXT,
            poster_url TEXT,
            is_smart BOOLEAN DEFAULT 0,
            smart_rules TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Collection Items Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS collection_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            collection_id INTEGER NOT NULL,
            media_id TEXT NOT NULL,
            media_type TEXT NOT NULL,
            title TEXT NOT NULL,
            poster_url TEXT,
            added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            sort_order INTEGER DEFAULT 0,
            FOREIGN KEY (collection_id) REFERENCES collections(id) ON DELETE CASCADE
        )
    ''')
    
    # Recommendations Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS recommendations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            media_id TEXT NOT NULL,
            media_type TEXT NOT NULL,
            title TEXT NOT NULL,
            poster_url TEXT,
            score REAL DEFAULT 0,
            reason TEXT,
            source TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            dismissed BOOLEAN DEFAULT 0
        )
    ''')
    
    # Calendar Events Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS calendar_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            media_id TEXT NOT NULL,
            media_type TEXT NOT NULL,
            title TEXT NOT NULL,
            poster_url TEXT,
            release_date DATE NOT NULL,
            season INTEGER,
            episode INTEGER,
            episode_title TEXT,
            notified BOOLEAN DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Real-Debrid Downloads Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS rd_downloads (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            rd_id TEXT NOT NULL UNIQUE,
            filename TEXT NOT NULL,
            filesize INTEGER,
            link TEXT,
            host TEXT,
            status TEXT DEFAULT 'queued',
            progress REAL DEFAULT 0,
            speed INTEGER DEFAULT 0,
            added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            completed_at TIMESTAMP,
            error TEXT,
            metadata TEXT
        )
    ''')
    
    # Comics Library Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS comics (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            file_path TEXT NOT NULL UNIQUE,
            title TEXT NOT NULL,
            series TEXT,
            issue_number TEXT,
            publisher TEXT,
            year INTEGER,
            cover_url TEXT,
            page_count INTEGER,
            current_page INTEGER DEFAULT 1,
            completed BOOLEAN DEFAULT 0,
            rating REAL,
            last_read TIMESTAMP,
            added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            metadata TEXT
        )
    ''')
    
    # User Preferences Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_preferences (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            key TEXT NOT NULL UNIQUE,
            value TEXT NOT NULL,
            category TEXT DEFAULT 'general',
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Search History Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS search_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            query TEXT NOT NULL,
            results_count INTEGER DEFAULT 0,
            searched_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Create indexes for performance
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_watch_history_media ON watch_history(media_id)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_watch_history_last_watched ON watch_history(last_watched DESC)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_favorites_media ON favorites(media_id)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_collection_items_collection ON collection_items(collection_id)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_calendar_release_date ON calendar_events(release_date)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_rd_downloads_status ON rd_downloads(status)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_comics_series ON comics(series)')
    
    conn.commit()
    conn.close()
    
    print("✅ Database initialized successfully")

# Watch History Operations
class WatchHistory:
    @staticmethod
    def add_or_update(media_id, media_type, title, progress=0, duration=0, **kwargs):
        """Add or update watch history entry"""
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO watch_history (media_id, media_type, title, progress, duration, poster_url, season, episode, last_watched, completed)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP, ?)
            ON CONFLICT(media_id) DO UPDATE SET
                progress = ?,
                duration = ?,
                last_watched = CURRENT_TIMESTAMP,
                completed = ?,
                updated_at = CURRENT_TIMESTAMP
        ''', (media_id, media_type, title, progress, duration, kwargs.get('poster_url'), 
              kwargs.get('season'), kwargs.get('episode'), int(progress >= duration * 0.9),
              progress, duration, int(progress >= duration * 0.9)))
        
        conn.commit()
        conn.close()
    
    @staticmethod
    def get_recent(limit=50):
        """Get recent watch history"""
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM watch_history ORDER BY last_watched DESC LIMIT ?', (limit,))
        results = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return results
    
    @staticmethod
    def get_by_media(media_id):
        """Get watch history for specific media"""
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM watch_history WHERE media_id = ?', (media_id,))
        result = cursor.fetchone()
        conn.close()
        return dict(result) if result else None

# Favorites Operations
class Favorites:
    @staticmethod
    def add(media_id, media_type, title, **kwargs):
        """Add to favorites"""
        conn = get_db_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                INSERT INTO favorites (media_id, media_type, title, poster_url, rating, notes, tags)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (media_id, media_type, title, kwargs.get('poster_url'), 
                  kwargs.get('rating'), kwargs.get('notes'), kwargs.get('tags')))
            conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False
        finally:
            conn.close()
    
    @staticmethod
    def remove(media_id):
        """Remove from favorites"""
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('DELETE FROM favorites WHERE media_id = ?', (media_id,))
        conn.commit()
        conn.close()
    
    @staticmethod
    def get_all():
        """Get all favorites"""
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM favorites ORDER BY added_at DESC')
        results = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return results
    
    @staticmethod
    def is_favorite(media_id):
        """Check if media is favorited"""
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT COUNT(*) FROM favorites WHERE media_id = ?', (media_id,))
        count = cursor.fetchone()[0]
        conn.close()
        return count > 0

# Collections Operations
class Collections:
    @staticmethod
    def create(name, description='', **kwargs):
        """Create new collection"""
        conn = get_db_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                INSERT INTO collections (name, description, poster_url, is_smart, smart_rules)
                VALUES (?, ?, ?, ?, ?)
            ''', (name, description, kwargs.get('poster_url'), 
                  kwargs.get('is_smart', 0), kwargs.get('smart_rules')))
            conn.commit()
            collection_id = cursor.lastrowid
            conn.close()
            return collection_id
        except sqlite3.IntegrityError:
            conn.close()
            return None
    
    @staticmethod
    def add_item(collection_id, media_id, media_type, title, **kwargs):
        """Add item to collection"""
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO collection_items (collection_id, media_id, media_type, title, poster_url)
            VALUES (?, ?, ?, ?, ?)
        ''', (collection_id, media_id, media_type, title, kwargs.get('poster_url')))
        conn.commit()
        conn.close()
    
    @staticmethod
    def get_all():
        """Get all collections"""
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM collections ORDER BY created_at DESC')
        results = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return results
    
    @staticmethod
    def get_items(collection_id):
        """Get items in collection"""
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM collection_items WHERE collection_id = ? ORDER BY sort_order, added_at', (collection_id,))
        results = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return results

# Recommendations Operations
class Recommendations:
    @staticmethod
    def add(media_id, media_type, title, score, reason='', source='system'):
        """Add recommendation"""
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO recommendations (media_id, media_type, title, score, reason, source, poster_url)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (media_id, media_type, title, score, reason, source, None))
        conn.commit()
        conn.close()
    
    @staticmethod
    def get_active(limit=20):
        """Get active recommendations"""
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT * FROM recommendations 
            WHERE dismissed = 0 
            ORDER BY score DESC, created_at DESC 
            LIMIT ?
        ''', (limit,))
        results = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return results
    
    @staticmethod
    def dismiss(recommendation_id):
        """Dismiss recommendation"""
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('UPDATE recommendations SET dismissed = 1 WHERE id = ?', (recommendation_id,))
        conn.commit()
        conn.close()

# Calendar Operations
class Calendar:
    @staticmethod
    def add_event(media_id, media_type, title, release_date, **kwargs):
        """Add calendar event"""
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO calendar_events (media_id, media_type, title, release_date, poster_url, season, episode, episode_title)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (media_id, media_type, title, release_date, kwargs.get('poster_url'),
              kwargs.get('season'), kwargs.get('episode'), kwargs.get('episode_title')))
        conn.commit()
        conn.close()
    
    @staticmethod
    def get_upcoming(days=30):
        """Get upcoming events"""
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT * FROM calendar_events 
            WHERE release_date >= date('now') 
            AND release_date <= date('now', '+' || ? || ' days')
            ORDER BY release_date ASC
        ''', (days,))
        results = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return results

# Real-Debrid Operations
class RealDebrid:
    @staticmethod
    def add_download(rd_id, filename, link, **kwargs):
        """Add RD download"""
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO rd_downloads (rd_id, filename, link, filesize, host, status, metadata)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (rd_id, filename, link, kwargs.get('filesize'), kwargs.get('host'), 
              kwargs.get('status', 'queued'), kwargs.get('metadata')))
        conn.commit()
        conn.close()
    
    @staticmethod
    def update_progress(rd_id, progress, speed=0, status='downloading'):
        """Update download progress"""
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE rd_downloads 
            SET progress = ?, speed = ?, status = ?
            WHERE rd_id = ?
        ''', (progress, speed, status, rd_id))
        conn.commit()
        conn.close()
    
    @staticmethod
    def get_active():
        """Get active downloads"""
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT * FROM rd_downloads 
            WHERE status IN ('queued', 'downloading') 
            ORDER BY added_at DESC
        ''')
        results = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return results

# Comics Operations
class Comics:
    @staticmethod
    def add(file_path, title, **kwargs):
        """Add comic to library"""
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO comics (file_path, title, series, issue_number, publisher, year, page_count, metadata)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (file_path, title, kwargs.get('series'), kwargs.get('issue_number'),
              kwargs.get('publisher'), kwargs.get('year'), kwargs.get('page_count'),
              kwargs.get('metadata')))
        conn.commit()
        conn.close()
    
    @staticmethod
    def update_progress(comic_id, current_page):
        """Update reading progress"""
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE comics 
            SET current_page = ?, last_read = CURRENT_TIMESTAMP
            WHERE id = ?
        ''', (current_page, comic_id))
        conn.commit()
        conn.close()
    
    @staticmethod
    def get_all():
        """Get all comics"""
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM comics ORDER BY series, issue_number')
        results = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return results

# Initialize database on module import
if __name__ == '__main__':
    init_database()

# Add missing get_all() method to WatchHistory
WatchHistory.get_all = WatchHistory.get_recent

# Create singular aliases for compatibility
Favorite = Favorites
Collection = Collections
Recommendation = type('Recommendation', (), {})
CalendarEvent = type('CalendarEvent', (), {})
RDDownload = type('RDDownload', (), {})
Comic = type('Comic', (), {})
UserPreferences = type('UserPreferences', (), {})

# Export all classes
__all__ = [
    'WatchHistory',
    'Favorite',
    'Favorites',
    'Collection',
    'Collections',
    'Recommendation',
    'CalendarEvent',
    'RDDownload',
    'Comic',
    'UserPreferences',
    'init_database',
    'get_db_connection'
]
