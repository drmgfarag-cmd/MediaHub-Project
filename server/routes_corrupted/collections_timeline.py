from flask import Blueprint, jsonify, request
import os, json, re, datetime
timeline_bp = Blueprint('collections_timeline', __name__)

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
STO  = os.path.join(ROOT, 'storage')
LIB  = os.path.join(STO, 'library_index.json')
COLL = os.path.join(STO, 'collections.json')

def _load(path, default):
    try: return json.load(open(path,'r',encoding='utf-8'))
        except Exception: return default

def _year_from_path(p):
    m = re.search(r'(19|20)\d{2}', p or '')
        return int(m.group(0)) if m else None

@timeline_bp.route('/api/collections/timeline')
def timeline():
    name = request.args.get('name') or request.args.get('id') or ''
    order = request.args.get('order','release')  # release|custom
    lib = _load(LIB, [])
    col = _load(COLL, {}).get('collections', [])
    # find collection by partial name
    rules = []
    for c in col:
        if name.lower() in (c.get('name','').lower()):
            rules = c.get('rules', []); break
    items = []
    for it in lib:
        path = it.get('path',''); title = it.get('title') or os.path.basename(path)
        for r in rules:
            pat = r.get('path_re')
            if pat and re.search(pat, path, flags=re.I):
                items.append({"title": title, "path": path, "year": it.get('year') or _year_from_path(path)}); break
    # order
    if order=='custom':
        # placeholder: alphabetical as proxy
        items.sort(key=lambda x: x['title'])
    else:
        items.sort(key=lambda x: (x.get('year') or 0, x['title']))
    return jsonify({"ok": True, "items": items, "order": order, "count": len(items)})
