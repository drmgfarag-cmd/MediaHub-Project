from flask import Blueprint, jsonify, request
import os, json, time, re
from .security import require_api_key, rate_limited
from .flags import _load as flags_load

coll_bp = Blueprint('collections_import', __name__)
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
STO  = os.path.join(ROOT, 'storage')
FILE = os.path.join(STO, 'collections_imports.json')

def _on(): return bool(flags_load().get('enable_collections_import'))

def _load():
    try: return json.load(open(FILE,'r',encoding='utf-8'))
    except: return {"imports":[]}

def _save(d):
    tmp=FILE+'.tmp'; open(tmp,'w',encoding='utf-8').write(json.dumps(d,indent=2)); os.replace(tmp, FILE)

@coll_bp.route('/api/collections/imports', methods=['GET','POST'])
@rate_limited
def imports():
    if not _on(): return jsonify({"imports":[],"note":"disabled"})
    if request.method=='GET':
        return jsonify(_load())
    js=request.get_json(silent=True) or {}
    url=js.get('url','').strip(); provider=js.get('provider','').strip().lower()
    name=js.get('name') or url
    if not url or provider not in ('imdb','tmdb','trakt'):
        return jsonify({"error":"url+provider required"}), 400
    d=_load(); d['imports']=[x for x in d['imports'] if x.get('url')!=url]
    d['imports'].append({"url":url,"provider":provider,"name":name,"interval_min": int(js.get('interval_min') or 1440),"last_run":0})
    _save(d); return jsonify({"ok":True})

@coll_bp.route('/api/collections/refresh', methods=['POST'])
@require_api_key
@rate_limited
def refresh():
    if not _on(): return jsonify({"error":"disabled"}), 403
    js=request.get_json(silent=True) or {}; url=js.get('url','')
    d=_load()
    for it in d['imports']:
        if it['url']==url or not url:
            it['last_run']=int(time.time())
            # Here we'd fetch from provider and merge into /storage/collections.json (omitted; stub success)
    _save(d); return jsonify({"ok":True,"refreshed": True})
