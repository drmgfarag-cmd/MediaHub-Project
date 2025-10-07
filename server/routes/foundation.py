"""
Foundation Verification API
Verifies build foundation integrity and completeness
"""
from flask import Blueprint, jsonify
import os
import sys
from datetime import datetime

foundation_bp = Blueprint('foundation', __name__)
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))

@foundation_bp.route('/api/foundation/verify', methods=['GET'])
def verify_foundation():
    """Comprehensive foundation integrity verification"""
    try:
        # Check Four Pillars
        pillars = ["mediahub_home.py", "text_editor.py", "downloader.py", "real_debrid_manager.py"]
        pillars_ok = all(os.path.exists(os.path.join(ROOT, p)) for p in pillars)
        
        # Check server structure
        server_ok = os.path.exists(os.path.join(ROOT, 'server', 'routes'))
        
        # Check web directory
        web_ok = os.path.exists(os.path.join(ROOT, 'web'))
        
        # Count routes
        routes_dir = os.path.join(ROOT, 'server', 'routes')
        route_count = len([f for f in os.listdir(routes_dir) if f.endswith('.py')]) if os.path.exists(routes_dir) else 0
        
        status = "HEALTHY" if (pillars_ok and server_ok and web_ok) else "DEGRADED"
        
        return jsonify({
            "ok": True,
            "timestamp": datetime.utcnow().isoformat(),
            "foundation_status": status,
            "components": {
                "four_pillars": pillars_ok,
                "server_structure": server_ok,
                "web_ui": web_ok
            },
            "statistics": {
                "route_files": route_count,
                "python_version": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
            }
        }), 200
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500
