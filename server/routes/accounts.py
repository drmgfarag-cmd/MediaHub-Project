from .security import require_api_key
from flask import Blueprint, request, jsonify
import os, json, time
from ..utils.secret_store import seal, open_sealed
acct_bp = Blueprint('accounts', __name__)
def _root(): return os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
def _file(): return os.path.join(_root(), "storage", "accounts.json")
def _load():
    try:
        with open(_file(),"r",encoding="utf-8") as f: return json.load(f)
    except Exception: return {"accounts":[]}
def _save(d):
    with open(_file(),"w",encoding="utf-8") as f: json.dump(d,f,indent=2,ensure_ascii=False)
@acct_bp.route("/api/accounts/list", methods=["GET"])
def list_accounts():
    d=_load(); out=[]
    for a in d.get("accounts", []):
        b=a.copy(); 
        if "secret" in b: b["has_secret"]=True; b.pop("secret", None)
        out.append(b)
    return jsonify({"accounts": out})
@acct_bp.route("/api/accounts/add", methods=["POST"])
@require_api_key
def add_account():
    data=request.get_json(silent=True) or {}; host=data.get("host"); user=data.get("user"); secret=data.get("secret","")
    if not host or not user: return jsonify({"error":"host and user required"}), 400
    d=_load()
    rec={"id": f"AC_{int(time.time())}", "host": host, "user": user, "secret": seal(secret), "status":"unknown","updated_ts":int(time.time()),"twofa":False,"traffic_left":None,"error":None}
    d.setdefault("accounts", []).append(rec); _save(d)
    rec2=rec.copy(); rec2["has_secret"]=True; rec2.pop("secret", None); return jsonify({"ok":True,"account":rec2})
@acct_bp.route("/api/accounts/update", methods=["POST"])
@require_api_key
def update_account():
    data=request.get_json(silent=True) or {}; aid=data.get("id"); fields=data.get("fields",{})
    d=_load()
    for a in d.get("accounts", []):
        if a.get("id")==aid:
            if "user" in fields: a["user"]=fields["user"]
            if "twofa" in fields: a["twofa"]=fields["twofa"]
            if "secret" in fields: a["secret"]=seal(fields.get("secret",""))
            a["updated_ts"]=int(time.time()); _save(d)
            b=a.copy(); b["has_secret"]=True; b.pop("secret", None); return jsonify({"ok":True,"account":b})
    return jsonify({"error":"id not found"}), 404
@acct_bp.route("/api/accounts/remove", methods=["POST"])
@require_api_key
def remove_account():
    data=request.get_json(silent=True) or {}; aid=data.get("id")
    d=_load(); d["accounts"]=[a for a in d.get("accounts", []) if a.get("id")!=aid]; _save(d); return jsonify({"ok":True})
@acct_bp.route("/api/accounts/refresh", methods=["POST"])
@require_api_key
def refresh_account():
    data=request.get_json(silent=True) or {}; aid=data.get("id")
    d=_load()
    for a in d.get("accounts", []):
        if a.get("id")==aid:
            a["status"]="ok"; a["traffic_left"]="unlimited" if a.get("host")=="rd" else None; a["error"]=None; a["updated_ts"]=int(time.time()); _save(d)
            b=a.copy(); b["has_secret"]=True; b.pop("secret", None); return jsonify({"ok":True,"account":b})
    return jsonify({"error":"id not found"}), 404