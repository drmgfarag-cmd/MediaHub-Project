#!/usr/bin/env python3
"""
Test that newly registered routes can be imported
"""

import sys
import os

# Add server directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'server'))

print("=" * 80)
print("Testing Route Imports - Batch 1 (Critical Routes)")
print("=" * 80)
print()

routes_to_test = [
    # Batch 1
    ('routes.audio_player', 'ap_bp'),
    ('routes.discovery', 'disc_bp'),
    ('routes.discovery_advanced', 'discovery_advanced_bp'),
    ('routes.toplists', 'tl_bp'),
    # Batch 2
    ('routes.audio_playlists', 'mix_bp'),
    ('routes.audio_replaygain', 'rg_bp'),
    ('routes.audio_settings', 'aset_bp'),
    ('routes.collections_api', 'coll_bp'),
    ('routes.collections_manage', 'col_bp'),
    ('routes.collections_timeline', 'timeline_bp'),
    ('routes.library_scan', 'scan_bp'),
    ('routes.media_collections', 'col_bp'),
]

success_count = 0
fail_count = 0

for module_name, bp_name in routes_to_test:
    try:
        module = __import__(module_name, fromlist=[bp_name])
        bp = getattr(module, bp_name)
        print(f"✅ {module_name}.{bp_name} - OK")
        print(f"   Blueprint name: {bp.name}")
        print(f"   URL prefix: {getattr(bp, 'url_prefix', 'None')}")
        success_count += 1
    except Exception as e:
        print(f"❌ {module_name}.{bp_name} - FAILED")
        print(f"   Error: {e}")
        fail_count += 1
    print()

print("=" * 80)
print(f"Results: {success_count} passed, {fail_count} failed")
print("=" * 80)

sys.exit(0 if fail_count == 0 else 1)
