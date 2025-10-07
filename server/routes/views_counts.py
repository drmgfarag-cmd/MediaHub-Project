from flask import Blueprint, jsonify
import os, json, re
vc_bp = Blueprint('views_counts', __name__)
def _root(): return os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
def _qfile(): return os.path.join(_root(), "data", "downloader_queue.json")
def _load(p, d): 
    try:
        with open(p,"r",encoding="utf-8") as f: return json.load(f)
    except Exception: return d
@vc_bp.route("/api/views/counts", methods=["GET"])
def counts():
    db=_load(_qfile(), {"downloads":[],"grabber":[]})
    rows=(db.get("downloads") or [])+(db.get("grabber") or [])
    status, ftype, host = {}, {}, {}
    for q in rows:
        s=(q.get("status") or "").lower(); status[s]=status.get(s,0)+1
        name=(q.get("title") or q.get("name") or "").lower()
        ft="other"
        if re.search(r"\.(mp4|mkv|avi|webm|mov)$", name): ft="video"
        elif re.search(r"\.(mp3|flac|aac|ogg|m4a)$", name): ft="audio"
        elif re.search(r"\.(zip|rar|7z|tar|gz)$", name): ft="archive"
        elif re.search(r"\.(png|jpg|jpeg|gif|webp|bmp)$", name): ft="image"
        elif re.search(r"\.(pdf|epub|doc|docx|txt)$", name): ft="doc"
        ftype[ft]=ftype.get(ft,0)+1
        h=(q.get("hoster_domain") or "").lower()
        if h: host[h]=host.get(h,0)+1
    host_top = sorted(host.items(), key=lambda x: x[1], reverse=True)[:25]
    return jsonify({"status": status, "ftype": ftype, "host_top": host_top})
