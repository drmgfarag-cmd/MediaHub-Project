from flask import Blueprint, jsonify
import os, json, time
sp_bp = Blueprint('metrics_speed', __name__)
def _root(): return os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
def _qfile(): return os.path.join(_root(), "data", "downloader_queue.json")
def _sfile(): return os.path.join(_root(), "storage", "speed_series.json")
def _load(p, d): 
    try:
        with open(p,"r",encoding="utf-8") as f: return json.load(f)
        except Exception: return d
def _save(p, d):
    with open(p,"w",encoding="utf-8") as f: json.dump(d,f,indent=2,ensure_ascii=False)
@sp_bp.route("/api/metrics/speed_series", methods=["GET"])
def series():
    try:
        q=_load(_qfile(), {"downloads":[]})
        total = sum(int(it.get("speed_bps") or 0) for it in q.get("downloads", []))
        s=_load(_sfile(), {"points":[]})
        now=int(time.time())
        s["points"].append([now,total]); s["points"]=s["points"][-300:]
        _save(_sfile(), s); return jsonify(s)
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
