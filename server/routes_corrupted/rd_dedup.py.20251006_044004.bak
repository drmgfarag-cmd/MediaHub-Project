from flask import Blueprint, jsonify
import os, json, re, requests

dedup_bp = Blueprint('rd_dedup', __name__)

def normalize(title):
    t = title or ''
    t = re.sub(r'\[(.*?)\]', ' ', t)
    t = re.sub(r'\.(mkv|mp4|avi|rar|zip|7z)$','', t, flags=re.I)
    t = re.sub(r'\b(2160p|1080p|720p|hdr|uhd|remux|blu[- ]?ray|web[- ]?dl|dv|atmos|dts|aac|x265|hevc|x264)\b','', t, flags=re.I)
    t = re.sub(r'\s+',' ', t).strip().lower()
    return t

@dedup_bp.route('/api/rd/dedup')
def dedup():
    try:
        j=requests.get('http://127.0.0.1:5000/api/rd/torrents', timeout=8).json()
        arr=j.get('items', [])
    except Exception:
        arr=[]
    groups={}
    for t in arr:
        name = t.get('name') or t.get('filename') or t.get('title') or ''
        key = normalize(name)
        if not key: continue
        groups.setdefault(key, []).append({
            "name": name,
            "id": t.get('id') or t.get('hash'),
            "status": t.get('status'),
            "size": t.get('size'),
            "links": t.get('links') or [],
            "magnet": t.get('magnet') or t.get('link') or ''
        })
    out=[{"key":k, "count":len(v), "items":v} for k,v in groups.items() if len(v)>1]
    return jsonify({"dupes": sorted(out, key=lambda x: -x['count'])[:500]})
