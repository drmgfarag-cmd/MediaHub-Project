#!/usr/bin/env python3
"""
Launcher script for the Advanced Text Editor
Handles environment setup and graceful error handling
"""

import sys
import os
import subprocess
from pathlib import Path

def check_dependencies():
    """Check if required dependencies are installed"""
    required_packages = [
        ('PyQt5', 'PyQt5'),
        ('PyQtWebEngine', 'PyQtWebEngine'),
        ('requests', 'requests')
    ]
    
    missing_packages = []
    
    for package_name, import_name in required_packages:
        try:
            __import__(import_name)
            print(f"✓ {package_name} is installed")
        except ImportError:
            missing_packages.append(package_name)
            print(f"✗ {package_name} is missing")
    
    return missing_packages

def install_dependencies(packages):
    """Install missing dependencies"""
    print(f"\nInstalling missing packages: {', '.join(packages)}")
    
    try:
        for package in packages:
            subprocess.check_call([sys.executable, '-m', 'pip', 'install', package])
            print(f"✓ Successfully installed {package}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"✗ Failed to install dependencies: {e}")
        return False

def check_monaco_editor():
    """Check if Monaco Editor is properly set up"""
    monaco_path = Path("static/monaco-editor/min/vs/loader.js")
    
    if monaco_path.exists():
        print("✓ Monaco Editor is properly installed")
        return True
    else:
        print("✗ Monaco Editor files are missing")
        return False

def download_monaco_editor():
    """Download and extract Monaco Editor"""
    print("\nDownloading Monaco Editor...")
    
    try:
        import requests
        import tarfile
        
        # Create directories
        os.makedirs("static", exist_ok=True)
        
        # Download Monaco Editor
        url = "https://registry.npmjs.org/monaco-editor/-/monaco-editor-0.45.0.tgz"
        response = requests.get(url, stream=True)
        response.raise_for_status()
        
        # Save and extract
        with open("static/monaco-editor.tgz", "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        
        # Extract
        with tarfile.open("static/monaco-editor.tgz", "r:gz") as tar:
            tar.extractall("static")
        
        # Move files to correct location
        if Path("static/package").exists():
            import shutil
            shutil.move("static/package", "static/monaco-editor")
        
        # Cleanup
        os.remove("static/monaco-editor.tgz")
        
        print("✓ Monaco Editor downloaded and extracted successfully")
        return True
        
    except Exception as e:
        print(f"✗ Failed to download Monaco Editor: {e}")
        return False

def main():
    """Main launcher function"""
    print("MediaHub Ultimate Text Editor - Launcher")
    print("=" * 50)
    
    # Check Python version
    if sys.version_info < (3, 6):
        print("✗ Python 3.6 or higher is required")
        sys.exit(1)
    else:
        print(f"✓ Python {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}")
    
    # Check dependencies
    print("\nChecking dependencies...")
    missing_packages = check_dependencies()
    
    if missing_packages:
        response = input(f"\nInstall missing packages automatically? (y/n): ")
        if response.lower() == 'y':
            if not install_dependencies(missing_packages):
                print("\nFailed to install dependencies. Please install manually:")
                print(f"pip install {' '.join(missing_packages)}")
                sys.exit(1)
        else:
            print("\nPlease install the required packages manually:")
            print(f"pip install {' '.join(missing_packages)}")
            sys.exit(1)
    
    # Check Monaco Editor
    print("\nChecking Monaco Editor...")
    if not check_monaco_editor():
        response = input("\nDownload Monaco Editor automatically? (y/n): ")
        if response.lower() == 'y':
            if not download_monaco_editor():
                print("\nFailed to download Monaco Editor. Please download manually.")
                sys.exit(1)
        else:
            print("\nPlease download Monaco Editor manually to static/monaco-editor/")
            sys.exit(1)
    
    # All checks passed, launch the editor
    print("\n" + "=" * 50)
    print("All dependencies are satisfied. Launching text editor...")
    print("=" * 50)
    
    try:
        from text_editor import main as editor_main
        editor_main()
    except ImportError as e:
        print(f"✗ Failed to import text editor: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"✗ Error starting text editor: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
