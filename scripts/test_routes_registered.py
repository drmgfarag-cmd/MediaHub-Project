#!/usr/bin/env python3
"""Test that all routes are properly registered"""

import sys
sys.path.insert(0, 'server')

print("Testing route registration...")
print("=" * 60)

# Test imports
try:
    from app import create_app
    print("✅ App module imported successfully")
except Exception as e:
    print(f"❌ Failed to import app: {e}")
    sys.exit(1)

# Create app instance
try:
    app_instance = create_app()
    print("✅ App instance created successfully")
except Exception as e:
    print(f"❌ Failed to create app: {e}")
    sys.exit(1)

# Check registered routes
try:
    app = app_instance.app
    routes = []
    for rule in app.url_map.iter_rules():
        if rule.endpoint != 'static':
            routes.append({
                'endpoint': rule.endpoint,
                'methods': ','.join(rule.methods - {'HEAD', 'OPTIONS'}),
                'path': str(rule)
            })
    
    print(f"\n✅ Total routes registered: {len(routes)}")
    print("\nSample routes:")
    for route in sorted(routes, key=lambda x: x['path'])[:20]:
        print(f"  {route['methods']:12} {route['path']}")
    
    print(f"\n... and {len(routes) - 20} more routes")
    
    # Check for specific important routes
    important_endpoints = [
        'discovery',
        'audio_player',
        'mobile_streaming',
        'casting_integration',
        'tags_system',
        'toplists'
    ]
    
    print("\n" + "=" * 60)
    print("Checking important endpoints:")
    registered_endpoints = {r['endpoint'].split('.')[0] for r in routes}
    
    for endpoint in important_endpoints:
        if endpoint in registered_endpoints:
            print(f"  ✅ {endpoint}")
        else:
            print(f"  ❌ {endpoint} NOT FOUND")
    
    print("\n" + "=" * 60)
    print("✅ Route registration test complete!")
    
except Exception as e:
    print(f"❌ Error checking routes: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
