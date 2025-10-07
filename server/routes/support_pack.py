from flask import Blueprint, jsonify, current_app, send_file, make_response
import os, json, zipfile, io, glob, sys
from datetime import datetime

support_bp = Blueprint("support", __name__)

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
STO = os.path.join(ROOT, "storage")

def _redact_sensitive_data(data, path=""):
    """
    Recursively redact sensitive information from configuration data
    """
    if isinstance(data, dict):
        redacted = {}
        for key, value in data.items():
            key_lower = key.lower()
            # Redact sensitive keys
            if any(sensitive in key_lower for sensitive in ['password', 'secret', 'token', 'api_key', 'apikey', 'auth']):
                if value and len(str(value)) > 0:
                    redacted[key] = "<REDACTED>"
                else:
                    redacted[key] = "<EMPTY>"
            else:
                redacted[key] = _redact_sensitive_data(value, f"{path}.{key}")
        return redacted
    elif isinstance(data, list):
        return [_redact_sensitive_data(item, f"{path}[{i}]") for i, item in enumerate(data)]
    else:
        return data

def _redact_config(config_path):
    """
    Load and redact a configuration file
    """
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            config = json.load(f)
        
        redacted = _redact_sensitive_data(config)
        return json.dumps(redacted, indent=2)
    except json.JSONDecodeError as e:
        return f"Error: Invalid JSON in {config_path}: {str(e)}"
    except Exception as e:
        return f"Error reading config {config_path}: {str(e)}"

def _collect_system_info():
    """
    Collect system information for diagnostics
    """
    info = {
        "python_version": sys.version,
        "platform": sys.platform,
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }
    
    # Try to get additional system info
    try:
        import platform
        info["os"] = platform.system()
        info["os_release"] = platform.release()
        info["architecture"] = platform.machine()
    except Exception:
        pass
    
    # Check disk space
    try:
        import shutil
        total, used, free = shutil.disk_usage(ROOT)
        info["disk_space"] = {
            "total_gb": round(total / (1024**3), 2),
            "used_gb": round(used / (1024**3), 2),
            "free_gb": round(free / (1024**3), 2),
            "usage_percent": round((used / total) * 100, 1)
        }
    except Exception:
        pass
    
    return info

