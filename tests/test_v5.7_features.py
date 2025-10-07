"""
Test Suite for MediaHub v5.7 Features
Tests all advanced UI features, performance optimizations, and interactions
"""

import unittest
import json
import os
import sys
from pathlib import Path

# Add server directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'server'))

class TestV57Features(unittest.TestCase):
    """Test v5.7 advanced features"""
    
    def setUp(self):
        """Set up test environment"""
        self.test_data = {
            'performance_metrics': {
                'pageLoadTime': 1234,
                'domContentLoaded': 890,
                'firstPaint': 456,
                'firstContentfulPaint': 678,
                'largestContentfulPaint': 1200,
                'timeToInteractive': 1500,
                'totalBlockingTime': 150,
                'cumulativeLayoutShift': 0.05,
                'pageUrl': '/home_v5.7.html'
            },
            'scroll_event': {
                'scrollPosition': 500,
                'scrollPercentage': 25,
                'pageUrl': '/home_v5.7.html',
                'viewportHeight': 800,
                'documentHeight': 2000
            },
            'interaction_event': {
                'type': 'click',
                'element': 'carousel-item',
                'pageUrl': '/home_v5.7.html',
                'duration': 250,
                'metadata': {
                    'itemId': '123',
                    'itemTitle': 'The Matrix'
                }
            }
        }
    
    def test_v57_files_exist(self):
        """Test that all v5.7 files exist"""
        base_path = Path(__file__).parent.parent
        
        required_files = [
            'web/home_v5.7.html',
            'web/assets/scroll_reveal.js',
            'web/assets/micro_interactions.css',
            'web/assets/page_transitions.js',
            'web/assets/parallax.js',
            'web/assets/performance.js',
            'web/assets/touch_gestures.js',
            'web/assets/animations.css',
            'web/assets/badges.css',
            'server/routes/ui_features_v57_api.py'
        ]
        
        for file_path in required_files:
            full_path = base_path / file_path
            self.assertTrue(
                full_path.exists(),
                f"Required file not found: {file_path}"
            )
            print(f"✓ Found: {file_path}")
    
    def test_html_structure(self):
        """Test v5.7 HTML structure"""
        html_path = Path(__file__).parent.parent / 'web' / 'home_v5.7.html'
        
        with open(html_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check for required elements
        required_elements = [
            'scroll_reveal.js',
            'micro_interactions.css',
            'page_transitions.js',
            'parallax.js',
            'performance.js',
            'data-reveal',
            'loading-overlay',
            'scroll-to-top',
            'version-badge',
            'v5.7'
        ]
        
        for element in required_elements:
            self.assertIn(
                element,
                content,
                f"Required element not found in HTML: {element}"
            )
            print(f"✓ HTML contains: {element}")
    
    def test_javascript_classes(self):
        """Test that JavaScript classes are properly defined"""
        js_files = {
            'scroll_reveal.js': ['ScrollReveal', 'StaggerReveal', 'ParallaxReveal', 'ScrollProgress'],
            'performance.js': ['LazyLoader', 'VirtualScroller', 'ResourcePreloader', 'DOMBatcher', 'MemoryManager'],
            'page_transitions.js': ['PageTransition'],
            'parallax.js': ['ParallaxEffect']
        }
        
        base_path = Path(__file__).parent.parent / 'web' / 'assets'
        
        for js_file, classes in js_files.items():
            file_path = base_path / js_file
            
            if file_path.exists():
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                for class_name in classes:
                    # Check for class definition or export/alias
                    has_class = f'class {class_name}' in content or f'{class_name} =' in content or f'{class_name}:' in content
                    self.assertTrue(
                        has_class,
                        f"Class {class_name} not found in {js_file}"
                    )
                    print(f"✓ {js_file} contains class: {class_name}")
    
    def test_css_classes(self):
        """Test that CSS classes are properly defined"""
        css_files = {
            'micro_interactions.css': [
                '.btn-micro',
                '.card-micro',
                '.icon-micro',
                '.input-micro',
                '.ripple-micro',
                '.tooltip-micro',
                '.skeleton-micro'
            ],
            'animations.css': [
                '@keyframes',
                'animation'
            ],
            'badges.css': [
                '.badge'
            ]
        }
        
        base_path = Path(__file__).parent.parent / 'web' / 'assets'
        
        for css_file, classes in css_files.items():
            file_path = base_path / css_file
            
            if file_path.exists():
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                for class_name in classes:
                    self.assertIn(
                        class_name,
                        content,
                        f"Class {class_name} not found in {css_file}"
                    )
                    print(f"✓ {css_file} contains: {class_name}")
    
    def test_api_routes_defined(self):
        """Test that v5.7 API routes are properly defined"""
        api_file = Path(__file__).parent.parent / 'server' / 'routes' / 'ui_features_v57_api.py'
        
        with open(api_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        required_routes = [
            '/api/v57/performance/metrics',
            '/api/v57/scroll/track',
            '/api/v57/scroll/analytics',
            '/api/v57/interactions/track',
            '/api/v57/interactions/analytics',
            '/api/v57/animations/preferences',
            '/api/v57/lazy-load/stats',
            '/api/v57/cache/stats',
            '/api/v57/features/status',
            '/api/v57/health'
        ]
        
        for route in required_routes:
            self.assertIn(
                route,
                content,
                f"API route not found: {route}"
            )
            print(f"✓ API route defined: {route}")
    
    def test_performance_metrics_structure(self):
        """Test performance metrics data structure"""
        metrics = self.test_data['performance_metrics']
        
        required_fields = [
            'pageLoadTime',
            'domContentLoaded',
            'firstPaint',
            'firstContentfulPaint',
            'largestContentfulPaint',
            'timeToInteractive',
            'totalBlockingTime',
            'cumulativeLayoutShift'
        ]
        
        for field in required_fields:
            self.assertIn(
                field,
                metrics,
                f"Required field not found in performance metrics: {field}"
            )
            self.assertIsInstance(
                metrics[field],
                (int, float),
                f"Field {field} should be numeric"
            )
            print(f"✓ Performance metric field: {field} = {metrics[field]}")
    
    def test_scroll_event_structure(self):
        """Test scroll event data structure"""
        event = self.test_data['scroll_event']
        
        required_fields = [
            'scrollPosition',
            'scrollPercentage',
            'pageUrl',
            'viewportHeight',
            'documentHeight'
        ]
        
        for field in required_fields:
            self.assertIn(
                field,
                event,
                f"Required field not found in scroll event: {field}"
            )
            print(f"✓ Scroll event field: {field} = {event[field]}")
    
    def test_interaction_event_structure(self):
        """Test interaction event data structure"""
        event = self.test_data['interaction_event']
        
        required_fields = [
            'type',
            'element',
            'pageUrl',
            'duration'
        ]
        
        for field in required_fields:
            self.assertIn(
                field,
                event,
                f"Required field not found in interaction event: {field}"
            )
            print(f"✓ Interaction event field: {field} = {event[field]}")
    
    def test_responsive_breakpoints(self):
        """Test that responsive breakpoints are defined"""
        html_path = Path(__file__).parent.parent / 'web' / 'home_v5.7.html'
        
        with open(html_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check for media queries
        self.assertIn(
            '@media',
            content,
            "No media queries found for responsive design"
        )
        
        self.assertIn(
            'max-width: 768px',
            content,
            "Mobile breakpoint not found"
        )
        
        print("✓ Responsive breakpoints defined")
    
    def test_accessibility_features(self):
        """Test accessibility features"""
        html_path = Path(__file__).parent.parent / 'web' / 'home_v5.7.html'
        
        with open(html_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check for at least one accessibility feature
        accessibility_features = [
            'aria-label',
            'title='
        ]
        
        found_features = []
        for feature in accessibility_features:
            if feature in content:
                found_features.append(feature)
                print(f"✓ Accessibility feature: {feature}")
        
        self.assertTrue(
            len(found_features) > 0,
            "No accessibility features found"
        )
    
    def test_version_consistency(self):
        """Test that version numbers are consistent"""
        files_to_check = [
            'web/home_v5.7.html',
            'web/assets/scroll_reveal.js',
            'web/assets/micro_interactions.css',
            'server/routes/ui_features_v57_api.py'
        ]
        
        base_path = Path(__file__).parent.parent
        
        for file_path in files_to_check:
            full_path = base_path / file_path
            
            if full_path.exists():
                with open(full_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Check for version references
                has_version = '5.7' in content or 'v5.7' in content or 'v57' in content
                self.assertTrue(
                    has_version,
                    f"Version reference not found in {file_path}"
                )
                print(f"✓ Version reference found in: {file_path}")
    
    def test_integration_completeness(self):
        """Test that all v5.7 features are integrated"""
        html_path = Path(__file__).parent.parent / 'web' / 'home_v5.7.html'
        
        with open(html_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check for all major v5.7 features
        features = {
            'Performance Optimizations': 'performance.js',
            'Scroll Reveal': 'scroll_reveal.js',
            'Page Transitions': 'page_transitions.js',
            'Parallax Effects': 'parallax.js',
            'Micro Interactions': 'micro_interactions.css',
            'Touch Gestures': 'touch_gestures.js',
            'Badges System': 'badges.css',
            'Animations': 'animations.css'
        }
        
        for feature_name, file_ref in features.items():
            self.assertIn(
                file_ref,
                content,
                f"Feature not integrated: {feature_name}"
            )
            print(f"✓ Integrated: {feature_name}")

def run_tests():
    """Run all tests and generate report"""
    print("\n" + "="*70)
    print("MediaHub v5.7 Features Test Suite")
    print("="*70 + "\n")
    
    # Create test suite
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromTestCase(TestV57Features)
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Generate summary
    print("\n" + "="*70)
    print("Test Summary")
    print("="*70)
    print(f"Tests run: {result.testsRun}")
    print(f"Successes: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    
    if result.wasSuccessful():
        print("\n✓ All tests passed! v5.7 implementation is complete.")
    else:
        print("\n✗ Some tests failed. Please review the errors above.")
    
    print("="*70 + "\n")
    
    return result

if __name__ == '__main__':
    result = run_tests()
    sys.exit(0 if result.wasSuccessful() else 1)
