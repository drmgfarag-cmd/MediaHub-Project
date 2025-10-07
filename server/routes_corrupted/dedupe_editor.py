from flask import Blueprint, jsonify
import os, json, re, collections
dedupe_bp = Blueprint('dedupe', __name__)
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
STO  = os.path.join(ROOT, 'storage')
LIB  = os.path.join(STO, 'library_index.json')

def normalize(title):
    t = re.sub(r'\.(mkv|mp4|avi|m4v|ts)$','', title, flags=re.I)
    t = re.sub(r'\b(2160p|1080p|720p|hdr|uhd|remux|blu[- ]?ray|web[- ]?dl|dv)\b','', t, flags=re.I)
    t = re.sub(r'\s+',' ', t).strip().lower()
    return t

@dedupe_bp.route('/api/dedupe/scan')
def scan():
    try:
        idx=json.load(open(LIB,'r',encoding='utf-8'))
    except Exception:
        idx=[]
    groups=collections.defaultdict(list)
    for it in idx:
        base=os.path.basename(it.get('path',''))
        n=normalize(base)
        groups[n].append({"path": it.get('path'), "size": it.get('size',0)})
    dups=[{"key":k,"items":v} for k,v in groups.items() if len(v)>1]
        return jsonify({"dupes": dups[:500]})