@support_bp.route("/api/support/pack", methods=["GET"])
def support_pack():
    """
    Generate a support pack containing:
    - Redacted configuration files
    - Log files
    - Self-test results
    - Guard enforcer scan results
    - Integration status
    - System information
    - Manifest of included files
    """
    memory_file = io.BytesIO()
    
    try:
        with zipfile.ZipFile(memory_file, "w", zipfile.ZIP_DEFLATED) as zf:
            files_added = []
            
            # 1. Add redacted config files
            config_dir = os.path.join(STO, "config")
            if os.path.exists(config_dir):
                for root, _, files in os.walk(config_dir):
                    for file in files:
                        if file.endswith(".json"):
                            full_path = os.path.join(root, file)
                            try:
                                redacted_content = _redact_config(full_path)
                                arcname = os.path.join("config", os.path.relpath(full_path, config_dir))
                                zf.writestr(arcname, redacted_content)
                                files_added.append(arcname)
                            except Exception as e:
                                error_msg = f"Error processing {file}: {str(e)}"
                                zf.writestr(f"config/errors/{file}.txt", error_msg)
            
            # 2. Add main config file if it exists
            main_config = os.path.join(STO, "config.json")
            if os.path.exists(main_config):
                try:
                    redacted_content = _redact_config(main_config)
                    zf.writestr("config/main_config.json", redacted_content)
                    files_added.append("config/main_config.json")
                except Exception as e:
                    zf.writestr("config/errors/main_config.txt", f"Error: {str(e)}")
            
            # 3. Add log files (limit size to avoid huge packs)
            log_dir = os.path.join(ROOT, "logs")
            if os.path.exists(log_dir):
                for root, _, files in os.walk(log_dir):
                    for file in files:
                        if file.endswith(".log"):
                            full_path = os.path.join(root, file)
                            try:
                                # Limit log file size to last 10MB
                                file_size = os.path.getsize(full_path)
                                arcname = os.path.join("logs", os.path.relpath(full_path, log_dir))
                                
                                if file_size > 10 * 1024 * 1024:  # 10MB
                                    # Read only the last 10MB
                                    with open(full_path, 'rb') as f:
                                        f.seek(-10 * 1024 * 1024, 2)
                                        content = f.read()
                                        zf.writestr(arcname, b"[...truncated...]\n" + content)
                                else:
                                    zf.write(full_path, arcname)
                                
                                files_added.append(arcname)
                            except Exception as e:
                                error_msg = f"Error reading log {file}: {str(e)}"
                                zf.writestr(f"logs/errors/{file}.txt", error_msg)
            
            # 4. Add latest self-test outcomes
            try:
                with current_app.test_client() as client:
                    response = client.get("/api/selftest/run?passes=5")
                    if response.status_code == 200:
                        selftest_results = response.get_json()
                        zf.writestr("diagnostics/selftest_5passes.json", json.dumps(selftest_results, indent=2))
                        files_added.append("diagnostics/selftest_5passes.json")
                    else:
                        error_msg = f"HTTP {response.status_code}: {response.data.decode()}"
                        zf.writestr("diagnostics/selftest_error.txt", error_msg)
            except Exception as e:
                zf.writestr("diagnostics/selftest_error.txt", f"Exception: {str(e)}")
            
            # 5. Add guard enforcer scan results
            try:
                with current_app.test_client() as client:
                    response = client.get("/api/guard/scan")
                    if response.status_code == 200:
                        guard_results = response.get_json()
                        zf.writestr("diagnostics/guard_scan.json", json.dumps(guard_results, indent=2))
                        files_added.append("diagnostics/guard_scan.json")
                    else:
                        error_msg = f"HTTP {response.status_code}: {response.data.decode()}"
                        zf.writestr("diagnostics/guard_scan_error.txt", error_msg)
            except Exception as e:
                zf.writestr("diagnostics/guard_scan_error.txt", f"Exception: {str(e)}")
            
            # 6. Add integration status
            try:
                with current_app.test_client() as client:
                    response = client.get("/integrations/status")
                    if response.status_code == 200:
                        status_results = response.get_json()
                        zf.writestr("diagnostics/integration_status.json", json.dumps(status_results, indent=2))
                        files_added.append("diagnostics/integration_status.json")
                    else:
                        error_msg = f"HTTP {response.status_code}: {response.data.decode()}"
                        zf.writestr("diagnostics/integration_status_error.txt", error_msg)
            except Exception as e:
                zf.writestr("diagnostics/integration_status_error.txt", f"Exception: {str(e)}")
            
            # 7. Add system information
            try:
                system_info = _collect_system_info()
                zf.writestr("diagnostics/system_info.json", json.dumps(system_info, indent=2))
                files_added.append("diagnostics/system_info.json")
            except Exception as e:
                zf.writestr("diagnostics/system_info_error.txt", f"Exception: {str(e)}")
            
            # 8. Add manifest (list of files included)
            manifest = {
                "generated_at": datetime.utcnow().isoformat() + "Z",
                "mediahub_version": "Phase2_Advanced_Enhanced_v1.0.0",
                "total_files": len(files_added),
                "files_included": sorted(files_added),
                "note": "Sensitive information (passwords, tokens, API keys) has been redacted"
            }
            zf.writestr("manifest.json", json.dumps(manifest, indent=2))
            
            # 9. Add README
            readme_content = """# MediaHub Support Pack

This archive contains diagnostic information for troubleshooting MediaHub.

## Contents:

- **config/**: Redacted configuration files
- **logs/**: Application log files (truncated if >10MB)
- **diagnostics/**: System diagnostics including:
  - Self-test results (5 passes)
  - Guard enforcer scan results
  - Integration status
  - System information
- **manifest.json**: Complete list of included files

## Privacy:

All sensitive information (passwords, tokens, API keys) has been automatically redacted.

## Usage:

Share this pack with MediaHub support or use it for self-diagnosis.

Generated: {}
""".format(manifest["generated_at"])
            zf.writestr("README.txt", readme_content)
    
    except Exception as e:
        # If zip creation fails, return error
        return jsonify({
            "ok": False,
            "error": f"Failed to create support pack: {str(e)}"
        }), 500
    
    memory_file.seek(0)
    timestamp_str = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    filename = f"mediahub_support_pack_{timestamp_str}.zip"
    
    response = make_response(send_file(
        memory_file,
        mimetype="application/zip",
        as_attachment=True,
        download_name=filename
    ))
    response.headers["Content-Disposition"] = f"attachment; filename={filename}"
    
    return response
