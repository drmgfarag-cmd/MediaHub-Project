"""
Feature Flags Management
Provides runtime feature toggles for MediaHub functionality
"""
from flask import Blueprint, jsonify, request
import os
import json
from .security import require_api_key, rate_limited

flags_bp = Blueprint('flags', __name__)

# Path configuration
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
STO = os.path.join(ROOT, 'storage')
FLAGS_FILE = os.path.join(STO, 'feature_flags.json')

# Default feature flags configuration
DEFAULT_FLAGS = {
    # Core features
    "enable_logs_tail": True,
    "enable_package_grouping": True,
    "enable_per_row_progress": True,
    "enable_bandwidth_limiter": True,
    "enable_linkgrabber_wizard": True,
    "enable_metrics_local": True,
    "enable_status_footer": True,
    "enable_downloader": True,
    "enable_rss": True,
    "enable_download_drawer": True,
    
    # Polish pack features
    "enable_polish_pack": True,
    "enable_bundles_polish": True,
    "enable_rails_polish": True,
    
    # Real-Debrid integration
    "enable_real_debrid": True,
    "enable_native_downloader": True,
    "enable_rss_to_rd": True,
    "enable_rd_adv_prefs": True,
    "enable_rd_cloud_pull": True,
    
    # UI enhancements
    "enable_immersion_hero": True,
    "enable_collections_import": True,
    "enable_collections_timelines": True,
    "enable_pinned_subcats": True,
    "enable_top50_lists": True,
    "enable_inline_bundles_table": True,
    "enable_table_extra_columns": True,
    "enable_row_progress_in_table": True,
    "enable_footer_graph": True,
    "enable_tree_view": True,
    
    # Advanced features
    "enable_rss_scheduler": True,
    "enable_clipboard_catcher": True,
    "enable_aria2": True,
    "enable_qbittorrent": True,
    "enable_kids_age_rails": True,
    "enable_sort_editor": True,
    "enable_dedupe_editor": True
}


def _load_flags():
    """Load feature flags from storage, merging with defaults"""
    try:
        if os.path.exists(FLAGS_FILE):
            with open(FLAGS_FILE, 'r', encoding='utf-8') as f:
                user_flags = json.load(f)
                # Merge user flags with defaults
                return {**DEFAULT_FLAGS, **user_flags}
        return DEFAULT_FLAGS.copy()
    except Exception as e:
        print(f"Error loading flags: {e}")
        return DEFAULT_FLAGS.copy()


def _save_flags(flags_data):
    """Save feature flags to storage atomically"""
    try:
        os.makedirs(STO, exist_ok=True)
        tmp_file = FLAGS_FILE + '.tmp'
        with open(tmp_file, 'w', encoding='utf-8') as f:
            json.dump(flags_data, f, indent=2, sort_keys=True)
        os.replace(tmp_file, FLAGS_FILE)
        return True
    except Exception as e:
        print(f"Error saving flags: {e}")
        return False


@flags_bp.route('/api/flags', methods=['GET'])
def get_flags():
    """Get all feature flags"""
    try:
        flags = _load_flags()
        return jsonify(flags), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@flags_bp.route('/api/flags', methods=['POST'])
@require_api_key
@rate_limited
def set_flags():
    """Update feature flags"""
    try:
        data = request.get_json(silent=True) or {}
        
        # Load current flags
        current_flags = _load_flags()
        
        # Update only valid flags (those that exist in DEFAULT_FLAGS)
        updated = False
        for key, value in data.items():
            if key in DEFAULT_FLAGS:
                if isinstance(value, bool):
                    current_flags[key] = value
                    updated = True
        
        if updated:
            if _save_flags(current_flags):
                return jsonify({"ok": True, "flags": current_flags}), 200
            else:
                return jsonify({"error": "Failed to save flags"}), 500
        else:
            return jsonify({"ok": True, "flags": current_flags, "message": "No valid flags to update"}), 200
            
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@flags_bp.route('/api/flags/<flag_name>', methods=['GET'])
def get_flag(flag_name):
    """Get a specific feature flag"""
    try:
        flags = _load_flags()
        if flag_name in flags:
            return jsonify({"flag": flag_name, "enabled": flags[flag_name]}), 200
        else:
            return jsonify({"error": "Flag not found"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@flags_bp.route('/api/flags/<flag_name>', methods=['PUT'])
@require_api_key
@rate_limited
def set_flag(flag_name):
    """Set a specific feature flag"""
    try:
        data = request.get_json(silent=True) or {}
        enabled = data.get('enabled', True)
        
        if flag_name not in DEFAULT_FLAGS:
            return jsonify({"error": "Invalid flag name"}), 400
        
        if not isinstance(enabled, bool):
            return jsonify({"error": "enabled must be a boolean"}), 400
        
        flags = _load_flags()
        flags[flag_name] = enabled
        
        if _save_flags(flags):
            return jsonify({"ok": True, "flag": flag_name, "enabled": enabled}), 200
        else:
            return jsonify({"error": "Failed to save flag"}), 500
            
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@flags_bp.route('/api/flags/reset', methods=['POST'])
@require_api_key
@rate_limited
def reset_flags():
    """Reset all flags to defaults"""
    try:
        if _save_flags(DEFAULT_FLAGS):
            return jsonify({"ok": True, "flags": DEFAULT_FLAGS, "message": "Flags reset to defaults"}), 200
        else:
            return jsonify({"error": "Failed to reset flags"}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# Helper function for other modules to check flags
def is_enabled(flag_name):
    """Check if a feature flag is enabled"""
    flags = _load_flags()
    return flags.get(flag_name, False)
