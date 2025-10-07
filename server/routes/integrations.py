"""
Third-Party Integrations Management
Handles API keys and credentials for external services (TMDb, Trakt, etc.)
"""
from flask import Blueprint, jsonify, request
import os
import json
from .security import require_api_key, rate_limited

integ_bp = Blueprint('integrations', __name__)

# Path configuration
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
STO = os.path.join(ROOT, "storage")
CFG_FILE = os.path.join(STO, "integrations.json")

# Default integration settings
DEFAULT_INTEGRATIONS = {
    "tmdb_api_key": "",
    "trakt_client_id": "",
    "trakt_client_secret": "",
    "real_debrid_api_key": "",
    "opensubtitles_api_key": "",
    "fanart_api_key": "",
    "omdb_api_key": ""
}


def _load_integrations():
    """Load integration settings from storage"""
    try:
        if os.path.exists(CFG_FILE):
            with open(CFG_FILE, "r", encoding="utf-8") as f:
                user_config = json.load(f)
                # Merge with defaults to ensure all keys exist
                return {**DEFAULT_INTEGRATIONS, **user_config}
        return DEFAULT_INTEGRATIONS.copy()
    except Exception as e:
        print(f"Error loading integrations: {e}")
        return DEFAULT_INTEGRATIONS.copy()


def _save_integrations(config_data):
    """Save integration settings atomically"""
    try:
        os.makedirs(STO, exist_ok=True)
        tmp_file = CFG_FILE + ".tmp"
        with open(tmp_file, "w", encoding="utf-8") as f:
            json.dump(config_data, f, indent=2, sort_keys=True)
        os.replace(tmp_file, CFG_FILE)
        return True
    except Exception as e:
        print(f"Error saving integrations: {e}")
        return False


@integ_bp.route("/api/integrations", methods=["GET"])
def get_integrations():
    """Get all integration settings (API keys masked for security)"""
    try:
        config = _load_integrations()
        # Mask sensitive data for GET requests
        masked_config = {}
        for key, value in config.items():
            if value and len(value) > 4:
                # Show first 4 chars and mask the rest
                masked_config[key] = value[:4] + "*" * (len(value) - 4)
            else:
                masked_config[key] = value if value else ""
        
        return jsonify(masked_config), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@integ_bp.route("/api/integrations", methods=["POST"])
@require_api_key
@rate_limited
def set_integrations():
    """Update integration settings"""
    try:
        data = request.get_json(silent=True) or {}
        
        # Load current config
        current_config = _load_integrations()
        
        # Update only valid keys
        updated = False
        for key, value in data.items():
            if key in DEFAULT_INTEGRATIONS:
                if isinstance(value, str):
                    current_config[key] = value.strip()
                    updated = True
        
        if updated:
            if _save_integrations(current_config):
                # Return masked version
                masked_config = {}
                for key, value in current_config.items():
                    if value and len(value) > 4:
                        masked_config[key] = value[:4] + "*" * (len(value) - 4)
                    else:
                        masked_config[key] = value if value else ""
                
                return jsonify({"ok": True, "saved": masked_config}), 200
            else:
                return jsonify({"error": "Failed to save integrations"}), 500
        else:
            return jsonify({"ok": True, "message": "No valid integrations to update"}), 200
            
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@integ_bp.route("/api/integrations/<service>", methods=["GET"])
def get_integration(service):
    """Get a specific integration setting"""
    try:
        config = _load_integrations()
        key = f"{service}_api_key" if not service.endswith("_api_key") else service
        
        if key in config:
            value = config[key]
            # Mask the value
            if value and len(value) > 4:
                masked_value = value[:4] + "*" * (len(value) - 4)
            else:
                masked_value = value if value else ""
            
            return jsonify({service: masked_value}), 200
        else:
            return jsonify({"error": "Integration not found"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@integ_bp.route("/api/integrations/<service>", methods=["PUT"])
@require_api_key
@rate_limited
def set_integration(service):
    """Set a specific integration"""
    try:
        data = request.get_json(silent=True) or {}
        value = data.get('value', '').strip()
        
        key = f"{service}_api_key" if not service.endswith("_api_key") else service
        
        if key not in DEFAULT_INTEGRATIONS:
            return jsonify({"error": "Invalid integration"}), 400
        
        config = _load_integrations()
        config[key] = value
        
        if _save_integrations(config):
            # Return masked value
            if value and len(value) > 4:
                masked_value = value[:4] + "*" * (len(value) - 4)
            else:
                masked_value = value if value else ""
            
            return jsonify({"ok": True, service: masked_value}), 200
        else:
            return jsonify({"error": "Failed to save integration"}), 500
            
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@integ_bp.route("/api/integrations/test/<service>", methods=["POST"])
@require_api_key
@rate_limited
def test_integration(service):
    """Test an integration by making a simple API call"""
    try:
        config = _load_integrations()
        
        if service == "tmdb":
            api_key = config.get("tmdb_api_key", "")
            if not api_key:
                return jsonify({"ok": False, "error": "API key not configured"}), 400
            
            # Test TMDb API
            import requests
            response = requests.get(
                f"https://api.themoviedb.org/3/configuration?api_key={api_key}",
                timeout=10
            )
            if response.status_code == 200:
                return jsonify({"ok": True, "message": "TMDb connection successful"}), 200
            else:
                return jsonify({"ok": False, "error": f"TMDb API error: {response.status_code}"}), 400
        
        elif service == "trakt":
            client_id = config.get("trakt_client_id", "")
            if not client_id:
                return jsonify({"ok": False, "error": "Client ID not configured"}), 400
            
            # Test Trakt API
            import requests
            response = requests.get(
                "https://api.trakt.tv/movies/trending",
                headers={
                    "Content-Type": "application/json",
                    "trakt-api-version": "2",
                    "trakt-api-key": client_id
                },
                timeout=10
            )
            if response.status_code == 200:
                return jsonify({"ok": True, "message": "Trakt connection successful"}), 200
            else:
                return jsonify({"ok": False, "error": f"Trakt API error: {response.status_code}"}), 400
        
        else:
            return jsonify({"ok": False, "error": "Service not supported for testing"}), 400
            
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500


@integ_bp.route("/api/integrations/reset", methods=["POST"])
@require_api_key
@rate_limited
def reset_integrations():
    """Reset all integrations to defaults"""
    try:
        if _save_integrations(DEFAULT_INTEGRATIONS):
            return jsonify({"ok": True, "message": "Integrations reset to defaults"}), 200
        else:
            return jsonify({"error": "Failed to reset integrations"}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# Helper function for other modules to access integrations
def get_api_key(service):
    """Get API key for a specific service"""
    config = _load_integrations()
    key = f"{service}_api_key" if not service.endswith("_api_key") else service
    return config.get(key, "")
