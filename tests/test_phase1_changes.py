#!/usr/bin/env python3.11
"""
Phase 1 Verification Test
Tests Arabic subtitle priority and API keys configuration
"""

import sys
import os
import json

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

def test_arabic_subtitle_priority():
    """Test that Arabic is prioritized over English in subtitle configuration"""
    print("\n=== Testing Arabic Subtitle Priority ===")
    
    try:
        # Import the function
        from server.routes.subtitles_advanced import _load_config
        
        # Load config
        config = _load_config()
        
        # Check priority
        priority = config.get('global_priority', [])
        
        print(f"Current priority: {priority}")
        
        if priority[0] == 'ar' and priority[1] == 'en':
            print("✅ PASS: Arabic is prioritized first, then English")
            return True
        else:
            print(f"❌ FAIL: Expected ['ar', 'en'], got {priority}")
            return False
            
    except Exception as e:
        print(f"❌ ERROR: {e}")
        return False

def test_api_keys_configuration():
    """Test that all 9 API keys are properly configured"""
    print("\n=== Testing API Keys Configuration ===")
    
    expected_keys = {
        'real_debrid': 'HMPNSB7QFO4RL2DCIKRRPKFKLKBIR7LSWWUOVNDAADNHOTC2SAXA',
        'tmdb': '3aca2154c1d9223036904a86202897ba',
        'google_books': 'AIzaSyA8OHWm7_imDTRCAEvC7rja2NZCInTw3d8',
        'tvdb': '72f8b186-1eb8-471d-94e7-85063cf7a1bf',
        'discogs': 'DlYcCvjWkCSKwuoxWznBrUDFitmPFTqBpIuoqizm',
        'acoustid': 'W48qHR6eir',
        'omdb': '95b991d3',
        'anilist_client_id': '30444',
        'anilist_client_secret': 'dc63l21fPbnvgpx7Qinlg9miT5ismqUu77oVSTj2'
    }
    
    try:
        # Check JSON file
        json_path = 'data/api_keys.json'
        if os.path.exists(json_path):
            with open(json_path, 'r') as f:
                actual_keys = json.load(f)
            
            print(f"Found {len(actual_keys)} keys in {json_path}")
            
            all_match = True
            for service, expected_key in expected_keys.items():
                actual_key = actual_keys.get(service)
                if actual_key == expected_key:
                    print(f"  ✅ {service}: Configured correctly")
                else:
                    print(f"  ❌ {service}: Mismatch or missing")
                    all_match = False
            
            if all_match:
                print("\n✅ PASS: All 9 API keys are correctly configured")
                return True
            else:
                print("\n❌ FAIL: Some API keys are missing or incorrect")
                return False
        else:
            print(f"❌ FAIL: {json_path} does not exist")
            return False
            
    except Exception as e:
        print(f"❌ ERROR: {e}")
        return False

def test_api_key_manager():
    """Test that APIKeyManager class initializes correctly"""
    print("\n=== Testing APIKeyManager Class ===")
    
    try:
        from server.config.api_keys import APIKeyManager
        
        # Initialize manager
        manager = APIKeyManager()
        
        # Check that all keys are loaded
        services = manager.get_all_services()
        
        configured_count = sum(1 for s in services.values() if s['configured'])
        
        print(f"APIKeyManager initialized successfully")
        print(f"Configured services: {configured_count}/15 total services")
        
        # Check our 9 required services
        required_services = [
            'real_debrid', 'tmdb', 'google_books', 'tvdb', 
            'discogs', 'acoustid', 'omdb', 
            'anilist_client_id', 'anilist_client_secret'
        ]
        
        all_configured = True
        for service in required_services:
            if services[service]['configured']:
                print(f"  ✅ {service}: {services[service]['masked_key']}")
            else:
                print(f"  ❌ {service}: Not configured")
                all_configured = False
        
        if all_configured:
            print("\n✅ PASS: APIKeyManager has all required keys")
            return True
        else:
            print("\n❌ FAIL: Some required keys are missing")
            return False
            
    except Exception as e:
        print(f"❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all Phase 1 verification tests"""
    print("=" * 60)
    print("PHASE 1 VERIFICATION TEST SUITE")
    print("=" * 60)
    
    results = []
    
    # Test 1: Arabic subtitle priority
    results.append(("Arabic Subtitle Priority", test_arabic_subtitle_priority()))
    
    # Test 2: API keys configuration
    results.append(("API Keys Configuration", test_api_keys_configuration()))
    
    # Test 3: APIKeyManager class
    results.append(("APIKeyManager Class", test_api_key_manager()))
    
    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {test_name}")
    
    print(f"\nTotal: {passed}/{total} tests passed ({passed/total*100:.1f}%)")
    
    if passed == total:
        print("\n🎉 ALL TESTS PASSED - Phase 1 Complete!")
        return 0
    else:
        print(f"\n⚠️  {total - passed} test(s) failed")
        return 1

if __name__ == '__main__':
    sys.exit(main())
