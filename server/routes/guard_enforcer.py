'''
Guard Enforcer - Audit & Compliance

Ensures that the MediaHub instance is compliant with the Golden Rules and project requirements.
'''

from flask import Blueprint, jsonify, current_app
import os
import json

guard_bp = Blueprint("guard", __name__)

def _get_storage_path():
    """Get storage path (deferred to avoid Flask context issues)"""
    try:
        return os.path.join(current_app.root_path, "..", os.environ.get("MH_STORAGE", "storage"))
    except:
        # Fallback if no app context
        return os.path.join(os.path.dirname(__file__), "..", "..", "storage")

def check_pillars():
    """
    Checks for the presence of essential UI pillar pages.
    These are the core HTML files that form the main sections of the UI.
    """

    required_pillar_pages = [
        os.path.join(current_app.root_path, "..", "web", "hub_enhanced.html"),
        os.path.join(current_app.root_path, "..", "web", "organizer.html"),
        os.path.join(current_app.root_path, "..", "web", "downloader.html"),
        os.path.join(current_app.root_path, "..", "web", "editor.html"),
        os.path.join(current_app.root_path, "..", "web", "settings.html"),
        os.path.join(current_app.root_path, "..", "web", "status.html"),
    ]
    missing_pages = []
    for page in required_pillar_pages:
        current_app.logger.debug(f"Checking for pillar page: {page}")
        if not os.path.exists(page):
            missing_pages.append(os.path.basename(page))
    if missing_pages:
        return {"passed": False, "reason": f"Missing essential UI pillar pages: {', '.join(missing_pages)}"}
    return {"passed": True, "reason": "All essential UI pillar pages are present."}

def check_profiles():
    """
    Checks for the presence and validity of essential configuration files (profiles).
    """
    config_dir = os.path.join(_get_storage_path(), "config")
    required_configs = [
        "subtitles.json", "providers.json", "rd_filters.json", 
        "rss_filters.json", "dedupe_policy.json", "renamer_patterns.json", 
        "org_rules.json", "services.json"
    ]
    missing_configs = []
    corrupt_configs = []

    for config_file in required_configs:
        config_path = os.path.join(config_dir, config_file)
        if not os.path.exists(config_path):
            missing_configs.append(config_file)
        else:
            # Check if the file is valid JSON
            try:
                with open(config_path, "r", encoding="utf-8") as f:
                    json.load(f)
            except (json.JSONDecodeError, UnicodeDecodeError):
                corrupt_configs.append(config_file)

    if missing_configs or corrupt_configs:
        reasons = []
        if missing_configs:
            reasons.append(f"Missing configuration files: {', '.join(missing_configs)}")
        if corrupt_configs:
            reasons.append(f"Corrupt or invalid JSON in configuration files: {', '.join(corrupt_configs)}")
        return {"passed": False, "reason": ". ".join(reasons)}

    return {"passed": True, "reason": "All required configuration profiles are present and valid."}

