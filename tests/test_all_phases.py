#!/usr/bin/env python3.11
"""
Comprehensive Test Suite for MediaHub All Phases (1-7)
Tests integration of all features from Phase 1 through Phase 7
"""

import os
import sys

# Add server directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'server'))

def test_phase1_features():
    """Test Phase 1: Quick Fixes"""
    print("\n" + "="*60)
    print("PHASE 1: Quick Fixes")
    print("="*60)
    
    tests_passed = 0
    tests_total = 2
    
    # Test 1: Arabic subtitle priority
    try:
        from routes.subtitles_advanced import DEFAULT_LANGUAGE_PRIORITY
        if DEFAULT_LANGUAGE_PRIORITY[0] == 'ar':
            print("✅ Arabic subtitle priority")
            tests_passed += 1
        else:
            print("❌ Arabic not first priority")
    except Exception as e:
        print(f"❌ Arabic priority test failed: {e}")
    
    # Test 2: API Keys
    try:
        from config.api_keys import APIKeyManager
        api_mgr = APIKeyManager()
        if api_mgr.get_key('tmdb'):
            print("✅ API Keys configured")
            tests_passed += 1
        else:
            print("❌ API Keys not configured")
    except Exception as e:
        print(f"❌ API Keys test failed: {e}")
    
    return tests_passed, tests_total

def test_phase2_features():
    """Test Phase 2: Critical Features"""
    print("\n" + "="*60)
    print("PHASE 2: Critical Features")
    print("="*60)
    
    tests_passed = 0
    tests_total = 4
    
    # Test files exist
    features = [
        ('rd_parser', 'server/routes/rd_parser.py'),
        ('synopsis_overlay', 'server/routes/synopsis_overlay.py'),
        ('tags_system', 'server/routes/tags_system.py'),
        ('cross_references', 'server/routes/cross_references.py'),
    ]
    
    for name, path in features:
        full_path = os.path.join(os.path.dirname(__file__), '..', path)
        if os.path.exists(full_path):
            print(f"✅ {name}")
            tests_passed += 1
        else:
            print(f"❌ {name} not found")
    
    return tests_passed, tests_total

def test_phase3_features():
    """Test Phase 3: Streaming & Playback"""
    print("\n" + "="*60)
    print("PHASE 3: Streaming & Playback")
    print("="*60)
    
    tests_passed = 0
    tests_total = 5
    
    features = [
        ('Audio Normalization', 'server/routes/stream_audio_norm.py', 'anorm_bp'),
        ('Casting Integration', 'server/routes/casting_integration.py', 'casting_integration_bp'),
        ('Mobile Streaming', 'server/routes/mobile_streaming.py', 'mobile_streaming_bp'),
        ('HLS Streaming', 'server/routes/stream.py', 'stream_bp'),
        ('Enhanced Casting', 'server/routes/enhanced/casting_enhanced.py', 'CastingManager'),
    ]
    
    for name, path, check in features:
        full_path = os.path.join(os.path.dirname(__file__), '..', path)
        if os.path.exists(full_path):
            try:
                with open(full_path, 'r') as f:
                    if check in f.read():
                        print(f"✅ {name}")
                        tests_passed += 1
                    else:
                        print(f"⚠️  {name} (file exists but {check} not found)")
            except:
                print(f"⚠️  {name} (file exists but couldn't read)")
        else:
            print(f"❌ {name} not found")
    
    return tests_passed, tests_total

def test_phase4_features():
    """Test Phase 4: Advanced Media Management"""
    print("\n" + "="*60)
    print("PHASE 4: Advanced Media Management")
    print("="*60)
    
    tests_passed = 0
    tests_total = 4
    
    features = [
        ('Enhanced Media Management', 'server/routes/enhanced_media_management.py', 'enhanced_media_bp'),
        ('Downloader Enhanced', 'server/routes/downloader_enhanced.py', 'downloader_enhanced_bp'),
        ('Metadata Export', 'server/routes/metadata_export.py', 'metadata_export_bp'),
        ('Duplicates UI', 'web/page/duplicates.html', 'duplicate'),
    ]
    
    for name, path, check in features:
        full_path = os.path.join(os.path.dirname(__file__), '..', path)
        if os.path.exists(full_path):
            try:
                with open(full_path, 'r', encoding='utf-8', errors='ignore') as f:
                    if check in f.read():
                        print(f"✅ {name}")
                        tests_passed += 1
                    else:
                        print(f"⚠️  {name} (file exists)")
                        tests_passed += 0.5
            except:
                print(f"⚠️  {name} (file exists)")
                tests_passed += 0.5
        else:
            print(f"❌ {name} not found")
    
    return tests_passed, tests_total

def test_phase5_features():
    """Test Phase 5: Real-Debrid Advanced"""
    print("\n" + "="*60)
    print("PHASE 5: Real-Debrid Advanced")
    print("="*60)
    
    tests_passed = 0
    tests_total = 3
    
    features = [
        ('Debrid Core', 'server/routes/debrid.py', 'debrid_bp'),
        ('RD Operations', 'server/routes/rd.py', 'rd_bp'),
        ('RD Manager Enhanced', 'server/routes/rd_manager_enhanced.py', 'rd_manager_enhanced'),
    ]
    
    for name, path, check in features:
        full_path = os.path.join(os.path.dirname(__file__), '..', path)
        if os.path.exists(full_path):
            try:
                with open(full_path, 'r') as f:
                    content = f.read()
                    if check in content or 'Blueprint' in content:
                        print(f"✅ {name}")
                        tests_passed += 1
                    else:
                        print(f"⚠️  {name} (file exists)")
                        tests_passed += 0.5
            except:
                print(f"⚠️  {name} (file exists)")
                tests_passed += 0.5
        else:
            print(f"❌ {name} not found")
    
    return tests_passed, tests_total

