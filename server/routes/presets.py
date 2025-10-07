"""
Collections Presets Management
Provides preset configurations for automated collection imports with scheduling
"""
from flask import Blueprint, jsonify, request
import os
import json
import time
import threading
import logging
from .security import require_api_key, rate_limited

presets_bp = Blueprint('presets', __name__)
log = logging.getLogger('presets')

# Path configuration
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
STO = os.path.join(ROOT, "storage")
PRESETS_FILE = os.path.join(STO, "collections_presets.json")
STATE_FILE = os.path.join(STO, 'presets_state.json')
PAUSED_FILE = os.path.join(STO, 'presets_paused.flag')
LOCK_FILE = os.path.join(STO, 'presets.lock')

# Default preset configurations
DEFAULT_PRESETS = {
    "presets": [
        {
            "id": "tmdb_top_movies",
            "name": "Top Movies — TMDb Top Rated",
            "source": "tmdb_top_rated_movies",
            "n": 50,
            "refresh_days": 7,
            "enabled": True
        },
        {
            "id": "tmdb_top_tv",
            "name": "Top TV — TMDb Top Rated",
            "source": "tmdb_top_rated_tv",
            "n": 50,
            "refresh_days": 7,
            "enabled": True
        },
        {
            "id": "tmdb_pop_movies",
            "name": "Popular Movies — TMDb",
            "source": "tmdb_popular_movies",
            "n": 50,
            "refresh_days": 1,
            "enabled": False
        },
        {
            "id": "tmdb_pop_tv",
            "name": "Popular TV — TMDb",
            "source": "tmdb_popular_tv",
            "n": 50,
            "refresh_days": 1,
            "enabled": False
        },
        {
            "id": "trakt_pop_movies",
            "name": "Popular Movies — Trakt",
            "source": "trakt_popular_movies",
            "n": 50,
            "refresh_days": 1,
            "enabled": False
        },
        {
            "id": "trakt_pop_shows",
            "name": "Popular TV — Trakt",
            "source": "trakt_popular_shows",
            "n": 50,
            "refresh_days": 1,
            "enabled": False
        },
        {
            "id": "trakt_trend_movies",
            "name": "Trending Movies — Trakt",
            "source": "trakt_trending_movies",
            "n": 50,
            "refresh_days": 1,
            "enabled": False
        },
        {
            "id": "trakt_trend_shows",
            "name": "Trending TV — Trakt",
            "source": "trakt_trending_shows",
            "n": 50,
            "refresh_days": 1,
            "enabled": False
        }
    ]
}


