from flask import Blueprint, jsonify, request
import os, json
from db.sqlite_index import query as sql_query, ensure as sql_ensure
ROOT=os.path.abspath(os.path.join(os.path.dirname(__file__),'..','..'))
STO=os.path.join(ROOT,'storage')
CFG=os.path.join(STO,'config.json')
IDX=os.path.join(STO,'library_index.json')

libsearch_bp = Blueprint('libsearch', __name__)

def _cfg():
    try: return json.load(open(CFG,'r',encoding='utf-8'))
        except Exception: return {}

@libsearch_bp.route('/api/library/search')
def search():
    q=request.args.get('q',''); typ=request.args.get('type'); n=int(request.args.get('n','100') or 100)
    c=_cfg(); use_sql = bool((c.get('db') or {}).get('sqlite_enabled', False))
    if use_sql:
        try:
            sql_ensure()
            items=sql_query(q, typ, n)
            return jsonify({'ok':True,'items': items, 'via':'sqlite'})
        except Exception as e:
            # fallback to JSON
            pass
    try:
        data=json.load(open(IDX,'r',encoding='utf-8'))
    except Exception:
        data=[]
    out=[]
    ql=q.lower()
    for it in data:
        if typ and it.get('type')!=typ: continue
        t=(it.get('title') or '').lower(); p=(it.get('path') or '').lower()
        if (not q) or (ql in t) or (ql in p):
            out.append({'title': it.get('title'), 'path': it.get('path'), 'type': it.get('type'), 'year': it.get('year')})
            if len(out)>=n: break
        return jsonify({'ok':True,'items': out, 'via':'json'})
