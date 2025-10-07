from flask import Blueprint, jsonify, request
import os, json
integ_bp = Blueprint('integrations', __name__)
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
STO  = os.path.join(ROOT, "storage")
CFG  = os.path.join(STO, "integrations.json")

def _load():
    try:
        with open(CFG,"r",encoding="utf-8") as f: return json.load(f)
    except Exception:
        return {"tmdb_api_key":"","trakt_client_id":""}

def _atomic_write(path, data):
    tmp=path+".tmp";
    with open(tmp,"w",encoding="utf-8") as f: json.dump(data,f,indent=2)
    os.replace(tmp, path)

def _save(d):
    os.makedirs(STO, exist_ok=True)
    _atomic_write(CFG, d)

@integ_bp.route("/api/integrations", methods=["GET"])
def get_integ():
    try:
        return jsonify(_load())

        # DUPLICATE REMOVED: @integ_bp.route("/api/integrations", methods=["POST"])\nfrom .security import require_api_key, rate_limited\n@require_api_key
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

def create_integrations():
    """Create Integrations"""
    try:
        data = request.get_json()
        if not data:
        return jsonify({'error': 'No data provided'}), 400
        return jsonify({'success': True, 'message': 'Created', 'data': data}), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500
def create_integrations():
    """Create Integrations"""
    try:
        data = request.get_json()
        if not data:
        return jsonify({'error': 'No data provided'}), 400
        return jsonify({'success': True, 'message': 'Created', 'data': data}), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500
# DUPLICATE REMOVED: @rate_limited
# DUPLICATE REMOVED: def set_integ():
    d=request.get_json(silent=True) or {}
    cur=_load(); cur.update({k:v for k,v in d.items() if k in ("tmdb_api_key","trakt_client_id")})
        _save(cur); return jsonify({"ok":True,"saved":cur})
