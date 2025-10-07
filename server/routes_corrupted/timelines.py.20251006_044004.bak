from flask import Blueprint, jsonify, request
import os, json, re, time
tl_bp = Blueprint('tl', __name__)
ROOT=os.path.abspath(os.path.join(os.path.dirname(__file__),'..','..'))
STO=os.path.join(ROOT,'storage')
COLS=os.path.join(STO,'collections.json')
LIB =os.path.join(STO,'library_index.json')

def _load(path, default):
    try: return json.load(open(path,'r',encoding='utf-8'))
    except Exception: return default

@tl_bp.route('/api/timeline/by_collection')
def by_collection():
    name=(request.args.get('name') or '').strip()
    cols=_load(COLS, {'collections':[]}).get('collections',[])
    col=next((c for c in cols if c.get('name')==name), None)
    if not col: return jsonify({'error':'not found'}), 404
    rules=col.get('rules') or []
    lib=_load(LIB, [])
    items=[]
    for it in lib:
        t=it.get('title') or os.path.basename(it.get('path') or '')
        p=it.get('path') or ''
        ok=False
        for r in rules:
            tre=r.get('title_re'); pre=r.get('path_re')
            if tre and re.search(tre, t, re.I): ok=True
            if pre and re.search(pre, p, re.I): ok=True
            if ok: break
        if ok:
            y = it.get('year') or ''
            try:
                y = int(y) if y else None
            except: y = None
            items.append({'title': t, 'type': it.get('type','other'), 'year': y, 'added_ts': it.get('added_ts',0), 'progress': it.get('progress', 100 if it.get('type')=='series' else None)})
    # group by year, fallback to 'Unknown'
    out={}
    for x in items:
        y=x['year'] if x['year'] else 'Unknown'
        out.setdefault(str(y), []).append(x)
    # sort keys descending years, unknown last
    keys=sorted([k for k in out.keys() if k!='Unknown'], key=lambda k:int(k), reverse=True)
    if 'Unknown' in out: keys.append('Unknown')
    return jsonify({'years': keys, 'items': out})
