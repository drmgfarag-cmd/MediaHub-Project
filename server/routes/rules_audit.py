"""
Rules Audit API
Validates compliance with Master Rulebook and Golden Surface requirements
"""
from flask import Blueprint, jsonify, request
import os
import json
from datetime import datetime

rules_audit_bp = Blueprint('rules_audit', __name__)

# Path configuration
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))

# Golden Surface API requirements
GOLDEN_SURFACE_APIS = {
    "core_infrastructure": [
        "/api/guard/scan",
        "/integrations/status",
        "/api/selftest/run",
        "/api/support/pack",
        "/api/rules_audit",
        "/api/health/comprehensive",
        "/api/foundation/verify"
    ],
    "media_management": [
        "/api/rd/filters/config",
        "/api/rss/filters/config",
        "/api/providers/profiles",
        "/api/dedupe/policy",
        "/api/dedupe/movie_list_resolve",
        "/api/dedupe/hash_index",
        "/api/subs/policy",
        "/api/media/organize",
        "/api/collections/manage",
        "/api/metadata/fetch"
    ],
    "four_pillars_home": [
        "/api/home/hero",
        "/api/home/carousels",
        "/api/home/subcategories",
        "/api/search/omnibox"
    ],
    "four_pillars_editor": [
        "/api/editor/documents",
        "/api/editor/syntax",
        "/api/editor/macros",
        "/api/editor/bookmarks"
    ],
    "four_pillars_downloader": [
        "/api/downloader/queue",
        "/api/downloader/auto",
        "/api/downloader/extraction"
    ],
    "four_pillars_rd": [
        "/api/rd/manager/browse",
        "/api/rd/manager/bulk",
        "/api/rd/manager/filters"
    ],
    "ui_ux": [
        "/api/ui/themes",
        "/api/ui/locale",
        "/api/casting/devices",
        "/api/streaming/hls"
    ]
}

# Four Pillars file requirements
FOUR_PILLARS = {
    "mediahub_home.py": "MediaHub Home - Prime UI interface",
    "text_editor.py": "Text Editor - Multi-document editor",
    "downloader.py": "Downloader - Queue management",
    "real_debrid_manager.py": "Real-Debrid Manager - Cloud management"
}


def _check_route_exists(route_path):
    """
    Check if a route actually exists by scanning route files for the exact endpoint
    This prevents false positives from just checking filenames or comments
    """
    import re
    routes_dir = os.path.join(ROOT, 'server', 'routes')
    
    if not os.path.exists(routes_dir):
        return False
    
    # Normalize the route path for comparison
    normalized_route = route_path.strip('/')
    
    # Recursively search all Python files in routes directory
    for root_dir, dirs, files in os.walk(routes_dir):
        for filename in files:
            if not filename.endswith('.py'):
                continue
            
            filepath = os.path.join(root_dir, filename)
            try:
                with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                    lines = f.readlines()
                    
                    for line in lines:
                        # Skip comments
                        if line.strip().startswith('#'):
                            continue
                        
                        # Search for route decorators with this exact path
                        # Matches: @bp.route('/api/home/hero') or @bp.route("/api/home/hero")
                        route_patterns = [
                            rf"@\w+\.route\(['\"]/{re.escape(normalized_route)}['\"]",
                            rf"@\w+\.route\(['\"]/{re.escape(normalized_route)}/['\"]",
                            rf"@\w+\.route\(['\"]/{re.escape(normalized_route)}<",
                        ]
                        
                        for pattern in route_patterns:
                            if re.search(pattern, line):
                                return True
                            
            except Exception:
                continue
    
    return False


def _check_four_pillars():
    """Check if all Four Pillars files exist"""
    results = {}
    for pillar_file, description in FOUR_PILLARS.items():
        file_path = os.path.join(ROOT, pillar_file)
        exists = os.path.exists(file_path)
        results[pillar_file] = {
            "exists": exists,
            "description": description,
            "path": file_path
        }
    return results


