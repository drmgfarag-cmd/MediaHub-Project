#!/usr/bin/env python3
"""
Route Registration Script for MediaHub
Analyzes all route files and generates registration code
"""

import os
import re
from pathlib import Path
from typing import List, Dict, Tuple

# Base directory
BASE_DIR = Path(__file__).parent.parent
ROUTES_DIR = BASE_DIR / "server" / "routes"
APP_PY = BASE_DIR / "server" / "app.py"
INVENTORY_DIR = BASE_DIR / "docs" / "inventory"

def extract_blueprint_info(route_file: Path) -> Tuple[str, str, str]:
    """
    Extract blueprint name and variable from a route file
    Returns: (blueprint_var, blueprint_name, url_prefix)
    """
    try:
        content = route_file.read_text(encoding='utf-8', errors='ignore')
        
        # Look for Blueprint definition
        # Pattern: variable_name = Blueprint('name', __name__)
        blueprint_pattern = r'(\w+)\s*=\s*Blueprint\([\'"]([^\'"]+)[\'"]'
        match = re.search(blueprint_pattern, content)
        
        if match:
            var_name = match.group(1)
            bp_name = match.group(2)
            
            # Try to determine URL prefix from routes or name
            url_prefix = f"/{bp_name.replace('_', '-')}"
            
            return (var_name, bp_name, url_prefix)
        
        return (None, None, None)
    except Exception as e:
        print(f"Error reading {route_file.name}: {e}")
        return (None, None, None)

def scan_all_routes() -> List[Dict]:
    """Scan all route files and extract blueprint info"""
    routes = []
    
    if not ROUTES_DIR.exists():
        print(f"Error: Routes directory not found: {ROUTES_DIR}")
        return routes
    
    # Get all Python files in routes directory
    route_files = sorted(ROUTES_DIR.glob("*.py"))
    
    for route_file in route_files:
        if route_file.name.startswith('__'):
            continue
            
        var_name, bp_name, url_prefix = extract_blueprint_info(route_file)
        
        if var_name and bp_name:
            routes.append({
                'file': route_file.name,
                'module': route_file.stem,
                'var_name': var_name,
                'bp_name': bp_name,
                'url_prefix': url_prefix,
                'import_statement': f"from routes.{route_file.stem} import {var_name}",
                'register_statement': f"app.register_blueprint({var_name}, url_prefix='{url_prefix}')"
            })
        else:
            # File exists but no blueprint found
            routes.append({
                'file': route_file.name,
                'module': route_file.stem,
                'var_name': None,
                'bp_name': None,
                'url_prefix': None,
                'import_statement': f"# TODO: Check routes.{route_file.stem} - no blueprint found",
                'register_statement': None
            })
    
    return routes

def get_currently_registered() -> List[str]:
    """Get list of currently registered blueprints from app.py"""
    registered = []
    
    if not APP_PY.exists():
        print(f"Error: app.py not found: {APP_PY}")
        return registered
    
    content = APP_PY.read_text(encoding='utf-8', errors='ignore')
    
    # Find all register_blueprint calls
    pattern = r'app\.register_blueprint\((\w+)'
    matches = re.findall(pattern, content)
    registered.extend(matches)
    
    # Also check for self.app.register_blueprint
    pattern2 = r'self\.app\.register_blueprint\((\w+)'
    matches2 = re.findall(pattern2, content)
    registered.extend(matches2)
    
    return list(set(registered))  # Remove duplicates

def categorize_routes(routes: List[Dict]) -> Dict[str, List[Dict]]:
    """Categorize routes by functionality"""
    categories = {
        'critical': [],
        'media': [],
        'automation': [],
        'ui': [],
        'tools': [],
        'testing': [],
        'other': []
    }
    
    critical_keywords = ['mobile', 'casting', 'discovery', 'toplists', 'tags', 'audio', 'comics', 'rd_api', 'dryrun']
    media_keywords = ['player', 'stream', 'reader', 'playlist', 'library', 'collection']
    automation_keywords = ['rss', 'automation', 'scheduler', 'torrent', 'download']
    ui_keywords = ['ui', 'editor', 'text', 'visual']
    tools_keywords = ['tools', 'organizer', 'rename', 'batch', 'bulk']
    testing_keywords = ['test', 'diagnostic', 'debug', 'selftest']
    
    for route in routes:
        module = route['module'].lower()
        categorized = False
        
        for keyword in critical_keywords:
            if keyword in module:
                categories['critical'].append(route)
                categorized = True
                break
        
        if not categorized:
            for keyword in media_keywords:
                if keyword in module:
                    categories['media'].append(route)
                    categorized = True
                    break
        
        if not categorized:
            for keyword in automation_keywords:
                if keyword in module:
                    categories['automation'].append(route)
                    categorized = True
                    break
        
        if not categorized:
            for keyword in ui_keywords:
                if keyword in module:
                    categories['ui'].append(route)
                    categorized = True
                    break
        
        if not categorized:
            for keyword in tools_keywords:
                if keyword in module:
                    categories['tools'].append(route)
                    categorized = True
                    break
        
        if not categorized:
            for keyword in testing_keywords:
                if keyword in module:
                    categories['testing'].append(route)
                    categorized = True
                    break
        
        if not categorized:
            categories['other'].append(route)
    
    return categories