def _load_presets():
    """Load presets from storage"""
    try:
        if os.path.exists(PRESETS_FILE):
            with open(PRESETS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        return DEFAULT_PRESETS.copy()
    except Exception as e:
        log.error(f"Error loading presets: {e}")
        return DEFAULT_PRESETS.copy()


def _save_presets(presets_data):
    """Save presets atomically"""
    try:
        os.makedirs(STO, exist_ok=True)
        tmp_file = PRESETS_FILE + ".tmp"
        with open(tmp_file, "w", encoding="utf-8") as f:
            json.dump(presets_data, f, indent=2)
        os.replace(tmp_file, PRESETS_FILE)
        return True
    except Exception as e:
        log.error(f"Error saving presets: {e}")
        return False


def _load_state():
    """Load scheduler state"""
    try:
        if os.path.exists(STATE_FILE):
            with open(STATE_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {"last_run": {}, "progress": {}, "last_status": {}, "last_count": {}}
    except Exception as e:
        log.error(f"Error loading state: {e}")
        return {"last_run": {}, "progress": {}, "last_status": {}, "last_count": {}}


def _save_state(state_data):
    """Save scheduler state atomically"""
    try:
        os.makedirs(STO, exist_ok=True)
        tmp_file = STATE_FILE + ".tmp"
        with open(tmp_file, "w", encoding="utf-8") as f:
            json.dump(state_data, f, indent=2)
        os.replace(tmp_file, STATE_FILE)
        return True
    except Exception as e:
        log.error(f"Error saving state: {e}")
        return False


def _load_integrations():
    """Load integration settings for API keys"""
    try:
        from .integrations import _load_integrations as load_integ
        return load_integ()
    except Exception as e:
        log.error(f"Error loading integrations: {e}")
        return {}


def _run_import(source, args):
    """Run collection import"""
    try:
        from .collections_import import run_import
        return run_import(source, args)
    except Exception as e:
        log.error(f"Error running import: {e}")
        return {"ok": False, "error": str(e)}


@presets_bp.route("/api/presets", methods=["GET"])
def get_presets():
    """Get all presets"""
    try:
        presets = _load_presets()
        return jsonify(presets), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@presets_bp.route("/api/presets", methods=["POST"])
@require_api_key
@rate_limited
def set_presets():
    """Update presets configuration"""
    try:
        data = request.get_json(silent=True) or {}
        
        if _save_presets(data):
            return jsonify({"ok": True}), 200
        else:
            return jsonify({"error": "Failed to save presets"}), 500
            
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@presets_bp.route("/api/presets/run", methods=["POST"])
@require_api_key
@rate_limited
def run_preset():
    """Run a specific preset manually"""
    try:
        data = request.get_json(silent=True) or {}
        preset_id = data.get("id")
        
        if not preset_id:
            return jsonify({"error": "Preset ID required"}), 400
        
        # Load presets and find the requested one
        config = _load_presets()
        preset = next((p for p in config.get("presets", []) if p.get("id") == preset_id), None)
        
        if not preset:
            return jsonify({"error": "Unknown preset"}), 404
        
        # Load integrations for API keys
        integrations = _load_integrations()
        
        # Build arguments for import
        args = {"n": preset.get("n", 50), "preset_id": preset_id}
        
        if preset["source"].startswith("tmdb"):
            args["api_key"] = integrations.get("tmdb_api_key", "")
        
        if preset["source"].startswith("trakt"):
            args["client_id"] = integrations.get("trakt_client_id", "")
        
        # Run the import
        result = _run_import(preset["source"], args)
        
        # Update state with results
        try:
            state = _load_state()
            
            # Update status
            if isinstance(result, dict) and result.get('ok'):
                state.setdefault('last_status', {})[preset_id] = 'ok'
            else:
                state.setdefault('last_status', {})[preset_id] = 'error'
            
            # Update count
            count = 0
            if isinstance(result, dict):
                created = result.get('created') or result.get('would_create') or []
                count = len(created)
            state.setdefault('last_count', {})[preset_id] = count
            
            # Update last run time
            state.setdefault('last_run', {})[preset_id] = time.time()
            
            _save_state(state)
        except Exception as e:
            log.warning(f"Failed to update state: {e}")
        
        return jsonify(result), 200
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@presets_bp.route('/api/presets/state', methods=['GET'])
def presets_state():
    """Get current scheduler state"""
    try:
        state = _load_state()
        paused = os.path.exists(PAUSED_FILE)
        
        return jsonify({
            "ok": True,
            "paused": paused,
            "last_run": state.get('last_run', {}),
            "progress": state.get('progress', {}),
            "last_status": state.get('last_status', {}),
            "last_count": state.get('last_count', {})
        }), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@presets_bp.route('/api/presets/pause', methods=['POST'])
@require_api_key
@rate_limited
def presets_pause():
    """Pause or resume the scheduler"""
    try:
        data = request.get_json(silent=True) or {}
        paused = bool(data.get('paused', True))
        
        if paused:
            # Create pause flag file
            with open(PAUSED_FILE, 'w') as f:
                f.write(str(time.time()))
        else:
            # Remove pause flag file
            if os.path.exists(PAUSED_FILE):
                os.remove(PAUSED_FILE)
        
        return jsonify({"ok": True, "paused": paused}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# Background scheduler thread
_scheduler_started = False
_last_run_times = {}


def _scheduler_thread():
    """Background thread that runs scheduled presets"""
    global _last_run_times
    
    log.info("Presets scheduler started")
    
    while True:
        try:
            # Check if paused
            if os.path.exists(PAUSED_FILE):
                time.sleep(300)  # Check every 5 minutes
                continue
            
            # Check for lock file to prevent overlapping runs
            now = time.time()
            busy = False
            
            if os.path.exists(LOCK_FILE):
                try:
                    lock_age = now - os.path.getmtime(LOCK_FILE)
                    if lock_age < 2400:  # 40 minutes
                        busy = True
                except Exception:
                    pass
            
            if busy:
                time.sleep(300)
                continue
            
            # Create lock file
            with open(LOCK_FILE, "w") as f:
                f.write(str(now))
            
            try:
                # Load presets and integrations
                config = _load_presets()
                integrations = _load_integrations()
                state = _load_state()
                
                # Process each enabled preset
                for preset in config.get("presets", []):
                    if not preset.get("enabled"):
                        continue
                    
                    preset_id = preset.get("id")
                    refresh_days = int(preset.get("refresh_days", 7))
                    
                    # Check if it's time to run this preset
                    last_run = state.get('last_run', {}).get(preset_id, 0)
                    
                    if now - last_run >= refresh_days * 86400:
                        log.info(f"Running scheduled preset: {preset_id}")
                        
                        # Build arguments
                        args = {"n": preset.get("n", 50), "preset_id": preset_id}
                        
                        if preset["source"].startswith("tmdb"):
                            args["api_key"] = integrations.get("tmdb_api_key", "")
                        
                        if preset["source"].startswith("trakt"):
                            args["client_id"] = integrations.get("trakt_client_id", "")
                        
                        # Run import
                        try:
                            result = _run_import(preset["source"], args)
                            
                            # Update state
                            if isinstance(result, dict) and result.get('ok'):
                                state.setdefault('last_status', {})[preset_id] = 'ok'
                            else:
                                state.setdefault('last_status', {})[preset_id] = 'error'
                            
                            count = 0
                            if isinstance(result, dict):
                                created = result.get('created') or result.get('would_create') or []
                                count = len(created)
                            state.setdefault('last_count', {})[preset_id] = count
                            
                            state.setdefault('last_run', {})[preset_id] = now
                            _save_state(state)
                            
                            log.info(f"Preset {preset_id} completed: {count} items")
                            
                        except Exception as e:
                            log.error(f"Preset {preset_id} failed: {e}")
                            state.setdefault('last_status', {})[preset_id] = 'error'
                            _save_state(state)
                
            finally:
                # Remove lock file
                try:
                    os.remove(LOCK_FILE)
                except Exception:
                    pass
            
        except Exception as e:
            log.error(f"Scheduler error: {e}")
        
        # Sleep for 5 minutes before next check
        time.sleep(300)


def _start_scheduler():
    """Start the background scheduler (called once)"""
    global _scheduler_started
    
    if not _scheduler_started:
        _scheduler_started = True
        thread = threading.Thread(target=_scheduler_thread, daemon=True)
        thread.start()
        log.info("Scheduler thread started")


# Start scheduler on module load
_start_scheduler()