def check_status():
    """
    Performs a series of status checks on critical components and configurations.
    """
    status_checks = []
    api_manager = current_app.config.get("api_manager")

    # 1. Check rd_token_present
    rd_token = api_manager.get_key("real_debrid")
    if rd_token and rd_token != "HMPNSB7QFO4RL2DCIKRRPKFKLKBIR7LSWWUOVNDAADNHOTC2SAXA":
        status_checks.append({"check": "Real-Debrid Token", "passed": True, "reason": "API token is configured."})
    else:
        status_checks.append({"check": "Real-Debrid Token", "passed": False, "reason": "API token is missing or is the default placeholder."})

    # 2. Check provider keys present
    required_keys = {
        "tmdb": "3aca2154c1d9223036904a86202897ba",
        "tvdb": "72f8b186-1eb8-471d-94e7-85063cf7a1bf",
        "google_books": "AIzaSyA8OHWm7_imDTRCAEvC7rja2NZCInTw3d8",
        "discogs": "DlYcCvjWkCSKwuoxWznBrUDFitmPFTqBpIuoqizm",
        "acoustid": "W48qHR6eir",
        "omdb": "95b991d3",
        "anilist_client_id": "30444",
        "anilist_client_secret": "dc63l21fPbnvgpx7Qinlg9miT5ismqUu77oVSTj2"
    }
    missing_provider_keys = []
    for key, default_value in required_keys.items():
        key_value = api_manager.get_key(key)
        if not key_value or key_value == default_value:
            missing_provider_keys.append(key)
    
    if missing_provider_keys:
        status_checks.append({"check": "Provider API Keys", "passed": False, "reason": f"Missing or default keys for: {', '.join(missing_provider_keys)}"})
    else:
        status_checks.append({"check": "Provider API Keys", "passed": True, "reason": "All required provider API keys are configured."})

    # 3. Check subtitles priority
    subtitles_config_path = os.path.join(_get_storage_path(), "config", "subtitles.json")
    subtitles_priority_status = False
    reason = "Subtitles language priorities are not configured."
    if os.path.exists(subtitles_config_path):
        try:
            with open(subtitles_config_path, "r", encoding="utf-8") as f:
                sub_cfg = json.load(f)
                if sub_cfg.get("priority_languages") and isinstance(sub_cfg["priority_languages"], list) and len(sub_cfg["priority_languages"]) > 0:
                    subtitles_priority_status = True
                    reason = "Subtitles language priorities are configured."
        except Exception as e:
            reason = f"Error reading subtitles config: {e}"
    status_checks.append({"check": "Subtitles Priority", "passed": subtitles_priority_status, "reason": reason})

    # 4. Check downloader cap
    limits_config_path = os.path.join(_get_storage_path(), "config", "downloader_limits.json")
    downloader_cap_status = False
    reason = "Downloader max_kbps is not set to 10000."
    if os.path.exists(limits_config_path):
        try:
            with open(limits_config_path, "r", encoding="utf-8") as f:
                lim_cfg = json.load(f)
                if lim_cfg.get("max_kbps") == 10000:
                    downloader_cap_status = True
                    reason = "Downloader max_kbps is set to 10000."
        except Exception as e:
            reason = f"Error reading downloader limits config: {e}"
    else: # If the file doesn't exist, it can't be set to 10000
        reason = "downloader_limits.json not found."

    status_checks.append({"check": "Downloader Speed Cap", "passed": downloader_cap_status, "reason": reason})

    overall_passed = all(s["passed"] for s in status_checks)
    return {"passed": overall_passed, "reason": status_checks}

def check_self_tests():
    """
    Checks if the self-test blueprint is registered.
    A full check would involve running the tests, but this is a good first step.
    """
    if "selftest" in current_app.blueprints:
        return {"passed": True, "reason": "Self-test blueprint is registered."}
    return {"passed": False, "reason": "Self-test blueprint is not registered."}

def check_seeds():
    """
    Checks for the presence of essential seed files (configs and scripts).
    """
    current_app.logger.debug(f"Seed check - current_app.root_path: {current_app.root_path}")
    seed_files = [
        # Config files
        os.path.join(_get_storage_path(), "config", "subtitles.json"),
        os.path.join(_get_storage_path(), "config", "providers.json"),
        os.path.join(_get_storage_path(), "config", "rd_filters.json"),
        os.path.join(_get_storage_path(), "config", "rss_filters.json"),
        os.path.join(_get_storage_path(), "config", "dedupe_policy.json"),
        os.path.join(_get_storage_path(), "config", "renamer_patterns.json"),
        os.path.join(_get_storage_path(), "config", "org_rules.json"),
        os.path.join(_get_storage_path(), "config", "services.json"),
        # Script files
        os.path.join(current_app.root_path, "..", "scripts", "setup.cmd"),
        os.path.join(current_app.root_path, "..", "scripts", "setup.sh"),
        os.path.join(current_app.root_path, "..", "scripts", "run.cmd"),
        os.path.join(current_app.root_path, "..", "scripts", "run.sh"),
        os.path.join(current_app.root_path, "..", "run_all.sh"),
        os.path.join(current_app.root_path, "..", "run_server.sh"),
    ]
    missing_seeds = []
    for seed_file in seed_files:
        current_app.logger.debug(f"Checking for seed file: {seed_file}")
        if not os.path.exists(seed_file):
            missing_seeds.append(os.path.relpath(seed_file, current_app.root_path))
    if missing_seeds:
        return {"passed": False, "reason": f"Missing essential seed files: {', '.join(missing_seeds)}"}
    return {"passed": True, "reason": "All essential seed files are present."}


@guard_bp.route("/api/guard/scan")
def scan():
    """
    Runs all guard checks and returns a comprehensive status report.
    """
    results = {
        "pillars": check_pillars(),
        "profiles": check_profiles(),
        "status": check_status(),
        "self_tests": check_self_tests(),
        "seeds": check_seeds(),
    }
    
    overall_passed = all(result["passed"] for result in results.values())
    
    return jsonify({
        "ok": True,
        "overall_passed": overall_passed,
        "surfaces": results
    })

