"""
Comprehensive Test Suite for MediaHub
Tests all features, APIs, database models, and frontend integration
"""
import sys
from pathlib import Path
import json
import sqlite3
from datetime import datetime

# Add parent directories to path
sys.path.insert(0, str(Path(__file__).parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent / 'server'))

# Test results
test_results = {
    'total': 0,
    'passed': 0,
    'failed': 0,
    'tests': []
}

def test(name):
    """Decorator for test functions"""
    def decorator(func):
        def wrapper():
            global test_results
            test_results['total'] += 1
            try:
                func()
                test_results['passed'] += 1
                test_results['tests'].append({'name': name, 'status': 'PASS', 'error': None})
                print(f"✅ {name}")
                return True
            except AssertionError as e:
                test_results['failed'] += 1
                test_results['tests'].append({'name': name, 'status': 'FAIL', 'error': str(e)})
                print(f"❌ {name}: {e}")
                return False
            except Exception as e:
                test_results['failed'] += 1
                test_results['tests'].append({'name': name, 'status': 'ERROR', 'error': str(e)})
                print(f"⚠️  {name}: {e}")
                return False
        return wrapper
    return decorator

# ============================================================================
# DATABASE TESTS
# ============================================================================

@test("Database file exists")
def test_database_exists():
    db_path = Path(__file__).parent.parent / "data" / "mediahub.db"
    assert db_path.exists(), f"Database not found at {db_path}"

@test("Database has all required tables")
def test_database_tables():
    db_path = Path(__file__).parent.parent / "data" / "mediahub.db"
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
    
    required_tables = [
        'watch_history', 'favorites', 'collections', 'collection_items',
        'recommendations', 'calendar_events', 'rd_downloads', 'comics',
        'user_preferences', 'search_history'
    ]
    
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [row[0] for row in cursor.fetchall()]
    conn.close()
    
    for table in required_tables:
        assert table in tables, f"Table '{table}' not found in database"

@test("Watch history table has correct schema")
def test_watch_history_schema():
    db_path = Path(__file__).parent.parent / "data" / "mediahub.db"
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
    
    cursor.execute("PRAGMA table_info(watch_history)")
    columns = {row[1] for row in cursor.fetchall()}
    conn.close()
    
    required_columns = {'id', 'media_id', 'media_type', 'title', 'progress', 'duration', 'last_watched'}
    assert required_columns.issubset(columns), f"Missing columns in watch_history"

@test("Favorites table has correct schema")
def test_favorites_schema():
    db_path = Path(__file__).parent.parent / "data" / "mediahub.db"
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
    
    cursor.execute("PRAGMA table_info(favorites)")
    columns = {row[1] for row in cursor.fetchall()}
    conn.close()
    
    required_columns = {'id', 'media_id', 'media_type', 'title', 'added_at'}
    assert required_columns.issubset(columns), f"Missing columns in favorites"

# ============================================================================
# MODEL TESTS
# ============================================================================

@test("Models module can be imported")
def test_models_import():
    try:
        import models
        assert hasattr(models, 'WatchHistory'), "WatchHistory class not found"
        assert hasattr(models, 'Favorites'), "Favorites class not found"
        assert hasattr(models, 'Collections'), "Collections class not found"
        assert hasattr(models, 'Recommendations'), "Recommendations class not found"
        assert hasattr(models, 'Calendar'), "Calendar class not found"
        assert hasattr(models, 'RealDebrid'), "RealDebrid class not found"
        assert hasattr(models, 'Comics'), "Comics class not found"
    except ImportError as e:
        raise AssertionError(f"Cannot import models: {e}")

@test("WatchHistory model has required methods")
def test_watch_history_methods():
    import models
    assert hasattr(models.WatchHistory, 'add_or_update'), "add_or_update method missing"
    assert hasattr(models.WatchHistory, 'get_recent'), "get_recent method missing"
    assert hasattr(models.WatchHistory, 'get_by_media'), "get_by_media method missing"

@test("Favorites model has required methods")
def test_favorites_methods():
    import models
    assert hasattr(models.Favorites, 'add'), "add method missing"
    assert hasattr(models.Favorites, 'remove'), "remove method missing"
    assert hasattr(models.Favorites, 'get_all'), "get_all method missing"
    assert hasattr(models.Favorites, 'is_favorite'), "is_favorite method missing"