def _check_golden_surfaces():
    """Check Golden Surface API coverage"""
    results = {}
    total_required = 0
    total_found = 0
    
    for category, apis in GOLDEN_SURFACE_APIS.items():
        category_results = []
        for api in apis:
            exists = _check_route_exists(api)
            category_results.append({
                "endpoint": api,
                "exists": exists
            })
            total_required += 1
            if exists:
                total_found += 1
        
        results[category] = {
            "apis": category_results,
            "count": len(apis),
            "found": sum(1 for r in category_results if r["exists"])
        }
    
    return results, total_required, total_found


def _check_architecture():
    """Check architecture compliance"""
    checks = {
        "pyqt6_desktop": False,
        "flask_backend": False,
        "four_pillars_complete": False,
        "web_ui_present": False
    }
    
    # Check for PyQt6
    for pillar in FOUR_PILLARS.keys():
        if os.path.exists(os.path.join(ROOT, pillar)):
            checks["pyqt6_desktop"] = True
            break
    
    # Check for Flask
    if os.path.exists(os.path.join(ROOT, 'run_server.py')):
        checks["flask_backend"] = True
    
    # Check Four Pillars completeness
    pillar_results = _check_four_pillars()
    checks["four_pillars_complete"] = all(p["exists"] for p in pillar_results.values())
    
    # Check for web UI
    web_dir = os.path.join(ROOT, 'web')
    if os.path.exists(web_dir):
        checks["web_ui_present"] = True
    
    return checks


def _check_configuration():
    """Check configuration and pre-configured keys"""
    config_checks = {
        "config_files_present": False,
        "storage_directory": False,
        "pre_configured_keys": False
    }
    
    # Check for config files
    config_paths = [
        os.path.join(ROOT, 'config.json'),
        os.path.join(ROOT, 'storage', 'config.json'),
        os.path.join(ROOT, 'config', 'config.json')
    ]
    
    for config_path in config_paths:
        if os.path.exists(config_path):
            config_checks["config_files_present"] = True
            try:
                with open(config_path, 'r') as f:
                    config = json.load(f)
                    if any(key in str(config).lower() for key in ['api_key', 'token', 'client_id']):
                        config_checks["pre_configured_keys"] = True
            except:
                pass
    
    # Check storage directory
    storage_dir = os.path.join(ROOT, 'storage')
    if os.path.exists(storage_dir):
        config_checks["storage_directory"] = True
    
    return config_checks


