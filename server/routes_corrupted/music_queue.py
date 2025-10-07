from .security import require_api_key
from flask import Blueprint, request, jsonify
import os, json, time

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
STO  = os.path.join(ROOT, "storage")
IDX  = os.path.join(STO, "library_index.json")
QF   = os.path.join(STO, "music_queue.json")

mq_bp = Blueprint('music_queue', __name__)

def _load_db():
    try:
        with open(IDX,"r",encoding="utf-8") as f: return json.load(f)
        except Exception: return {"items":[]}

def _save_q(state):
    os.makedirs(STO, exist_ok=True)
    with open(QF,"w",encoding="utf-8") as f: json.dump(state,f,indent=2)

def _load_q():
    try:
        with open(QF,"r",encoding="utf-8") as f: return json.load(f)
        except Exception: return {"now": None, "queue": [], "history": []}

def _find_item(id_or_path):
    db=_load_db()
    for it in db.get("items", []):
        if str(it.get("id"))==str(id_or_path) or it.get("path")==id_or_path:
        return it
        return None

@mq_bp.route("/api/music/queue", methods=["GET"])
def getq():
        return jsonify(_load_q())

# DUPLICATE REMOVED: @mq_bp.route("/api/music/queue", methods=["POST"])
def create_music_queue():
    """Create Queue"""
    try:
        data = request.get_json()
        if not data:
        return jsonify({'error': 'No data provided'}), 400
        return jsonify({'success': True, 'message': 'Created', 'data': data}), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500
def create_music_queue():
    """Create Queue"""
    try:
        data = request.get_json()
        if not data:
        return jsonify({'error': 'No data provided'}), 400
        return jsonify({'success': True, 'message': 'Created', 'data': data}), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500
# DUPLICATE REMOVED: @require_api_key
# DUPLICATE REMOVED: def postq():
    data = request.get_json(silent=True) or {}
    op = data.get("op")
    state = _load_q()
    if op == "enqueue":
        it = _find_item(data.get("id",""))
        if it: state["queue"].append({"id": it.get("id"), "title": it.get("title") or it.get("name"), "stream": it.get("stream"), "cover": it.get("cover") or it.get("poster")})
    elif op == "playnow":
        it = _find_item(data.get("id",""))
        if it:
            if state.get("now"): state["history"].append(state["now"])
            state["now"] = {"id": it.get("id"), "title": it.get("title") or it.get("name"), "stream": it.get("stream"), "cover": it.get("cover") or it.get("poster")}
    elif op == "next":
        if state["queue"]:
            if state.get("now"): state["history"].append(state["now"])
            state["now"] = state["queue"].pop(0)
    elif op == "clear":
        state = {"now": state.get("now"), "queue": [], "history": state.get("history",[])}
    elif op == "remove":
        idx = data.get("index")
        if isinstance(idx,int) and 0 <= idx < len(state["queue"]):
            state["queue"].pop(idx)
    _save_q(state); return jsonify(state)