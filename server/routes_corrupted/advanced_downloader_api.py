"""
Advanced Downloader API - Endpoints for clipboard watcher and password manager
Provides RESTful API access to advanced downloader functionality
"""

from flask import Blueprint, jsonify, request
import os
import json
import logging
from datetime import datetime
from utils.advanced_downloader import get_advanced_downloader

advanced_dl_bp = Blueprint('advanced_downloader', __name__)
logger = logging.getLogger(__name__)

@advanced_dl_bp.route('/api/downloader/advanced/status')
def get_status():
    """Get advanced downloader status"""
    try:
        downloader = get_advanced_downloader()
        status = downloader.get_status()
        
        return jsonify({
            'success': True,
            'status': status,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error getting downloader status: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@advanced_dl_bp.route('/api/downloader/advanced/start', methods=['POST'])
def start_downloader():
    """Start advanced downloader with clipboard monitoring"""
    try:
        downloader = get_advanced_downloader()
        downloader.start()
        
        return jsonify({
            'success': True,
            'message': 'Advanced downloader started',
            'clipboard_monitoring': downloader.clipboard_watcher.running
        })
        
    except Exception as e:
        logger.error(f"Error starting downloader: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@advanced_dl_bp.route('/api/downloader/advanced/stop', methods=['POST'])
def stop_downloader():
    """Stop advanced downloader"""
    try:
        downloader = get_advanced_downloader()
        downloader.stop()
        
        return jsonify({
            'success': True,
            'message': 'Advanced downloader stopped'
        })
        
    except Exception as e:
        logger.error(f"Error stopping downloader: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@advanced_dl_bp.route('/api/downloader/advanced/queue')
def get_queue():
    """Get download queue status"""
    try:
        downloader = get_advanced_downloader()
        
        return jsonify({
            'success': True,
            'queue': {
                'active': list(downloader.active_downloads.values()),
                'queued': [d for d in downloader.download_queue if d['status'] == 'queued'],
                'completed': downloader.completed_downloads[-20:],  # Last 20
                'failed': downloader.failed_downloads[-10:]  # Last 10
            },
            'stats': {
                'active_count': len(downloader.active_downloads),
                'queued_count': len([d for d in downloader.download_queue if d['status'] == 'queued']),
                'completed_count': len(downloader.completed_downloads),
                'failed_count': len(downloader.failed_downloads)
            }
        })
        
    except Exception as e:
        logger.error(f"Error getting queue: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@advanced_dl_bp.route('/api/downloader/advanced/add', methods=['POST'])
def add_download():
    """Manually add download to queue"""
    try:
        data = request.get_json()
        url = data.get('url', '').strip()
        
        if not url:
        return jsonify({
                'success': False,
                'error': 'URL is required'
            }), 400
        
        downloader = get_advanced_downloader()
        
        # Detect link type
        detected_links = downloader.clipboard_watcher.detect_links(url)
        
        if not detected_links:
        return jsonify({
                'success': False,
                'error': 'No supported link types detected'
            }), 400
        
        # Create download info
        link_type = list(detected_links.keys())[0]
        download_info = {
            'url': url,
            'type': link_type,
            'detected_at': datetime.now().isoformat(),
            'context': data.get('context', 'Manual addition'),
            'auto_added': True,
            'status': 'queued',
            'manual': True
        }
        
        downloader.add_to_queue(download_info)
        
        return jsonify({
            'success': True,
            'message': 'Download added to queue',
            'download_id': download_info.get('id'),
            'type': link_type
        })
        
    except Exception as e:
        logger.error(f"Error adding download: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@advanced_dl_bp.route('/api/downloader/advanced/remove/<download_id>', methods=['DELETE'])
def remove_download(download_id):
    """Remove download from queue"""
    try:
        downloader = get_advanced_downloader()
        
        # Check active downloads
        if download_id in downloader.active_downloads:
            # In a real implementation, this would cancel the active download
            del downloader.active_downloads[download_id]
        return jsonify({
                'success': True,
                'message': 'Active download cancelled'
            })
        
        # Check queued downloads
        for download in downloader.download_queue[:]:
            if download.get('id') == download_id:
                downloader.download_queue.remove(download)
        return jsonify({
                    'success': True,
                    'message': 'Download removed from queue'
                })
        
        return jsonify({
            'success': False,
            'error': 'Download not found'
        }), 404
        
    except Exception as e:
        logger.error(f"Error removing download: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@advanced_dl_bp.route('/api/downloader/advanced/retry/<download_id>', methods=['POST'])
def retry_download(download_id):
    """Retry a failed download"""
    try:
        downloader = get_advanced_downloader()
        
        # Find failed download
        for download in downloader.failed_downloads:
            if download.get('id') == download_id:
                downloader._retry_download(download)
        return jsonify({
                    'success': True,
                    'message': 'Download queued for retry'
                })
        
        return jsonify({
            'success': False,
            'error': 'Failed download not found'
        }), 404
        
    except Exception as e:
        logger.error(f"Error retrying download: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@advanced_dl_bp.route('/api/downloader/advanced/settings')
def get_settings():
    """Get downloader settings"""
    try:
        downloader = get_advanced_downloader()
        settings = downloader.settings.copy()
        
        # Convert set to list for JSON serialization
        settings['trusted_domains'] = list(settings['trusted_domains'])
        
        return jsonify({
            'success': True,
            'settings': settings
        })
        
    except Exception as e:
        logger.error(f"Error getting settings: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# DUPLICATE REMOVED: @advanced_dl_bp.route('/api/downloader/advanced/settings', methods=['GET'])
# DUPLICATE REMOVED: def update_settings():
    """Update downloader settings"""
    try:
        data = request.get_json()
        downloader = get_advanced_downloader()
        
        # Update settings
        for key, value in data.items():
            if key in downloader.settings:
                if key == 'trusted_domains':
                    downloader.settings[key] = set(value)
                else:
                    downloader.settings[key] = value
        
        # Save settings
        downloader.save_settings()
        
        # Restart clipboard monitoring if setting changed
        if 'clipboard_monitoring' in data:
            if data['clipboard_monitoring'] and not downloader.clipboard_watcher.running:
                downloader.clipboard_watcher.start_monitoring()
            elif not data['clipboard_monitoring'] and downloader.clipboard_watcher.running:
                downloader.clipboard_watcher.stop_monitoring()
        
        return jsonify({
            'success': True,
            'message': 'Settings updated'
        })
        
    except Exception as e:
        logger.error(f"Error updating settings: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# Password Manager Endpoints

@advanced_dl_bp.route('/api/downloader/passwords/list')
def get_passwords():
    """Get password list"""
    try:
        downloader = get_advanced_downloader()
        pm = downloader.password_manager
        
        return jsonify({
            'success': True,
            'passwords': {
                'common': pm.common_passwords,
                'history': pm.password_history,
                'successful': pm.successful_passwords,
                'site_specific': pm.site_passwords
            },
            'stats': {
                'total_passwords': len(pm.common_passwords),
                'successful_patterns': len(pm.successful_passwords),
                'site_patterns': len(pm.site_passwords)
            }
        })
        
    except Exception as e:
        logger.error(f"Error getting passwords: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@advanced_dl_bp.route('/api/downloader/passwords/add', methods=['POST'])
def add_password():
    """Add password to list"""
    try:
        data = request.get_json()
        password = data.get('password', '').strip()
        source = data.get('source', 'manual')
        
        if not password:
        return jsonify({
                'success': False,
                'error': 'Password is required'
            }), 400
        
        downloader = get_advanced_downloader()
        downloader.password_manager.add_password(password, source)
        
        return jsonify({
            'success': True,
            'message': 'Password added'
        })
        
    except Exception as e:
        logger.error(f"Error adding password: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@advanced_dl_bp.route('/api/downloader/passwords/import', methods=['POST'])
def import_passwords():
    """Import password list"""
    try:
        data = request.get_json()
        passwords = data.get('passwords', [])
        source = data.get('source', 'import')
        
        if not passwords or not isinstance(passwords, list):
        return jsonify({
                'success': False,
                'error': 'Password list is required'
            }), 400
        
        downloader = get_advanced_downloader()
        added_count = downloader.password_manager.import_passwords(passwords, source)
        
        return jsonify({
            'success': True,
            'message': f'Imported {added_count} new passwords',
            'added_count': added_count
        })
        
    except Exception as e:
        logger.error(f"Error importing passwords: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@advanced_dl_bp.route('/api/downloader/passwords/export')
def export_passwords():
    """Export passwords for backup"""
    try:
        downloader = get_advanced_downloader()
        export_data = downloader.password_manager.export_passwords()
        
        return jsonify({
            'success': True,
            'export_data': export_data
        })
        
    except Exception as e:
        logger.error(f"Error exporting passwords: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@advanced_dl_bp.route('/api/downloader/passwords/generate/<archive_name>')
def generate_password_list(archive_name):
    """Generate password list for specific archive"""
    try:
        source_url = request.args.get('source_url', '')
        
        downloader = get_advanced_downloader()
        passwords = downloader.password_manager.get_password_list(archive_name, source_url)
        
        return jsonify({
            'success': True,
            'archive_name': archive_name,
            'source_url': source_url,
            'passwords': passwords,
            'count': len(passwords)
        })
        
    except Exception as e:
        logger.error(f"Error generating password list: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# Clipboard Monitoring Endpoints

@advanced_dl_bp.route('/api/downloader/clipboard/status')
def get_clipboard_status():
    """Get clipboard monitoring status"""
    try:
        downloader = get_advanced_downloader()
        
        return jsonify({
            'success': True,
            'clipboard_monitoring': {
                'running': downloader.clipboard_watcher.running,
                'available': downloader.clipboard_watcher.CLIPBOARD_AVAILABLE if hasattr(downloader.clipboard_watcher, 'CLIPBOARD_AVAILABLE') else True,
                'processed_links_count': len(downloader.clipboard_watcher.processed_links),
                'trusted_domains': list(downloader.clipboard_watcher.auto_add_trusted_domains)
            }
        })
        
    except Exception as e:
        logger.error(f"Error getting clipboard status: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@advanced_dl_bp.route('/api/downloader/clipboard/detect', methods=['POST'])
def detect_links():
    """Manually detect links in text"""
    try:
        data = request.get_json()
        text = data.get('text', '').strip()
        
        if not text:
        return jsonify({
                'success': False,
                'error': 'Text is required'
            }), 400
        
        downloader = get_advanced_downloader()
        detected_links = downloader.clipboard_watcher.detect_links(text)
        
        return jsonify({
            'success': True,
            'detected_links': detected_links,
            'total_links': sum(len(links) for links in detected_links.values())
        })
        
    except Exception as e:
        logger.error(f"Error detecting links: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@advanced_dl_bp.route('/api/downloader/clipboard/trusted_domains', methods=['POST'])
def add_trusted_domain():
    """Add domain to trusted list"""
    try:
        data = request.get_json()
        domain = data.get('domain', '').strip().lower()
        
        if not domain:
        return jsonify({
                'success': False,
                'error': 'Domain is required'
            }), 400
        
        downloader = get_advanced_downloader()
        downloader.clipboard_watcher.add_trusted_domain(domain)
        downloader.settings['trusted_domains'].add(domain)
        downloader.save_settings()
        
        return jsonify({
            'success': True,
            'message': f'Added {domain} to trusted domains'
        })
        
    except Exception as e:
        logger.error(f"Error adding trusted domain: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
