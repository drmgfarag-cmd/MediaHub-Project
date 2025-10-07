from .security import require_api_key
from flask import Blueprint, request, jsonify
import os, json, time

pins_bp = Blueprint('home_pins', __name__)
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
STO  = os.path.join(ROOT, "storage")
PINS = os.path.join(STO, "home_rails.json")

def _load():
    try:
        with open(PINS,"r",encoding="utf-8") as f: return json.load(f)
    except Exception: return {"order": [], "pinned": []}

def _save(d):
    os.makedirs(STO, exist_ok=True)
    with open(PINS,"w",encoding="utf-8") as f: json.dump(d,f,indent=2)

@pins_bp.route("/api/home/rails/order", methods=["GET"])
def get_order():
    return jsonify(_load())

@pins_bp.route("/api/home/rails/order", methods=["POST"])
@require_api_key
def set_order():
    data = request.get_json(silent=True) or {}
    order = data.get("order") or []
    pinned = data.get("pinned") or []
    d=_load(); d["order"]=order; d["pinned"]=pinned; d["updated_ts"]=int(time.time()); _save(d)
    return jsonify({"ok": True, "state": d})