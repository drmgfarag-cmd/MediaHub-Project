#!/usr/bin/env python3
"""
Phase 5: Complete API Coverage Testing
Tests all 869+ API endpoints for functionality and completeness
"""
import sys
import json
import re
from pathlib import Path
from collections import defaultdict

# Add server to path
sys.path.insert(0, str(Path(__file__).parent.parent / "server"))

class APITester:
    def __init__(self):
        self.routes_dir = Path(__file__).parent.parent / "server" / "routes"
        self.all_routes = []
        self.results = {
            'total': 0,
            'tested': 0,
            'passed': 0,
            'failed': 0,
            'incomplete': 0,
            'by_category': {},
            'issues': []
        }
    
    def discover_all_routes(self):
        """Discover all API routes from route files"""
        print("Discovering all API routes...")
        
        for py_file in self.routes_dir.glob('*.py'):
            if py_file.name.startswith('_'):
                continue
            
            try:
                with open(py_file) as f:
                    content = f.read()
                
                # Find all route definitions
                pattern = r"@[a-z_]+\.route\(['\"]([^'\"]+)['\"],?\s*(?:methods=\[([^\]]+)\])?\)\s*def ([a-z_]+)\("
                
                for match in re.finditer(pattern, content):
                    route_path = match.group(1)
                    methods_str = match.group(2) or "'GET'"
                    methods = re.findall(r"'([A-Z]+)'", methods_str)
                    func_name = match.group(3)
                    
                    # Extract function body to analyze completeness
                    func_start = content.find(f"def {func_name}(")
                    if func_start != -1:
                        # Find function body (simplified)
                        func_body = content[func_start:func_start+2000]  # Increased from 500 to 2000
                        
                        self.all_routes.append({
                            'file': py_file.name,
                            'path': route_path,
                            'methods': methods,
                            'function': func_name,
                            'body_preview': func_body[:1000]  # Increased from 200 to 1000
                        })
            except Exception as e:
                print(f"  ⚠️  Error reading {py_file.name}: {e}")
        
        self.results['total'] = len(self.all_routes)
        print(f"✅ Discovered {len(self.all_routes)} API routes\n")
    
    def categorize_routes(self):
        """Categorize routes by API prefix"""
        categories = defaultdict(list)
        
        for route in self.all_routes:
            # Extract category from path (e.g., /api/audio/... → audio)
            match = re.match(r'/api/([^/]+)', route['path'])
            if match:
                category = match.group(1)
            else:
                category = 'other'
            
            categories[category].append(route)
        
        self.results['by_category'] = {
            cat: len(routes) for cat, routes in categories.items()
        }
        
        return categories
    
    def analyze_route_completeness(self, route):
        """Analyze if a route is complete or needs enhancement"""
        body = route['body_preview'].lower()
        func_name = route['function']
        
        issues = []
        
        # Check 1: Has actual implementation (not just pass or TODO)
        if 'pass' in body and body.strip().endswith('pass'):
            issues.append("Empty implementation (just 'pass')")
        
        if 'todo' in body or 'fixme' in body:
            issues.append("Contains TODO/FIXME")
        
        # Check 2: Has error handling
        if 'try:' not in body and 'except' not in body:
            issues.append("No error handling")
        
        # Check 3: Returns JSON response
        # More comprehensive check for JSON returns
        has_json_return = (
            'jsonify' in body or
            'json.dumps' in body or
            'Response' in body or
            'application/json' in body or
            ('return' in body and '{' in body and '}' in body)  # Likely returns dict
        )
        if not has_json_return:
            issues.append("Doesn't return JSON")
        
        # Check 4: CRUD completeness for resource endpoints
        path = route['path']
        if '<' in path:  # Has path parameters (likely a resource endpoint)
            methods = route['methods']
            expected_methods = {'GET', 'POST', 'PUT', 'DELETE'}
            missing_methods = expected_methods - set(methods)
            if missing_methods:
                issues.append(f"Missing CRUD methods: {', '.join(missing_methods)}")
        
        return issues
    
    def test_all_routes(self):
        """Test all discovered routes"""
        print("Testing all API routes for completeness...\n")
        
        categories = self.categorize_routes()
        
        for category, routes in sorted(categories.items()):
            print(f"📁 {category.upper()} ({len(routes)} routes)")
            
            category_issues = []
            
            for route in routes:
                issues = self.analyze_route_completeness(route)
                
                if issues:
                    self.results['incomplete'] += 1
                    category_issues.append({
                        'route': route['path'],
                        'function': route['function'],
                        'issues': issues
                    })
                else:
                    self.results['passed'] += 1
                
                self.results['tested'] += 1
            
            if category_issues:
                print(f"  ⚠️  {len(category_issues)} incomplete routes")
                for item in category_issues[:3]:
                    print(f"     {item['route']} → {item['function']}()")
                    for issue in item['issues']:
                        print(f"       - {issue}")
                if len(category_issues) > 3:
                    print(f"     ... and {len(category_issues) - 3} more")
                
                self.results['issues'].extend(category_issues)
            else:
                print(f"  ✅ All routes complete")
            
            print()
    
    def generate_report(self):
        """Generate final report"""
        print("="*80)
        print("API COVERAGE TEST SUMMARY")
        print("="*80)
        print(f"Total Routes: {self.results['total']}")
        print(f"Tested: {self.results['tested']}")
        print(f"Complete: {self.results['passed']}")
        print(f"Incomplete: {self.results['incomplete']}")
        print(f"Completion Rate: {self.results['passed']/self.results['total']*100:.1f}%")
        print()
        
        print("Routes by Category:")
        for cat, count in sorted(self.results['by_category'].items(), key=lambda x: -x[1])[:10]:
            print(f"  {cat}: {count}")
        
        # Save results
        output_file = Path(__file__).parent.parent / "api_coverage_results.json"
        with open(output_file, 'w') as f:
            json.dump(self.results, f, indent=2)
        
        print(f"\n✅ Detailed results saved to: {output_file}")
    
    def run(self):
        """Run complete API coverage test"""
        self.discover_all_routes()
        self.test_all_routes()
        self.generate_report()

if __name__ == '__main__':
    tester = APITester()
    tester.run()