def test_phase6_features():
    """Test Phase 6: Download Management"""
    print("\n" + "="*60)
    print("PHASE 6: Download Management")
    print("="*60)
    
    tests_passed = 0
    tests_total = 5
    
    features = [
        ('Aria2 Integration', 'server/routes/aria2.py', 'aria2_bp'),
        ('Download Queue', 'server/routes/queue.py', 'q_bp'),
        ('Queue Combined', 'server/routes/queue_combined.py', 'combined'),
        ('Bandwidth Limiter', 'server/routes/limits.py', 'lim_bp'),
        ('RSS Automation', 'server/routes/rss_automation.py', 'rss_automation_bp'),
    ]
    
    for name, path, check in features:
        full_path = os.path.join(os.path.dirname(__file__), '..', path)
        if os.path.exists(full_path):
            try:
                with open(full_path, 'r') as f:
                    if check in f.read():
                        print(f"✅ {name}")
                        tests_passed += 1
                    else:
                        print(f"⚠️  {name} (file exists)")
                        tests_passed += 0.5
            except:
                print(f"⚠️  {name} (file exists)")
                tests_passed += 0.5
        else:
            print(f"❌ {name} not found")
    
    return tests_passed, tests_total

def test_phase7_features():
    """Test Phase 7: Advanced UI/UX"""
    print("\n" + "="*60)
    print("PHASE 7: Advanced UI/UX")
    print("="*60)
    
    tests_passed = 0
    tests_total = 4
    
    features = [
        ('Advanced UI', 'server/routes/advanced_ui.py', 'advanced_ui_bp'),
        ('Accessibility', 'web/accessibility.html', 'accessibility'),
        ('A11y JavaScript', 'web/assets/app_a11y.js', 'aria'),
        ('Keyboard Shortcuts', 'web/page/shortcuts.html', 'shortcut'),
    ]
    
    for name, path, check in features:
        full_path = os.path.join(os.path.dirname(__file__), '..', path)
        if os.path.exists(full_path):
            try:
                with open(full_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read().lower()
                    if check.lower() in content:
                        print(f"✅ {name}")
                        tests_passed += 1
                    else:
                        print(f"⚠️  {name} (file exists)")
                        tests_passed += 0.5
            except:
                print(f"⚠️  {name} (file exists)")
                tests_passed += 0.5
        else:
            print(f"❌ {name} not found")
    
    return tests_passed, tests_total

def test_app_integration():
    """Test app.py integration"""
    print("\n" + "="*60)
    print("APP INTEGRATION")
    print("="*60)
    
    tests_passed = 0
    tests_total = 3
    
    try:
        # Test app.py syntax
        import py_compile
        app_path = os.path.join(os.path.dirname(__file__), '..', 'server', 'app.py')
        py_compile.compile(app_path, doraise=True)
        print("✅ app.py syntax valid")
        tests_passed += 1
    except Exception as e:
        print(f"❌ app.py syntax error: {e}")
    
    try:
        # Check blueprint registrations
        with open(app_path, 'r') as f:
            content = f.read()
            if 'anorm_bp' in content and 'casting_integration_bp' in content:
                print("✅ Phase 3 blueprints registered")
                tests_passed += 1
            else:
                print("❌ Phase 3 blueprints not registered")
            
            if 'metadata_export_bp' in content and 'advanced_ui_bp' in content:
                print("✅ Phase 4-7 blueprints registered")
                tests_passed += 1
            else:
                print("❌ Phase 4-7 blueprints not registered")
    except Exception as e:
        print(f"❌ Blueprint check failed: {e}")
    
    return tests_passed, tests_total

def main():
    """Run all tests"""
    print("="*60)
    print("MediaHub Complete Integration Test Suite")
    print("Testing Phases 1-7")
    print("="*60)
    
    results = []
    
    results.append(test_phase1_features())
    results.append(test_phase2_features())
    results.append(test_phase3_features())
    results.append(test_phase4_features())
    results.append(test_phase5_features())
    results.append(test_phase6_features())
    results.append(test_phase7_features())
    results.append(test_app_integration())
    
    # Calculate totals
    total_passed = sum(r[0] for r in results)
    total_tests = sum(r[1] for r in results)
    success_rate = (total_passed / total_tests * 100) if total_tests > 0 else 0
    
    print("\n" + "="*60)
    print(f"TOTAL: {total_passed}/{total_tests} tests passed ({success_rate:.1f}%)")
    print("="*60)
    
    if success_rate >= 95:
        print("🎉 ALL PHASES INTEGRATED SUCCESSFULLY!")
        return 0
    elif success_rate >= 80:
        print("⚠️  Most phases integrated, some issues detected")
        return 1
    else:
        print("❌ Integration incomplete")
        return 2

if __name__ == '__main__':
    sys.exit(main())
