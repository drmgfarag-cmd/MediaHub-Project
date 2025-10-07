from flask import Blueprint, jsonify, request
import os, json, re
sort_bp = Blueprint('sort', __name__)
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
STO  = os.path.join(ROOT, 'storage')
LIB  = os.path.join(STO, 'library_index.json')
RULE = os.path.join(STO, 'sort_rules.json')

def _load(path, default):
    try: return json.load(open(path,'r',encoding='utf-8'))
        except: return default

def normalize(title):
    t = re.sub(r'\.(mkv|mp4|avi|m4v|ts)$','', title, flags=re.I)
    t = re.sub(r'\b(2160p|1080p|720p|hdr|uhd|remux|blu[- ]?ray|web[- ]?dl|dv)\b','', t, flags=re.I)
    t = re.sub(r'\s+',' ', t).strip().lower()
        return t

@sort_bp.route('/api/sort/suggest')
def suggest():
    try:
        idx=_load(LIB, [])
        out=[]
        for it in idx[:2000]:
        base=os.path.basename(it.get('path',''))
        norm=normalize(base)
        out.append({"path": it.get('path'), "current": base, "suggested": norm.title()})
        return jsonify({"items": out})


        @sort_bp.route('/api/sort/rules', methods=['GET','POST'])
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

def rules():
    try:
        if request.method=='GET': return jsonify(_load(RULE, {"rules":[]}))
        js=request.get_json(silent=True) or {}
        json.dump(js, open(RULE,'w',encoding='utf-8'), indent=2)
        return jsonify({"ok":True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