# ============================================================================
# FRONTEND TESTS
# ============================================================================

@test("Watch History page exists")
def test_watch_history_page():
    page_path = Path(__file__).parent.parent / "web" / "watch_history.html"
    assert page_path.exists(), "watch_history.html not found"
    content = page_path.read_text()
    assert '/api/watch-history' in content, "API endpoint not referenced"
    assert 'loadHistory' in content, "JavaScript function missing"

@test("Favorites page exists")
def test_favorites_page():
    page_path = Path(__file__).parent.parent / "web" / "favorites.html"
    assert page_path.exists(), "favorites.html not found"
    content = page_path.read_text()
    assert '/api/favorites' in content, "API endpoint not referenced"
    assert 'loadFavorites' in content, "JavaScript function missing"

@test("Recommendations page exists")
def test_recommendations_page():
    page_path = Path(__file__).parent.parent / "web" / "recommendations.html"
    assert page_path.exists(), "recommendations.html not found"
    content = page_path.read_text()
    assert '/api/recommendations' in content, "API endpoint not referenced"

@test("Calendar page exists")
def test_calendar_page():
    page_path = Path(__file__).parent.parent / "web" / "calendar.html"
    assert page_path.exists(), "calendar.html not found"
    content = page_path.read_text()
    assert '/api/calendar' in content, "API endpoint not referenced"

@test("Real-Debrid page exists")
def test_real_debrid_page():
    page_path = Path(__file__).parent.parent / "web" / "real_debrid.html"
    assert page_path.exists(), "real_debrid.html not found"
    content = page_path.read_text()
    assert '/api/rd/downloads' in content, "API endpoint not referenced"

@test("Comics page exists")
def test_comics_page():
    page_path = Path(__file__).parent.parent / "web" / "comics.html"
    assert page_path.exists(), "comics.html not found"
    content = page_path.read_text()
    assert '/api/comics' in content, "API endpoint not referenced"

# ============================================================================
# API ROUTES TESTS
# ============================================================================

@test("Frontend API routes file exists")
def test_frontend_apis_exist():
    api_path = Path(__file__).parent.parent / "server" / "routes" / "frontend_apis.py"
    assert api_path.exists(), "frontend_apis.py not found"

@test("Frontend API routes define all endpoints")
def test_frontend_api_endpoints():
    api_path = Path(__file__).parent.parent / "server" / "routes" / "frontend_apis.py"
    content = api_path.read_text()
    
    required_routes = [
        '/api/watch-history',
        '/api/favorites',
        '/api/recommendations',
        '/api/calendar',
        '/api/rd/downloads',
        '/api/comics'
    ]
    
    for route in required_routes:
        assert route in content, f"Route {route} not defined"

# ============================================================================
# FOUR PILLARS TESTS
# ============================================================================

@test("MediaHub Home pillar exists")
def test_mediahub_home_exists():
    pillar_path = Path(__file__).parent.parent / "mediahub_home.py"
    assert pillar_path.exists(), "mediahub_home.py not found"

@test("Text Editor pillar exists")
def test_text_editor_exists():
    pillar_path = Path(__file__).parent.parent / "text_editor.py"
    assert pillar_path.exists(), "text_editor.py not found"

@test("Downloader pillar exists")
def test_downloader_exists():
    pillar_path = Path(__file__).parent.parent / "downloader.py"
    assert pillar_path.exists(), "downloader.py not found"

@test("Real-Debrid Manager pillar exists")
def test_rd_manager_exists():
    pillar_path = Path(__file__).parent.parent / "real_debrid_manager.py"
    assert pillar_path.exists(), "real_debrid_manager.py not found"

# ============================================================================
# INTEGRATION TESTS
# ============================================================================

@test("Can create watch history entry")
def test_create_watch_history():
    import models
    try:
        models.WatchHistory.add_or_update(
            'test_movie_123',
            'movie',
            'Test Movie',
            progress=300,
            duration=6000
        )
        # Verify it was added
        entry = models.WatchHistory.get_by_media('test_movie_123')
        assert entry is not None, "Watch history entry not created"
        assert entry['title'] == 'Test Movie', "Title mismatch"
    except Exception as e:
        raise AssertionError(f"Failed to create watch history: {e}")

