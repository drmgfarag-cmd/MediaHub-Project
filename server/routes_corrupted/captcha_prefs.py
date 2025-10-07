from .security import require_api_key
from flask import Blueprint, request, jsonify
import os, json
cap_bp = Blueprint('captcha', __name__)
def _root(): return os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
def _file(): return os.path.join(_root(), "storage", "captcha_prefs.json")
def _load():
    try:
        with open(_file(),"r",encoding="utf-8") as f: return json.load(f)
        except Exception: return {"enabled": True, "order": ["manual", "extern1", "extern2"], "timeouts":{"manual":60}, "sound": True}
def _save(d):
    with open(_file(),"w",encoding="utf-8") as f: json.dump(d,f,indent=2,ensure_ascii=False)
@cap_bp.route("/api/captcha/prefs/get", methods=["GET"])
def get_prefs():
try:
    return jsonify(_load())
    @cap_bp.route("/api/captcha/prefs/set", methods=["POST"])
    @require_api_key
except Exception as e:
    return jsonify({'success': False, 'error': str(e)}), 500

def set_prefs():
    data=request.get_json(silent=True) or {}; d=_load()
    for k in ("enabled","order","timeouts","sound"):
        if k in data: d[k]=data[k]
    _save(d); return jsonify({"ok": True, "prefs": d})