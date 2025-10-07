#!/usr/bin/env python3
"""Automatically fix missing route imports in app.py"""

import re
import os

print("Fixing missing route imports in app.py...")
print("=" * 60)

# Read app.py
with open('server/app.py', 'r') as f:
    content = f.read()
    lines = content.split('\n')

# Find all route imports
imports = re.findall(r'from routes\.(\w+) import (\w+)', content)

missing = []
for module, bp_name in imports:
    filepath = f'server/routes/{module}.py'
    if not os.path.exists(filepath):
        missing.append((module, bp_name))
        print(f"❌ Missing: routes/{module}.py (imports {bp_name})")

print(f"\nTotal missing: {len(missing)}")

if not missing:
    print("✅ No missing imports found!")
    exit(0)

print("\nCommenting out missing imports...")

# Comment out missing imports
for module, bp_name in missing:
    old_import = f"from routes.{module} import {bp_name}"
    new_import = f"# {old_import}  # File doesn't exist"
    content = content.replace(old_import, new_import)
    print(f"  ✓ Commented: {old_import}")

# Remove from registration lists
print("\nRemoving from registration...")
for module, bp_name in missing:
    # Remove standalone occurrences
    content = re.sub(rf'\b{bp_name},\s*', '', content)
    content = re.sub(rf',\s*{bp_name}\b', '', content)
    print(f"  ✓ Removed: {bp_name}")

# Write back
with open('server/app.py', 'w') as f:
    f.write(content)

print("\n" + "=" * 60)
print(f"✅ Fixed {len(missing)} missing imports!")
print("App.py has been updated.")