@rules_audit_bp.route('/api/rules_audit', methods=['GET'])
def rules_audit():
    """
    Comprehensive audit of Master Rulebook compliance
    Returns detailed compliance report
    """
    try:
        # Perform all checks
        four_pillars = _check_four_pillars()
        golden_surfaces, total_apis, found_apis = _check_golden_surfaces()
        architecture = _check_architecture()
        configuration = _check_configuration()
        
        # Calculate compliance scores
        four_pillars_score = sum(1 for p in four_pillars.values() if p["exists"]) / len(four_pillars) * 100
        golden_surface_score = (found_apis / total_apis * 100) if total_apis > 0 else 0
        architecture_score = sum(1 for v in architecture.values() if v) / len(architecture) * 100
        config_score = sum(1 for v in configuration.values() if v) / len(configuration) * 100
        
        # Overall compliance score
        overall_score = (four_pillars_score + golden_surface_score + architecture_score + config_score) / 4
        
        # Determine compliance status
        if overall_score >= 90:
            status = "COMPLIANT"
            status_icon = "✅"
        elif overall_score >= 70:
            status = "PARTIAL_COMPLIANCE"
            status_icon = "⚠️"
        else:
            status = "NON_COMPLIANT"
            status_icon = "❌"
        
        # Build response
        response = {
            "ok": True,
            "audit_timestamp": datetime.utcnow().isoformat(),
            "overall_compliance": {
                "score": round(overall_score, 2),
                "status": status,
                "status_icon": status_icon
            },
            "four_pillars": {
                "score": round(four_pillars_score, 2),
                "status": "COMPLETE" if four_pillars_score == 100 else "INCOMPLETE",
                "details": four_pillars
            },
            "golden_surfaces": {
                "score": round(golden_surface_score, 2),
                "total_required": total_apis,
                "total_found": found_apis,
                "coverage": f"{found_apis}/{total_apis}",
                "categories": golden_surfaces
            },
            "architecture": {
                "score": round(architecture_score, 2),
                "checks": architecture,
                "type": "HYBRID_PYQT6_FLASK" if architecture["pyqt6_desktop"] and architecture["flask_backend"] else "UNKNOWN"
            },
            "configuration": {
                "score": round(config_score, 2),
                "checks": configuration
            },
            "recommendations": []
        }
        
        # Add recommendations based on findings
        if four_pillars_score < 100:
            response["recommendations"].append({
                "priority": "HIGH",
                "category": "Four Pillars",
                "message": "Not all Four Pillars files are present"
            })
        
        if golden_surface_score < 90:
            response["recommendations"].append({
                "priority": "HIGH",
                "category": "Golden Surfaces",
                "message": f"Only {found_apis}/{total_apis} Golden Surface APIs found"
            })
        
        if not architecture["pyqt6_desktop"]:
            response["recommendations"].append({
                "priority": "CRITICAL",
                "category": "Architecture",
                "message": "PyQt6 desktop application not detected"
            })
        
        if not configuration["pre_configured_keys"]:
            response["recommendations"].append({
                "priority": "MEDIUM",
                "category": "Configuration",
                "message": "Pre-configured keys not detected"
            })
        
        return jsonify(response), 200
        
    except Exception as e:
        return jsonify({
            "ok": False,
            "error": str(e),
            "audit_timestamp": datetime.utcnow().isoformat()
        }), 500


@rules_audit_bp.route('/api/rules_audit/summary', methods=['GET'])
def rules_audit_summary():
    """Get a quick summary of compliance status"""
    try:
        # Run quick checks
        four_pillars = _check_four_pillars()
        _, total_apis, found_apis = _check_golden_surfaces()
        architecture = _check_architecture()
        
        four_pillars_complete = all(p["exists"] for p in four_pillars.values())
        golden_surface_coverage = (found_apis / total_apis * 100) if total_apis > 0 else 0
        
        return jsonify({
            "ok": True,
            "summary": {
                "four_pillars_complete": four_pillars_complete,
                "golden_surface_coverage": round(golden_surface_coverage, 2),
                "architecture_type": "HYBRID_PYQT6_FLASK" if architecture["pyqt6_desktop"] and architecture["flask_backend"] else "UNKNOWN",
                "quick_status": "✅ PASS" if four_pillars_complete and golden_surface_coverage >= 90 else "⚠️ NEEDS ATTENTION"
            }
        }), 200
        
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500


@rules_audit_bp.route('/api/rules_audit/golden_surfaces', methods=['GET'])
def golden_surfaces_check():
    """Detailed check of Golden Surface API coverage"""
    try:
        golden_surfaces, total_apis, found_apis = _check_golden_surfaces()
        
        return jsonify({
            "ok": True,
            "golden_surfaces": golden_surfaces,
            "summary": {
                "total_required": total_apis,
                "total_found": found_apis,
                "coverage_percent": round((found_apis / total_apis * 100), 2) if total_apis > 0 else 0
            }
        }), 200
        
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500


@rules_audit_bp.route('/api/rules_audit/four_pillars', methods=['GET'])
def four_pillars_check():
    """Check Four Pillars completeness"""
    try:
        four_pillars = _check_four_pillars()
        all_present = all(p["exists"] for p in four_pillars.values())
        
        return jsonify({
            "ok": True,
            "four_pillars": four_pillars,
            "all_present": all_present,
            "status": "✅ COMPLETE" if all_present else "❌ INCOMPLETE"
        }), 200
        
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500
