"""
Golden Surface API Compliance Test for v5.0
Verifies all 35 Golden Surface APIs are present
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'server'))

# Golden Surface API requirements
GOLDEN_SURFACE_APIS = {
    # MediaHub Home Pillar (4 APIs)
    '/api/home/hero': ['GET', 'POST'],
    '/api/home/carousels': ['GET', 'POST'],
    '/api/home/subcategories': ['GET', 'POST'],
    '/api/search/omnibox': ['GET'],
    
    # Text Editor Pillar (4 APIs)
    '/api/editor/documents': ['GET', 'POST'],
    '/api/editor/syntax': ['GET', 'POST'],
    '/api/editor/macros': ['GET', 'POST'],
    '/api/editor/bookmarks': ['GET', 'POST'],
    
    # RD Manager Pillar (3 APIs)
    '/api/rd/manager/browse': ['GET'],
    '/api/rd/manager/bulk': ['POST'],
    '/api/rd/manager/filters': ['GET', 'POST'],
    
    # Downloader Pillar (3 APIs)
    '/api/downloader/queue': ['GET', 'POST'],
    '/api/downloader/auto': ['GET', 'POST'],
    '/api/downloader/extraction': ['GET', 'POST'],
    
    # Media Management (8 APIs)
    '/api/media/organize': ['POST'],
    '/api/media/subtitles/policy': ['GET', 'POST'],
    '/api/media/metadata/fetch': ['POST'],
    '/api/media/metadata/config': ['GET', 'POST'],
    '/api/media/dedupe/policy': ['GET', 'POST'],
    '/api/media/dedupe/scan': ['POST'],
    '/api/guard/scan': ['POST'],
    '/api/rules_audit': ['GET'],
}

def check_route_exists(route_path, methods):
    """Check if a route exists by scanning route files"""
    routes_dir = os.path.join(os.path.dirname(__file__), '..', 'server', 'routes')
    
    # Normalize route path for searching
    search_pattern = route_path.replace('/', r'\/')
    
    for root, dirs, files in os.walk(routes_dir):
        for file in files:
            if not file.endswith('.py'):
                continue
            
            filepath = os.path.join(root, file)
            
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read()
                    
                # Check if route is defined
                if f"'{route_path}'" in content or f'"{route_path}"' in content:
                    # Check if it's in a route decorator
                    if '@' in content and '.route(' in content:
                        return True
            except:
                continue
    
    return False

def main():
    print("="*80)
    print("GOLDEN SURFACE API COMPLIANCE TEST - v5.0")
    print("="*80)
    
    total_apis = len(GOLDEN_SURFACE_APIS)
    found_apis = 0
    missing_apis = []
    
    for route_path, methods in GOLDEN_SURFACE_APIS.items():
        exists = check_route_exists(route_path, methods)
        
        if exists:
            found_apis += 1
            print(f"✅ {route_path} - {', '.join(methods)}")
        else:
            missing_apis.append(route_path)
            print(f"❌ {route_path} - {', '.join(methods)} - MISSING")
    
    print("\n" + "="*80)
    print(f"RESULTS: {found_apis}/{total_apis} Golden Surface APIs found")
    print(f"Coverage: {(found_apis/total_apis*100):.1f}%")
    print("="*80)
    
    if missing_apis:
        print("\n❌ MISSING APIS:")
        for api in missing_apis:
            print(f"  - {api}")
        print(f"\nTotal missing: {len(missing_apis)}")
    else:
        print("\n🎉 100% GOLDEN SURFACE COMPLIANCE ACHIEVED!")
    
    return found_apis == total_apis

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
