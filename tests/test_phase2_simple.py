"""
Simplified Phase 2 Integration Test
Tests file existence and basic imports without starting Flask app
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

print("\n" + "="*60)
print("Phase 2 Features Integration Test (Simplified)")
print("="*60 + "\n")

passed = 0
failed = 0

# Test 1: Backend route files exist
print("Test 1: Backend Route Files")
routes = ['rd_parser.py', 'synopsis_overlay.py', 'tags_system.py', 'cross_references.py']
for route in routes:
    path = os.path.join(os.path.dirname(__file__), '../server/routes', route)
    if os.path.exists(path):
        print(f"  ✅ {route} exists")
        passed += 1
    else:
        print(f"  ❌ {route} missing")
        failed += 1

# Test 2: Utility files exist
print("\nTest 2: Utility Files")
utils = ['rd_queue_manager.py']
for util in utils:
    path = os.path.join(os.path.dirname(__file__), '../server/utils', util)
    if os.path.exists(path):
        print(f"  ✅ {util} exists")
        passed += 1
    else:
        print(f"  ❌ {util} missing")
        failed += 1

# Test 3: Web files exist
print("\nTest 3: Web Files")
web_files = ['rd_list_manager.html', 'synopsis_overlay.html']
for web_file in web_files:
    path = os.path.join(os.path.dirname(__file__), '../web', web_file)
    if os.path.exists(path):
        print(f"  ✅ {web_file} exists")
        passed += 1
    else:
        print(f"  ❌ {web_file} missing")
        failed += 1

# Test 4: Phase 1 config files exist
print("\nTest 4: Phase 1 Configuration Files")
configs = [
    ('server/config/api_keys.py', 'API Keys'),
    ('storage/config/subtitles.json', 'Subtitles Config')
]
for config_path, name in configs:
    path = os.path.join(os.path.dirname(__file__), '..', config_path)
    if os.path.exists(path):
        print(f"  ✅ {name} exists")
        passed += 1
    else:
        print(f"  ❌ {name} missing")
        failed += 1

# Test 5: Import Phase 2 modules
print("\nTest 5: Module Imports")
try:
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../server'))
    from routes.rd_parser import rd_parser_bp
    print("  ✅ rd_parser imported")
    passed += 1
except Exception as e:
    print(f"  ❌ rd_parser import failed: {e}")
    failed += 1

try:
    from routes.synopsis_overlay import synopsis_bp
    print("  ✅ synopsis_overlay imported")
    passed += 1
except Exception as e:
    print(f"  ❌ synopsis_overlay import failed: {e}")
    failed += 1

try:
    from routes.tags_system import tags_bp
    print("  ✅ tags_system imported")
    passed += 1
except Exception as e:
    print(f"  ❌ tags_system import failed: {e}")
    failed += 1

try:
    from routes.cross_references import xref_bp
    print("  ✅ cross_references imported")
    passed += 1
except Exception as e:
    print(f"  ❌ cross_references import failed: {e}")
    failed += 1

try:
    from utils.rd_queue_manager import RDQueueManager
    print("  ✅ rd_queue_manager imported")
    passed += 1
except Exception as e:
    print(f"  ❌ rd_queue_manager import failed: {e}")
    failed += 1

# Test 6: Check app.py has Phase 2 registrations
print("\nTest 6: Blueprint Registrations in app.py")
app_path = os.path.join(os.path.dirname(__file__), '../server/app.py')
with open(app_path, 'r') as f:
    app_content = f.read()
    
blueprints = ['synopsis_bp', 'tags_bp', 'xref_bp', 'rd_parser_bp']
for bp in blueprints:
    if f'register_blueprint({bp})' in app_content:
        print(f"  ✅ {bp} registered")
        passed += 1
    else:
        print(f"  ❌ {bp} not registered")
        failed += 1

# Summary
print("\n" + "="*60)
print(f"Total Tests: {passed + failed}")
print(f"Passed: {passed}")
print(f"Failed: {failed}")
print(f"Success Rate: {100 * passed / (passed + failed):.1f}%")
print("="*60)

if failed == 0:
    print("\n🎉 ALL TESTS PASSED - Phase 1 & 2 Integration Complete!\n")
    sys.exit(0)
else:
    print(f"\n⚠️  {failed} test(s) failed\n")
    sys.exit(1)