def generate_inventory_files(routes: List[Dict], registered: List[str], categories: Dict):
    """Generate inventory and checklist files"""
    
    # Create inventory directory
    INVENTORY_DIR.mkdir(parents=True, exist_ok=True)
    
    # 1. All routes file
    all_routes_file = INVENTORY_DIR / "all_route_files.txt"
    with open(all_routes_file, 'w') as f:
        f.write("=" * 80 + "\n")
        f.write("MediaHub - All Route Files Inventory\n")
        f.write(f"Generated: {Path(__file__).name}\n")
        f.write("=" * 80 + "\n\n")
        
        f.write(f"Total route files: {len(routes)}\n")
        f.write(f"Currently registered: {len(registered)}\n")
        f.write(f"Unregistered: {len([r for r in routes if r['var_name'] and r['var_name'] not in registered])}\n\n")
        
        for route in routes:
            status = "✅ REGISTERED" if route['var_name'] in registered else "❌ NOT REGISTERED"
            f.write(f"{status} - {route['file']}\n")
            if route['var_name']:
                f.write(f"  Blueprint: {route['var_name']} ('{route['bp_name']}')\n")
                f.write(f"  Import: {route['import_statement']}\n")
                if route['register_statement']:
                    f.write(f"  Register: {route['register_statement']}\n")
            else:
                f.write(f"  ⚠️  No blueprint found in file\n")
            f.write("\n")
    
    print(f"✅ Created: {all_routes_file}")
    
    # 2. Registration checklist
    checklist_file = INVENTORY_DIR / "route_registration_checklist.md"
    with open(checklist_file, 'w') as f:
        f.write("# Route Registration Checklist\n\n")
        f.write(f"**Total Routes:** {len(routes)}  \n")
        f.write(f"**Currently Registered:** {len(registered)}  \n")
        f.write(f"**To Register:** {len([r for r in routes if r['var_name'] and r['var_name'] not in registered])}  \n\n")
        
        f.write("---\n\n")
        
        # By category
        for category, cat_routes in categories.items():
            if not cat_routes:
                continue
            
            unregistered = [r for r in cat_routes if r['var_name'] and r['var_name'] not in registered]
            if not unregistered:
                continue
            
            f.write(f"## {category.upper()} Routes ({len(unregistered)} to register)\n\n")
            
            for route in unregistered:
                f.write(f"- [ ] **{route['file']}**\n")
                f.write(f"  - Import: `{route['import_statement']}`\n")
                f.write(f"  - Register: `{route['register_statement']}`\n\n")
        
        f.write("---\n\n")
        f.write("## Already Registered\n\n")
        for route in routes:
            if route['var_name'] in registered:
                f.write(f"- [x] {route['file']}\n")
    
    print(f"✅ Created: {checklist_file}")
    
    # 3. Generate code to add to app.py
    code_file = INVENTORY_DIR / "registration_code.py"
    with open(code_file, 'w') as f:
        f.write("# Code to add to app.py\n")
        f.write("# Add these imports at the top of the file\n\n")
        
        f.write("# IMPORTS\n")
        for route in routes:
            if route['var_name'] and route['var_name'] not in registered:
                f.write(f"{route['import_statement']}\n")
        
        f.write("\n\n")
        f.write("# REGISTRATIONS\n")
        f.write("# Add these inside the register_routes() method or __init__\n\n")
        
        for category, cat_routes in categories.items():
            unregistered = [r for r in cat_routes if r['var_name'] and r['var_name'] not in registered]
            if unregistered:
                f.write(f"\n# {category.upper()} Routes\n")
                for route in unregistered:
                    if route['register_statement']:
                        f.write(f"{route['register_statement']}\n")
    
    print(f"✅ Created: {code_file}")

def main():
    """Main execution"""
    print("=" * 80)
    print("MediaHub Route Registration Script")
    print("=" * 80)
    print()
    
    # Scan all routes
    print("📁 Scanning route files...")
    routes = scan_all_routes()
    print(f"   Found {len(routes)} route files\n")
    
    # Get currently registered
    print("🔍 Checking currently registered routes...")
    registered = get_currently_registered()
    print(f"   Found {len(registered)} registered blueprints\n")
    
    # Categorize
    print("📊 Categorizing routes...")
    categories = categorize_routes(routes)
    for category, cat_routes in categories.items():
        unregistered = [r for r in cat_routes if r['var_name'] and r['var_name'] not in registered]
        if unregistered:
            print(f"   {category.upper()}: {len(unregistered)} to register")
    print()
    
    # Generate inventory files
    print("📝 Generating inventory files...")
    generate_inventory_files(routes, registered, categories)
    print()
    
    # Summary
    total_to_register = len([r for r in routes if r['var_name'] and r['var_name'] not in registered])
    print("=" * 80)
    print(f"✅ COMPLETE!")
    print(f"   Total routes: {len(routes)}")
    print(f"   Registered: {len(registered)}")
    print(f"   To register: {total_to_register}")
    print()
    print(f"📂 Inventory files created in: {INVENTORY_DIR}")
    print("=" * 80)

if __name__ == "__main__":
    main()