@test("Can add and remove favorite")
def test_favorite_operations():
    import models
    try:
        # Add favorite
        success = models.Favorites.add('test_fav_123', 'movie', 'Test Favorite')
        assert success, "Failed to add favorite"
        
        # Check if favorite
        is_fav = models.Favorites.is_favorite('test_fav_123')
        assert is_fav, "Favorite not found after adding"
        
        # Remove favorite
        models.Favorites.remove('test_fav_123')
        is_fav = models.Favorites.is_favorite('test_fav_123')
        assert not is_fav, "Favorite still exists after removal"
    except Exception as e:
        raise AssertionError(f"Favorite operations failed: {e}")

@test("Can create collection")
def test_create_collection():
    import models
    try:
        collection_id = models.Collections.create('Test Collection', 'Test description')
        assert collection_id is not None, "Collection not created"
        
        # Add item to collection
        models.Collections.add_item(collection_id, 'test_media_123', 'movie', 'Test Movie')
        
        # Get collection items
        items = models.Collections.get_items(collection_id)
        assert len(items) > 0, "Collection items not retrieved"
    except Exception as e:
        raise AssertionError(f"Collection operations failed: {e}")

# ============================================================================
# FILE STRUCTURE TESTS
# ============================================================================

@test("Server directory exists")
def test_server_directory():
    server_path = Path(__file__).parent.parent / "server"
    assert server_path.exists(), "server directory not found"

@test("Web directory exists")
def test_web_directory():
    web_path = Path(__file__).parent.parent / "web"
    assert web_path.exists(), "web directory not found"

@test("Data directory exists")
def test_data_directory():
    data_path = Path(__file__).parent.parent / "data"
    assert data_path.exists(), "data directory not found"

@test("Routes directory exists")
def test_routes_directory():
    routes_path = Path(__file__).parent.parent / "server" / "routes"
    assert routes_path.exists(), "server/routes directory not found"

@test("HTML pages count")
def test_html_pages_count():
    web_path = Path(__file__).parent.parent / "web"
    html_files = list(web_path.rglob("*.html"))  # Use rglob to search recursively
    assert len(html_files) >= 108, f"Expected at least 108 HTML pages, found {len(html_files)}"

# ============================================================================
# RUN ALL TESTS
# ============================================================================

def run_all_tests():
    """Run all tests and generate report"""
    print("="*80)
    print("MEDIAHUB COMPREHENSIVE TEST SUITE")
    print("="*80)
    print()
    
    print("Running Database Tests...")
    test_database_exists()
    test_database_tables()
    test_watch_history_schema()
    test_favorites_schema()
    print()
    
    print("Running Model Tests...")
    test_models_import()
    test_watch_history_methods()
    test_favorites_methods()
    print()
    
    print("Running Frontend Tests...")
    test_watch_history_page()
    test_favorites_page()
    test_recommendations_page()
    test_calendar_page()
    test_real_debrid_page()
    test_comics_page()
    print()
    
    print("Running API Tests...")
    test_frontend_apis_exist()
    test_frontend_api_endpoints()
    print()
    
    print("Running Four Pillars Tests...")
    test_mediahub_home_exists()
    test_text_editor_exists()
    test_downloader_exists()
    test_rd_manager_exists()
    print()
    
    print("Running Integration Tests...")
    test_create_watch_history()
    test_favorite_operations()
    test_create_collection()
    print()
    
    print("Running File Structure Tests...")
    test_server_directory()
    test_web_directory()
    test_data_directory()
    test_routes_directory()
    test_html_pages_count()
    print()
    
    # Print summary
    print("="*80)
    print("TEST SUMMARY")
    print("="*80)
    print(f"Total Tests: {test_results['total']}")
    print(f"Passed: {test_results['passed']} ✅")
    print(f"Failed: {test_results['failed']} ❌")
    print(f"Success Rate: {(test_results['passed']/test_results['total']*100):.1f}%")
    print()
    
    if test_results['failed'] > 0:
        print("FAILED TESTS:")
        for test in test_results['tests']:
            if test['status'] != 'PASS':
                print(f"  ❌ {test['name']}: {test['error']}")
        print()
    
    # Save results
    results_path = Path(__file__).parent.parent / "test_results.json"
    with open(results_path, 'w') as f:
        json.dump(test_results, f, indent=2)
    
    print(f"✅ Test results saved to: {results_path}")
    
    return test_results['passed'] == test_results['total']

if __name__ == '__main__':
    success = run_all_tests()
    sys.exit(0 if success else 1)
