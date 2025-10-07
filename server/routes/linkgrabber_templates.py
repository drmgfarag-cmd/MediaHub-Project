from .security import require_api_key
from flask import Blueprint, request, jsonify
import os, json
tmpl_bp = Blueprint('link_templates', __name__)
def _root(): return os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
def _p(): return os.path.join(_root(), "storage", "linkgrabber_templates.json")
def _load(): 
    try:
        with open(_p(),"r",encoding="utf-8") as f: return json.load(f)
    except Exception: return {"templates":{}}
def _save(d):
    with open(_p(),"w",encoding="utf-8") as f: json.dump(d,f,indent=2,ensure_ascii=False)
@tmpl_bp.route("/api/linkgrabber/templates/get", methods=["GET"])
def get():
    return jsonify(_load())
@tmpl_bp.route("/api/linkgrabber/templates/save", methods=["POST"])
@require_api_key
def save():
    data=request.get_json(silent=True) or {}
    name=(data.get("name") or "").strip(); cfg=data.get("config") or {}
    if not name: return jsonify({"error":"name required"}), 400
    d=_load(); d.setdefault("templates",{})[name]=cfg; _save(d)
    return jsonify({"ok": True})
@tmpl_bp.route("/api/linkgrabber/templates/delete", methods=["POST"])
@require_api_key
def delete():
    data=request.get_json(silent=True) or {}
    name=(data.get("name") or "").strip(); d=_load(); d.get("templates",{}).pop(name, None); _save(d)
    return jsonify({"ok": True})