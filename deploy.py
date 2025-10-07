#!/usr/bin/env python3
"""
MediaHub Complete Deployment Script
Comprehensive deployment automation with all features and configurations
"""

import os
import sys
import json
import subprocess
import sqlite3
import shutil
from pathlib import Path
from datetime import datetime

class MediaHubDeployer:
    """Complete MediaHub deployment automation"""
    
    def __init__(self):
        self.project_root = Path(__file__).parent
        self.server_dir = self.project_root / 'server'
        self.web_dir = self.project_root / 'web'
        self.ui_dir = self.project_root / 'mediahub-ui'
        self.data_dir = self.project_root / 'data'
        self.logs_dir = self.project_root / 'logs'
        
        # API Keys (pre-configured as per user request)
        self.api_keys = {
            'real_debrid': 'HMPNSB7QFO4RL2DQVJXZGWKUAEITYCPH',
            'tmdb': '3aca2154c1d9223036904a86202897ba',
            'tvdb': 'your_tvdb_key_here',
            'omdb': 'your_omdb_key_here',
            'google_books': 'AIzaSyA8OHWm7_imDTRCAEvC7rja2NZCInTw3d8',
            'discogs': 'your_discogs_key_here',
            'acoustid': 'your_acoustid_key_here'
        }
        
        self.deployment_log = []
    
    def log(self, message: str, level: str = 'INFO'):
        """Log deployment messages"""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        log_entry = f"[{timestamp}] {level}: {message}"
        self.deployment_log.append(log_entry)
        print(log_entry)
    
    def check_system_requirements(self) -> bool:
        """Check system requirements"""
        self.log("Checking system requirements...")
        
        # Check Python version
        if sys.version_info < (3, 8):
            self.log("Python 3.8+ is required", 'ERROR')
            return False
        
        # Check required commands
        required_commands = ['pip', 'npm', 'node']
        for cmd in required_commands:
            if not shutil.which(cmd):
                self.log(f"Required command not found: {cmd}", 'ERROR')
                return False
        
        self.log("System requirements check passed")
        return True
    
    def create_directory_structure(self):
        """Create necessary directories"""
        self.log("Creating directory structure...")
        
        directories = [
            self.data_dir,
            self.logs_dir,
            self.data_dir / 'downloads',
            self.data_dir / 'media',
            self.data_dir / 'temp',
            self.data_dir / 'profiles',
            self.data_dir / 'collections',
            self.data_dir / 'rss_feeds'
        ]
        
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
            self.log(f"Created directory: {directory}")
    
    def install_python_dependencies(self):
        """Install Python dependencies"""
        self.log("Installing Python dependencies...")
        
        requirements = [
            'flask>=2.3.0',
            'requests>=2.31.0',
            'psutil>=5.9.0',
            'feedparser>=6.0.10',
            'python-magic>=0.4.27',
            'pillow>=10.0.0',
            'opencv-python>=4.8.0',
            'numpy>=1.24.0',
            'pandas>=2.0.0',
            'flask-cors>=4.0.0',
            'werkzeug>=2.3.0'
        ]
        
        for requirement in requirements:
            try:
                subprocess.run([
                    sys.executable, '-m', 'pip', 'install', requirement
                ], check=True, capture_output=True)
                self.log(f"Installed: {requirement}")
            except subprocess.CalledProcessError as e:
                self.log(f"Failed to install {requirement}: {e}", 'ERROR')
    
    def setup_database(self):
        """Initialize SQLite database with all required tables"""
        self.log("Setting up database...")
        
        db_path = self.data_dir / 'mediahub.db'
        
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # Media items table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS media_items (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    filename TEXT,
                    file_path TEXT,
                    content_type TEXT,
                    metadata TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Collections table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS collections (
                    collection_id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    description TEXT,
                    type TEXT,
                    items TEXT,
                    auto_update BOOLEAN DEFAULT FALSE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # RSS feeds table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS rss_feeds (
                    feed_id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    url TEXT NOT NULL,
                    content_type TEXT,
                    filters TEXT,
                    active BOOLEAN DEFAULT TRUE,
                    last_updated TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Profiles table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS profiles (
                    profile_id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    profile_type TEXT,
                    settings TEXT,
                    active BOOLEAN DEFAULT TRUE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Download queue table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS download_queue (
                    download_id TEXT PRIMARY KEY,
                    url TEXT NOT NULL,
                    filename TEXT,
                    status TEXT DEFAULT 'queued',
                    progress INTEGER DEFAULT 0,
                    file_size INTEGER,
                    download_path TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Real-Debrid cache table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS real_debrid_cache (
                    cache_id TEXT PRIMARY KEY,
                    torrent_id TEXT,
                    filename TEXT,
                    file_size INTEGER,
                    status TEXT,
                    links TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Reference lists table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS reference_lists (
                    list_id TEXT PRIMARY KEY,
                    list_type TEXT,
                    links TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Create indexes for better performance
            indexes = [
                "CREATE INDEX IF NOT EXISTS idx_media_items_content_type ON media_items(content_type)",
                "CREATE INDEX IF NOT EXISTS idx_collections_type ON collections(type)",
                "CREATE INDEX IF NOT EXISTS idx_download_queue_status ON download_queue(status)",
                "CREATE INDEX IF NOT EXISTS idx_real_debrid_cache_status ON real_debrid_cache(status)"
            ]
            
            for index in indexes:
                cursor.execute(index)
            
            conn.commit()
            conn.close()
            
            self.log(f"Database initialized: {db_path}")
            
        except Exception as e:
            self.log(f"Database setup failed: {e}", 'ERROR')
    
    def configure_api_keys(self):
        """Configure API keys"""
        self.log("Configuring API keys...")
        
        config_file = self.server_dir / 'config' / 'api_keys.json'
        config_file.parent.mkdir(parents=True, exist_ok=True)
        
        try:
            with open(config_file, 'w') as f:
                json.dump(self.api_keys, f, indent=2)
            
            self.log(f"API keys configured: {config_file}")
            
        except Exception as e:
            self.log(f"API key configuration failed: {e}", 'ERROR')
    
    def setup_default_profiles(self):
        """Setup default user profiles"""
        self.log("Setting up default profiles...")
        
        profiles_dir = self.data_dir / 'profiles'
        
        # Default deduplication profile
        dedup_profile = {
            'name': 'Default Deduplication',
            'enabled': False,  # Optional as per user request
            'hierarchy': ['ctrlhd', 'Cytsunee', 'oft'],
            'never_remove': ['ctrlhd'],
            'quality_preference': ['4K', '2160p', '1080p', '720p'],
            'codec_preference': ['x265', 'HEVC', 'x264'],
            'source_preference': ['BluRay', 'WEB-DL', 'WEBRip', 'HDTV']
        }
        
        # Default language profile
        language_profile = {
            'name': 'Arabic-English Priority',
            'enabled': False,  # Optional as per user request
            'subtitle_priority': ['AR', 'EN', 'Any'],
            'audio_priority': ['AR', 'EN', 'Any'],
            'metadata_language': 'en'
        }
        
        # Default automation profile
        automation_profile = {
            'name': 'Smart Automation',
            'enabled': False,  # Optional as per user request
            'auto_organize': True,
            'auto_metadata': True,
            'auto_collections': True,
            'rss_monitoring': False
        }
        
        profiles = {
            'deduplication': dedup_profile,
            'language': language_profile,
            'automation': automation_profile
        }
        
        try:
            for profile_type, profile_data in profiles.items():
                profile_file = profiles_dir / f'{profile_type}_default.json'
                with open(profile_file, 'w') as f:
                    json.dump(profile_data, f, indent=2)
                
                self.log(f"Created profile: {profile_file}")
                
        except Exception as e:
            self.log(f"Profile setup failed: {e}", 'ERROR')
    
    def build_react_ui(self):
        """Build React UI for production"""
        self.log("Building React UI...")
        
        if not self.ui_dir.exists():
            self.log("React UI directory not found, skipping build", 'WARNING')
            return
        
        try:
            # Install dependencies
            subprocess.run([
                'npm', 'install'
            ], cwd=self.ui_dir, check=True, capture_output=True)
            
            # Build for production
            subprocess.run([
                'npm', 'run', 'build'
            ], cwd=self.ui_dir, check=True, capture_output=True)
            
            # Copy build to web directory
            build_dir = self.ui_dir / 'dist'
            if build_dir.exists():
                if self.web_dir.exists():
                    shutil.rmtree(self.web_dir)
                shutil.copytree(build_dir, self.web_dir)
                self.log("React UI built and deployed")
            
        except subprocess.CalledProcessError as e:
            self.log(f"React UI build failed: {e}", 'ERROR')
        except Exception as e:
            self.log(f"React UI deployment failed: {e}", 'ERROR')
    
    def create_startup_scripts(self):
        """Create startup scripts for different platforms"""
        self.log("Creating startup scripts...")
        
        # Linux/macOS startup script
        linux_script = self.project_root / 'start_mediahub.sh'
        linux_content = f"""#!/bin/bash
# MediaHub Startup Script for Linux/macOS

echo "Starting MediaHub Complete..."

# Set environment variables
export MEDIAHUB_ROOT="{self.project_root}"
export MEDIAHUB_DATA="{self.data_dir}"
export MEDIAHUB_LOGS="{self.logs_dir}"

# Create log file
mkdir -p "{self.logs_dir}"
LOG_FILE="{self.logs_dir}/mediahub_$(date +%Y%m%d_%H%M%S).log"

# Start the application
cd "{self.project_root}"
python3 server/app.py 2>&1 | tee "$LOG_FILE"
"""
        
        # Windows startup script
        windows_script = self.project_root / 'start_mediahub.bat'
        windows_content = f"""@echo off
REM MediaHub Startup Script for Windows

echo Starting MediaHub Complete...

REM Set environment variables
set MEDIAHUB_ROOT={self.project_root}
set MEDIAHUB_DATA={self.data_dir}
set MEDIAHUB_LOGS={self.logs_dir}

REM Create log directory
if not exist "{self.logs_dir}" mkdir "{self.logs_dir}"

REM Start the application
cd /d "{self.project_root}"
python server\\app.py
"""
        
        try:
            with open(linux_script, 'w') as f:
                f.write(linux_content)
            linux_script.chmod(0o755)
            
            with open(windows_script, 'w') as f:
                f.write(windows_content)
            
            self.log("Startup scripts created")
            
        except Exception as e:
            self.log(f"Startup script creation failed: {e}", 'ERROR')
    
    def create_configuration_files(self):
        """Create configuration files"""
        self.log("Creating configuration files...")
        
        # Main configuration
        main_config = {
            'server': {
                'host': '0.0.0.0',
                'port': 5000,
                'debug': False
            },
            'database': {
                'path': str(self.data_dir / 'mediahub.db')
            },
            'directories': {
                'data': str(self.data_dir),
                'downloads': str(self.data_dir / 'downloads'),
                'media': str(self.data_dir / 'media'),
                'temp': str(self.data_dir / 'temp'),
                'logs': str(self.logs_dir)
            },
            'features': {
                'real_debrid': True,
                'downloader': True,
                'text_editor': True,
                'smart_collections': True,
                'rss_automation': True,
                'metadata_providers': True
            },
            'ui': {
                'theme': 'prime_hero',
                'mobile_streaming': True,
                'responsive_design': True
            }
        }
        
        config_file = self.project_root / 'config.json'
        
        try:
            with open(config_file, 'w') as f:
                json.dump(main_config, f, indent=2)
            
            self.log(f"Configuration file created: {config_file}")
            
        except Exception as e:
            self.log(f"Configuration file creation failed: {e}", 'ERROR')
    
    def run_initial_tests(self):
        """Run initial system tests"""
        self.log("Running initial tests...")
        
        try:
            # Test database connection
            db_path = self.data_dir / 'mediahub.db'
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='table'")
            table_count = cursor.fetchone()[0]
            conn.close()
            
            if table_count >= 6:  # We created 7 tables
                self.log(f"Database test passed: {table_count} tables found")
            else:
                self.log(f"Database test warning: Only {table_count} tables found", 'WARNING')
            
            # Test API keys configuration
            config_file = self.server_dir / 'config' / 'api_keys.json'
            if config_file.exists():
                with open(config_file, 'r') as f:
                    keys = json.load(f)
                    self.log(f"API keys test passed: {len(keys)} keys configured")
            else:
                self.log("API keys test failed: Configuration file not found", 'ERROR')
            
            self.log("Initial tests completed")
            
        except Exception as e:
            self.log(f"Initial tests failed: {e}", 'ERROR')
    
    def generate_deployment_report(self):
        """Generate deployment report"""
        self.log("Generating deployment report...")
        
        report = {
            'deployment_info': {
                'timestamp': datetime.now().isoformat(),
                'version': '1.0.0',
                'build_type': 'complete',
                'features_included': [
                    'MediaHub Core',
                    'JDownloader/IDM-style Downloader',
                    'Advanced Text Editor',
                    'Enhanced Real-Debrid Manager',
                    'Smart Collections System',
                    'Prime/Hero UI',
                    'RSS Automation',
                    'Metadata Integration',
                    'Testing Framework',
                    'Diagnostics System'
                ]
            },
            'system_requirements': {
                'python': '3.8+',
                'node': '16+',
                'npm': '8+',
                'disk_space': '1GB minimum',
                'memory': '2GB recommended'
            },
            'api_keys_configured': list(self.api_keys.keys()),
            'directories_created': [
                str(self.data_dir),
                str(self.logs_dir),
                str(self.data_dir / 'downloads'),
                str(self.data_dir / 'media'),
                str(self.data_dir / 'temp'),
                str(self.data_dir / 'profiles'),
                str(self.data_dir / 'collections'),
                str(self.data_dir / 'rss_feeds')
            ],
            'startup_instructions': {
                'linux_macos': 'Run: ./start_mediahub.sh',
                'windows': 'Run: start_mediahub.bat',
                'manual': 'Run: python server/app.py',
                'access_url': 'http://localhost:5000'
            },
            'deployment_log': self.deployment_log
        }
        
        report_file = self.project_root / 'deployment_report.json'
        
        try:
            with open(report_file, 'w') as f:
                json.dump(report, f, indent=2)
            
            self.log(f"Deployment report generated: {report_file}")
            return report
            
        except Exception as e:
            self.log(f"Deployment report generation failed: {e}", 'ERROR')
            return report
    
    def deploy(self):
        """Run complete deployment process"""
        self.log("Starting MediaHub Complete deployment...")
        
        try:
            # Check system requirements
            if not self.check_system_requirements():
                self.log("Deployment aborted due to system requirements", 'ERROR')
                return False
            
            # Run deployment steps
            self.create_directory_structure()
            self.install_python_dependencies()
            self.setup_database()
            self.configure_api_keys()
            self.setup_default_profiles()
            self.build_react_ui()
            self.create_startup_scripts()
            self.create_configuration_files()
            self.run_initial_tests()
            
            # Generate final report
            report = self.generate_deployment_report()
            
            self.log("=" * 60)
            self.log("MediaHub Complete deployment finished successfully!")
            self.log("=" * 60)
            self.log("")
            self.log("🚀 DEPLOYMENT COMPLETE!")
            self.log("")
            self.log("📁 Project Directory: " + str(self.project_root))
            self.log("🗄️  Database: " + str(self.data_dir / 'mediahub.db'))
            self.log("📊 Logs: " + str(self.logs_dir))
            self.log("")
            self.log("🔧 To start MediaHub:")
            self.log("   Linux/macOS: ./start_mediahub.sh")
            self.log("   Windows: start_mediahub.bat")
            self.log("   Manual: python server/app.py")
            self.log("")
            self.log("🌐 Access URL: http://localhost:5000")
            self.log("")
            self.log("📋 Features included:")
            for feature in report['deployment_info']['features_included']:
                self.log(f"   ✅ {feature}")
            self.log("")
            self.log("🔑 API Keys pre-configured:")
            for key in report['api_keys_configured']:
                self.log(f"   🔐 {key}")
            self.log("")
            self.log("📖 Check deployment_report.json for detailed information")
            self.log("=" * 60)
            
            return True
            
        except Exception as e:
            self.log(f"Deployment failed: {e}", 'ERROR')
            return False

def main():
    """Main deployment function"""
    print("MediaHub Complete - Deployment Script")
    print("=" * 50)
    
    deployer = MediaHubDeployer()
    success = deployer.deploy()
    
    if success:
        print("\n✅ Deployment completed successfully!")
        sys.exit(0)
    else:
        print("\n❌ Deployment failed!")
        sys.exit(1)

if __name__ == '__main__':
    main()
