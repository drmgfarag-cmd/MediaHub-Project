"""
Core Infrastructure Golden Surface APIs - Master Rulebook Compliance
Provides system health and integrations status
"""
from flask import Blueprint, jsonify
import os
import sys
import json
import psutil
from datetime import datetime

core_infra_bp = Blueprint('core_infra', __name__)

# Storage paths
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
STORAGE = os.path.join(ROOT, 'storage')

def load_json(path, default=None):
    """Load JSON file with default fallback"""
    if default is None:
        default = {}
    try:
        if os.path.exists(path):
            with open(path, 'r', encoding='utf-8') as f:
                return json.load(f)
    except:
        pass
    return default

@core_infra_bp.route('/integrations/status', methods=['GET'])
def integrations_status():
    """Get status of all integrations"""
    
    # Check API keys
    api_keys_path = os.path.join(STORAGE, 'api_keys.json')
    api_keys = load_json(api_keys_path, {})
    
    integrations = {
        'tmdb': {
            'name': 'The Movie Database (TMDB)',
            'status': 'configured' if api_keys.get('tmdb_api_key') else 'not_configured',
            'required': True,
            'type': 'metadata'
        },
        'real_debrid': {
            'name': 'Real-Debrid',
            'status': 'configured' if api_keys.get('real_debrid_api_key') else 'not_configured',
            'required': True,
            'type': 'debrid'
        },
        'opensubtitles': {
            'name': 'OpenSubtitles',
            'status': 'configured' if api_keys.get('opensubtitles_api_key') else 'not_configured',
            'required': False,
            'type': 'subtitles'
        },
        'trakt': {
            'name': 'Trakt',
            'status': 'configured' if api_keys.get('trakt_client_id') else 'not_configured',
            'required': False,
            'type': 'tracking'
        },
        'plex': {
            'name': 'Plex',
            'status': 'configured' if api_keys.get('plex_token') else 'not_configured',
            'required': False,
            'type': 'media_server'
        },
        'emby': {
            'name': 'Emby',
            'status': 'configured' if api_keys.get('emby_api_key') else 'not_configured',
            'required': False,
            'type': 'media_server'
        },
        'jellyfin': {
            'name': 'Jellyfin',
            'status': 'configured' if api_keys.get('jellyfin_api_key') else 'not_configured',
            'required': False,
            'type': 'media_server'
        },
        'aria2': {
            'name': 'Aria2',
            'status': 'configured' if api_keys.get('aria2_secret') else 'not_configured',
            'required': False,
            'type': 'downloader'
        },
        'jackett': {
            'name': 'Jackett',
            'status': 'configured' if api_keys.get('jackett_api_key') else 'not_configured',
            'required': False,
            'type': 'indexer'
        }
    }
    
    # Count statuses
    total = len(integrations)
    configured = sum(1 for i in integrations.values() if i['status'] == 'configured')
    required_configured = sum(1 for i in integrations.values() if i['required'] and i['status'] == 'configured')
    required_total = sum(1 for i in integrations.values() if i['required'])
    
    return jsonify({
        'success': True,
        'integrations': integrations,
        'summary': {
            'total': total,
            'configured': configured,
            'not_configured': total - configured,
            'required_configured': required_configured,
            'required_total': required_total,
            'all_required_configured': required_configured == required_total
        },
        'checked_at': datetime.now().isoformat()
    })

@core_infra_bp.route('/api/health/comprehensive', methods=['GET'])
def health_comprehensive():
    """Comprehensive system health check"""
    
    health = {
        'success': True,
        'overall_status': 'healthy',
        'checks': {},
        'checked_at': datetime.now().isoformat()
    }
    
    # 1. System Resources
    try:
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        health['checks']['system_resources'] = {
            'status': 'healthy' if cpu_percent < 80 and memory.percent < 80 and disk.percent < 90 else 'warning',
            'cpu_percent': cpu_percent,
            'memory_percent': memory.percent,
            'memory_available_gb': memory.available / (1024**3),
            'disk_percent': disk.percent,
            'disk_free_gb': disk.free / (1024**3)
        }
    except Exception as e:
        health['checks']['system_resources'] = {
            'status': 'error',
            'error': str(e)
        }
    
    # 2. Storage Directory
    try:
        storage_exists = os.path.exists(STORAGE)
        storage_writable = os.access(STORAGE, os.W_OK) if storage_exists else False
        
        health['checks']['storage'] = {
            'status': 'healthy' if storage_exists and storage_writable else 'error',
            'exists': storage_exists,
            'writable': storage_writable,
            'path': STORAGE
        }
    except Exception as e:
        health['checks']['storage'] = {
            'status': 'error',
            'error': str(e)
        }
    
    # 3. API Keys Configuration
    try:
        api_keys_path = os.path.join(STORAGE, 'api_keys.json')
        api_keys = load_json(api_keys_path, {})
        required_keys = ['tmdb_api_key', 'real_debrid_api_key']
        has_required = all(api_keys.get(key) for key in required_keys)
        
        health['checks']['api_keys'] = {
            'status': 'healthy' if has_required else 'warning',
            'configured_count': len([k for k in api_keys.values() if k]),
            'required_configured': has_required
        }
    except Exception as e:
        health['checks']['api_keys'] = {
            'status': 'error',
            'error': str(e)
        }
    
    # 4. Database
    try:
        db_path = os.path.join(STORAGE, 'mediahub.db')
        db_exists = os.path.exists(db_path)
        db_size_mb = os.path.getsize(db_path) / (1024**2) if db_exists else 0
        
        health['checks']['database'] = {
            'status': 'healthy' if db_exists else 'warning',
            'exists': db_exists,
            'size_mb': round(db_size_mb, 2),
            'path': db_path
        }
    except Exception as e:
        health['checks']['database'] = {
            'status': 'warning',
            'error': str(e)
        }
    
    # 5. Python Environment
    try:
        health['checks']['python'] = {
            'status': 'healthy',
            'version': sys.version,
            'executable': sys.executable,
            'platform': sys.platform
        }
    except Exception as e:
        health['checks']['python'] = {
            'status': 'error',
            'error': str(e)
        }
    
    # 6. Routes/Modules
    try:
        routes_dir = os.path.join(ROOT, 'server', 'routes')
        route_files = [f for f in os.listdir(routes_dir) if f.endswith('.py') and not f.startswith('__')]
        
        health['checks']['routes'] = {
            'status': 'healthy',
            'route_files_count': len(route_files),
            'routes_directory': routes_dir
        }
    except Exception as e:
        health['checks']['routes'] = {
            'status': 'error',
            'error': str(e)
        }
    
    # 7. Web Directory
    try:
        web_dir = os.path.join(ROOT, 'web')
        web_exists = os.path.exists(web_dir)
        html_files = len([f for f in os.listdir(web_dir) if f.endswith('.html')]) if web_exists else 0
        
        health['checks']['web'] = {
            'status': 'healthy' if web_exists else 'warning',
            'exists': web_exists,
            'html_files_count': html_files,
            'path': web_dir
        }
    except Exception as e:
        health['checks']['web'] = {
            'status': 'error',
            'error': str(e)
        }
    
    # Determine overall status
    statuses = [check.get('status') for check in health['checks'].values()]
    if 'error' in statuses:
        health['overall_status'] = 'unhealthy'
    elif 'warning' in statuses:
        health['overall_status'] = 'degraded'
    else:
        health['overall_status'] = 'healthy'
    
    return jsonify(health)
